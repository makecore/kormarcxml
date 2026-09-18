"""Extract code tokens, without official explanatory prose, from pinned annex HTML.

These are snapshot membership sets including historical entries. Active/obsolete
classification and latest-table policy require separate review.
"""

from hashlib import sha256
import json
from pathlib import Path
import re
from lxml import html

TABLES = {
    1: ("country", r"[a-z]{2,3}"),
    2: ("university", r"[A-Z]{2}"),
    3: ("language", r"[a-z]{3}"),
    4: ("government", r"[A-Z]{2}"),
}


def main():
    output = {"standard": "KS X 6006-0:2023", "complete": False, "tables": {}}
    for number, (name, pattern) in TABLES.items():
        path = Path(f".audit-cache/sub/annex_{number}.html")
        raw = path.read_bytes()
        doc = html.fromstring(raw)
        tokens = [
            "".join(n.itertext()).strip()
            for n in doc.xpath(
                '//*[@id="contentsWrap"]//span[contains(concat(" ",normalize-space(@class)," ")," r ")]'
            )
        ]
        codes = sorted({t for t in tokens if re.fullmatch(pattern, t)})
        unresolved = sorted({t for t in tokens if t and not re.fullmatch(pattern, t)})
        output["tables"][name] = {
            "source": f"https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/annex_{number}.html",
            "source_sha256": sha256(raw).hexdigest(),
            "snapshot_retrieved": "2026-09-17",
            "scope": "Explicit code tokens including historical codes; not active-code certification",
            "codes": codes,
            "unresolved_code_tokens": unresolved,
        }
    Path("src/kormarcxml/resources/rules/code-tables.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        {
            k: {"codes": len(v["codes"]), "unresolved": v["unresolved_code_tokens"]}
            for k, v in output["tables"].items()
        }
    )


if __name__ == "__main__":
    main()
