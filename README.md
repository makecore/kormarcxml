# KORMARCXML

[한국어](README.ko.md) · [Architecture](docs/architecture.md) · [API](docs/api.md) · [Limitations](docs/limitations.md)

**An unofficial open-source framework for processing KORMARC in XML environments.**
KORMARCXML is not an official National Library of Korea or KS standard, and its
name does not designate an approved metadata format.

Version 0.1.0 provides an ordered record API, ISO 2709 ↔ XML conversion, a layered
validator, metadata crosswalks, presentations, a CLI, and streaming collection
processing. Its KORMARC bibliographic rule profile targets **KS X 6006-0:2023**
but contains only a documented, verified subset. A clean validation report is
**not full KORMARC conformance certification**.

## What works

- ISO 2709 decoding/encoding with byte-based directory calculations and strict
  encoding errors by default; explicit legacy byte codecs.
- UTF-8 XML in the familiar MARCXML generic vocabulary; ordered fields and
  subfields, repeats, blank indicators, and local fields remain in the model.
- An independently authored structural XSD; separate JSON-driven KORMARC tagging
  and content rules with machine-readable issues and institutional extensions.
- HTML, tagged text, raw JSON, Dublin Core, MODS subset, and analytics CSV.
- A reusable Python API and `convert`, `batch`, `validate`, `transform`, `inspect`
  commands, including stdin/stdout.
- Synthetic fixtures, round-trip demonstrations, malformed-input tests,
  cross-implementation structural checks, and a streaming benchmark.

The XML namespace is `http://www.loc.gov/MARC21/slim`. **Shared syntax does not
mean MARC 21 semantics.** The bundled XSD is not the official LC XSD; see the
[namespace decision](docs/adr/001-xml-transport.md). Dublin Core and MODS exports
are lossy mappings, not transport round trips.

## Install from this checkout

Requires Python 3.11 or newer. The package is not claimed to be published on PyPI.

```sh
python -m venv .venv
```

Activate on macOS/Linux with `source .venv/bin/activate`, or in Windows PowerShell
with `.venv\Scripts\Activate.ps1`. Then:

```sh
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps -e .
kormarcxml --help
```

The lock pins the development environment; operating-system-specific binary
wheels may differ. For library-only use, `python -m pip install .` resolves the
runtime dependencies declared in `pyproject.toml`.

## Reproduce a complete workflow

Run from the repository root:

```sh
python scripts/demo.py
kormarcxml convert examples/book.mrc --from iso2709 --to xml -o examples/converted.xml
kormarcxml validate examples/converted.xml --level 1
kormarcxml validate examples/converted.xml --level 3 -o examples/report.jsonl
kormarcxml transform examples/converted.xml --to html -o examples/catalog.html
kormarcxml transform examples/converted.xml --to tagged -o examples/tagged.txt
kormarcxml convert examples/converted.xml --to iso2709 -o examples/restored.mrc
python -c "from pathlib import Path; assert Path('examples/book.mrc').read_bytes() == Path('examples/restored.mrc').read_bytes()"
```

The demo generates synthetic examples and asserts structural, code-point, and
same-encoding byte equality for its canonical UTF-8 and explicit EUC-KR fixtures.
It also processes a six-record collection. Results are written to
`examples/demo-result.json`. These are transport demonstrations, not proof that
all material-specific KORMARC content rules are implemented.

For collections and legacy input:

```sh
kormarcxml batch examples/collection.mrc --from iso2709 --to xml -o examples/batch.xml
kormarcxml transform examples/batch.xml --to html --output-dir examples/pages
kormarcxml convert examples/book-euc-kr.mrc --from iso2709 --encoding euc-kr --to xml -o examples/legacy.xml
```

`-` denotes stdin/stdout; diagnostics go to stderr. Binary pipes require a shell
that preserves bytes: on macOS/Linux, for example,
`kormarcxml convert examples/book.mrc --from iso2709 --to xml | kormarcxml validate -`.
Use files for binary ISO 2709 output in shells whose native-command pipelines
transcode bytes. Named output files are promoted atomically on success. Standard output and
output directories can be partial on failure; check exit codes before consuming
a batch result. Exit codes are 0 for success, 1 for validation
errors, and 2 for fatal processing errors.

## API

```python
from kormarcxml import iter_iso2709, write_xml
from kormarcxml.validation import validate

with open("examples/book.mrc", "rb") as source:
    for record in iter_iso2709(source):
        print(record.identifier, validate(record))

with open("examples/collection.mrc", "rb") as source:
    with open("examples/api-collection.xml", "wb") as output:
        write_xml(iter_iso2709(source), output)
```

See [API and extensions](docs/api.md) for editing, schema checks, custom
validators, and custom consumers of the XML bus.

## Verify and benchmark

```sh
python -m ruff check .
python -m ruff format --check .
python -m mypy src/kormarcxml
python -m pytest -q
python scripts/demo.py
python scripts/benchmark.py --records 10000
python -m build
```

GitHub Actions is configured for Linux, Windows, and macOS with Python
3.11–3.13. A workflow file is not evidence of a remote CI run: inspect the actual
Actions results after publishing. The benchmark reports throughput and Python
allocation measurements; native XML-library allocations are excluded.

## Documentation map

| Topic | Document |
|---|---|
| Architecture, bus, security | [Architecture](docs/architecture.md) |
| Namespace choice | [ADR 001](docs/adr/001-xml-transport.md) |
| Language and tooling | [ADR 002](docs/adr/002-stack.md) |
| Record API and extensions | [API](docs/api.md) |
| Physical format and round trip | [ISO 2709](docs/iso2709.md) |
| Character codecs | [Encoding](docs/encoding.md) |
| Rule coverage and reports | [Validation](docs/validation.md) |
| Crosswalk scope and loss | [Transformations](docs/transformations.md) |
| LC component inventory | [LC parity matrix](docs/lc-parity.md) |
| Official evidence | [KORMARC sources](docs/kormarc-sources.md) |
| Reuse and licensing | [Provenance](docs/provenance-license.md) |
| Executed verification | [Verification](docs/verification.md) |
| Unsupported behavior | [Limitations](docs/limitations.md) |
| Future milestones | [Roadmap](docs/roadmap.md) |

Original project code is MIT licensed. Consult provenance documentation before
adding externally sourced schemas, stylesheets, standards text, or production
data. Official source retrieval was incomplete during initial development;
provenance distinguishes directly read material from official search excerpts.
