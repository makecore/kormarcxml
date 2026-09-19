"""Source-backed dependencies are local to each field occurrence, not a record-wide union."""

import pytest
from kormarcxml import Record, DataField, Subfield
from kormarcxml.validation import validate


def field(tag, pairs, ind2=" "):
    return DataField(tag, " ", ind2, [Subfield(c, v) for c, v in pairs])


def issues(*fields, level=3):
    return validate(Record("00000nam a2200000   4500", list(fields)), level=level)


def ids(*fields, level=3):
    return {i.rule_id for i in issues(*fields, level=level)}


def test_017_valid_display_and_repeated_numbers():
    value = field("017", [("i", "Registration:"), ("a", "A1"), ("a", "A2"), ("b", "Agency")], "8")
    assert not any(i.rule_id.startswith("field.017.") for i in issues(value))
    bad = field("017", [("a", "A1"), ("b", "Agency"), ("i", "Registration:"), ("a", "A2")])
    assert {
        "field.017.display.order",
        "field.017.display.indicator",
        "field.017.agency.order",
    } <= ids(bad)
    assert not any(i.rule_id.startswith("field.017.display") for i in issues(bad, level=2))


def test_017_agency_rule_and_cancelled_only_provisional_policy():
    assert "field.017.number.requires-agency" in ids(field("017", [("a", "A1")]))
    found = issues(field("017", [("z", "Cancelled")]))
    assert any(i.rule_id == "decision.KX-011" and i.severity == "warning" for i in found)
    assert not any(i.rule_id.startswith("field.017.") for i in found)
    assert "decision.KX-011" not in ids(field("017", [("z", "Cancelled"), ("b", "Agency")]))


@pytest.mark.parametrize("scheme", ["pe", "da"])
def test_031_scheme_and_notation_require_time_signature(scheme):
    assert "field.031.scheme.requires-time" in ids(field("031", [("2", scheme)]))
    assert "field.031.scheme.requires-time" not in ids(field("031", [("2", scheme), ("o", "nd")]))
    assert "field.031.notation.requires-scheme-time" in ids(field("031", [("p", "notation")]))
    assert "field.031.notation.requires-scheme-time" not in ids(
        field("031", [("p", "notation"), ("2", scheme), ("o", "c")])
    )
    assert "field.031.scheme.requires-time" not in ids(field("031", [("2", "other")]))


@pytest.mark.parametrize("missing", list("defg"))
def test_034_coordinates_require_all_four_in_each_occurrence(missing):
    coords = [(c, "E0010000") for c in "defg"]
    good = field("034", coords)
    bad = field("034", [(c, v) for c, v in coords if c != missing])
    found = [i for i in issues(good, bad) if i.rule_id == "field.034.coordinates.together"]
    assert len(found) == 1 and found[0].occurrence == 2
    assert "field.034.coordinates.together" not in ids(field("034", [("a", "a")]))


def test_dependencies_preserve_data_and_do_not_borrow_from_another_field():
    one = field("031", [("p", "notation")])
    two = field("031", [("2", "pe"), ("o", "c")])
    before = repr((one, two))
    assert "field.031.notation.requires-scheme-time" in ids(one, two)
    assert repr((one, two)) == before
    assert "field.031.notation.requires-scheme-time" not in ids(one, two, level=2)
