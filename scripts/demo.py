"""Reproduce the release demonstration; all records are synthetic MIT fixtures."""

from __future__ import annotations

from dataclasses import asdict
import io
import json
from pathlib import Path

from kormarcxml import (
    ControlField,
    DataField,
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
from kormarcxml.transforms import transform, report_html
from kormarcxml.validation import validate


def sample(identifier: str = "synthetic-001", kind: str = "a") -> Record:
    leader = list("00000nam a2200000   4500")
    leader[6] = kind
    return Record(
        "".join(leader),
        [
            ControlField("001", identifier),
            ControlField("005", "20260916090000"),
            ControlField("008", "260916s2026    ulk           000   kor  "),
            DataField(
                "245",
                "0",
                "0",
                [
                    Subfield("a", "도서관 데이터"),
                    Subfield("b", "한글 漢字 XML"),
                    Subfield("d", "김예시 지음"),
                ],
            ),
            DataField(
                "260",
                " ",
                " ",
                [Subfield("a", "서울"), Subfield("b", "예시출판사"), Subfield("c", "2026")],
            ),
            DataField("300", " ", " ", [Subfield("a", "123 p.")]),
            DataField("700", "1", " ", [Subfield("a", "김예시")]),
            DataField("700", "1", " ", [Subfield("a", "박예시")]),
            DataField("999", " ", " ", [Subfield("x", "기관 로컬값"), Subfield("x", "반복값")]),
        ],
    )


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "examples"
    out.mkdir(exist_ok=True)
    logical = sample()
    # Construct the fixed field visibly: 40 characters, no implicit truncation.
    if len(logical.fields[2].value) != 40:
        raise AssertionError(f"008 fixture has {len(logical.fields[2].value)} characters")
    raw = encode_record(logical)
    (out / "book.mrc").write_bytes(raw)
    decoded = decode_record(raw)
    xml = record_to_xml(decoded)
    (out / "book.xml").write_bytes(xml)
    assert not schema_validate(xml)
    issues = validate(decoded)
    assert not [i for i in issues if i.severity in ("error", "fatal")], issues
    (out / "validation.json").write_text(
        json.dumps([asdict(i) for i in issues], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "validation.html").write_text(report_html(issues), encoding="utf-8")
    for target, suffix in (
        ("html", "html"),
        ("tagged", "txt"),
        ("dc", "dc.xml"),
        ("mods", "mods.xml"),
        ("json", "json"),
        ("csv", "csv"),
    ):
        (out / f"book.{suffix}").write_text(transform(decoded, target), encoding="utf-8")
    again = next(iter_xml(io.BytesIO(xml)))
    roundtrip = encode_record(again)
    (out / "book-roundtrip.mrc").write_bytes(roundtrip)
    assert decoded == again
    assert raw == roundtrip
    collection = b"".join(
        encode_record(sample(f"synthetic-{n:03d}", kind))
        for n, kind in enumerate(("a", "e", "c", "i", "g", "m"), 1)
    )
    (out / "collection.mrc").write_bytes(collection)
    buffer = io.BytesIO()
    write_xml(iter_iso2709(io.BytesIO(collection)), buffer)
    (out / "collection.xml").write_bytes(buffer.getvalue())
    assert not schema_validate(buffer.getvalue())
    restored = b"".join(encode_record(r) for r in iter_xml(io.BytesIO(buffer.getvalue())))
    assert restored == collection
    legacy = Record(logical.leader[:9] + " " + logical.leader[10:], logical.fields)
    legacy_bytes = encode_record(legacy, encoding="euc-kr")
    legacy_xml = record_to_xml(decode_record(legacy_bytes, encoding="euc-kr"))
    assert encode_record(next(iter_xml(io.BytesIO(legacy_xml))), encoding="euc-kr") == legacy_bytes
    (out / "book-euc-kr.mrc").write_bytes(legacy_bytes)
    (out / "book-euc-kr.xml").write_bytes(legacy_xml)
    result = {
        "synthetic": True,
        "single_record_bytes": len(raw),
        "collection_records": 6,
        "structural_equivalence": True,
        "bibliographic_equivalence": True,
        "codepoint_equivalence": True,
        "ordering_and_repetition": True,
        "indicators_and_fixed_fields": True,
        "utf8_byte_identical": True,
        "euc_kr_byte_identical_with_explicit_codec": True,
        "collection_byte_identical": True,
        "schema_errors": 0,
        "partial_profile_errors": 0,
        "partial_profile_issue_count": len(issues),
        "recalculated": [
            "leader/00-04",
            "leader/12-16",
            "directory lengths and offsets",
            "terminators",
        ],
        "limitation": "Synthetic transport fixtures; material codes do not establish all material-specific content conformance.",
    }
    (out / "demo-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
