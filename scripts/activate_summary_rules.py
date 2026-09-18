"""Merge explicit summary facts into the partial validator registry.

Run after build_source_catalog.py. No required-field, cross-field, fixed-position
or prose-derived rule is inferred. Ambiguous markers leave constraints open.
Existing independently reviewed content rules are retained.
"""

import json
from pathlib import Path


def main():
    catalog = json.loads(Path("research/field-catalog.json").read_text(encoding="utf-8"))
    path = Path("src/kormarcxml/resources/rules/bibliographic.json")
    registry = json.loads(path.read_text(encoding="utf-8"))
    for field in catalog["fields"]:
        target = registry["fields"].setdefault(field["tag"], {})
        target.update(
            {key: field[key] for key in ("label", "source", "repeatable") if key in field}
        )
        target["summary_status"] = (
            "Direct HTML technical summary; detailed semantic coverage incomplete"
        )
        target["obligation_marker"] = field["obligation_marker"]
        target["application_levels"] = field.get("application_levels", {})
        if field.get("definition_scope"):
            target["definition_scope"] = field["definition_scope"]
            target["summary_status"] = field["review_status"]
        target.pop("indicators", None)
        target.pop("closed_subfields", None)
        for index, indicator in field["indicators"].items():
            if indicator["values"] and not indicator["unresolved"]:
                target.setdefault("indicators", {})[index] = indicator["values"]
        for code, subfield in field["subfields"].items():
            target.setdefault("subfields", {}).setdefault(code, {}).pop("repeatable", None)
            target.setdefault("subfields", {}).setdefault(code, {}).update(
                {k: subfield[k] for k in ("label", "repeatable") if k in subfield}
            )
        if field["subfields"] and not field["unresolved_summary_items"]:
            target["closed_subfields"] = True
        target["unresolved_summary_items"] = field["unresolved_summary_items"]
    registry["fields"] = dict(sorted(registry["fields"].items()))
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(registry["fields"]), "field summaries; complete remains false")


if __name__ == "__main__":
    main()
