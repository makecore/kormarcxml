"""007 material-specific regression cases; synthetic, not catalog records."""

from kormarcxml import ControlField, Record
from kormarcxml.validation import validate


def issues(value, level=3):
    record = Record("00000nam a2200000   4500", [ControlField("007", value)])
    return {i.rule_id for i in validate(record, level=level)}


def test_map_length_and_color_are_material_specific():
    assert not issues("aj canzn")
    assert "field.007.a.length" in issues("aj canz", level=2)
    assert "field.007.a.position.03" in issues("aj zanzn")
    assert "field.007.a.position.03" not in issues("aj zanzn", level=2)
    assert not any(k.startswith("field.007.c.") for k in issues("aj zanzn"))


def test_electronic_mandatory_prefix_and_optional_tail():
    assert not issues("cr||||")
    assert "field.007.c.length" in issues("cr|||", level=2)
    assert "field.007.c.length" in issues("cr" + "|" * 13, level=2)
    # An optional position is still checked when supplied.
    assert "field.007.c.position.09" in issues("cr|||||||!")


def test_material_category_is_required_and_old_book_is_distinct():
    assert "field.007.category" in issues("|")
    assert "field.007.category" in issues("")
    assert not issues("ou")
    assert "field.007.o.length" in issues("ou ")


def test_text_and_unspecified_are_two_position_layouts():
    assert not issues("ta")
    assert not issues("zu")
    assert "field.007.t.length" in issues("ta ")
