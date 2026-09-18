import pytest
from kormarcxml import Record, DataField, Subfield
from kormarcxml.validation import validate


def issues(tag, ind1=" ", subfields=(), level=3):
    return validate(
        Record("00000nam a2200000   4500", [DataField(tag, ind1, " ", list(subfields))]),
        level=level,
    )


@pytest.mark.parametrize("tag", ["100", "600", "700", "800"])
def test_generational_number_requires_forename_indicator(tag):
    subs = [Subfield("a", "John"), Subfield("b", "II")]
    rule = f"field.{tag}.b.forename"
    assert not any(i.rule_id == rule for i in issues(tag, "0", subs))
    assert any(i.rule_id == rule for i in issues(tag, "1", subs))
    assert not any(i.rule_id == rule for i in issues(tag, "1", [subs[0]]))
    assert not any(i.rule_id == rule for i in issues(tag, "1", subs, level=2))


@pytest.mark.parametrize("tag", ["800", "810", "811", "830"])
def test_series_control_code_is_optional_but_nonempty_when_present(tag):
    for value in ("a", "|", "am"):
        assert not any(
            i.rule_id.startswith(f"field.{tag}.7.")
            for i in issues(tag, subfields=[Subfield("7", value)])
        )
    for value in ("", " ", "x", "amm"):
        assert any(
            i.rule_id.startswith(f"field.{tag}.7.")
            for i in issues(tag, subfields=[Subfield("7", value)])
        )
    assert not any(i.rule_id.startswith(f"field.{tag}.7.") for i in issues(tag))
