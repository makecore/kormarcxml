"""Extract technical summary facts and XML paths; never infer prose rules.

This is an audit candidate catalog, not an automatically activated validator.
"""

import json
import hashlib
from pathlib import Path
import re

from lxml import html

BASE = "https://librarian.nl.go.kr/kormarc/KSX6006-0/"


# Explicitly reviewed punctuation defects, not a permissive marker parser.
# Exact text guards prevent a changed upstream definition inheriting a stale fix.
REVIEWED_MARKERS = {
    ("031", "s"): "유효성 검증 주기 [반복",
    ("377", "l"): "언어 용어 반복]",
    ("610", "n"): "권차/편차/회차 [반복}",
}


def text(node):
    return " ".join(node.text_content().split())


def extract(path):
    doc = html.parse(str(path))
    headings = doc.xpath("//h3")
    heading = text(headings[0]) if headings else ""
    match = re.match(r"^(\d{3})\s+(.+)", heading)
    if not match:
        return None
    tag, label = match.groups()
    # Material-specific 007/008 pages describe positions, not new fields.
    if not re.search(r"_" + tag + r"\.html$", path.name):
        return None
    flags = doc.xpath('//ul[@class="textbtn"]//img/@alt')
    result = {
        "tag": tag,
        "label": label,
        "source": BASE + "sub/" + path.name,
        "review_status": "summary-extracted; prose review pending",
        "xml": f"m:record/m:{'controlfield' if tag.startswith('00') else 'datafield'}[@tag='{tag}']",
        "obligation_marker": next((s for s in flags if s not in ("반복", "반복불가")), None),
    }
    if "반복불가" in flags:
        result["repeatable"] = False
    elif "반복" in flags:
        result["repeatable"] = True
    indicators = {}
    for listing in doc.xpath(
        '//*[contains(concat(" ", normalize-space(@class), " "), " topJisi ")]//ul[@class="jisi"]/li'
    ):
        title = " ".join(listing.xpath("./strong//text()"))
        index = re.search(r"제\s*([12])\s*지시기호", title)
        if not index:
            continue
        codes = []
        unresolved = []
        for span in listing.xpath("./ul/li/span"):
            raw = text(span)
            if span.get("class") == "charB" or raw == "b/":
                codes.append(" ")
            elif re.fullmatch(r"[0-9a-z]", raw):
                codes.append(raw)
            elif re.fullmatch(r"[0-9]\s*[-–~]\s*[0-9]", raw):
                codes.extend(str(i) for i in range(int(raw[0]), int(raw[-1]) + 1))
            else:
                unresolved.append(raw)
        indicators[index.group(1)] = {
            "values": sorted(set(codes)),
            "unresolved": unresolved,
            "xml": result["xml"] + "/@ind" + index.group(1),
        }
    result["indicators"] = indicators
    subs = {}
    unresolved = []
    for item in doc.xpath(
        '//*[contains(concat(" ", normalize-space(@class), " "), " topJisi ")]'
        '//ul[contains(concat(" ", normalize-space(@class), " "), " abcMark ")]/li'
    ):
        value = text(item)
        if not value or not re.match(r"[▾▼▽$]", value):
            continue  # Section labels are not subfields.
        code = re.match(r"[▾▼▽$]\s*([a-z0-9])(?:\s*-\s*([a-z0-9]))?\s*(.*)", value)
        if not code:
            unresolved.append({"code": None, "reason": "Unrecognized code notation"})
            continue
        first, last, tail = code.groups()
        codes = [chr(n) for n in range(ord(first), ord(last) + 1)] if last else [first]
        repeat = re.search(r"[［\[]\s*(반복불가|반복)\s*[］\]]", tail)
        label = tail[: repeat.start()].strip() if repeat else re.split(r"[［\[]", tail)[0].strip()
        for c in codes:
            entry = {"label": label, "xml": result["xml"] + f"/m:subfield[@code='{c}']"}
            # Ranges inherit related/foreign field semantics; an overlapping
            # code (886$a/$b/$2) has different roles by occurrence.
            if last or c in subs:
                entry["context_dependent"] = True
            elif repeat:
                entry["repeatable"] = repeat.group(1) == "반복"
            elif REVIEWED_MARKERS.get((tag, c)) == tail:
                entry["repeatable"] = True
                entry["label"] = re.sub(r"\s*[［\[]?반복[］\]}]?\s*$", "", tail).strip()
                entry["review"] = {
                    "status": "reviewed-explicit-word; malformed-bracket",
                    "source_marker": tail,
                    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "reason": "The explicit repetition word is intact; only its enclosing punctuation is malformed.",
                    "scope": "summary repetition marker only; no prose certification",
                }
            else:
                unresolved.append({"code": c, "reason": "Missing or malformed repetition marker"})
            subs[c] = entry
    overrides = json.loads(
        (Path(__file__).resolve().parents[1] / "research/source-overrides.json").read_text(
            encoding="utf-8"
        )
    )["fields"].get(tag)
    if overrides and hashlib.sha256(path.read_bytes()).hexdigest() == overrides["source_sha256"]:
        for c, patch in overrides["subfields"].items():
            entry = subs.setdefault(c, {"xml": result["xml"] + f"/m:subfield[@code='{c}']"})
            entry.update(patch)
            entry["review"]["source_sha256"] = overrides["source_sha256"]
    result["subfields"] = subs
    result["unresolved_summary_items"] = unresolved
    return result


