"""Verify source HTML field groups locally without redistributing official examples.

The HTML contains examples, not complete ISO records. A synthetic leader is
explicitly supplied only for the transport experiment. Hidden examples require
an opt-in and are never counted as currently published visible examples.
"""

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re

from lxml import html

from kormarcxml import DataField, Record, Subfield
from kormarcxml.iso2709 import decode_record, encode_record
from kormarcxml.transforms import tagged, to_html
from kormarcxml.validation import validate
from kormarcxml.xmlio import iter_xml, record_to_xml, schema_validate, write_xml

SOURCE = "https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/appendix_d.html"
SYNTHETIC_LEADER = "00000nam a2200000   4500"


def parse_field(node):
    """Decode displayed indicators, preserving all subfield text verbatim."""
    line = node.text_content()
    prefix, separator, rest = line.partition("▾")
    match = re.fullmatch(r"\s*(\d{3})\s+((?:b/|[0-9 ]){2})", prefix)
    if not separator or match is None:
        raise ValueError("Displayed field must explicitly contain two indicators and subfields")
    indicators = match[2].replace("b/", " ")
    pieces = rest.split("▾")
    if any(len(piece) < 1 or not re.fullmatch(r"[a-z0-9]", piece[0]) for piece in pieces):
        raise ValueError("Invalid displayed subfield code")
    return DataField(match[1], *indicators, [Subfield(p[0], p[1:]) for p in pieces])


def verify(source_bytes, *, include_hidden=False):
    # The pinned official source is UTF-8. Decode strictly so an absent HTML
    # charset declaration cannot silently turn subfield delimiters into mojibake.
    document = html.fromstring(source_bytes.decode("utf-8"))
    results = []
    transported = []
    for index, group in enumerate(document.xpath('//ul[@class="giho"]'), 1):
        hidden = any(
            "display:none" in ancestor.get("style", "").replace(" ", "").lower()
            for ancestor in [group, *group.iterancestors()]
        )
        result = {"group": index, "hidden_in_source": hidden}
        results.append(result)
        if hidden and not include_hidden:
            result["status"] = "excluded-hidden"
            continue
        try:
            fields = [parse_field(node) for node in group.xpath("./li")]
        except ValueError as exc:
            result.update(status="unparseable-without-editorial-repair", reason=str(exc))
            continue
        logical = Record(SYNTHETIC_LEADER, fields)
        raw = encode_record(logical)
        canonical = decode_record(raw)
        xml = record_to_xml(canonical)
        restored = next(iter_xml(BytesIO(xml)))
        if schema_validate(xml):
            raise AssertionError("XML schema failure")
        if restored != canonical or restored.fields != fields or encode_record(restored) != raw:
            raise AssertionError("Source field group transport changed data")
        if not to_html(restored) or not tagged(restored):
            raise AssertionError("Presentation missing")
        transported.append(canonical)
        issues = validate(canonical)
        result.update(
            status="transport-passed-with-synthetic-leader",
            fields=len(fields),
            schema_valid=True,
            codepoints_order_indicators_preserved=True,
            generated_iso_bytes_equal=True,
            semantic_issue_counts=dict(sorted(Counter(i.rule_id for i in issues).items())),
            semantic_certification=False,
            placeholder_text_present=any("script]" in s.value for f in fields for s in f.subfields),
        )
    collection = BytesIO()
    write_xml(transported, collection)
    assert list(iter_xml(BytesIO(collection.getvalue()))) == transported
    return {
        "source": SOURCE,
        "source_sha256": sha256(source_bytes).hexdigest(),
        "generator": "scripts/verify_official_examples.py",
        "include_hidden": include_hidden,
        "source_contains_complete_iso_records": False,
        "source_contains_leader_directory": False,
        "synthetic_leader": SYNTHETIC_LEADER,
        "production_sample_verification": "not-performed-no-production-ISO-bytes-supplied",
        "original_iso_byte_equality": "not-testable-no-original-ISO-bytes",
        "normalization": "none; only displayed b/ indicators decoded to spaces",
        "collection_round_trip_records": len(transported),
        "groups": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="User-supplied appendix_d.html cache")
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.source.read_bytes(), include_hidden=args.include_hidden)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
