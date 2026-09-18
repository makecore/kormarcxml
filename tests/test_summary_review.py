"""Reviewed summary punctuation repairs must not infer missing semantics."""

import importlib.util
import json
from pathlib import Path

import pytest

from kormarcxml import DataField, Record, Subfield
from kormarcxml.validation import load_registry, validate

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "catalog_generator", ROOT / "scripts/build_source_catalog.py"
)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


@pytest.mark.parametrize("tag,code", [("031", "s"), ("377", "l"), ("610", "n")])
def test_reviewed_repetition_survives_registry_and_preserves_record(tag, code):
    catalog = json.loads((ROOT / "research/field-catalog.json").read_text(encoding="utf-8"))
    field = next(f for f in catalog["fields"] if f["tag"] == tag)
    entry = field["subfields"][code]
    assert entry["repeatable"] is True
    assert len(entry["review"]["source_sha256"]) == 64
    assert entry["review"] == load_registry()["fields"][tag]["subfields"][code]["review"]
    record = Record(
        "00000nam a2200000   4500",
        [DataField(tag, subfields=[Subfield(code, "first"), Subfield(code, "second")])],
    )
    before = repr(record)
    assert not any("repeatability" in issue.rule_id for issue in validate(record))
    assert repr(record) == before


@pytest.mark.parametrize("exact", [True, False])
def test_reviewed_repair_only_applies_to_exact_source_marker(tmp_path, exact):
    tail = "유효성 검증 주기 [반복" if exact else "유효성 검증 주기 [알수없음"
    path = tmp_path / "01X_09X_031.html"
    path.write_text(
        '<html><meta charset="utf-8"><h3>031 음악</h3><div class="topJisi">'
        f'<ul class="abcMark"><li>▾s {tail}</li></ul></div></html>',
        encoding="utf-8",
    )
    field = generator.extract(path)
    assert field is not None
    entry = field["subfields"]["s"]
    assert (entry.get("repeatable") is True) == exact
    assert bool(field["unresolved_summary_items"]) != exact


def test_missing_240_marker_stays_open():
    field = load_registry()["fields"]["240"]
    assert "repeatable" not in field["subfields"]["2"]
    assert any(item["code"] == "2" for item in field["unresolved_summary_items"])


def test_020_allows_price_only_and_cancelled_identifier_only():
    for code in ("c", "z"):
        record = Record(
            "00000nam a2200000   4500", [DataField("020", subfields=[Subfield(code, "value")])]
        )
        assert not any(issue.tag == "020" for issue in validate(record))


@pytest.mark.parametrize("tag,decision", [("022", "KX-006"), ("034", "KX-007")])
def test_prose_defined_sources_are_preserved_pending_repetition_decision(tag, decision):
    record = Record(
        "00000nam a2200000   4500",
        [DataField(tag, subfields=[Subfield("2", "source-one"), Subfield("2", "source-two")])],
    )
    before = repr(record)
    issues = validate(record)
    assert not any(
        i.rule_id in (f"field.{tag}.subfield.allowed", f"field.{tag}.subfield.2.repeatability")
        for i in issues
    )
    assert any(i.rule_id == f"decision.{decision}" and i.severity == "warning" for i in issues)
    assert repr(record) == before


@pytest.mark.parametrize(
    "tag,codes,decision",
    [("502", "0o", "KX-008"), ("583", "cxz", "KX-009"), ("890", "ab", "KX-010")],
)
def test_conflicting_codes_are_preserved_not_renamed(tag, codes, decision):
    record = Record(
        "00000nam a2200000   4500",
        [DataField(tag, subfields=[Subfield(c, "source text") for c in codes])],
    )
    before = repr(record)
    issues = validate(record)
    assert not any(i.rule_id == f"field.{tag}.subfield.allowed" for i in issues)
    assert {i.subfield for i in issues if i.rule_id == f"decision.{decision}"} == set(codes)
    assert all(i.severity == "warning" for i in issues if i.rule_id == f"decision.{decision}")
    assert repr(record) == before
    assert not any(i.rule_id == f"decision.{decision}" for i in validate(record, level=2))
