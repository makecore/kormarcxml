# Library API and extension guide

Examples run after installation from the repository root. Run `python scripts/demo.py`
first to generate the synthetic input files.

## Parse, edit, serialize

```python
import io
from pathlib import Path
from kormarcxml import (
    DataField,
    Subfield,
    decode_record,
    encode_record,
    iter_xml,
    record_to_xml,
    schema_validate,
)
from kormarcxml.validation import validate

original = Path("examples/book.mrc").read_bytes()
record = decode_record(original)
assert record.identifier == "synthetic-001"
titles = record.get_fields("245")
assert titles

# Helpers return a new record; field/subfield lists remain ordered.
updated = record.add_field(DataField("999", " ", " ", [Subfield("a", "기관 메모")]))
updated = updated.replace_field(
    len(updated.fields) - 1, DataField("999", " ", " ", [Subfield("a", "수정한 기관 메모")])
)
without_local = updated.remove_fields("999")  # removes every occurrence of this tag

xml = record_to_xml(record)  # UTF-8 bytes, one record document
assert schema_validate(xml) == []
restored = next(iter_xml(io.BytesIO(xml)))
assert restored == record
assert encode_record(restored) == original  # this canonical fixture, same codec
issues = validate(restored, level=3)
```

A `Record` has a string `leader` and an ordered `fields` list. A `ControlField` has
`tag` and `value`; a `DataField` has `tag`, `ind1`, `ind2`, and ordered `subfields`;
a `Subfield` has `code` and `value`. Use literal space for a blank indicator.
`get_fields()` without tags returns all fields. Indices for edits are zero-based.
Frozen dataclasses do not make nested lists deeply immutable.

## Stream a collection

```python
from kormarcxml import iter_iso2709, write_xml

with open("examples/collection.mrc", "rb") as source:
    with open("examples/api-collection.xml", "wb") as destination:
        write_xml(iter_iso2709(source), destination)
```

`iter_xml` also accepts a binary stream and supports a single record or collection.
Do not collect every yielded record into memory for large jobs. Streams remain
owned by the caller. Parsing does not automatically run the semantic validator.

## Encoding and recovery

```python
from pathlib import Path
from kormarcxml import decode_record, encode_record

raw = Path("examples/book-euc-kr.mrc").read_bytes()
record = decode_record(raw, encoding="euc-kr")
assert encode_record(record, encoding="euc-kr") == raw
```

Supported explicit codecs are `utf-8`, `euc-kr`, `cp949`, and `ascii`. UTF-8 is
selected by default only for the supported Unicode leader case. Encoding labels
must match the bytes; they are not auto-detected. Leader/09 `a` with a non-UTF-8
codec is rejected. Transcoding requires an explicit, deliberate leader change.

`decode_record(..., errors="strict")` is the default. `errors="warn"` and
`errors="replacement"` both replace undecodable bytes and emit a warning; such
results are lossy. Writing supports strict encoding only. `recover=True` permits
the implemented directory-order recovery, reporting issues through an optional
`issues=[]` list; it is not a general repair mode. See [encoding](encoding.md).

## Validate and render reports

```python
from pathlib import Path
from kormarcxml import decode_record, record_to_xml, schema_validate
from kormarcxml.transforms import report_html
from kormarcxml.validation import coverage, validate

record = decode_record(Path("examples/book.mrc").read_bytes())
issues = schema_validate(record_to_xml(record)) + validate(record, level=3)
Path("examples/api-report.html").write_text(report_html(issues), encoding="utf-8")
print(coverage())  # complete=False, implemented tags and source references
```

To validate incoming XML syntax and XSD constraints, pass the original XML bytes
to `schema_validate`; reserializing a parsed record checks the generated document
instead. `validate` accepts only levels 2 and 3. Level 1 is an XML-document check.

Issue objects carry severity, rule ID, message, and applicable context such as
identifier, tag, occurrence, subfield, position, and remediation. Serialize with
`dataclasses.asdict`. Occurrences are one-based; ordinary rule positions are
zero-based character positions. Parse byte offsets and XSD line positions have
different meanings; consult the originating rule.

## Extend the profile

```python
from kormarcxml.validation import validate

institutional = {
    "id": "example-institution-1",
    "fields": {"999": {"repeatable": False}},
}
issues = validate(record, profile=institutional)
```

A profile may be a dictionary or a local JSON-file path. Dictionaries merge
recursively; lists and scalar values replace the base value. Do not label
institutional requirements as official KS rules. Keep their provenance alongside
the profile and test both conforming and failing examples.

For rules that cannot be expressed by the registry, pass callbacks:

```python
from kormarcxml import Issue
from kormarcxml.validation import validate


def require_local_identifier(record):
    if not record.get_fields("999"):
        yield Issue(
            "warning",
            "institution.local-id",
            "Institutional local field 999 is absent",
            record_identifier=record.identifier,
            tag="999",
        )


issues = validate(record, validators=[require_local_identifier])
```

## Transform and add a consumer

```python
from kormarcxml.transforms import (
    from_json,
    register_transform,
    to_json,
    transform,
    transformation_catalog,
)

assert from_json(to_json(record)) == record
print(transformation_catalog())  # includes mapping-loss statements
html = transform(record, "html")
dublin_core = transform(record, "dc")  # lossy crosswalk

register_transform(
    "institution-id",
    lambda record: record.identifier or "",
    limitation="Exports only control number 001; all other data is omitted.",
)
assert transform(record, "institution-id") == record.identifier
```

Registration changes the process-local transform registry and refuses duplicate
names. It is a trusted Python API extension; the CLI has a fixed set of built-in
choices and does not discover installed plugins. `from_json` is an API adapter,
not a CLI input option. Tagged text is display-only, not a reversible parser format.
