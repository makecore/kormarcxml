"""006/008 material selection must use KORMARC's own leader and positions."""

from kormarcxml import Record, ControlField
from kormarcxml.validation import validate


def check(tag, value, kind="a", bib="m", level=3):
    leader = list("00000nam a2200000   4500")
    leader[6], leader[7] = kind, bib
    return {
        i.rule_id
        for i in validate(Record("".join(leader), [ControlField(tag, value)]), level=level)
    }


def test_book_vs_continuing_resource_rules_use_bibliographic_level():
    value = list("260917s2026    ulk           000   kor  ")
    value[29] = "x"
    assert "field.008.BK.position.29" in check("008", "".join(value))
    assert "field.008.BK.position.29" not in check("008", "".join(value), bib="s")
    assert "field.008.CR.position.29" in check("008", "".join(value), bib="s")
    assert "field.008.BK.position.29" not in check("008", "".join(value), level=2)


def test_006_uses_its_own_material_code_and_kormarc_position_remap():
    # 006/09 corresponds to 008/29; 006 is 14 characters in KORMARC.
    value = list("a" + "|" * 13)
    value[9] = "x"
    assert "field.006.BK.position.09" in check("006", "".join(value), kind="m")
    value[0] = "s"
    assert "field.006.BK.position.09" not in check("006", "".join(value))
    assert "field.006.CR.position.09" in check("006", "".join(value))


def test_old_book_is_not_checked_as_modern_book():
    value = list("260917s2026    ulk           000   kor  ")
    value[19] = "!"
    assert "field.008.RB.position.19" in check("008", "".join(value), kind="w")
    assert "field.008.RB.position.19" not in check("008", "".join(value), kind="a")
