"""Cross-field KORMARC content checks, independently tested from transport."""

import pytest
from kormarcxml import Record, ControlField, DataField, Subfield
from kormarcxml.validation import validate


def record(position, code, *fields):
    fixed = list("260917s2026    ulk           000   kor  ")
    fixed[position] = code
    return Record("00000nam a2200000   4500", [ControlField("008", "".join(fixed)), *fields])


def ids(value, level=3):
    return {i.rule_id for i in validate(value, level=level)}


@pytest.mark.parametrize("code", list("bhrsx"))
def test_modified_code_requires_890_without_mutation(code):
    value = record(28, code)
    before = repr(value)
    assert "record.008.modified.requires-890" in ids(value)
    assert repr(value) == before
    assert "record.008.modified.requires-890" not in ids(value, level=2)
    assert "record.008.modified.requires-890" not in ids(
        record(28, code, DataField("890", subfields=[Subfield("a", "unencoded")]))
    )


def test_unknown_cataloging_source_requires_transcriber_and_excludes_original_source():
    missing = record(32, "u")
    assert "record.008.unknown-source.requires-040c" in ids(missing)
    good = DataField("040", subfields=[Subfield("c", "011001")])
    assert "record.008.unknown-source.requires-040c" not in ids(record(32, "u", good))
    bad = DataField("040", subfields=[Subfield("a", "011001"), Subfield("c", "011001")])
    assert "record.008.unknown-source.forbids-040a" in ids(record(32, "u", bad))
    assert "record.008.unknown-source.forbids-040a" not in ids(record(32, " ", bad))


def test_country_fill_is_rejected_without_conflating_with_form_of_item_conflict():
    value = record(15, "|")
    assert "field.008.country.fill" in ids(value)
    assert "field.008.country.fill" not in ids(value, level=2)


def test_relation_reports_source_position_and_record_identifier():
    value = record(28, "h", ControlField("001", "audit-case"))
    issue = next(i for i in validate(value) if i.rule_id == "record.008.modified.requires-890")
    assert (issue.record_identifier, issue.tag, issue.position, issue.occurrence) == (
        "audit-case",
        "008",
        28,
        1,
    )
