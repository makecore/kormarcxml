"""Explicitly scoped metadata crosswalks and safe, independent presentations."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, is_dataclass
from typing import Any

from lxml import etree

from .model import ControlField, DataField, Record, Subfield

DC = "http://purl.org/dc/elements/1.1/"
OAI_DC = "http://www.openarchives.org/OAI/2.0/oai_dc/"
MODS = "http://www.loc.gov/mods/v3"
LABELS = {
    "001": "제어번호",
    "005": "최종처리일시",
    "008": "부호화정보필드",
    "020": "국제표준도서번호",
    "100": "기본표목: 개인명",
    "245": "표제와 책임표시사항",
    "250": "판사항",
    "260": "발행사항",
    "300": "형태사항",
    "500": "일반주기",
    "650": "주제명",
    "700": "부출표목: 개인명",
}


def values(record: Record, tags: tuple[str, ...], codes: str) -> list[str]:
    return [
        s.value
        for f in record.get_fields(*tags)
        if isinstance(f, DataField)
        for s in f.subfields
        if s.code in codes
    ]


def to_json(record: Record) -> str:
    """Ordered logical representation; no directory bytes or encoding provenance."""
    fields = []
    for f in record.fields:
        item = asdict(f)
        item["kind"] = "control" if isinstance(f, ControlField) else "data"
        fields.append(item)
    return json.dumps(
        {"format": "kormarcxml-record-1", "leader": record.leader, "fields": fields},
        ensure_ascii=False,
        indent=2,
    )


def from_json(text: str) -> Record:
    """Strict shape checks prevent silent dropping of unknown JSON properties."""
    obj = json.loads(text)
    if not isinstance(obj, dict) or set(obj) != {"format", "leader", "fields"}:
        raise ValueError("Expected versioned record object with leader and fields")
    if obj["format"] != "kormarcxml-record-1" or not isinstance(obj["leader"], str):
        raise ValueError("Unsupported JSON format or leader")
    if not isinstance(obj["fields"], list):
        raise ValueError("fields must be an ordered array")
    fields: list[ControlField | DataField] = []
    for f in obj["fields"]:
        if not isinstance(f, dict) or not isinstance(f.get("tag"), str):
            raise ValueError("Invalid field")
        if f.get("kind") == "control" and set(f) == {"kind", "tag", "value"}:
            if not isinstance(f["value"], str):
                raise ValueError("Field value must be string")
            fields.append(ControlField(f["tag"], f["value"]))
        elif f.get("kind") == "data" and set(f) == {"kind", "tag", "ind1", "ind2", "subfields"}:
            if not all(isinstance(f[k], str) for k in ("ind1", "ind2")) or not isinstance(
                f["subfields"], list
            ):
                raise ValueError("Invalid datafield shape")
            subs = []
            for s in f["subfields"]:
                if (
                    not isinstance(s, dict)
                    or set(s) != {"code", "value"}
                    or not all(isinstance(v, str) for v in s.values())
                ):
                    raise ValueError("Invalid subfield shape")
                subs.append(Subfield(s["code"], s["value"]))
            fields.append(DataField(f["tag"], f["ind1"], f["ind2"], subs))
        else:
            raise ValueError("Unsupported field properties or kind")
    return Record(obj["leader"], fields)


def tagged(record: Record) -> str:
    """Display only: literal # and $ are ambiguous; do not ingest this view."""
    lines = ["=LDR  " + record.leader]
    for f in record.fields:
        if isinstance(f, ControlField):
            lines.append(f"={f.tag}  {f.value}")
        else:
            lines.append(
                f"={f.tag}  {f.ind1.replace(' ', '#')}{f.ind2.replace(' ', '#')}"
                + "".join("$" + s.code + s.value for s in f.subfields)
            )
    return "\n".join(lines) + "\n"


