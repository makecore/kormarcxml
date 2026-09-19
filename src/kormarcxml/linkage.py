"""Record-local Appendix A linkage assertions; never reorder or repair data."""

from collections import Counter, defaultdict
import re

from .errors import Issue
from .model import DataField, Record


def validate_linkage(record: Record, config: dict, fields: dict) -> list[Issue]:
    issues: list[Issue] = []
    occurrences: Counter[str] = Counter()
    links: dict[str, list[tuple[DataField, int, str]]] = defaultdict(list)
    groups: dict[str, list[tuple[DataField, int, str | None]]] = defaultdict(list)

    def emit(rule: str, field: DataField, occurrence: int, code: str) -> None:
        spec = config["rules"][rule]
        issues.append(
            Issue(
                spec.get("severity", "error"),
                rule,
                spec["message"],
                record.identifier,
                field.tag,
                occurrence,
                code,
                remediation=spec.get("remediation"),
            )
        )

    for field in record.fields:
        occurrences[field.tag] += 1
        if not isinstance(field, DataField):
            continue
        occurrence = occurrences[field.tag]
        subdefs = fields.get(field.tag, {}).get("subfields", {})
        sixes = [s.value for s in field.subfields if s.code == "6"]
        if field.tag == "880" and not sixes:
            emit("linkage.6.required", field, occurrence, "6")
        if "6" in subdefs or field.tag == "880":
            # Repeated leading aliases are provisionally retained (KX-012).
            seen_data = False
            misplaced = False
            for sub in field.subfields:
                if sub.code == "6":
                    misplaced |= seen_data
                else:
                    seen_data = True
            if misplaced:
                emit("linkage.6.first", field, occurrence, "6")
            bases = set()
            for value in sixes:
                match = re.fullmatch(config["six_pattern"], value, re.ASCII)
                if match is None:
                    emit("linkage.6.syntax", field, occurrence, "6")
                    continue
                target, number, script, _direction = match.groups()
                if script and script not in config["legacy_scripts"]:
                    if script in config["display_scripts"]:
                        emit("decision.KX-013", field, occurrence, "6")
                    elif re.fullmatch(config["iso_script_pattern"], script, re.ASCII):
                        emit("linkage.6.script-unverified", field, occurrence, "6")
                    else:
                        emit("linkage.6.script", field, occurrence, "6")
                if (field.tag != "880" and target != "880") or (
                    field.tag == "880" and (target == "880" or target.startswith("00"))
                ):
                    emit("linkage.6.target", field, occurrence, "6")
                    continue
                if number == "00":
                    if field.tag != "880":
                        emit("linkage.6.unlinked", field, occurrence, "6")
                    continue
                bases.add((target, number))
            if len(bases) > 1:
                emit("linkage.6.alias-conflict", field, occurrence, "6")
            for target, number in sorted(bases):
                links[number].append((field, occurrence, target))
        if "8" not in subdefs or field.tag in config["eight_excluded_tags"]:
            continue
        for sub in field.subfields:
            if sub.code != "8":
                continue
            match = re.fullmatch(config["eight_pattern"], sub.value, re.ASCII)
            if match is None:
                emit("linkage.8.syntax", field, occurrence, "8")
                continue
            number, sequence, separator, kind = match.groups()
            if separator in config["display_separators"]:
                emit("decision.KX-014", field, occurrence, "8")
            if kind is None and field.tag[:2] not in config["eight_type_optional_prefixes"]:
                emit("linkage.8.type-required", field, occurrence, "8")
            if kind is not None and kind not in config["eight_types"]:
                emit("linkage.8.type", field, occurrence, "8")
            if kind in config["eight_sequence_types"] and sequence is None:
                emit("linkage.8.sequence-required", field, occurrence, "8")
            # Arbitrarily long integers need no int conversion or magnitude limit.
            groups[number.lstrip("0") or "0"].append((field, occurrence, sequence))

    for members in links.values():
        regular = [m for m in members if m[0].tag != "880"]
        if len(regular) > 1:
            for field, occurrence, _target in regular:
                emit("linkage.6.occurrence-unique", field, occurrence, "6")
        # Index pairs once; malformed large groups must not trigger quadratic scans.
        pairs: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
        for field, _occurrence, target in members:
            pairs[(field.tag, target)].add((field.ind1, field.ind2))
        for field, occurrence, target in members:
            peer_indicators = pairs.get((target, field.tag), set())
            if not peer_indicators:
                if target not in fields or "6" not in fields[target].get("subfields", {}):
                    emit("linkage.6.peer-unverified", field, occurrence, "6")
                else:
                    emit("linkage.6.reciprocal", field, occurrence, "6")
            elif peer_indicators != {(field.ind1, field.ind2)}:
                emit("linkage.6.indicators", field, occurrence, "6")
    for group in groups.values():
        if any(sequence is not None for _, _, sequence in group):
            for field, occurrence, sequence in group:
                if sequence is None:
                    emit("linkage.8.group-sequence", field, occurrence, "8")
    return issues