def main():
    fields = [
        item
        for path in sorted(Path(".audit-cache/sub").glob("*.html"))
        if (item := extract(path)) is not None
    ]
    # Annex 9 is the complete tag inventory including definitions delegated to
    # the holdings standard. Preserve its M/A/O markers without inventing policy.
    annex = html.parse(".audit-cache/sub/annex_9.html")
    by_tag = {f["tag"]: f for f in fields}
    for row in annex.xpath("//tr"):
        cells = [text(cell) for cell in row.xpath("./td|./th")]
        if len(cells) != 4 or not re.fullmatch(r"[0-9]{3}", cells[0]):
            continue
        tag, label, full, minimal = cells
        if tag not in by_tag:
            by_tag[tag] = {
                "tag": tag,
                "label": label,
                "source": BASE + "sub/841_89X_overview.html",
                "review_status": "Definition delegated to KS X 6006-5; transport only",
                "definition_scope": "holdings-delegated",
                "xml": f"m:record/m:datafield[@tag='{tag}']",
                "obligation_marker": None,
                "indicators": {},
                "subfields": {},
                "unresolved_summary_items": [
                    {"code": None, "reason": "Detailed definition belongs to holdings standard"}
                ],
            }
        by_tag[tag]["application_levels"] = {
            "full": full,
            "minimal": minimal,
            "source": BASE + "sub/annex_9.html",
        }
    fields = sorted(by_tag.values(), key=lambda f: f["tag"])
    output = {
        "standard": "KS X 6006-0:2023",
        "complete": False,
        "namespace": {"m": "http://www.loc.gov/MARC21/slim"},
        "status": "Technical summary extraction; not full semantic review or crosswalk certification",
        "fields": fields,
    }
    Path("research/field-catalog.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# KORMARC → XML 필드 대응표",
        "",
        "공식 페이지의 기술 요약에서 생성한 대응표입니다. 세부 본문·조건·예외까지 검증 완료했다는 뜻이 아닙니다.",
        "모든 값과 반복 순서는 그대로 보존합니다. `m`은 MARCXML namespace입니다.",
        "",
        "| 필드 | 명칭 | 반복 | 식별기호 | 완전/최소 수준 | 검토 범위 | XML 경로 | 공식 출처 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in fields:
        lines.append(
            f"| {f['tag']} | {f['label']} | {f.get('repeatable', '미추출')} | {' '.join(f['subfields']) or ('소장규격 위임' if f.get('definition_scope') else '해당없음')} | {f.get('application_levels', {}).get('full', '?')}/{f.get('application_levels', {}).get('minimal', '?')} | {'소장규격 위임' if f.get('definition_scope') else '기술 요약; 본문 미완료'} | `{f['xml']}` | [원문]({f['source']}) |"
        )
    Path("docs/field-mapping.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("fields", len(fields), "subfields", sum(len(f["subfields"]) for f in fields))


if __name__ == "__main__":
    main()
