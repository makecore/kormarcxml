"""Independent pymarc ISO 2709 verification; no MARC 21 semantic inference."""

import io

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
)


@pytest.mark.parametrize("text", ["한글 漢字", "e\u0301 é 😀", "line\r\n\t"])
def test_pymarc_origin_round_trip(text):
    source = pymarc.Record(leader="00000nam a2200000   4500", force_utf8=True)
    source.add_field(pymarc.Field(tag="001", data="independent"))
    source.add_field(
        pymarc.Field(
            tag="999",
            indicators=[" ", " "],
            subfields=[pymarc.Subfield("a", text), pymarc.Subfield("a", "repeat")],
        )
    )
    # Interleaved controlfield order is a transport property, no tagging assertion.
    source.add_field(pymarc.Field(tag="008", data=" " * 40))
    source.add_field(
        pymarc.Field(tag="999", indicators=["0", " "], subfields=[pymarc.Subfield("x", "local")])
    )
    original = source.as_marc()
    parsed = decode_record(original)
    assert [f.tag for f in parsed.fields] == ["001", "999", "008", "999"]
    assert parsed.fields[1].subfields == [Subfield("a", text), Subfield("a", "repeat")]
    reloaded = next(iter_xml(io.BytesIO(record_to_xml(parsed))))
    assert encode_record(reloaded) == original


def test_pymarc_checks_euc_kr_directory_byte_offsets():
    source = Record(
        "00000nam  2200000   4500",
        [
            ControlField("001", "id"),
            DataField("245", " ", " ", [Subfield("a", "한글 漢字")]),
            DataField("999", " ", " ", [Subfield("x", "뒤")]),
        ],
    )
    raw = encode_record(source, encoding="euc-kr")
    # Request raw fields: pymarc's MARC-8 decoder is intentionally not used.
    independent = next(pymarc.MARCReader(raw, to_unicode=False))
    assert independent is not None
    assert independent["245"].get_subfields("a") == ["한글 漢字".encode("euc-kr")]
    assert independent["999"].get_subfields("x") == ["뒤".encode("euc-kr")]
    assert independent.as_marc() == raw