def _page(title: str) -> tuple[Any, Any]:
    root = etree.Element("html", lang="ko")
    head = etree.SubElement(root, "head")
    etree.SubElement(head, "meta", charset="utf-8")
    etree.SubElement(head, "meta", name="viewport", content="width=device-width, initial-scale=1")
    etree.SubElement(head, "title").text = title
    etree.SubElement(head, "style").text = (
        'body{font-family:"Noto Sans KR",sans-serif;max-width:70rem;'
        "margin:2rem auto;padding:1rem;color:#17212b}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ccc;padding:.5rem;text-align:left;vertical-align:top}"
        "pre,td{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}"
    )
    body = etree.SubElement(root, "body")
    etree.SubElement(body, "h1").text = title
    return root, body


def _html(root: Any) -> str:
    return "<!DOCTYPE html>\n" + etree.tostring(root, encoding="unicode", method="html")


def to_html(record: Record) -> str:
    root, body = _page("KORMARC 레코드 보기")
    etree.SubElement(
        body, "p"
    ).text = "비공식 오픈소스 프레임워크 · 공백 지시기호는 #으로 표시합니다."
    table = etree.SubElement(body, "table")
    tr = etree.SubElement(table, "tr")
    for heading in ("필드", "표시기호명", "내용"):
        etree.SubElement(tr, "th", scope="col").text = heading
    for field in record.fields:
        tr = etree.SubElement(table, "tr")
        etree.SubElement(tr, "td").text = field.tag
        etree.SubElement(tr, "td").text = LABELS.get(
            field.tag, "로컬 필드" if field.tag.startswith("9") else "필드"
        )
        etree.SubElement(tr, "td").text = (
            field.value
            if isinstance(field, ControlField)
            else f"[{field.ind1.replace(' ', '#')}{field.ind2.replace(' ', '#')}] "
            + " ".join(f"▾{s.code} {s.value}" for s in field.subfields)
        )
    details = etree.SubElement(body, "details")
    etree.SubElement(details, "summary").text = "원시 논리 구조 검사 (Leader 포함)"
    etree.SubElement(details, "pre").text = to_json(record)
    return _html(root)


def report_html(issues: Iterable[Any]) -> str:
    root, body = _page("KORMARC 검증 보고서")
    table = etree.SubElement(body, "table")
    keys = (
        "severity",
        "rule_id",
        "record_identifier",
        "tag",
        "occurrence",
        "subfield",
        "message",
        "remediation",
    )
    header = etree.SubElement(table, "tr")
    for key in keys:
        etree.SubElement(header, "th", scope="col").text = key
    for issue in issues:
        item = asdict(issue) if is_dataclass(issue) and not isinstance(issue, type) else dict(issue)
        row = etree.SubElement(table, "tr")
        for key in keys:
            value = item.get(key)
            if key == "record_identifier":
                value = item.get(key, item.get("record_id"))
            if key == "remediation":
                value = item.get(key, item.get("suggested_remediation"))
            etree.SubElement(row, "td").text = "" if value is None else str(value)
    return _html(root)


def _xml(root: Any) -> str:
    return etree.tostring(root, encoding="unicode", pretty_print=True)


def to_dc(record: Record) -> str:
    """Conservative, lossy simple Dublin Core. No inferred names from 245$d/e."""
    root = etree.Element(f"{{{OAI_DC}}}dc", nsmap={"oai_dc": OAI_DC, "dc": DC})
    mappings = [
        ("title", ("245",), "abnp"),
        ("creator", ("100", "110", "111"), "a"),
        ("contributor", ("700", "710", "711"), "a"),
        ("publisher", ("260",), "b"),
        ("date", ("260",), "c"),
        ("description", ("500", "520"), "a"),
        ("identifier", ("020", "022"), "a"),
    ]
    for name, tags, codes in mappings:
        for f in record.get_fields(*tags):
            if isinstance(f, DataField):
                vals = [s.value for s in f.subfields if s.code in codes]
                if vals:
                    etree.SubElement(root, f"{{{DC}}}{name}").text = " ".join(vals)
    for responsibility in values(record, ("245",), "de"):
        etree.SubElement(root, f"{{{DC}}}description").text = responsibility
    if record.identifier is not None:
        etree.SubElement(root, f"{{{DC}}}identifier").text = record.identifier
    return _xml(root)


