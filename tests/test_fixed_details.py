"""Behavioral tests for the reviewed fixed-field detail constraints."""

import pytest

from kormarcxml.model import ControlField, Record
from kormarcxml.validation import validate


def issues(tag, value, material="a", bibliographic="m", level=3):
    leader = list("00000nam a2200000   4500")
    leader[6], leader[7] = material, bibliographic
    return [
        issue
        for issue in validate(Record("".join(leader), [ControlField(tag, value)]), level=level)
        if ".detail." in issue.rule_id
    ]


def fixed(start, content):
    value = list(" " * 40)
    value[start : start + len(content)] = content
    return "".join(value)


@pytest.mark.parametrize("good,bad", [("a   ", " a  "), ("ab  ", "a b "), ("||||", "a|||")])
def test_book_illustrations_padding_and_whole_block_fill(good, bad):
    assert not issues("008", fixed(18, good))
    found = issues("008", fixed(18, bad))
    assert any(i.position == 18 and i.severity == "error" for i in found)
    assert not issues("008", fixed(18, bad), level=2)


@pytest.mark.parametrize("material,start,good,bad", [("e", 22, "bd", "bx"), ("c", 18, "kf", "kx")])
def test_two_character_codes_are_atomic(material, start, good, bad):
    assert not any(i.position == start for i in issues("008", fixed(start, good), material))
    assert any(i.position == start for i in issues("008", fixed(start, bad), material))


@pytest.mark.parametrize("good", ["000", "001", "999", "nnn", "---", "|||"])
def test_visual_runtime(good):
    assert not any(i.position == 18 for i in issues("008", fixed(18, good), "g"))
    assert any(i.position == 18 for i in issues("008", fixed(18, " 12"), "g"))


def test_006_uses_its_own_category_not_leader():
    assert not issues("006", "e" + " " * 4 + "bd" + " " * 7)
    assert any(i.position == 5 for i in issues("006", "e" + " " * 4 + "bx" + " " * 7))
    assert not any(i.position == 5 for i in issues("006", "a" + " " * 4 + "bx" + " " * 7))


def test_undefined_and_old_book_institution_positions():
    assert any(i.position == 18 for i in issues("008", fixed(18, "x"), "m"))
    assert not any(i.position == 18 for i in issues("008", fixed(18, " | |"), "m"))
    assert any(i.position == 26 for i in issues("008", fixed(26, "AA"), "w"))
    assert not any(i.position == 26 for i in issues("008", fixed(26, "AA"), "a"))


@pytest.mark.parametrize("good", ["001", "024", "999", "mmm", "nnn", "---", "|||"])
def test_electronic_bit_depth(good):
    assert not issues("007", "cr mn " + good)
    assert any(i.position == 6 for i in issues("007", "cr mn 000"))
    assert any(i.position == 6 for i in issues("007", "cr mn 02-"))
    assert not issues("007", "cr mn ")
    assert any(i.position == 6 for i in issues("007", "cr mn 0"))


@pytest.mark.parametrize("good", ["024", "03-", "1--", "---", "|||"])
def test_microform_partial_unknown_reduction(good):
    assert not issues("007", "he bmb" + good + "baca")
    assert any(i.position == 6 for i in issues("007", "he bmbabc" + "baca"))


def test_remote_sensing_atomic_pair_and_undefined():
    assert not issues("007", "ru ac0aabga")
    assert any(i.position == 9 for i in issues("007", "ru ac0aabgx"))
    assert any(i.position == 2 for i in issues("007", "ruxac0aabga"))
