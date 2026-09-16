"""Verified KORMARC differences, custom rules and incomplete coverage tests."""

from dataclasses import replace

import pytest

from kormarcxml.errors import Issue
from kormarcxml.model import ControlField, DataField, Record, Subfield
from kormarcxml.validation import coverage, load_registry, validate


def record(*fields):
    return Record("00000nam a2200000   4500", list(fields))


def ids(value, **kwargs):
    return {i.rule_id for i in validate(value, **kwargs)}


@pytest.mark.parametrize("tag,length", [("005", 14), ("006", 14), ("008", 40)])
def test_kormarc_fixed_lengths(tag, length):
    assert f"field.{tag}.length" not in ids(record(ControlField(tag, "0" * length)))
    assert f"field.{tag}.length" in ids(record(ControlField(tag, "0" * (length + 2))))


def test_repeatable_kormarc_title_and_responsibility_subfields():
    title = DataField(
        "245",
        "0",
        "0",
        [
            Subfield("a", "제목"),
            Subfield("a", "다른 제목"),
            Subfield("d", "김지음"),
            Subfield("d", "박지음"),
        ],
    )
    assert not [i for i in validate(record(title)) if i.severity == "error"]
    assert "field.245.repeatability" in ids(record(title, title))


def test_kormarc_ddc_institution_indicator_and_coded_content():
    good = DataField(
        "082", "7", "1", [Subfield("a", "020"), Subfield("2", "23"), Subfield("m", "a")]
    )
    assert not [i for i in validate(record(good)) if i.severity == "error"]
    bad = replace(good, ind2="9", subfields=[Subfield("m", "z")])
    assert "field.082.indicator2" in ids(record(bad), level=2)
    assert "field.082.subfield.m.code" not in ids(record(bad), level=2)
    assert "field.082.subfield.m.code" in ids(record(bad), level=3)


def test_nonrepeatable_and_unrecognized_subfields():
    field = DataField("082", "0", "1", [Subfield("b", "1"), Subfield("b", "2"), Subfield("z", "3")])
    found = ids(record(field))
    assert "field.082.subfield.b.repeatability" in found
    assert "field.082.subfield.allowed" in found


def test_unknown_local_fields_preserved_and_reported():
    value = record(DataField("999", " ", " ", [Subfield("a", "local")]), DataField("888"))
    before = repr(value)
    issues = validate(value)
    assert repr(value) == before
    assert next(i for i in issues if i.rule_id == "coverage.local-field").severity == "info"
    assert next(i for i in issues if i.rule_id == "coverage.unverified-field").severity == "warning"


def test_leader09_is_content_and_other_is_valid_code():
    value = record()
    for code in " az":
        good = replace(value, leader=value.leader[:9] + code + value.leader[10:])
        assert "leader.encoding" not in ids(good)
    bad = replace(value, leader=value.leader[:9] + "x" + value.leader[10:])
    assert "leader.encoding" not in ids(bad, level=2)
    assert "leader.encoding" in ids(bad)


def test_generic_bad_structure():
    value = record(
        DataField("00A", "##", "한", [Subfield("AA", "bad")]), ControlField("245", "wrong")
    )
    found = ids(value)
    assert {
        "structure.tag",
        "structure.field-kind",
        "structure.indicator",
        "structure.subfield-code",
    } <= found


def test_external_profile_does_not_mutate_default_registry():
    extra = {"fields": {"999": {"required": True, "repeatable": False}}}
    assert "field.999.required" in ids(record(), profile=extra)
    assert "999" not in load_registry()["fields"]
    assert coverage()["complete"] is False


def test_rule_extension_and_machine_readable_context():
    extra = {
        "fields": {
            "999": {
                "subfields": {
                    "a": {
                        "rules": [
                            {
                                "id": "local.date",
                                "date_format": "%Y%m%d",
                                "pattern": "[0-9]{8}",
                                "message": "Invalid date",
                                "source": "institutional policy",
                            }
                        ]
                    }
                }
            }
        }
    }
    value = record(
        ControlField("001", "test-id"), DataField("999", subfields=[Subfield("a", "20260230")])
    )
    issue = next(i for i in validate(value, profile=extra) if i.rule_id == "local.date")
    assert issue.to_dict()["record_identifier"] == "test-id"
    assert (issue.tag, issue.occurrence, issue.subfield, issue.position) == ("999", 1, "a", 0)


def test_consumer_validator_and_bad_level():
    def consumer(value):
        yield Issue("info", "local.review", "Reviewed", record_identifier=value.identifier)

    assert "local.review" in ids(record(), validators=[consumer])
    with pytest.raises(ValueError):
        validate(record(), level=1)


def test_370_blank_indicators_and_repeated_place():
    good = DataField("370", subfields=[Subfield("c", "대한민국"), Subfield("c", "일본")])
    assert not [i for i in validate(record(good)) if i.severity == "error"]
    assert "field.370.indicator1" in ids(record(replace(good, ind1="0")))


def test_688_content_dependency_is_separate_from_tagging():
    field = DataField("688", " ", "7", [Subfield("a", "도서관")])
    assert "field.688.source.requires" in ids(record(field))
    assert "field.688.source.requires" not in ids(record(field), level=2)
    sourced = replace(field, subfields=field.subfields + [Subfield("2", "local")])
    assert "field.688.source.requires" not in ids(record(sourced))
    assert "field.688.source.only7" in ids(record(replace(sourced, ind2=" ")))


def test_timestamp_calendar_and_008_fill():
    assert "field.005.timestamp" not in ids(record(ControlField("005", "20260916123456")))
    assert "field.005.timestamp" in ids(record(ControlField("005", "20260230123456")))
    assert "field.008.entered-date.fill" in ids(record(ControlField("008", "||||||" + " " * 34)))
