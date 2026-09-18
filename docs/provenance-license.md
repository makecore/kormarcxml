# Provenance and licensing

KORMARCXML is an independently developed open-source framework for processing
KORMARC in XML. It is not published or certified by the National Library of Korea,
the Korean Standards authorities, or the Library of Congress.

## Project material

The project license covers original code, independently written schema and
stylesheets, documentation, and synthetic examples. See `LICENSE` for the exact
terms. It does not relicense KORMARC/KS explanatory text, LC assets, third-party
packages, or real cataloguing records. Synthetic fixtures are test data, not an
official bibliography, authoritative cataloguing example, or complete gold set.

## Sources and reuse policy

| Source | Purpose | Material included here | License/reuse status |
|---|---|---|---|
| [NLK KORMARC integrated bibliographic format](https://librarian.nl.go.kr/kormarc/KSX6006-0/index.html) | KORMARC rules and technical facts | Short identifiers, field codes, executable constraints, source URLs and original explanations | Do not assume the complete KS text or all website assets can be redistributed; no wholesale standard copy |
| KS X 6006-0:2023 | Intended bibliographic profile edition | Edition identifier and independently encoded verified rules | The project license does not grant rights to KS publications |
| [LC MARCXML](https://www.loc.gov/standards/marcxml/) | Architectural comparison and parity inventory | Links and original analysis | Asset-level notices not verified; no LC implementation copied |
| [LC MARCXML schema](https://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd) | Compatibility target | Namespace identifier and independently authored grammar | Official file retrieval blocked; bundled schema is not an official LC distribution |
| [LC legal page](https://www.loc.gov/legal/) | Rights investigation | Link only | Direct retrieval returned HTTP 403; no blanket public-domain or permissive-license assertion |
| [OAI MARCXML guidance](https://www.openarchives.org/OAI/2.0/guidelines-marcxml.htm) | Primary interoperability evidence | Link and paraphrased finding | Original example record not redistributed |
| [ABES IdRef developer guidance](https://documentation.abes.fr/aideidref/helpdeveloper/ch03s02.html) | Non-MARC21 transport precedent | Link and short paraphrase | Source text and authority example not copied |

Research access date: 2026-09-16. Search-index excerpts can establish that a
component is advertised; they do not establish the license or current contents of
its downloadable file. See `lc-parity.md` for source-access limitations.

## Machine-readable rule provenance

Each encoded rule should identify its source URL, field/position, profile edition,
and whether it is verified, partial, or an institutional policy. Explanatory prose
is written independently. A rule missing authoritative evidence must remain
unimplemented/unknown rather than becoming an invented KORMARC requirement.
Technical extraction is reviewed against examples and tested; generated artifacts
must identify their generator. Changes in an official page do not silently change
a released ruleset.

## Third-party dependencies

Dependencies remain governed by their own licenses. Before redistributing a
binary bundle, collect notices from the exact locked package versions (including
native XML libraries, if bundled). Installing dependencies with the documented
package manager is different from relicensing or copying their source here.
An optional comparison library validates transport behaviour only; its MARC 21
semantic assumptions do not become KORMARC rules.

## If upstream assets are added later

Record upstream URL, version/date, SHA-256, copyright/license notice, local path,
and modifications in a third-party manifest. Retain required notices. Do not put
an upstream asset under the project license merely because it is publicly
downloadable or hosted by a government institution. If reuse terms remain
unclear, keep a reference or user-supplied local-file option instead of vendoring
the asset. Never fetch schemas/DTDs from instance-provided URLs during parsing.

## 2026-09-17 audit update

Direct NLK HTML retrieval now works through a standard HTTP client. `research/source-inventory.json` records each source hash and access result, while `research/field-catalog.json` contains technical summary facts and XML paths. This supersedes the initial excerpt-only access limitation, but does not establish review of every semantic rule. Raw official HTML is excluded from Git; source explanatory prose is not redistributed. `research/verified-rules.json` remains the historical initial evidence ledger. See [audit](audit.md).
