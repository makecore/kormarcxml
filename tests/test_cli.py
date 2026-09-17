"""Executable CLI integration and failed-write safety."""

import json
import os
from pathlib import Path
import subprocess
import sys

from kormarcxml import ControlField, Record, encode_record

ROOT = Path(__file__).resolve().parents[1]


def run(*args, data=None):
    return subprocess.run(
        [sys.executable, "-m", "kormarcxml", *map(str, args)],
        input=data,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )


def test_pipe_roundtrip_and_schema():
    raw = encode_record(Record("00000nam a2200000   4500", [ControlField("001", "cli")]))
    xml = run("convert", "--from", "iso2709", "--to", "xml", data=raw)
    assert xml.returncode == 0, xml.stderr
    assert run("validate", "--level", "1", data=xml.stdout).returncode == 0
    back = run("batch", "--to", "iso2709", data=xml.stdout)
    assert back.returncode == 0 and back.stdout == raw


def test_failed_conversion_preserves_output(tmp_path):
    source, dest = tmp_path / "bad.mrc", tmp_path / "out.xml"
    raw = encode_record(Record("00000nam a2200000   4500", [ControlField("001", "cli")]))
    source.write_bytes(raw + b"broken")
    dest.write_bytes(b"previous result")
    result = run("convert", source, "--from", "iso2709", "--to", "xml", "-o", dest)
    assert result.returncode == 2
    assert dest.read_bytes() == b"previous result"
    assert not list(tmp_path.glob(".kormarcxml-*"))
    assert json.loads(result.stderr)["rule_id"] == "iso.framing"


def test_validation_levels_include_schema():
    xml = b'<record xmlns="http://www.loc.gov/MARC21/slim"><leader>short</leader></record>'
    result = run("validate", "--level", "3", data=xml)
    assert result.returncode == 1
    assert "xml.schema" in {i["rule_id"] for i in json.loads(result.stdout)["issues"]}


def test_raw_extension_and_same_file(tmp_path):
    source = ROOT / "examples/book.xml"
    result = run("transform", source, "--to", "raw", "--output-dir", tmp_path)
    assert result.returncode == 0, result.stderr
    assert (
        json.loads((tmp_path / "record-00000001.json").read_text(encoding="utf-8"))["format"]
        == "kormarcxml-record-1"
    )
    duplicate = tmp_path / "same.xml"
    duplicate.write_bytes(source.read_bytes())
    before = duplicate.read_bytes()
    assert run("convert", duplicate, "--to", "xml", "-o", duplicate).returncode == 2
    assert duplicate.read_bytes() == before
