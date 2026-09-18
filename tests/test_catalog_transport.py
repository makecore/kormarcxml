"""Exercise every catalogued field/subfield through the actual XML/ISO codecs.

These synthetic values establish transport preservation, not cataloging validity.
Pymarc independently checks the directory and ordered logical data.
"""

import io
import json
from pathlib import Path

from lxml import etree
import pymarc
import pytest

from kormarcxml import (
    ControlField,
    DataField,
    Record,
    Subfield,
    decode_record,
    encode_record,
    iter_xml,
    record_to_xml,
    schema_validate,
)

CATALOG = json.loads(
    (Path(__file__).resolve().parents[1] / "research/field-catalog.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("spec", CATALOG["fields"], ids=lambda spec: spec["tag"])
def test_each_documented_field_and_subfield_survives_xml_and_iso(spec):
    tag = spec["tag"]
    if tag.startswith("00"):
        field = ControlField(tag, "한글 漢字 e\u0301 ")
    else:
        indicators = [spec["indicators"].get(str(i), {}).get("values") or [" "] for i in (1, 2)]
        subs = []
        for code, item in spec["subfields"].items():
            for repeat in range(2 if item.get("repeatable") else 1):
                subs.append(Subfield(code, f"{tag}:{code}:{repeat}:한글 漢字 e\u0301 "))
        field = DataField(tag, indicators[0][0], indicators[1][0], subs)
    source = Record("00000nam a2200000   4500", [field])
    raw = encode_record(source)
    parsed = decode_record(raw)
    xml = record_to_xml(parsed)
    assert schema_validate(xml) == []
    root = etree.fromstring(xml)
    # Verify published XPath addresses the real serialized field and every code.
    assert root.getroottree().xpath("//" + spec["xml"], namespaces=CATALOG["namespace"])
    for code, sub in spec["subfields"].items():
        nodes = root.getroottree().xpath("//" + sub["xml"], namespaces=CATALOG["namespace"])
        assert [n.text for n in nodes] == [s.value for s in field.subfields if s.code == code]
    again = next(iter_xml(io.BytesIO(xml)))
    assert again.fields == source.fields
    assert encode_record(again) == raw
    independent = next(pymarc.MARCReader(raw, force_utf8=True))
    assert independent is not None
    assert independent.as_marc() == raw
    if isinstance(field, DataField):
        assert [(s.code, s.value) for s in independent.fields[0].subfields] == [
            (s.code, s.value) for s in field.subfields
        ]
    else:
        assert independent.fields[0].data == field.value
