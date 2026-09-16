"""Ordered logical records. Mutating helpers return new records."""

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Subfield:
    code: str
    value: str


@dataclass(frozen=True)
class ControlField:
    tag: str
    value: str


@dataclass(frozen=True)
class DataField:
    tag: str
    ind1: str = " "
    ind2: str = " "
    subfields: list[Subfield] = field(default_factory=list)


@dataclass(frozen=True)
class Record:
    leader: str
    fields: list[ControlField | DataField] = field(default_factory=list)

    @property
    def identifier(self) -> str | None:
        return next(
            (f.value for f in self.fields if isinstance(f, ControlField) and f.tag == "001"), None
        )

    def get_fields(self, *tags: str) -> list[ControlField | DataField]:
        return [f for f in self.fields if not tags or f.tag in tags]

    def add_field(self, value: ControlField | DataField, index: int | None = None) -> "Record":
        fields = list(self.fields)
        fields.insert(len(fields) if index is None else index, value)
        return replace(self, fields=fields)

    def remove_fields(self, *tags: str) -> "Record":
        return replace(self, fields=[f for f in self.fields if f.tag not in tags])

    def replace_field(self, index: int, value: ControlField | DataField) -> "Record":
        fields = list(self.fields)
        fields[index] = value
        return replace(self, fields=fields)
