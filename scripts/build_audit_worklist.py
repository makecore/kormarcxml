"""Reconcile field inventory and implementation without inventing a completion rate."""

import json
from pathlib import Path
from kormarcxml.validation import coverage, load_registry


def main():
    catalog = json.loads(Path("research/field-catalog.json").read_text(encoding="utf-8"))
    inventory = json.loads(Path("research/source-inventory.json").read_text(encoding="utf-8"))
    pages = {p["url"]: p for p in inventory["pages"]}
    registry = load_registry()
    counts = coverage()["field_rule_counts"]
    entries = []
    for field in catalog["fields"]:
        tag = field["tag"]
        spec = registry["fields"][tag]
        ids = [
            r["id"]
            for r in spec.get("rules", [])
            + spec.get("conditions", [])
            + spec.get("dependencies", [])
        ]
        for sub in spec.get("subfields", {}).values():
            ids.extend(r["id"] for r in sub.get("rules", []))
        entries.append(
            {
                "tag": tag,
                "source": field["source"],
                "source_sha256": pages.get(field["source"], {}).get("sha256"),
                "xml_mapping": field["xml"],
                "definition_scope": field.get("definition_scope", "bibliographic"),
                "summary_status": field["review_status"],
                "executable_assertion_templates": counts[tag],
                "explicit_content_rule_ids": sorted(ids),
                "transport_test_module": "tests/test_catalog_transport.py",
                "full_prose_review": "not-complete",
                "full_dependency_review": "not-complete",
                "application_level_enforcement": "metadata-only",
                "semantic_test_coverage": "partial; no per-clause completion certificate",
            }
        )
    output = {
        "standard": catalog["standard"],
        "complete": False,
        "unit": "annex-listed field; NOT individual normative clause",
        "field_count": len(entries),
        "normative_clause_total": None,
        "semantic_completion_percent": None,
        "note": "Automated reconciliation is not evidence of prose review. All fields remain open for complete clause-level sign-off.",
        "fields": entries,
    }
    Path("research/audit-worklist.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print({"fields": len(entries), "semantic_completion_percent": None})


if __name__ == "__main__":
    main()
