"""Generate scoped 008 and corresponding 006 code checks from official HTML.

Single-position explicit code lists only. Form-of-item positions are held back
because the overview and detailed pages disagree about fill characters.
"""

import json
from pathlib import Path
import re

from lxml import html

BASE = "https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/"
# Selectors transcribed from each page's definition-and-scope section.
MATERIALS = {
    2: ("BK", {"6": list("at"), "7": list("acdm")}, "at", 23),
    3: ("ER", {"6": ["m"]}, "m", 23),
    4: ("MP", {"6": list("ef")}, "ef", 29),
    5: ("MU", {"6": list("cdij")}, "cdij", 23),
    6: ("CR", {"6": ["a"], "7": list("bis")}, "s", 23),
    7: ("VM", {"6": list("gkro")}, "gkro", 29),
    8: ("RB", {"6": ["w"]}, "w", 23),
    9: ("MX", {"6": ["p"]}, "p", 23),
}
POSITIONS_006 = {
    position: index + 1
    for index, position in enumerate(
        list(range(18, 26)) + list(range(29, 32)) + list(range(33, 35))
    )
}


def main():
    rules = {"006": [], "008": []}
    held = []
    for number, (material, leader, codes, form) in MATERIALS.items():
        name = f"00X_008_{number}.html"
        doc = html.parse(str(Path(".audit-cache/sub") / name))
        table = doc.xpath('//*[@id="contentsWrap"]//table')[0]
        for heading in table.xpath(".//strong[span]"):
            raw = "".join(heading.xpath("./span[1]//text()")).strip()
            if not re.fullmatch(r"\d{2}", raw):
                continue
            position = int(raw)
            if position == form:
                held.append(
                    {
                        "material": material,
                        "position": position,
                        "leader": leader,
                        "auxiliary_codes": list(codes),
                        "auxiliary_position": POSITIONS_006[position],
                        "source": BASE + name,
                        "reason": "Overview prohibits fill; material detail permits it. Needs authoritative reconciliation.",
                    }
                )
                continue
            if position not in POSITIONS_006:
                continue
            values = []
            for sibling in heading.itersiblings():
                if sibling.tag == "strong":
                    break
                if sibling.tag == "ul" and "jisi" in sibling.get("class", "").split():
                    for span in sibling.xpath("./li/span[1]"):
                        value = "".join(span.itertext()).strip()
                        values.append(" " if value == "b/" else value)
                    break
            if not values or any(len(v) != 1 for v in values):
                continue
            for tag, start, when in [
                ("008", position, {"leader": leader}),
                ("006", POSITIONS_006[position], {"value_codes": list(codes)}),
            ]:
                rules[tag].append(
                    {
                        "id": f"field.{tag}.{material}.position.{start:02d}",
                        "start": start,
                        "end": start + 1,
                        "values": values,
                        "when": when,
                        "message": f"{tag}/{start:02d} contains a code outside the {material} material summary",
                        "source": BASE + name,
                    }
                )
    output = {
        "standard": "KS X 6006-0:2023",
        "complete": False,
        "scope": "Single-position enumerations and source-defined material selectors; no complete prose validation",
        "fields": rules,
        "held_for_review": held,
    }
    Path("src/kormarcxml/resources/rules/materials.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print({tag: len(items) for tag, items in rules.items()}, "held", len(held))


if __name__ == "__main__":
    main()
