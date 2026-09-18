"""Extract unambiguous 007 position code sets from cached official summaries.

Only single-position enumerations are activated. Multi-position codes and
prose dependencies are explicitly outside this generated rule set.
"""

import json
from pathlib import Path
import re

from lxml import html

BASE = "https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/"
LENGTHS = {
    1: 8,
    3: 6,
    4: 10,
    5: 9,
    6: 13,
    7: 6,
    8: 23,
    9: 2,
    10: 11,
    11: 2,
    12: 14,
    13: 2,
    14: 9,
    15: 2,
    16: 2,
}


def main():
    rules = []
    categories = []
    for number in range(1, 17):
        name = f"00X_007_{number}.html"
        doc = html.parse(str(Path(".audit-cache/sub") / name))
        table = doc.xpath('//*[@id="contentsWrap"]//table')[0]
        positions = []
        for heading in table.xpath(".//strong[span]"):
            position = "".join(heading.xpath("./span[1]//text()")).strip()
            values = []
            for sibling in heading.itersiblings():
                if sibling.tag == "strong":
                    break
                if sibling.tag == "ul" and "jisi" in sibling.get("class", "").split():
                    for span in sibling.xpath("./li/span[1]"):
                        value = "".join(span.itertext()).strip()
                        values.append(" " if value == "b/" else value)
                    break
            positions.append({"position": position, "values": values})
        category = next(p["values"][0] for p in positions if p["position"] == "00")
        assert len(category) == 1
        categories.append(category)
        source = BASE + name
        length_rule = {
            "id": f"field.007.{category}.length",
            "level": 2,
            "when": {"prefix": category},
            "source": source,
            "message": "007 length is outside the documented material layout",
        }
        if number == 2:
            # The first six positions are mandatory; the remaining positions
            # may be supplied by an institution. Do not demand a 14-char field.
            length_rule.update(min_length=6, max_length=14)
        else:
            length_rule["length"] = LENGTHS[number]
        rules.append(length_rule)
        for item in positions:
            if not re.fullmatch(r"\d{2}", item["position"]):
                continue
            index = int(item["position"])
            if index == 0 or not item["values"] or any(len(v) != 1 for v in item["values"]):
                continue
            rules.append(
                {
                    "id": f"field.007.{category}.position.{index:02d}",
                    "when": {"prefix": category},
                    "start": index,
                    "end": index + 1,
                    "optional": number == 2 and index >= 6,
                    "values": item["values"],
                    "source": source,
                    "message": f"007/{index:02d} contains a code outside this material summary",
                }
            )
    rules.insert(
        0,
        {
            "id": "field.007.category",
            "start": 0,
            "end": 1,
            "values": categories,
            "message": "007/00 requires a documented material category; fill is not allowed",
            "source": BASE + "00X_007.html",
        },
    )
    result = {
        "standard": "KS X 6006-0:2023",
        "complete": False,
        "scope": "007 material lengths and explicit single-position code enumerations; no inferred dependencies",
        "rules": rules,
    }
    Path("src/kormarcxml/resources/rules/physical.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("categories", "".join(categories), "checks", len(rules))


if __name__ == "__main__":
    main()
