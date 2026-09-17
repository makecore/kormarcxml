"""Adversarial transport boundaries: no dropped data or hidden XML expansion."""

import io

import pytest

from kormarcxml import (
    ControlField,
    DataField,
    ParseError,
    Record,
    Subfield,
    decode_record,
    encode_record,
    iter_iso2709,
    iter_xml,
    record_to_xml,
)

NS = "http://www.loc.gov/MARC21/slim"
LEADER = "00000nam a2200000   4500".ljust(24)


def record():
    # Exact leader width/layout, independent of semantic field rules.
    return Record(
        "00000nam a2200000   4500",
        [ControlField("001", "id"), DataField("999", " ", " ", [Subfield("a", "local")])],
    )


def xml_body():
    return record_to_xml(record()).split(b"?>", 1)[1]


@pytest.mark.parametrize(
    "template",
    [
        '<collection xmlns="{ns}" unexpected="data">{body}</collection>',
        '<collection xmlns="{ns}">unexpected{body}</collection>',
        '<collection xmlns="{ns}">{body}unexpected</collection>',
    ],
)
def test_collection_cannot_silently_drop_data(template):
    xml = template.format(ns=NS, body=xml_body().decode()).encode()
    with pytest.raises(ParseError):
        list(iter_xml(io.BytesIO(xml)))


@pytest.mark.parametrize(
    "declaration",
    [
        '<!DOCTYPE record [<!ENTITY secret SYSTEM "file:///etc/passwd">]>',
        '<!DOCTYPE record [<!ENTITY secret "expanded">]>',
        '<!DOCTYPE record SYSTEM "https://invalid.example/no-network.dtd">',
    ],
)
def test_dtd_never_accepted(declaration):
    xml = declaration.encode() + xml_body()
    with pytest.raises(ParseError):
        list(iter_xml(io.BytesIO(xml)))


def test_directory_overlap_rejected():
    data = bytearray(encode_record(record()))
    # Second field points at first field, which has the same terminator offset.
    data[36 + 3 : 36 + 12] = data[24 + 3 : 24 + 12]
    with pytest.raises(ParseError):
        decode_record(bytes(data))


def test_directory_gap_rejected():
    data = bytearray(encode_record(record()))
    # Skip first payload byte while retaining that field's terminator.
    length = int(data[27:31])
    data[27:36] = f"{length - 1:04d}00001".encode()
    with pytest.raises(ParseError):
        decode_record(bytes(data))


def test_directory_physical_order_recovery_is_explicit():
    data = bytearray(encode_record(record()))
    first, second = data[24:36], data[36:48]
    data[24:36], data[36:48] = second, first
    with pytest.raises(ParseError):
        decode_record(bytes(data))
    issues = []
    recovered = decode_record(bytes(data), recover=True, issues=issues)
    assert [f.tag for f in recovered.fields] == ["999", "001"]
    assert any(i.rule_id == "iso.directory_order" for i in issues)
    assert encode_record(recovered) != bytes(data)


class ShortReads(io.BytesIO):
    def read(self, size=-1):
        assert size >= 0, "Streaming codec must use bounded reads"
        return super().read(min(size, 3))


def test_short_read_binary_pipe():
    raw = encode_record(record())
    assert [encode_record(r) for r in iter_iso2709(ShortReads(raw * 3))] == [raw] * 3


def test_short_read_xml_pipe():
    assert list(iter_xml(ShortReads(record_to_xml(record())))) == [record()]


def test_normalization_and_xml_escaping_are_reversible():
    texts = ["\r", "\r\n", "\t", "e\u0301", "\u00e9", '<&>"', "漢字 한글 😀"]
    source = Record(
        record().leader, [DataField("999", " ", " ", [Subfield("a", text) for text in texts])]
    )
    raw = encode_record(source)
    parsed = decode_record(raw)
    again = next(iter_xml(io.BytesIO(record_to_xml(parsed))))
    assert [s.value for s in again.fields[0].subfields] == texts
    assert encode_record(again) == raw


def test_xml_limit_is_per_record_not_collection_chunk():
    body = xml_body()
    xml = b'<collection xmlns="' + NS.encode() + b'">' + body * 20 + b"</collection>"
    assert len(list(iter_xml(io.BytesIO(xml), max_record_bytes=512))) == 20


def test_xml_record_limit_not_reset_by_preceding_record():
    small = xml_body()
    large = record_to_xml(Record(record().leader, [ControlField("001", "x" * 700)]))
    large = large.split(b"?>", 1)[1]
    xml = b'<collection xmlns="' + NS.encode() + b'">' + small + large + b"</collection>"
    with pytest.raises(ParseError, match="limit"):
        list(iter_xml(ShortReads(xml), max_record_bytes=512))


def test_xml_unfinished_record_is_bounded():
    xml = b'<record xmlns="' + NS.encode() + b'"><leader>' + b"x" * 5000
    with pytest.raises(ParseError, match="limit"):
        list(iter_xml(ShortReads(xml), max_record_bytes=512))


def test_xml_limit_must_be_positive():
    with pytest.raises(ValueError):
        list(iter_xml(io.BytesIO(xml_body()), max_record_bytes=0))
