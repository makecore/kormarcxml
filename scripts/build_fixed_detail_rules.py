"""Generate reviewed multi-position/undefined fixed-field constraints.

Input is the pinned official HTML cache. This does not infer full semantic rules
from headings: only the explicitly selected clauses documented in the audit.
"""

import hashlib
import json
from pathlib import Path
import re

from lxml import html

from build_material_rules import BASE, MATERIALS, POSITIONS_006

CACHE = Path(".audit-cache/sub")
OUTPUT = Path("src/kormarcxml/resources/rules/fixed-details.json")


def code_list(page, start):
    tree = html.parse(str(CACHE / page))
    table = tree.xpath('//*[@id="contentsWrap"]//table')[0]
    for heading in table.xpath(".//strong[span]"):
        raw = "".join(heading.xpath("./span[1]//text()")).strip()
        if re.match(rf"^{start:02d}(?:\s*-|$)", raw):
            values = []
            for sibling in heading.itersiblings():
                if sibling.tag == "strong":
                    break
                if sibling.tag == "ul" and "jisi" in sibling.get("class", "").split():
                    values.extend(
                        "".join(s.itertext()).strip().replace("b/", " ")
                        for s in sibling.xpath("./li/span[1]")
                    )
            return values
    raise ValueError((page, start))


def main():
    fields = {"006": [], "007": [], "008": []}
    sources = {}

    def add(tag, name, start, end, when, page, **constraint):
        sources[page] = {
            "url": BASE + page,
            "sha256": hashlib.sha256((CACHE / page).read_bytes()).hexdigest(),
        }
        fields[tag].append(
            {
                "id": f"field.{tag}.detail.{name}.{start:02d}",
                "start": start,
                "end": end,
                "when": when,
                "source": BASE + page,
                "message": f"{tag}/{start:02d}-{end - 1:02d} violates the reviewed {name} constraint",
                **constraint,
            }
        )

    def pair(number, start, end, name, **constraint):
        material, leader, codes, _ = MATERIALS[number]
        page = f"00X_008_{number}.html"
        add("008", material + "." + name, start, end, {"leader": leader}, page, **constraint)
        add(
            "006",
            material + "." + name,
            POSITIONS_006[start],
            POSITIONS_006[end - 1] + 1,
            {"value_codes": list(codes)},
            page,
            **constraint,
        )

    # One-character codes repeated across a block, left justified, unused
    # positions blank. Whole-block fill is explicitly described in the prose.
    for number, start, end in [
        (2, 18, 22),
        (2, 24, 26),
        (4, 18, 22),
        (4, 33, 35),
        (5, 24, 26),
        (5, 30, 32),
        (6, 24, 26),
        (8, 24, 26),
    ]:
        values = code_list(f"00X_008_{number}.html", start)
        alphabet = "".join(v for v in values if len(v) == 1 and v not in " |")
        width = end - start
        pattern = (
            "(?:"
            + "|".join(f"[{re.escape(alphabet)}]{{{n}}} {{{width - n}}}" for n in range(width + 1))
            + rf"|\|{{{width}}})"
        )
        pair(number, start, end, "code-block", pattern=pattern)

    for number, start in [(4, 22), (5, 18)]:
        values = code_list(f"00X_008_{number}.html", start)
        # Projection blank is b/b/ in the prose; HTML splits its two spans.
        values = ["  " if v == " " else v for v in values]
        assert values and all(len(v) == 2 for v in values)
        pair(number, start, start + 2, "code-pair", values=values)

    pair(7, 18, 21, "runtime", pattern=r"(?:[0-9]{3}|nnn|---|\|{3})")

    # Undefined positions explicitly permit blank or fill. No undocumented
    # requirement that every position in a block use the same choice.
    undefined = {
        3: [(18, 22), (24, 25), (29, 32), (33, 35)],
        4: [(24, 25), (30, 31)],
        5: [(29, 30), (34, 35)],
        6: [(20, 21), (30, 32)],
        7: [(21, 22), (23, 26), (30, 32)],
        9: [(18, 23), (24, 26), (29, 32), (33, 35)],
    }
    for number, ranges in undefined.items():
        for start, end in ranges:
            pair(number, start, end, "undefined", pattern=rf"[ |]{{{end - start}}}")
    for start in [26, 38]:
        add(
            "008",
            "RB.undefined",
            start,
            start + 2,
            {"leader": {"6": ["w"]}},
            "00X_008_8.html",
            values=["  "],
        )

    categories = {
        1: "a",
        2: "c",
        3: "d",
        4: "f",
        5: "g",
        6: "h",
        7: "k",
        8: "m",
        10: "r",
        12: "s",
        14: "v",
    }
    for number, category in categories.items():
        add(
            "007",
            category + ".undefined",
            2,
            3,
            {"prefix": category},
            f"00X_007_{number}.html",
            values=[" ", "|"],
        )
    add(
        "007",
        "c.bit-depth",
        6,
        9,
        {"prefix": "c"},
        "00X_007_2.html",
        optional=True,
        pattern=r"(?:(?!000)[0-9]{3}|mmm|nnn|---|\|{3})",
    )
    add(
        "007",
        "h.reduction",
        6,
        9,
        {"prefix": "h"},
        "00X_007_6.html",
        pattern=r"(?:[0-9-]{3}|\|{3})",
    )
    values = code_list("00X_007_10.html", 9)
    assert values and all(len(v) == 2 for v in values)
    add("007", "r.data-type", 9, 11, {"prefix": "r"}, "00X_007_10.html", values=values)
    result = {
        "standard": "KS X 6006-0:2023",
        "complete": False,
        "scope": "Reviewed selected block syntax, code pairs and undefined positions; not complete content validation",
        "sources": sources,
        "fields": fields,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({tag: len(rules) for tag, rules in fields.items()})


if __name__ == "__main__":
    main()
