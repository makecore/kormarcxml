"""Pinned code memberships are advisory, and distinct from normative validity."""

from dataclasses import replace
from kormarcxml import Record, ControlField
from kormarcxml.validation import validate


def record(start, text, kind="a"):
    value = list("260917s2026    ulk           000   kor  ")
    value[start : start + len(text)] = text
    leader = list("00000nam a2200000   4500")
    leader[6] = kind
    return Record("".join(leader), [ControlField("008", "".join(value))])


def table_issues(value):
    return [i for i in validate(value) if i.rule_id.startswith("code-table.")]


def test_country_padding_and_korean_specific_code():
    assert not table_issues(record(15, "ulk"))
    assert not table_issues(record(15, "us "))
    issue = next(i for i in table_issues(record(15, "!!!")) if i.rule_id.endswith("country"))
    assert issue.severity == "warning"
    assert (issue.tag, issue.position) == ("008", 15)


def test_unknown_language_is_advisory_not_a_silent_substitution():
    value = record(35, "!!!")
    before = repr(value)
    assert any(i.rule_id == "code-table.008.language" for i in table_issues(value))
    assert repr(value) == before
    assert not any(i.rule_id.startswith("code-table.") for i in validate(value, level=2))


def test_korean_national_tables_are_not_applied_to_old_book_positions():
    value = record(26, "!!", kind="w")
    value = replace(value, fields=[ControlField("008", value.fields[0].value[:38] + "!!")])
    assert not table_issues(value)
    assert any(i.rule_id == "code-table.008.university" for i in table_issues(record(26, "!!")))
