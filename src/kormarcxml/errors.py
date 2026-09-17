"""Stable, serializable diagnostic model shared by parsers and validators."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Issue:
    severity: str
    rule_id: str
    message: str
    record_identifier: str | None = None
    tag: str | None = None
    occurrence: int | None = None
    subfield: str | None = None
    position: int | None = None
    remediation: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class KormarcError(ValueError):
    """Base exception. The diagnostic is available through .issue."""

    def __init__(self, message: str, rule_id: str = "parse.invalid", **context):
        super().__init__(message)
        self.issue = Issue("fatal", rule_id, message, **context)


class ParseError(KormarcError):
    pass


class EncodingError(KormarcError):
    pass
