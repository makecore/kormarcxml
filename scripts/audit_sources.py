"""Inventory NLK HTML pages without publishing official explanatory prose.

Raw cache is ignored by Git. Metadata is a retrieval inventory, NOT proof that
all prose or all semantic dependencies have been reviewed.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urljoin, urldefrag, quote
from urllib.request import urlopen

from lxml import html

BASE = "https://librarian.nl.go.kr/kormarc/KSX6006-0/"
CACHE = Path(".audit-cache")
OUT = Path("research/source-inventory.json")


def fetch(url):
    path = CACHE / url.removeprefix(BASE)
    try:
        if path.exists():
            raw = path.read_bytes()
        else:
            raw = urlopen(quote(url, safe=":/%"), timeout=40).read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        doc = html.fromstring(raw)
        # The menu fragment is injected into /sub/ pages by jQuery.
        context = BASE + "sub/" if url.endswith("layout/leftM.html") else url
        links = sorted({urldefrag(urljoin(context, h))[0] for h in doc.xpath("//a/@href")})
        other_links = [u for u in links if not (u.startswith(BASE) and u.endswith(".html"))]
        links = [u for u in links if u.startswith(BASE) and u.endswith(".html")]
        return {
            "url": url,
            "status": "retrieved",
            "sha256": sha256(raw).hexdigest(),
            "bytes": len(raw),
            "links": links,
            "other_links": other_links,
            "semantic_review": "pending",
        }
    except Exception as exc:
        return {"url": url, "status": "failed", "error": str(exc)}


def main():
    inventory = {}
    pending = {BASE + "index.html", BASE + "layout/leftM.html"}
    depth = 0
    while pending:
        following = set()
        with ThreadPoolExecutor(max_workers=6) as pool:
            for future in as_completed([pool.submit(fetch, u) for u in sorted(pending)]):
                item = future.result()
                item["discovery_depth"] = depth
                inventory[item["url"]] = item
                following.update(item.get("links", []))
                OUT.write_text(
                    json.dumps(
                        {
                            "base": BASE,
                            "retrieved_date": "2026-09-17",
                            "review_note": "Retrieval is not semantic verification.",
                            "pages": sorted(inventory.values(), key=lambda x: x["url"]),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                print(len(inventory), item["status"], item["url"], flush=True)
        pending = following - inventory.keys()
        depth += 1


if __name__ == "__main__":
    main()
