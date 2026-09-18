# Transformations and presentation

All built-in transformations are original project code (MIT). They do not reuse LC XSLT source. Semantic exports are intentionally conservative subsets, not a claim of full LC crosswalk parity. The source logical record is never modified. Keep the canonical XML alongside lossy exports.

## Available targets

| Target / API | Purpose | Preservation and loss |
|---|---|---|
| `json`, `to_json` / `from_json` | Versioned JSON ingest and export | Exact logical model: Leader, ordered fields, repeated subfields, code points, blank indicators. No original bytes, directory, encoding provenance. Unknown object properties are rejected, not discarded. |
| `raw`, `inspect` | Raw logical inspection | Same ordered JSON as above; not a hex dump. |
| `tagged` | Cataloging display | Field order retained; blank indicators shown as `#`. Literal `$`, `#`, and newlines make the view ambiguous. No tagged ingest. |
| `html` | Korean labeled cataloger view | Every field shown, with raw JSON and Leader in an expandable panel. Escaped static markup; no scripts, network fonts, links generated from record values, or external dependencies. Display output is not canonical transport. |
| `report_html(issues)` | Diagnostic presentation | Human view of issue context. Retain machine-readable issue JSON for processing. |
| `dc` | Simple Dublin Core XML | Lossy mapping below; fixed fields, indicators, local fields, most subfields and relationships omitted. |
| `mods` | MODS 3.8 subset XML | Lossy mapping below; no authority reconciliation, fixed-code translation, role inference or comprehensive mapping. Well-formedness/mapping tests run; complete target XSD validation has not been performed. |
| `csv` | Long-form analysis | One row per subfield, including field/subfield indexes; empty datafields included. Leader and physical format omitted. CSV quotes newlines and delimiters; text is unmodified, including formula-like strings. Import columns as text in spreadsheet applications. |

`transformation_catalog()` returns each target's limitation statement. The CLI can display it. No RDF, JSON-LD, BIBFRAME, ONIX, OAI-MARC, MODS-to-KORMARC or Dublin-Core-to-KORMARC mapping is claimed. These require separate reviewed crosswalks and identifiers; JSON serialization alone does not produce linked data.

## Implemented mappings

| KORMARC source | Dublin Core | MODS |
|---|---|---|
| 245 `$a`, `$b`, `$n`, `$p` | One joined `title` per repeated `$a` work | Separate `titleInfo` per repeated `$a`; `title`, `subTitle`, `partNumber`, `partName` |
| 245 `$x` | Separate `title` | `titleInfo type="alternative"/title` (language is not inferred) |
| 245 `$d`, `$e` | Repeated `description` | `note type="statement of responsibility"` |
| 100/110/111 `$a` | `creator` | Typed `name/namePart` |
| 700/710/711 `$a` | `contributor` | Typed `name/namePart` |
| 260 `$a` | Omitted | `originInfo/place/placeTerm type="text"` |
| 260 `$b`, `$c` | `publisher`, `date` (raw text) | `originInfo/publisher`, `dateIssued` (raw text) |
| 020 `$a` | `identifier` | `identifier type="isbn"` |
| 022 `$a` | `identifier` | Omitted |
| 500 `$a` | `description` | `note` |
| 520 `$a` | `description` | Omitted |
| 001 | `identifier` | `recordInfo/recordIdentifier` |

The 245 responsibility treatment is KORMARC-specific: `$d` and `$e` are not MARC 21's `$c`. Transcribed responsibility can contain role text and multiple names. It is preserved as a statement, not treated as a resolved person. Name headings currently retain only `$a`; dates, subordinate units, relators, identifiers, title linkage and family distinctions need future richer mappings. DC's creator/contributor distinction is an explicit main/added-entry approximation. Output order groups semantic elements and is not original MARC field order. Punctuation is not normalized or trimmed. All source code points in selected values are retained.

Sources consulted 2026-09-16:

- [NLK official KORMARC 245](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/20X_24X_245.html): full official page retrieved directly on 2026-09-17; repeated titles, parallel titles, indicators and responsibility were reviewed. Exact rule-level provenance and review status are tracked with the rule registry; no official explanatory text is copied here.
- [NLK 1XX overview](https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/1XX_overview.html): primary-source indexed overview of main entries.
- [LC MODS name guidance](https://www.loc.gov/standards/mods/userguide/name.html): directly retrieved; recommends a typed statement-of-responsibility note for transcribed responsibility.
- [MODS 3.8 schema](https://www.loc.gov/standards/mods/v3/mods-3-8.xsd): retrieval attempted, returned 403; no target-schema validation claimed.

## API and extension

```python
from kormarcxml.transforms import transform, from_json, register_transform

json_text = transform(record, "json")
assert from_json(json_text) == record
html = transform(record, "html")

register_transform(
    "institution-id",
    lambda r: r.identifier or "",
    limitation="Exports record identifier only; all other data omitted.",
)
assert transform(record, "institution-id") == (record.identifier or "")
```

Registration requires a unique name, callable and explicit limitation. It never silently overrides built-ins. Extensions execute trusted Python code: installation/registration is an application decision, never driven by input metadata. Iterating records and calling `transform` processes one record at a time. Each call returns one complete document/string; concatenating XML documents does **not** produce a valid XML collection. Use a target-specific collection writer in an external consumer. JSON Lines can be produced by compacting each JSON record. CSV collection output should write a header once and append subsequent records' rows.

## Independent XSLT

`src/kormarcxml/stylesheets/tagged.xsl` is an original XSLT 1.0 stylesheet for a MARCXML record or collection. It has no external includes, extension functions, or document loads. It creates the same tagged display as the Python renderer; tests compare exact outputs. Consumers should disable external file and network access in their XSLT processor. The Python HTML renderer and data serialization are separate consumers; neither modifies canonical XML.

## Tests

`tests/test_transforms.py` checks exact JSON round trip with repeats and combining characters; safe HTML/XML escaping; KORMARC-specific responsibility mapping; long-form CSV ordering and embedded newlines; extension collision handling; JSON unknown-property rejection; unsupported BIBFRAME rejection; and XSLT/Python display parity. Fixtures are synthetic and have no copied catalog records.

## Audit clarification (2026-09-17)

The 245 second indicator is not a MARC 21 nonfiling-character count. Parentheses and title text remain unchanged. Parallel titles are exported as alternative MODS titles without inferring language or translation relationships. `$d`/`$e` notes do not retain their association with each repeated work in this subset. A record with `$k`/`$f` and no `$a` is not rejected merely for lacking `$a`; DC/MODS still omit these collection-title elements. The generic XML/JSON transport retains them.
