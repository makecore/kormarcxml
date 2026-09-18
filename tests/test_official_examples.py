"""Test cache verifier with independent tiny HTML, not copied official prose."""

import importlib.util
from pathlib import Path

from lxml import html
import pytest

spec = importlib.util.spec_from_file_location(
    "official_verifier", Path(__file__).resolve().parents[1] / "scripts/verify_official_examples.py"
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_displayed_indicators_and_text_are_preserved_without_normalization():
    field = verifier.parse_field(
        html.fromstring("<li><span>245</span> 0<span>b/</span>▾ae\u0301 한글  ▾a반복 </li>")
    )
    assert (field.ind1, field.ind2) == ("0", " ")
    assert [(s.code, s.value) for s in field.subfields] == [("a", "e\u0301 한글  "), ("a", "반복 ")]


def test_missing_indicator_is_never_silently_repaired():
    with pytest.raises(ValueError):
        verifier.parse_field(html.fromstring("<li>880 1▾aTest</li>"))


def test_hidden_groups_require_explicit_opt_in():
    raw = (
        b'<div style="display: none"><ul class="giho"><li>245 00\xe2\x96\xbeaTest </li></ul></div>'
    )
    omitted = verifier.verify(raw)
    assert omitted["groups"][0]["status"] == "excluded-hidden"
    assert omitted["collection_round_trip_records"] == 0
    included = verifier.verify(raw, include_hidden=True)
    group = included["groups"][0]
    assert group["generated_iso_bytes_equal"]
    assert not group["semantic_certification"]
    assert included["collection_round_trip_records"] == 1
    assert not included["source_contains_complete_iso_records"]


def test_invalid_group_excluded_whole_not_partially_converted():
    raw = '<ul class="giho"><li>245 00▾aTest</li><li>880 1▾aBad</li></ul>'.encode()
    report = verifier.verify(raw)
    assert report["groups"][0]["status"] == "unparseable-without-editorial-repair"
    assert report["collection_round_trip_records"] == 0
