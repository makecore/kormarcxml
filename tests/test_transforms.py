import csv
import io
import json

import pytest
from lxml import etree

from kormarcxml.model import ControlField, DataField, Record, Subfield
from kormarcxml.transforms import (
    DC,
    MODS,
    from_json,
    register_transform,
    report_html,
    to_json,
    transform,
    transformation_catalog,
)


@pytest.fixture
def record():
    return Record(
        "00000nam a2200000   4500",
        [
            ControlField("001", "synthetic-1"),
            DataField(
                "245",
                "0",
                "0",
                [
                    Subfield("a", "<script>alert(1)</script> 한글 漢字 e\u0301"),
                    Subfield("b", "부제"),
                    Subfield("d", "김사서 지음"),
                    Subfield("e", "이사서 옮김"),
                ],
            ),
            DataField("100", "1", " ", [Subfield("a", "김사서")]),
            DataField(
                "260",
                " ",
                " ",
                [Subfield("a", "서울"), Subfield("b", "가상출판사"), Subfield("c", "2023")],
            ),
            DataField("999", " ", " ", [Subfield("a", "=1+1"), Subfield("a", "repeat\nline")]),
            DataField("999", " ", " ", []),
        ],
    )


def test_json_order_repeats_codepoints(record):
    assert from_json(to_json(record)) == record
    assert "\u0301" in to_json(record)


@pytest.mark.parametrize("target", ["dc", "mods"])
def test_crosswalk_safe_xml(record, target):
    root = etree.fromstring(transform(record, target).encode())
    assert root.xpath("string(.)").find("김사서") >= 0
    assert not root.xpath('//*[local-name()="script"]')


def test_dc_responsibility_not_agent(record):
    root = etree.fromstring(transform(record, "dc").encode())
    assert root.findall(f"{{{DC}}}creator")[0].text == "김사서"
    assert "김사서 지음" in [n.text for n in root.findall(f"{{{DC}}}description")]
    assert "이사서 옮김" not in [n.text for n in root.findall(f"{{{DC}}}contributor")]


def test_mods_responsibility_note(record):
    root = etree.fromstring(transform(record, "mods").encode())
    assert root.find(f"{{{MODS}}}note").text == "김사서 지음"
    assert root.find(f"{{{MODS}}}titleInfo/{{{MODS}}}subTitle").text == "부제"


def test_html_escapes_and_inspects(record):
    output = transform(record, "html")
    assert "<script>" not in output
    assert "&lt;script&gt;" in output
    assert "원시 논리 구조" in output
    assert "표제와 책임표시사항" in output
    assert "kormarcxml-record-1" in output


def test_tagged_blank_repeated_local(record):
    output = transform(record, "tagged")
    assert "=999  ##$a=1+1$a" in output
    assert output.count("=999") == 2


def test_csv_quotes_and_order(record):
    rows = list(csv.DictReader(io.StringIO(transform(record, "csv"))))
    local = [r for r in rows if r["tag"] == "999"]
    assert [r["value"] for r in local] == ["=1+1", "repeat\nline", ""]
    assert local[1]["subfield_index"] == "1"


def test_report_escapes():
    output = report_html([{"severity": "error", "rule_id": "K-test", "message": "<script>"}])
    assert "<script>" not in output
    assert "&lt;script&gt;" in output


def test_extensions(record):
    register_transform(
        "test-institution", lambda r: r.identifier or "", limitation="Identifier only"
    )
    assert transform(record, "test-institution") == "synthetic-1"
    with pytest.raises(ValueError):
        register_transform("json", to_json, limitation="none")
    assert transformation_catalog()["test-institution"] == "Identifier only"
    with pytest.raises(ValueError, match="Unsupported"):
        transform(record, "bibframe")


def test_json_rejects_silent_extra_data(record):
    obj = json.loads(to_json(record))
    obj["fields"][0]["extra"] = "must not discard"
    with pytest.raises(ValueError):
        from_json(json.dumps(obj))


def test_bundled_xslt_matches_python(record):
    from importlib.resources import files
    from kormarcxml.xmlio import record_to_xml

    stylesheet = files("kormarcxml").joinpath("stylesheets/tagged.xsl").read_bytes()
    processor = etree.XSLT(
        etree.fromstring(stylesheet), access_control=etree.XSLTAccessControl.DENY_ALL
    )
    xml = record_to_xml(record)
    if isinstance(xml, str):
        xml = xml.encode()
    output = str(processor(etree.fromstring(xml)))
    assert output == transform(record, "tagged")
    assert transform(record, "raw") == transform(record, "json")
