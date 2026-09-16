"""Streaming command-line adapter; core APIs never depend on argparse."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from dataclasses import asdict
import json
from pathlib import Path
import sys
import os
import tempfile

from .errors import KormarcError
from .iso2709 import encode_record, iter_iso2709
from .xmlio import iter_xml, record_to_xml, schema_validate, write_xml
from .validation import validate
from .transforms import transform


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="KORMARCXML: unofficial KORMARC XML framework")
    p.add_argument("--version", action="version", version="KORMARCXML 0.1.0")
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("convert", "batch", "validate", "transform", "inspect"):
        c = commands.add_parser(name)
        c.add_argument("input", nargs="?", default="-", help="path or - for stdin")
        c.add_argument("-o", "--output", default="-", help="path or - for stdout")
        c.add_argument("--from", dest="source", choices=("iso2709", "xml"), default="xml")
        c.add_argument("--encoding", help="ISO byte codec; required for non-Unicode leaders")
        if name in ("convert", "batch"):
            c.add_argument("--to", dest="target", choices=("iso2709", "xml"), required=True)
            c.add_argument("--output-encoding", help="output ISO codec (default: leader-dependent)")
        if name == "validate":
            c.add_argument("--level", type=int, choices=(1, 2, 3), default=3)
            c.add_argument("--profile", help="institutional JSON rule registry")
        if name == "transform":
            c.add_argument(
                "--to",
                dest="target",
                required=True,
                choices=("html", "tagged", "raw", "dc", "mods", "json", "csv"),
            )
            c.add_argument("--output-dir", help="one document per record; filenames are sequential")
    return p


class AtomicOutput:
    """Commit a named output only after the entire command succeeds."""

    def __init__(self, path):
        self.path = Path(path)
        self.temporary = None

    def __enter__(self):
        fd, self.temporary = tempfile.mkstemp(prefix=".kormarcxml-", dir=self.path.parent)
        self.stream = os.fdopen(fd, "wb")
        return self.stream

    def __exit__(self, kind, value, traceback):
        assert self.temporary is not None
        try:
            self.stream.close()
            if kind is None:
                os.replace(self.temporary, self.path)
            else:
                os.unlink(self.temporary)
        except OSError:
            if self.temporary and os.path.exists(self.temporary):
                os.unlink(self.temporary)
            raise


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.input != "-" and args.output != "-":
        if Path(args.input).resolve() == Path(args.output).resolve():
            print("Input and output must be different files.", file=sys.stderr)
            return 2
    try:
        with ExitStack() as stack:
            source = (
                sys.stdin.buffer
                if args.input == "-"
                else stack.enter_context(open(args.input, "rb"))
            )
            dest = (
                sys.stdout.buffer
                if args.output == "-"
                else stack.enter_context(AtomicOutput(args.output))
            )
            if args.command == "validate" and args.level == 1:
                if args.source != "xml":
                    raise ValueError("Level 1 is XML schema validation; use level 2 for ISO 2709")
                issues = schema_validate(source)
                for issue in issues:
                    dest.write(
                        (json.dumps(asdict(issue), ensure_ascii=False) + "\n").encode("utf-8")
                    )
                return 1 if any(i.severity in ("error", "fatal") for i in issues) else 0
            records = (
                iter_iso2709(source, encoding=args.encoding)
                if args.source == "iso2709"
                else iter_xml(source)
            )
            if args.command in ("convert", "batch"):
                if args.target == "xml":
                    write_xml(records, dest)
                else:
                    for record in records:
                        dest.write(
                            encode_record(record, encoding=args.output_encoding or args.encoding)
                        )
                return 0
            failed = False
            count = 0
            for count, record in enumerate(records, 1):
                if args.command == "validate":
                    issues = schema_validate(record_to_xml(record)) + validate(
                        record, level=args.level, profile=args.profile
                    )
                    failed |= any(i.severity in ("error", "fatal") for i in issues)
                    payload = {
                        "record": count,
                        "record_identifier": record.identifier,
                        "issues": [asdict(i) for i in issues],
                        "scope": "partial KORMARC profile; no-issues is not full conformance",
                    }
                    dest.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
                elif args.command == "inspect":
                    dest.write((transform(record, "json") + "\n").encode("utf-8"))
                else:
                    if not args.output_dir and count > 1:
                        raise ValueError(
                            "Multiple records: use --output-dir for separate valid documents"
                        )
                    data = transform(record, args.target).encode("utf-8")
                    if args.output_dir:
                        outdir = Path(args.output_dir)
                        outdir.mkdir(parents=True, exist_ok=True)
                        suffix = {"raw": "json", "dc": "xml", "mods": "xml", "tagged": "txt"}.get(
                            args.target, args.target
                        )
                        (outdir / f"record-{count:08d}.{suffix}").write_bytes(data)
                    else:
                        dest.write(data)
            print(f"Processed {count} record(s).", file=sys.stderr)
            return 1 if failed else 0
    except (KormarcError, ValueError, OSError) as exc:
        payload = (
            exc.issue.to_dict()
            if isinstance(exc, KormarcError)
            else {"severity": "fatal", "message": str(exc)}
        )
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2
