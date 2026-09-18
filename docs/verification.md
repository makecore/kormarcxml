# Verification report

## Source-audit update — 2026-09-17

351 local tests passed (including the 2026-09-18 007 and 006/008 extensions), including 249 catalog-driven transport cases with pymarc cross-checks. Ruff lint/format and Mypy passed. Demonstration UTF-8, explicit EUC-KR and six-record collection byte comparisons passed; the book has zero implemented-rule errors and one local-field information issue. See [audit](audit.md) for source review boundaries. PR #2, commit a0dacec512b3c9fa4e2e70a3d16b47521b341e14, passed all nine CI combinations (348 tests) in run 35290309650. The subsequent 006/008 extension has separate CI evidence in its pull request.

## Historical baseline — 0.1.0

Executed 2026-09-16 in the Linux Python 3.12 environment. This is an initial
working release, not completion of the full original framework scope.

| Gate | Observed result |
|---|---|
| Automated tests | 68 passed, 0 skipped |
| Ruff lint | Passed |
| Ruff format | Passed |
| Mypy | Passed for 9 library source files |
| Demonstration | Single record + 6-record collection passed |
| Same-codec byte comparison | UTF-8, explicit EUC-KR, and collection passed |
| XSD | Synthetic book and collection passed bundled independent schema |
| Semantic profile | Book: 0 errors; 2 uncovered-field warnings and 1 local-field information issue |
| Independent implementation | pymarc transport cross-check tests passed; no MARC 21 semantic equivalence claimed |
| API documentation examples | All Python blocks executed successfully |
| Build | Wheel and source distribution built successfully |
| Installed wheel | Tested outside source directory: packaged XSD/rules, validation, byte round trip passed |
| Extracted source distribution | 68 tests passed |
| GitHub Actions | Configuration supplied; remote workflow NOT executed |
| Windows/macOS | CI matrix configured; not executed in this session |
| Official LC XSD conformance | Not verified; independent bundled schema is not the LC schema |
| Full KS rule conformance | Not verified; only a partial profile is implemented |

## Demonstration

Run `python scripts/demo.py`. Machine-readable evidence is in
`examples/demo-result.json`; original and restored binaries, XML, HTML, tagged
text, validation HTML/JSON, DC, MODS and analytical CSV are in `examples/`.
The directory, Leader/00–04 record length and Leader/12–16 base address are
recalculated; for these canonical fixtures the recomputed values equal the
original values. Characters, code points (no normalization), field/subfield
order, repeats, indicators and fixed-field contents are preserved. Equality
for these fixtures is not a promise for arbitrary malformed or transcoded input.

## Benchmark

`python scripts/benchmark.py --records 10000 --output examples/benchmark.json`

10,000 synthetic 370-byte records → streaming XML → records → ISO byte comparison:
41.596 seconds, 240.4 complete round trips/second. Input 3,700,000 bytes;
XML 10,430,103 bytes. Peak traced Python allocations: 385,071 bytes.
`tracemalloc` was enabled and affects timing; native lxml/libxml2 memory is
excluded. These are measured development results, not total RSS, a throughput
promise, a comparison with LC tooling, or a production KOLIS-NET benchmark.

## Remaining acceptance gates

- Obtain the complete official KORMARC edition and amendment/code-table sources;
  the official site returned HTTP 417, and LC direct retrieval returned HTTP 403.
- Complete field-by-field semantics and conditional requirements. Eleven tags
  have some bundled rules; this does not mean eleven fully implemented fields.
- Independently verify all LC linked components, official XSD and legacy ingest
  crosswalks. LC parity remains partial, especially DC/MODS/ONIX/OAI MARC ingest.
- Acquire licensed, representative real-world records and run institutional QA.
- Execute the configured OS/Python CI matrix in the selected GitHub repository.

No full-project completion or production-readiness claim is made.
