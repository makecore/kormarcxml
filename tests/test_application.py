"""Annex application levels: presence, contextual applicability and transport separation."""

from copy import deepcopy
import json
import pytest
from kormarcxml import ControlField, DataField, Record
from kormarcxml.validation import validate, coverage

MANDATORY = {"001", "003", "005", "008", "040", "245", "300"}


def record(tags=(), encoding_level=" ", bibliographic="m"):
    leader = list("00000nam a2200000   4500")
    leader[17], leader[7] = encoding_level, bibliographic
    fields = [ControlField(t, "") if t.startswith("00") else DataField(t) for t in sorted(tags)]
    return Record("".join(leader), fields)


def findings(value, **kw):
    return [i for i in validate(value, **kw) if i.rule_id.startswith("application.")]


@pytest.mark.parametrize("code,name", [(" ", "full"), ("7", "minimal")])
def test_mandatory_presence_by_level(code, name):
    found = findings(record(encoding_level=code))
    errors = [i for i in found if i.severity == "error"]
    assert {i.tag for i in errors} == MANDATORY
    assert {i.rule_id for i in errors} == {f"application.{name}.{t}.required" for t in MANDATORY}
    assert not [i for i in findings(record(MANDATORY, code)) if i.severity == "error"]
    assert set(coverage()["application_mandatory_fields"][name]) == MANDATORY


@pytest.mark.parametrize("code", ["1", "2", "3", "4", "5", "8", "u", "z"])
def test_no_annex_level_inference(code):
    found = findings(record(encoding_level=code))
    assert any(i.rule_id == "application.level-unreviewed" for i in found)
    assert not any(".required" in i.rule_id for i in found)


def test_missing_a_is_not_missing_m_and_dash_is_not_forbidden():
    value = record(MANDATORY | {"013"}, "7")
    found = findings(value)
    assert not [i for i in found if i.severity == "error"]
    assert any(i.rule_id == "application.applicability-unverified" for i in found)
    profile = {"application": {"applicable_fields": ["020"]}}
    found = findings(value, profile=profile)
    assert {i.tag for i in found if i.severity == "error"} == {"020"}
    assert not [
        i
        for i in findings(record(MANDATORY | {"020"}, "7"), profile=profile)
        if i.severity == "error"
    ]


@pytest.mark.parametrize("bib", ["a", "b", "d"])
def test_host_required_when_leader_confirms_component(bib):
    assert any(
        i.rule_id == "application.component.requires-773"
        for i in findings(record(bibliographic=bib))
    )
    assert not any(
        i.rule_id == "application.component.requires-773"
        for i in findings(record({"773"}, bibliographic=bib))
    )


def test_core_authentication_and_content_not_certified_by_presence():
    assert any(
        i.rule_id == "application.core.requires-042" for i in findings(record(encoding_level="4"))
    )
    assert not any(
        i.rule_id == "application.core.requires-042" for i in findings(record({"042"}, "4"))
    )
    value = record(MANDATORY)
    # Presence alone never certifies valid content: empty fixed fields remain invalid.
    assert any(i.rule_id == "field.008.length" for i in validate(value))
    before = deepcopy(value)
    validate(value)
    assert value == before


def test_level_two_and_profile_errors():
    assert not findings(record(), level=2)
    for bad in ["020", ["999999"], [True]]:
        with pytest.raises(ValueError, match="applicable_fields"):
            findings(record(), profile={"application": {"applicable_fields": bad}})


def test_cli_default_and_profile_context(tmp_path):
    from test_cli import run
    from kormarcxml import record_to_xml

    xml = record_to_xml(record())
    result = run("validate", data=xml)
    assert result.returncode == 1
    assert "application.full.003.required" in {
        i["rule_id"] for i in json.loads(result.stdout)["issues"]
    }
    profile = tmp_path / "context.json"
    profile.write_text(
        json.dumps({"application": {"applicable_fields": ["020"]}}), encoding="utf-8"
    )
    result = run("validate", "--profile", profile, data=xml)
    assert "application.full.020.applicable" in {
        i["rule_id"] for i in json.loads(result.stdout)["issues"]
    }
