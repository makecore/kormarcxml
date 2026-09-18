"""Three-level validation: XSD is in xmlio; this module implements levels 2/3.

The JSON registry is the semantic source of truth. Unknown fields are reported,
not discarded or asserted invalid. Institutional profiles can extend the registry.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from copy import deepcopy
from datetime import datetime
from importlib.resources import files
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

from .errors import Issue
from .model import ControlField, DataField, Record

Validator = Callable[[Record], Iterable[Issue]]


def _merge(base: dict, update: dict) -> dict:
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = deepcopy(value)
    return base


@lru_cache(maxsize=1)
def _bundled_registry() -> dict[str, Any]:
    # Private read-only use; public callers always receive an independent copy.
    path = files("kormarcxml").joinpath("resources/rules/bibliographic.json")
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(profile: str | Path | dict | None = None) -> dict[str, Any]:
    """Load the bundled bibliography subset and optionally merge local JSON.

    Dictionary keys merge recursively; lists and scalar values replace. A custom
    profile is trusted configuration, never code and never a remotely fetched URL.
    """
    registry = deepcopy(_bundled_registry())
    if profile is None or profile == "bibliographic":
        return registry
    extra = profile if isinstance(profile, dict) else json.loads(Path(profile).read_text("utf-8"))
    if not isinstance(extra, dict):
        raise ValueError("A profile must be a JSON object")
    return _merge(registry, extra)


def coverage(profile: str | Path | dict | None = None) -> dict:
    """Return explicit implemented coverage; this is not full KS conformance."""
    registry = (
        _bundled_registry()
        if profile is None or profile == "bibliographic"
        else load_registry(profile)
    )

    # Count executable assertion templates, not metadata keys or permitted
    # repetition declarations (which cannot produce a violation).
    def count_field(specification: dict) -> int:
        count = int(bool(specification.get("required")))
        count += int(specification.get("repeatable") is False)
        count += len(specification.get("rules", []))
        count += sum(value is not None for value in specification.get("indicators", {}).values())
        count += int(bool(specification.get("closed_subfields")))
        count += len(specification.get("conditions", []))
        for sub in specification.get("subfields", {}).values():
            count += int(bool(sub.get("required")))
            count += int(sub.get("repeatable") is False)
            count += len(sub.get("rules", []))
        return count

    field_counts = {tag: count_field(spec) for tag, spec in registry["fields"].items()}
    return {
        "profile": registry["id"],
        "standard": registry["standard"],
        "complete": False,
        "fields": sorted(registry["fields"]),
        "leader_rules": len(registry.get("leader", [])),
        "field_rules": sum(field_counts.values()),
        "field_rule_counts": field_counts,
        "fields_without_constraints": sorted(
            tag for tag, count in field_counts.items() if not count
        ),
        "counting_basis": "Executable assertion templates; excludes metadata and generic transport checks",
        "provenance": registry.get("provenance", {}),
        "sources": registry.get("sources", {}),
    }


def validate(
    record: Record,
    level: int = 3,
    profile: str | Path | dict | None = None,
    *,
    validators: Iterable[Validator] = (),
) -> list[Issue]:
    """Validate an ordered record without modifying it.

    Level 2 checks structure/tagging; level 3 adds content/coded values. Level 1
    requires XML bytes and must use xmlio.schema_validate instead of this API.
    Occurrences are one-based, positions are zero-based character positions.
    """
    if level not in (2, 3):
        raise ValueError(
            "Record validation level must be 2 or 3; use XML XSD validation for level 1"
        )
    registry = (
        _bundled_registry()
        if profile is None or profile == "bibliographic"
        else load_registry(profile)
    )
    issues: list[Issue] = []

    def emit(rule_id: str, message: str, severity: str = "error", **context: Any) -> None:
        issues.append(
            Issue(severity, rule_id, message, record_identifier=record.identifier, **context)
        )

    def check_value(value: str, rule: dict, **context: Any) -> None:
        if rule.get("level", 3) > level:
            return
        start = rule.get("start", 0)
        end = rule.get("end", len(value))
        part = value[start:end]
        # Python slices silently truncate: absent required positions must not
        # satisfy a forbidden-character or permissive pattern rule.
        valid = start <= len(value) and ("end" not in rule or end <= len(value))
        if "length" in rule:
            valid = valid and len(value) == rule["length"]
        if "values" in rule:
            valid = valid and part in rule["values"]
        if "pattern" in rule:
            valid = valid and re.fullmatch(rule["pattern"], part, flags=re.ASCII) is not None
        if "forbidden" in rule:
            valid = valid and not any(character in part for character in rule["forbidden"])
        if rule.get("date_format") and valid:
            try:
                datetime.strptime(part, rule["date_format"])
            except ValueError:
                valid = False
        if not valid:
            emit(
                rule["id"],
                rule["message"],
                rule.get("severity", "error"),
                position=start,
                remediation=rule.get("remediation"),
                **context,
            )

    def check_delimiters(value: str, **context: Any) -> None:
        position = next(
            (index for index, character in enumerate(value) if character in "\x1d\x1e\x1f"), None
        )
        if position is not None:
            emit(
                "structure.delimiter",
                "Field text contains a reserved ISO 2709 delimiter",
                position=position,
                remediation="Review and explicitly repair the text before ISO 2709 serialization",
                **context,
            )

    for rule in registry.get("leader", []):
        check_value(record.leader, rule)
    counts = Counter(f.tag for f in record.fields)
    for tag, specification in registry["fields"].items():
        if specification.get("required") and not counts[tag]:
            emit(f"field.{tag}.required", f"Required field {tag} is absent", tag=tag)
        if specification.get("repeatable") is False and counts[tag] > 1:
            emit(f"field.{tag}.repeatability", f"Field {tag} is not repeatable", tag=tag)
    occurrences: Counter = Counter()
    for field in record.fields:
        occurrences[field.tag] += 1
        context: dict[str, Any] = {"tag": field.tag, "occurrence": occurrences[field.tag]}
        if re.fullmatch(r"[0-9]{3}", field.tag) is None or field.tag == "000":
            emit(
                "structure.tag",
                "A field tag must contain three ASCII digits and cannot be 000",
                **context,
            )
        control_tag = field.tag.startswith("00")
        if control_tag != isinstance(field, ControlField):
            emit(
                "structure.field-kind",
                "00X fields require controlfield; other tags require datafield",
                **context,
            )
        specification = registry["fields"].get(field.tag)
        if specification is None:
            emit(
                "coverage.local-field"
                if field.tag.startswith("9")
                else "coverage.unverified-field",
                "Field is preserved; no field-specific semantic rules are bundled for this tag",
                "info" if field.tag.startswith("9") else "warning",
                **context,
            )
            specification = {}
        if specification.get("definition_scope") == "holdings-delegated":
            emit(
                "coverage.delegated-holdings",
                "Detailed rules are delegated to KS X 6006-5; bibliographic profile preserves this field without verifying holdings semantics",
                "warning",
                **context,
            )
        if isinstance(field, ControlField):
            check_delimiters(field.value, **context)
            for rule in specification.get("rules", []):
                check_value(field.value, rule, **context)
        elif isinstance(field, DataField):
            for index, indicator in enumerate((field.ind1, field.ind2), start=1):
                if len(indicator) != 1 or re.fullmatch(r"[ -~]", indicator) is None:
                    emit(
                        "structure.indicator",
                        "Indicators must be one printable ASCII character; blank is a space",
                        **context,
                    )
                allowed = specification.get("indicators", {}).get(str(index))
                if allowed is not None and indicator not in allowed:
                    emit(
                        f"field.{field.tag}.indicator{index}",
                        f"Indicator {index} is not allowed by the selected profile",
                        **context,
                    )
            subcounts = Counter(s.code for s in field.subfields)
            subspecs = specification.get("subfields", {})
            for condition in specification.get("conditions", []):
                if condition.get("level", 3) > level:
                    continue
                indicator = field.ind1 if condition.get("indicator") == 1 else field.ind2
                applies = indicator == condition["equals"]
                if condition.get("negate"):
                    applies = not applies
                if applies:
                    missing = any(not subcounts[code] for code in condition.get("requires", []))
                    forbidden = any(subcounts[code] for code in condition.get("forbids", []))
                    if missing or forbidden:
                        emit(
                            condition["id"],
                            condition["message"],
                            condition.get("severity", "error"),
                            remediation=condition.get("remediation"),
                            **context,
                        )
            for code, subrules in subspecs.items():
                if subrules.get("repeatable") is False and subcounts[code] > 1:
                    emit(
                        f"field.{field.tag}.subfield.{code}.repeatability",
                        "Subfield is not repeatable",
                        subfield=code,
                        **context,
                    )
                if subrules.get("required") and not subcounts[code]:
                    emit(
                        f"field.{field.tag}.subfield.{code}.required",
                        "Required subfield is absent",
                        subfield=code,
                        **context,
                    )
            for sub in field.subfields:
                check_delimiters(sub.value, subfield=sub.code, **context)
                if re.fullmatch(r"[0-9a-z]", sub.code) is None:
                    emit(
                        "structure.subfield-code",
                        "Subfield code must be one lowercase ASCII letter or digit",
                        subfield=sub.code,
                        **context,
                    )
                if specification.get("closed_subfields") and sub.code not in subspecs:
                    emit(
                        f"field.{field.tag}.subfield.allowed",
                        "Subfield is not defined for this field in the selected profile",
                        subfield=sub.code,
                        **context,
                    )
                for rule in subspecs.get(sub.code, {}).get("rules", []):
                    check_value(sub.value, rule, subfield=sub.code, **context)
    for custom_validator in validators:
        issues.extend(custom_validator(record))
    return issues
