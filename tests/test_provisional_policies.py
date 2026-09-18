"""Provisional decisions preserve data and leave confirmed constraints active."""

import json
from importlib.resources import files
import pytest
from kormarcxml import Record, ControlField, DataField, Subfield
from kormarcxml.validation import validate

HELD = json.loads(
    files("kormarcxml").joinpath("resources/rules/materials.json").read_text(encoding="utf-8")
)["held_for_review"]


@pytest.mark.parametrize("held", HELD, ids=lambda h: h["material"])
@pytest.mark.parametrize("tag", ["006", "008"])
def test_material_fill_warning_is_scoped_and_non_destructive(held, tag):
    leader = list("00000nam a2200000   4500")
    for position, codes in held["leader"].items():
        leader[int(position)] = codes[0]
    value = list(" " * (14 if tag == "006" else 40))
    position = held["auxiliary_position"] if tag == "006" else held["position"]
    if tag == "006":
        value[0] = held["auxiliary_codes"][0]
        leader[6] = "m"  # 006 selects its own material, independently of Leader.
    value[position] = "|"
    record = Record("".join(leader), [ControlField(tag, "".join(value))])
    before = repr(record)
    issues = [i for i in validate(record) if i.rule_id.startswith("decision.KX-001")]
    assert len(issues) == 1
    assert (issues[0].severity, issues[0].position) == ("warning", position)
    assert repr(record) == before
    assert not any(i.rule_id.startswith("decision.") for i in validate(record, level=2))
    value[position] = " "
    assert not any(
        i.rule_id.startswith("decision.KX-001")
        for i in validate(Record("".join(leader), [ControlField(tag, "".join(value))]))
    )


def test_repeated_240_source_retained_with_warning_and_confirmed_rules_still_run():
    record = Record(
        "00000nam a2200000   4500",
        [
            DataField("240", subfields=[Subfield("2", "one"), Subfield("2", "two")]),
            ControlField("008", " " * 15 + "|" + " " * 24),
        ],
    )
    before = repr(record)
    issues = validate(record)
    assert any(i.rule_id == "decision.KX-002" and i.severity == "warning" for i in issues)
    assert not any(i.rule_id == "field.240.subfield.2.repeatability" for i in issues)
    assert any(i.rule_id == "field.008.country.fill" and i.severity == "error" for i in issues)
    assert repr(record) == before
