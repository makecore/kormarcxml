import io

import pytest

from kormarcxml import (
    ControlField,
    DataField,
    EncodingError,
    ParseError,
    Record,
    Subfield,
    decode_record,
    encode_record,
    iter_iso2709,
    iter_xml,
    record_to_xml,
    schema_validate,
    write_xml,
)


def sample(text="한글 漢字 Latin e\u0301 😀"):
    return Record(
        "00000nam a2200000   4500",
        [
            ControlField("001", "test"),
            DataField("245", "1", " ", [Subfield("a", text), Subfield("a", "반복")]),
            ControlField("008", " " * 40),
            DataField("999", " ", " ", [Subfield("x", "local")]),
        ],
    )


def test_roundtrip():
    original = encode_record(sample())
    parsed = decode_record(original)
    xml = record_to_xml(parsed)
    assert schema_validate(xml) == []
    again = list(iter_xml(io.BytesIO(xml)))[0]
    assert parsed == again
    assert original == encode_record(again)
    assert parsed.fields == sample().fields
    assert parsed.leader[5:12] == sample().leader[5:12]


def test_euc_kr():
    record = sample("한글 漢字")
    record = Record(record.leader[:9] + " " + record.leader[10:], record.fields)
    with pytest.raises(EncodingError):
        encode_record(record)
    raw = encode_record(record, encoding="euc-kr")
    parsed = decode_record(raw, encoding="euc-kr")
    assert parsed.fields == record.fields
    assert (
        encode_record(list(iter_xml(io.BytesIO(record_to_xml(parsed))))[0], encoding="euc-kr")
        == raw
    )


def test_unrepresentable():
    record = sample()
    record = Record(record.leader[:9] + " " + record.leader[10:], record.fields)
    with pytest.raises(EncodingError):
        encode_record(record, encoding="euc-kr")


def test_batch():
    binary = encode_record(sample()) * 1000
    out = io.BytesIO()
    write_xml(iter_iso2709(io.BytesIO(binary)), out)
    records = iter_xml(io.BytesIO(out.getvalue()))
    assert b"".join(encode_record(r) for r in records) == binary


@pytest.mark.parametrize(
    "mutation",
    [
        lambda b: b[:-1],
        lambda b: b[:24] + b"xxx" + b[27:],
        lambda b: b[:-1] + b"x",
        lambda b: b[:12] + b"99999" + b[17:],
    ],
)
def test_bad_binary(mutation):
    with pytest.raises(ParseError):
        decode_record(mutation(encode_record(sample())))


def test_invalid_bytes():
    raw = encode_record(sample())
    raw = raw.replace("한".encode(), b"\xff\xff\xff", 1)
    with pytest.raises(EncodingError):
        decode_record(raw)
    with pytest.warns(UnicodeWarning):
        rec = decode_record(raw, errors="warn")
    assert "\ufffd" in rec.fields[1].subfields[0].value


@pytest.mark.parametrize(
    "xml",
    [
        b'<!DOCTYPE record [<!ENTITY x SYSTEM "file:///etc/passwd">]><record xmlns="http://www.loc.gov/MARC21/slim"><leader>&x;</leader></record>',
        b'<collection xmlns="http://www.loc.gov/MARC21/slim"><other/></collection>',
        b'<record xmlns="http://www.loc.gov/MARC21/slim"><leader>short</leader><unknown/></record>',
    ],
)
def test_bad_xml(xml):
    with pytest.raises(ParseError):
        list(iter_xml(io.BytesIO(xml)))


def test_xml_invalid_character():
    with pytest.raises(ParseError):
        record_to_xml(sample("\x00"))


def test_xml_codepoints():
    record = sample("line\r\n\t e\u0301")
    assert list(iter_xml(io.BytesIO(record_to_xml(record)))) == [record]


def test_lengths():
    with pytest.raises(ParseError):
        encode_record(sample("x" * 10000))
    with pytest.raises(ParseError):
        list(iter_xml(io.BytesIO(record_to_xml(sample())), max_record_bytes=40))


def test_model_edit():
    r = sample()
    r2 = r.remove_fields("245").add_field(DataField("246", subfields=[Subfield("a", "Title")]))
    assert r.get_fields("245") and not r2.get_fields("245")
    assert r.identifier == "test"


def test_pymarc_transport_crosscheck():
    """Independent ISO 2709 transport check only, not MARC 21 semantics."""
    pymarc = pytest.importorskip("pymarc")
    raw = encode_record(sample())
    other = next(pymarc.MARCReader(raw, to_unicode=True, force_utf8=True))
    assert other is not None
    assert other["001"].data == "test"
    assert other["245"].get_subfields("a") == ["한글 漢字 Latin e\u0301 😀", "반복"]
    assert other.as_marc() == raw
