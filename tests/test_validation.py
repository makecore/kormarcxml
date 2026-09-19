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
    assert not [
        i
        for i in validate(record(title))
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]
    assert "field.245.repeatability" in ids(record(title, title))


def test_kormarc_ddc_institution_indicator_and_coded_content():
    good = DataField(
        "082", "7", "1", [Subfield("a", "020"), Subfield("2", "23"), Subfield("m", "a")]
    )
    assert not [
        i
        for i in validate(record(good))
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]
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
    assert not [
        i
        for i in validate(record(good))
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]
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


def test_coverage_counts_checks_not_labels_or_provenance():
    base = coverage()
    metadata = {"fields": {"999": {"label": "Local", "source": "local policy", "repeatable": True}}}
    extended = coverage(metadata)
    assert extended["field_rules"] == base["field_rules"]
    assert extended["field_rule_counts"]["999"] == 0
    assert "999" in extended["fields_without_constraints"]
    asserted = coverage(
        {
            "fields": {
                "999": {
                    "required": True,
                    "repeatable": False,
                    "indicators": {"1": [" "]},
                    "closed_subfields": True,
                    "subfields": {
                        "a": {
                            "required": True,
                            "repeatable": False,
                            "rules": [
                                {"id": "local.value", "values": ["x"], "message": "Expected x"}
                            ],
                        }
                    },
                }
            }
        }
    )
    assert asserted["field_rule_counts"]["999"] == 7
    assert asserted["field_rules"] == base["field_rules"] + 7


def test_condition_retains_severity_and_remediation():
    profile = {
        "fields": {
            "999": {
                "conditions": [
                    {
                        "id": "local.condition",
                        "indicator": 2,
                        "equals": "7",
                        "requires": ["2"],
                        "message": "Missing source",
                        "severity": "warning",
                        "remediation": "Add source",
                    }
                ]
            }
        }
    }
    value = record(DataField("999", " ", "7", []))
    issue = next(i for i in validate(value, profile=profile) if i.rule_id == "local.condition")
    assert issue.severity == "warning"
    assert issue.remediation == "Add source"
    assert "local.condition" not in ids(value, profile=profile, level=2)


def test_content_rule_cannot_pass_with_missing_positions():
    profile = {
        "fields": {
            "009": {
                "rules": [
                    {
                        "id": "local.positions",
                        "start": 2,
                        "end": 5,
                        "forbidden": ["|"],
                        "message": "Positions 2 through 4 required",
                    }
                ]
            }
        }
    }
    assert "local.positions" in ids(record(ControlField("009", "ab")), profile=profile)
    assert "local.positions" not in ids(record(ControlField("009", "abcde")), profile=profile)


@pytest.mark.parametrize("delimiter", ["\x1d", "\x1e", "\x1f"])
def test_logical_record_delimiters_reported_before_serialization(delimiter):
    value = record(
        ControlField("001", "ab" + delimiter),
        DataField("999", subfields=[Subfield("a", "xy" + delimiter)]),
    )
    findings = [i for i in validate(value, level=2) if i.rule_id == "structure.delimiter"]
    assert [(i.tag, i.subfield, i.position) for i in findings] == [
        ("001", None, 2),
        ("999", "a", 2),
    ]


@pytest.mark.parametrize("code", ["2", "9"])
def test_245_filing_indicator_is_not_marc21_character_count(code):
    field = DataField("245", "2", code, [Subfield("a", "제목")])
    assert "field.245.indicator2" in ids(record(field), level=2)
    assert "field.245.indicator1" not in ids(record(field), level=2)


def test_245_parallel_title_repeats_but_material_designation_does_not():
    field = DataField(
        "245",
        "0",
        "0",
        [
            Subfield("x", "Parallel one"),
            Subfield("x", "Parallel two"),
            Subfield("h", "[text]"),
            Subfield("h", "[text]"),
        ],
    )
    found = ids(record(field))
    assert "field.245.subfield.h.repeatability" in found
    assert "field.245.subfield.x.repeatability" not in found
    assert "field.245.subfield.allowed" not in found


@pytest.mark.parametrize(
    "position,good,bad",
    [
        (5, "p", "x"),
        (6, "w", "z"),
        (7, "i", "z"),
        (8, "a", "z"),
        (17, "7", "6"),
        (18, "n", "z"),
        (19, "c", "z"),
    ],
)
def test_reviewed_leader_code_domains(position, good, bad):
    original = record()

    def changed(code):
        return replace(
            original, leader=original.leader[:position] + code + original.leader[position + 1 :]
        )

    assert not [
        i
        for i in validate(changed(good))
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]
    assert [
        i
        for i in validate(changed(bad))
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]
    assert not [
        i
        for i in validate(changed(bad), level=2)
        if i.severity == "error" and not i.rule_id.startswith("application.")
    ]


def test_006_material_cannot_be_fill_and_has_korean_old_book():
    assert "field.006.material" not in ids(record(ControlField("006", "w" + "|" * 13)))
    assert "field.006.material" in ids(record(ControlField("006", "|" * 14)))


@pytest.mark.parametrize(
    "start,value,rule",
    [
        (6, "z", "date-type"),
        (28, "a", "modified"),
        (32, "b", "cataloging-source"),
        (7, "||||", "year1.fill"),
        (11, "2|||", "year2.mixed-fill"),
    ],
)
def test_008_kormarc_common_positions(start, value, rule):
    data = list("260917s2026    ulk           000   kor  ")
    assert len(data) == 40
    data[start : start + len(value)] = value
    result = record(ControlField("008", "".join(data)))
    assert "field.008." + rule in ids(result)
    assert "field.008." + rule not in ids(result, level=2)


def test_holdings_delegation_is_reported_not_silently_certified():
    issues = validate(record(DataField("841", subfields=[Subfield("a", "local")])))
    assert any(
        i.rule_id == "coverage.delegated-holdings" and i.severity == "warning" for i in issues
    )
    assert not any(i.rule_id == "field.841.subfield.allowed" for i in issues)


def test_886_embedded_foreign_subfield_can_repeat_reserved_code():
    field = DataField(
        "886",
        "2",
        " ",
        [
            Subfield("2", "foreign"),
            Subfield("a", "245"),
            Subfield("b", "00"),
            Subfield("a", "foreign title"),
        ],
    )
    assert "field.886.subfield.a.repeatability" not in ids(record(field))


def test_later_template_pages_keep_both_indicators():
    assert "field.881.indicator2" in ids(record(DataField("881", " ", "1")))
    assert "field.880.indicator2" not in ids(record(DataField("880", "1", "1")))


def test_public_registry_mutation_cannot_change_cached_validator():
    registry = load_registry()
    registry["fields"]["245"]["indicators"]["2"].append("9")
    assert "field.245.indicator2" in ids(record(DataField("245", "0", "9")))
    assert "9" not in load_registry()["fields"]["245"]["indicators"]["2"]
