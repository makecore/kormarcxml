# LC MARCXML parity inventory

Research date: 2026-09-16. This is a capability inventory and implementation
checklist, not a claim of complete LC compatibility or KORMARC standards
certification. KORMARCXML is an independent framework.

## Evidence status

Direct retrieval of the LC MARCXML home, design, architecture, XSD, MODS and legal
pages returned HTTP 403 in this environment. Official search-index text confirmed
the component families below, but **all linked files have not been fetched or
audited**. Rows labelled `inventory pending` retain requested/historical
components as a checklist and do not assert that a current downloadable asset was
inspected. No LC source code, XSD or stylesheet was copied into this repository.
Successful primary-source reads of OAI and ABES are recorded in ADR 001.

`Core` means implemented functionality subject to the repository test results;
`partial` means bounded mapping/rule coverage; `deferred` means no supported
implementation. Test references identify test areas, not an unexecuted claim of
passing tests. See the generated verification report for actual results.

## Matrix

| LC MARCXML component | LC purpose | KORMARCXML counterpart | Implementation status | Differences | Modern improvement | Tests | Source/reference |
|---|---|---|---|---|---|---|---|
| Architecture | Processing framework | Core XML bus + consumers | Core | KORMARC semantics isolated | Reusable API / streaming | End-to-end demo | [Architecture](https://www.loc.gov/standards/marcxml/marcxml-architecture.html), indexed |
| Design considerations | Generic, reversible representation | ADR 001, round-trip contract | Core | Independent structural XSD | Explicit equivalence criteria | Round-trip / ordering | [Design](https://www.loc.gov/standards/marcxml/marcxml-design.html), indexed |
| Uses and features | Explain application patterns | Architecture / API documentation | Core | Institutional extension examples | API + CLI | CLI integration | [LC index](https://www.loc.gov/standards/marcxml/), indexed heading |
| Schema | XML structural grammar | Bundled XSD | Core | Not identical to official LC XSD | Separate semantics / security | Schema positives/negatives | [LC XSD](https://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd), retrieval blocked |
| MARCXML Illustrated | Visual explanation | Architecture diagram / worked examples | Core counterpart; inventory pending | Original documentation | Executable demonstration | Example workflow | [LC index](https://www.loc.gov/standards/marcxml/) |
| Example documents / MARCXML instance / collection | Demonstrate representations | Synthetic KORMARC fixtures | Core | Not copied LC records | Korean, Hanja, repeated data | Fixtures / collections | [OAI example](https://www.openarchives.org/OAI/2.0/guidelines-marcxml.htm), directly read |
| MARC 21 ↔ MARCXML conversion | Binary/XML conversion | KORMARC ISO 2709 ↔ XML | Core | KORMARC encoding contract | Strict decoding / streaming | Binary / XML / round-trip | [LC index](https://www.loc.gov/standards/marcxml/), indexed |
| MARCXML Toolkit | Java conversion utilities | Python library and CLI | Core | New implementation | Packaging / CI / Unix pipes | CLI / library integration | [LC index](https://www.loc.gov/standards/marcxml/), indexed Java toolkit description |
| Character conversion | Character-set conversion | Explicit Python codecs and policies | Partial | No MARC-8 equivalence claim; legacy Korean encoding is explicit | No silent replacement | Invalid sequences / Unicode / Korean encoding | [LC index](https://www.loc.gov/standards/marcxml/), indexed |
| MODS output stylesheet (index names v3.7) | Richer descriptive crosswalk | MODS subset export | Partial | KORMARC mapping, not MARC 21 stylesheet reuse | Mapping-loss documentation | MODS values / XML structure | [LC index](https://www.loc.gov/standards/marcxml/), indexed |
| MODS → MARCXML | Ingest MODS | Future ingest adapter | Deferred | Cannot reconstruct omitted MARC detail | Require provenance / explicit defaults | Not supported | [MODS](https://www.loc.gov/standards/mods/), retrieval blocked; [MARBI record](https://www.loc.gov/marc/marbi/minutes/mw-03.html), indexed |
| RDF-encoded simple Dublin Core | RDF/DC projection | DC export; future RDF serializer | Partial DC; RDF deferred | DC XML is not RDF | Explicit projection limitations | DC mapping | [LC index](https://www.loc.gov/standards/marcxml/), indexed |
| OAI-encoded simple Dublin Core | OAI DC projection | OAI DC XML export | Partial | Selected KORMARC fields | Deterministic mapping | DC namespaces / values | [MARBI record](https://www.loc.gov/marc/marbi/minutes/mw-03.html), indexed |
| SRW-encoded simple Dublin Core | SRW wrapper | Future SRW adapter | Deferred; inventory pending | No SRU/SRW server | Keep transport wrapper external | Not supported | [LC index](https://www.loc.gov/standards/marcxml/) |
| Dublin Core → MARCXML | DC ingest | Future ingest adapter | Deferred | Requires defaults, cannot infer cataloguing facts | Reject fabricated enrichment | Not supported | [MARBI record](https://www.loc.gov/marc/marbi/minutes/mw-03.html), indexed |
| OAI MARC → MARCXML | Legacy format migration | Future explicit OAI MARC ingest | Deferred | Current core accepts generic MARCXML only | Versioned ingest contract | Not supported | [OAI migration guidance](https://www.openarchives.org/OAI/2.0/guidelines-marcxml.htm), directly read |
| ONIX → MARCXML stylesheet / conversion utility | Publisher metadata ingest | Future KORMARC ONIX crosswalk | Deferred | MARC 21 mappings are not KORMARC mappings | Require ONIX-version and Korean mapping fixtures | Not supported | [ONIX mapping](https://www.loc.gov/marc/marc2onix.html), indexed |
| MARCXML → MARC DTD: bibliographic | Legacy XML dialect | Future external adapter | Deferred; inventory pending | No DTD generation | Avoid external DTD dependency | Not supported | [LC index](https://www.loc.gov/standards/marcxml/) |
| MARCXML → MARC DTD: authority | Legacy authority XML dialect | Future external adapter | Deferred; inventory pending | Authority semantics out of initial scope | Profile-based extension | Not supported | [LC index](https://www.loc.gov/standards/marcxml/) |
| MARCXML → MARC DTD: mixed / reverse conversion | Legacy interoperability | Future dialect adapter | Deferred; inventory pending | Exact direction/assets need audit | Do not guess legacy grammar | Not supported | [LC index](https://www.loc.gov/standards/marcxml/) |
| HTML tagged presentation | Numeric MARC display | Tagged output + HTML | Core | KORMARC labels | UTF-8 / escaped user data | Presentation / escaping | [LC index](https://www.loc.gov/standards/marcxml/), asset audit pending |
| English-labelled HTML presentation | Human-readable display | Korean cataloguer HTML | Core | Localized labels from registry | Presentation separated from data | HTML / repeated fields | [LC index](https://www.loc.gov/standards/marcxml/), asset audit pending |
| Validation stylesheet / validator | MARC rule checking | Three-level validator | Partial | KORMARC registry only | Structured issue IDs / provenance | Rules / fixed fields / reports | [Design](https://www.loc.gov/standards/marcxml/marcxml-design.html), indexed |
| Related XML formats: MODS, MADS, METS, SRU | Ecosystem links | Roadmap / adapter boundaries | Partial MODS; others deferred | No implicit authority or packaging support | Explicit interfaces | Supported targets only | [RFC 6207](https://www.rfc-editor.org/info/rfc6207/), indexed |
| FRBR Display Tool (related LC tool) | Group/display records | Future grouping consumer | Deferred | No identity resolution or deduplication claim | Can consume the bus without modifying transport | Not supported | [LC FRBR tool](https://www.loc.gov/marc/marc-functional-analysis/tool.html), indexed |
| Specialized MARC tools directory | Link external implementations | Cross-implementation test approach | Partial | Tool listing is not endorsement | Independent binary reader checks | Interoperability tests | [LC tools](https://www.loc.gov/marc/marctools.html), indexed |
| Toolkit download / survey / feedback | Distribution and feedback | Python package / GitHub-ready repository | Core package; remote pending | No Java binary reuse | CI and versioned releases | Build / install smoke | [LC survey](https://www.loc.gov/standards/marcxml/marcxml-survey.php), indexed |
| JSON / CSV (project extension) | Not claimed as historical LC parity | Ordered JSON / analytical CSV | Core | CSV is a projection | Modern pipeline integration | JSON order / CSV export | Project implementation |
| JSON-LD / RDF / BIBFRAME / SHACL (project extension) | Future linked data layer | Adapter roadmap | Deferred | Not implemented or lossless | Separate identity and semantic design | Not supported | Project roadmap |

## What remains before claiming full parity

1. Retrieve and inventory every actual LC index hyperlink, recording redirects,
   asset version, content hash, availability and per-file license. In particular,
   verify Illustrated, all DC dialects, all DTD variants, exact presentation and
   validation stylesheet filenames, and ancillary toolkit files.
2. Test against a separately acquired official LC XSD. The independent bundled
   schema is not a substitute for this cross-implementation gate.
3. Build reviewed KORMARC ingest crosswalks for DC, MODS, ONIX and OAI MARC with
   representative source fixtures; record every inferred/defaulted value.
4. Expand the KORMARC rule registry and national code tables using verified
   provenance. A passing partial validator is not proof of full conformance.

Legacy adapters are deferred because unsupported semantic defaults would be
more damaging than an explicit unsupported-format result. They can be added as
bus consumers/producers without rewriting binary parsing. These omissions mean
that this release does **not** claim full LC feature parity.