def to_mods(record: Record) -> str:
    """Conservative MODS 3.8 subset; responsibility stays a transcription note."""
    root = etree.Element(f"{{{MODS}}}mods", nsmap={None: MODS}, version="3.8")

    def child(parent: Any, name: str, value: str | None = None, **attrs: str) -> Any:
        node = etree.SubElement(parent, f"{{{MODS}}}{name}", **attrs)
        node.text = value
        return node

    for f in record.get_fields("245"):
        if isinstance(f, DataField):
            title = child(root, "titleInfo")
            for s in f.subfields:
                if s.code in "abnp":
                    child(
                        title,
                        {"a": "title", "b": "subTitle", "n": "partNumber", "p": "partName"}[s.code],
                        s.value,
                    )
            for s in f.subfields:
                if s.code in "de":
                    child(root, "note", s.value, type="statement of responsibility")
    for tag in ("100", "110", "111", "700", "710", "711"):
        for value in values(record, (tag,), "a"):
            node = child(
                root,
                "name",
                type={"00": "personal", "10": "corporate", "11": "conference"}[tag[1:]],
            )
            child(node, "namePart", value)
    for f in record.get_fields("260"):
        if isinstance(f, DataField):
            origin = child(root, "originInfo")
            for s in f.subfields:
                if s.code == "a":
                    child(child(origin, "place"), "placeTerm", s.value, type="text")
                elif s.code in "bc":
                    child(origin, "publisher" if s.code == "b" else "dateIssued", s.value)
    for value in values(record, ("020",), "a"):
        child(root, "identifier", value, type="isbn")
    for value in values(record, ("500",), "a"):
        child(root, "note", value)
    if record.identifier is not None:
        child(child(root, "recordInfo"), "recordIdentifier", record.identifier)
    return _xml(root)


def to_csv(record: Record) -> str:
    """Long-form logical fields for analysis, not spreadsheet formula execution."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(
        ("record_id", "field_index", "tag", "ind1", "ind2", "subfield_index", "code", "value")
    )
    for index, f in enumerate(record.fields):
        if isinstance(f, ControlField):
            writer.writerow((record.identifier, index, f.tag, "", "", "", "", f.value))
        elif not f.subfields:
            writer.writerow((record.identifier, index, f.tag, f.ind1, f.ind2, "", "", ""))
        else:
            for subindex, s in enumerate(f.subfields):
                writer.writerow(
                    (record.identifier, index, f.tag, f.ind1, f.ind2, subindex, s.code, s.value)
                )
    return out.getvalue()


_TRANSFORMS: dict[str, Callable[[Record], str]] = {
    "tagged": tagged,
    "html": to_html,
    "json": to_json,
    "dc": to_dc,
    "mods": to_mods,
    "csv": to_csv,
    "inspect": to_json,
    "raw": to_json,
}
_LIMITATIONS = {
    "tagged": "Display only; delimiters are ambiguous; blank indicators displayed as #.",
    "html": "Presentation only; raw ordered JSON is embedded for inspection.",
    "json": "Preserves the logical model exactly, not source bytes or encoding provenance.",
    "raw": "Preserves the logical model exactly, not source bytes or encoding provenance.",
    "inspect": "Preserves the logical model exactly, not source bytes or encoding provenance.",
    "dc": "Lossy subset; omitted fields, flattened title parts and names; responsibility retained as description.",
    "mods": "Lossy subset; no authority reconciliation, name roles, fixed codes or unlisted fields.",
    "csv": "Analysis rows omit Leader and physical encoding; not an interchange format; cell text is unmodified.",
}


def register_transform(name: str, transformer: Callable[[Record], str], *, limitation: str) -> None:
    """Register a consumer explicitly. Existing names cannot be shadowed."""
    if not name or name in _TRANSFORMS or not limitation.strip() or not callable(transformer):
        raise ValueError("Unique nonempty name, callable, and loss statement required")
    _TRANSFORMS[name] = transformer
    _LIMITATIONS[name] = limitation


def transformation_catalog() -> Mapping[str, str]:
    return dict(_LIMITATIONS)


def transform(record: Record, target: str) -> str:
    if target not in _TRANSFORMS:
        raise ValueError(
            f"Unsupported transformation: {target}; available: {', '.join(_TRANSFORMS)}"
        )
    return _TRANSFORMS[target](record)
