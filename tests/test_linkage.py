"""Appendices A/D and 880: field-set relationships and preservation boundaries."""

from copy import deepcopy
import pytest
from kormarcxml import DataField, Record, Subfield
from kormarcxml.validation import validate, load_registry


def f(tag, *values, code="6", indicators="  "):
    return DataField(
        tag, *indicators, [Subfield(code, v) for v in values] + [Subfield("a", "한글")]
    )


def check(*fields, level=3, profile=None):
    return [
        i
        for i in validate(
            Record("00000nam a2200000   4500", list(fields)), level=level, profile=profile
        )
        if i.rule_id.startswith(("linkage.", "decision.KX-01"))
    ]


def ids(*fields, **kw):
    return {i.rule_id for i in check(*fields, **kw)}


def test_reciprocal_one_to_many_and_unlinked_exception():
    assert not check(f("245", "880-01"), f("880", "245-01/(B"), f("880", "245-01/$1"))
    assert not check(f("880", "530-00/(2/r"))
    assert "linkage.6.unlinked" in ids(f("245", "880-00"))
    assert "linkage.6.reciprocal" in ids(f("245", "880-01"), f("880", "245-02/(B"))


def test_unique_sets_and_indicators():
    assert "linkage.6.occurrence-unique" in ids(f("245", "880-01"), f("260", "880-01"))
    assert "linkage.6.indicators" in ids(f("245", "880-01", indicators="10"), f("880", "245-01/(B"))
    assert "linkage.6.required" in ids(f("880"))


@pytest.mark.parametrize(
    "value", ["245-1", "245-001", "245-01/(B/l", "245-01/", "２４５-01", "245-01/(B/", "245-01(B"]
)
def test_six_syntax(value):
    assert "linkage.6.syntax" in ids(f("880", value))


def test_repeated_aliases_warn_and_preserve():
    field = f("880", "245-01/(N", "245-01/Cyrl")
    original = deepcopy(field)
    found = check(f("245", "880-01"), field)
    assert {i.rule_id for i in found} == {"decision.KX-012", "linkage.6.script-unverified"}
    assert all(i.severity == "warning" for i in found)
    assert field == original
    all_issues = validate(Record("00000nam a2200000   4500", [field]))
    assert not any(i.rule_id == "field.880.subfield.6.repeatability" for i in all_issues)
    misplaced = DataField("880", " ", " ", [Subfield("a", "data"), Subfield("6", "245-00/(B")])
    assert "linkage.6.first" in ids(misplaced)


def test_scripts_and_targets():
    assert "decision.KX-013" in ids(f("880", "245-00/▾1"))
    assert "linkage.6.script" in ids(f("880", "245-00/invalid"))
    assert "linkage.6.target" in ids(f("245", "260-01"))
    assert "linkage.6.target" in ids(f("880", "001-00"))
    assert not check(f("245", "880-01/(B/r"), f("880", "245-01/(2/r"))


def test_eight_group_sequence_and_type():
    assert not check(f("505", "1.9\\x", code="8"), f("505", "1.2\\x", code="8"))
    assert "linkage.8.group-sequence" in ids(
        f("505", "01.2\\u", code="8"), f("505", "1\\u", code="8")
    )
    assert "linkage.8.sequence-required" in ids(f("505", "1\\x", code="8"))
    assert "linkage.8.type-required" in ids(f("505", "1", code="8"))
    assert "linkage.8.type" in ids(f("505", "1\\z", code="8"))
    assert "decision.KX-014" in ids(f("505", "1∖u", code="8"))


@pytest.mark.parametrize(
    "value", ["", "1.", "-1\\u", "1.2.3\\x", "1\\xx", "1/2", "１\\u", "1\\", " 1\\u"]
)
def test_eight_syntax(value):
    assert "linkage.8.syntax" in ids(f("505", value, code="8"))


def test_eight_repeat_groups_large_numbers_and_holdings_scope():
    assert not check(f("505", "1\\u", "2\\c", code="8"))
    assert not check(f("505", "9" * 5000 + "\\u", code="8"))
    profile = {"fields": {"853": {"subfields": {"8": {}}}, "852": {"subfields": {"8": {}}}}}
    assert not check(
        f("853", "1.2", code="8"), f("852", "not-appendix-A", code="8"), profile=profile
    )
    assert not check(f("999", "local", code="8"))


def test_level_two_and_profile_isolation():
    assert not check(f("245", "bad"), f("505", "bad", code="8"), level=2)
    profile = load_registry()
    profile["linkage"]["eight_types"].append("z")
    assert not check(f("505", "1\\z", code="8"), profile=profile)
    assert "linkage.8.type" in ids(f("505", "1\\z", code="8"))
