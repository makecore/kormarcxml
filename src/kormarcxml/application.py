"""Application-level presence checks, distinct from field content validation."""

from .errors import Issue
from .model import Record


def validate_application(record: Record, config: dict, fields: dict) -> list[Issue]:
    issues: list[Issue] = []
    present = {field.tag for field in record.fields}
    selected = config["leader_levels"].get(record.leader[17:18])
    applicable = config.get("applicable_fields", [])
    if not isinstance(applicable, list) or any(
        not isinstance(tag, str) or tag not in fields for tag in applicable
    ):
        raise ValueError("application.applicable_fields must list tags defined in the profile")

    def emit(rule: str, message: str, tag: str | None = None, severity: str = "error") -> None:
        issues.append(Issue(severity, rule, message, record_identifier=record.identifier, tag=tag))

    if selected is None:
        emit(
            "application.level-unreviewed",
            "Annex application requirements cover Leader/17 blank and 7 only; this level has not been inferred",
            severity="info",
        )
    else:
        unresolved = 0
        for tag, spec in fields.items():
            marker = spec.get("application_levels", {}).get(selected)
            if marker == "M" and tag not in present:
                emit(
                    f"application.{selected}.{tag}.required",
                    f"Field {tag} is mandatory at the selected {selected} level",
                    tag,
                )
            elif marker == "A" and tag not in present:
                if tag in applicable:
                    emit(
                        f"application.{selected}.{tag}.applicable",
                        f"Field {tag} is mandatory given caller-confirmed applicability",
                        tag,
                    )
                else:
                    unresolved += 1
        if unresolved:
            emit(
                "application.applicability-unverified",
                f"Applicability of {unresolved} absent conditional fields cannot be established from absence alone",
                severity="info",
            )
    for rule in config["leader_dependencies"]:
        if all(
            record.leader[int(p) : int(p) + 1] in codes for p, codes in rule["when_leader"].items()
        ):
            for tag in rule["requires"]:
                if tag not in present:
                    emit(rule["id"], rule["message"], tag)
    return issues
