# Known limitations and claim boundaries

This document is part of the release contract. No result should be described as
full KORMARC conformance, official certification, or universally lossless.

| Area | Current boundary | Consequence |
|---|---|---|
| Official source review | Some primary pages were unavailable directly; evidence includes official search-index excerpts | Whole-standard verification remains incomplete; see source ledger |
| Semantic coverage | Only the bundled, source-linked bibliographic subset is implemented | A clean report does not establish KS X 6006-0:2023 conformance |
| Unverified fields | Retained with coverage warnings; 9XX retained with informational issues | Unknown does not mean invalid, or verified |
| Authority/holdings | Generic transport only, no dedicated verified semantic profiles | Do not apply the bibliographic validator as an authority/holdings validator |
| XML interoperability | MARCXML vocabulary, independently authored XSD | Passing our XSD does not mean passing LC's official XSD |
| XML metadata | Unsupported attributes are rejected; comments and processing instructions are not retained | This is a logical MARC transport, not an arbitrary XML document archive |
| Physical preservation | Directory, lengths, base address and delimiters are regenerated | Byte identity requires canonical input and the same encoding |
| Encoding provenance | Codec is supplied by caller and is not stored in the record | Keep a job manifest when exact output encoding matters |
| Legacy encodings | Explicit UTF-8, EUC-KR, CP949, ASCII codecs only | KS X 1001 character repertoire is not a universal byte-decoding instruction |
| Encoding recovery | Replacement decoding emits warnings; output encoding is strict | Replacement is irreversible; default strict mode is preferable |
| Unicode | No normalization; XML 1.0 character limits apply | Unsupported control characters are rejected, not silently removed |
| ISO layout | Leader layout 22/4500; conventional directory widths | Unsupported layouts and oversized physical records are rejected |
| Malformed records | One directory-order recovery case; otherwise safe rejection | No general resynchronization, repair, or quarantine pipeline |
| DC/MODS | Conservative partial crosswalks | Unmapped values and distinctions are omitted; no reversible crosswalk claim |
| MODS validation | Mapping tests do not imply exhaustive official MODS schema coverage | External schema validation and broader mappings remain release work |
| CSV | Leader omitted; values preserved without formula neutralization | Treat cells as text when importing; CSV is an analysis export |
| RDF/BIBFRAME/JSON-LD | Not implemented | Extension interfaces and plans are not implemented exporters |
| Historic LC ingest tools | ONIX, OAI MARC, MARC DTD ingest not implemented | See parity matrix for justification and evidence |
| CLI transforms | Multiple records require an output directory | No single aggregate DC/MODS/HTML document command |
| XML XSD memory | Whole-document schema gate capped at 10 MiB | Use per-record validation for large collections and distinguish collection constraints |
| Performance evidence | Synthetic benchmark; Python allocations exclude native XML allocations | Do not infer total RSS, production throughput, or capacity from it |
| Test data | Synthetic transport cases and regression fixtures | Material-type codes do not demonstrate exhaustive content-rule coverage |
| Model immutability | Frozen dataclasses contain mutable lists | Do not mutate lists shared between records |
| Remote CI | Configuration is included | Local test success does not prove all remote OS/Python jobs passed |

CLI named output files are promoted atomically only on successful processing.
Standard output and per-record output directories may contain partial results if
a later record fails. Applications must inspect exit status and manage failed
batch artifacts accordingly. Schema and semantics are separate API gates; the
CLI combines per-record XSD checks with level 2/3 validation, while `--level 1`
checks the original bounded XML document.

The original source code is MIT licensed. This does not license official KS/NLK
text or third-party assets. Full standards text and production records are not
bundled. See [provenance and licensing](provenance-license.md).
