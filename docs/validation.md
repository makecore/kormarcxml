# Validation and rule coverage

KORMARCXML is an independent open-source implementation, not a KS conformance
certification service. A report with no errors means only that the implemented
checks found no violations. The initial registry is **deliberately incomplete**.

## Layers

1. XML structure: the base XSD validates generic transport structure, through the
   XML module. It cannot prove KORMARC semantic validity.
2. Tagging structure: `validate(record, level=2)` checks field kinds, tag shape,
   indicator/subfield shape, and the verified field-specific lengths,
   repeatability and allowed indicators/subfields described below.
3. Content: `validate(record, level=3)` additionally checks the reviewed Leader
   code domains, 005 calendar timestamp, 006/00, selected 008 common positions,
   082$m codes and the 688 indicator/source dependency.
   The ISO parser independently checks directory addresses/lengths and
   terminators; these are not reconstructed from a logical record for validation.

Both record levels return `list[Issue]` without mutating the record. Level 1 is
not accepted by this API because it requires XML input, not a parsed Record.
Reports distinguish errors, warnings and information. Unknown nonlocal fields
receive coverage warnings rather than fabricated "invalid tag" judgments.
Unknown 9XX fields receive informational coverage messages. Recognized 940 is
validated by its own rules, because not every 9XX field is merely local.

## Precisely implemented semantic coverage

The single source of truth is
`src/kormarcxml/resources/rules/bibliographic.json`. `coverage()` reads the same
registry. Rules carry source URLs; no official descriptive prose is bundled.

The registry now also includes directly extracted technical summaries from the
full linked field-page inventory. Each field exposes its source and summary
status. Ambiguous repetition markers are left unconstrained; incomplete
subfield summaries are not automatically closed. The official obligation marker
is recorded as metadata, not treated as an unconditional required-field rule.

Reviewed content checks cover Leader code domains and layout, 005 timestamps,
006/00 material type, 008 common-position codes and fill restrictions, 082$m,
and the existing 688 indicator/source relationship. Material-specific fixed
positions, all code tables, obligations and prose dependencies remain incomplete.
See [the audit](audit.md), [field mapping](field-mapping.md), and the JSON catalog
for exact per-field extraction status. `coverage()` reports executable assertion
templates, per-field counts, and fields with no assertions; it is not a compliance
percentage. XML/ISO transport tests cover each catalogued tag and subfield.

The 005 and 006 lengths are KORMARC-specific: 14, not MARC 21's 16 and 18.
Repeated 245$a and responsibility in 245$d must not be interpreted using MARC 21
rules. KORMARC 245's second indicator is 0/1, not a nonfiling character count.

## Institutional profiles and consumers

Profiles are local JSON objects merged recursively with the bundled registry.
Objects merge; lists and scalars replace. A profile can be passed as a dictionary
or filesystem path. No remote retrieval or dynamic execution occurs.

```python
from kormarcxml.validation import validate

profile = {
    "fields": {
        "999": {
            "source": "institutional policy version 1",
            "required": True,
            "repeatable": False,
            "subfields": {"a": {"required": True}},
        }
    }
}
issues = validate(record, profile=profile)
report = [issue.to_dict() for issue in issues]
```

`required` is available for an institution's explicit profile; the base registry
does not invent universal mandatory fields. `closed_subfields` should only be
enabled when the **complete** allowed set has been verified. Each subfield can
contain `rules`, using `id`, `source`, `message`, `level`, `start`/`end`, `length`,
`values`, `pattern`, `forbidden`, and `date_format`. Positions are zero-based,
end-exclusive character offsets. `level` defaults to 3. Occurrences in reports
are one-based field occurrences. Profile authors must supply provenance for new
rules. JSON profiles are trusted administrative configuration, not user uploads.

For complex cross-field/material dependencies, register a pure consumer rather
than duplicating the base registry:

```python
from kormarcxml.errors import Issue


def institutional_rule(record):
    if record.get_fields("999") and not record.get_fields("001"):
        yield Issue("warning", "institution.local-identifier", "Local record needs identifier")


issues = validate(record, validators=[institutional_rule])
```

The rule engine was selected over Schematron for simple Python integration and
streaming one-record checks. Schematron/SHACL are future consumers, not presently
implemented features. No rule auto-repairs or normalizes bibliographic data.

CLI levels 2/3 additionally apply the bundled XSD to each parsed record. For validation of the original XML document use CLI level 1 separately.

## Material-specific 007 rules

The bundled registry composes `bibliographic.json` with `physical.json`. The latter holds 104 source-linked checks: material categories, documented material lengths and explicit single-position enumerations. Electronic material accepts the mandatory six-position prefix and optional trailing positions, within the documented maximum of 14. Optional positions are checked when present. Multi-position numeric/compound codes, material relationships and every undefined-position rule remain outside this subset. `when.prefix`, `optional`, `min_length` and `max_length` are data-driven value-rule operators. The private composed registry is cached; public callers receive isolated copies.

## Material-specific 006/008 subset

The composed registry now also loads `fixed-details.json`: 72 additional checks for selected multi-position blocks, atomic pairs, undefined positions, bit depth, reduction ratio, and runtime. See [the detail audit](fixed-detail-audit.md). The source-conflict overrides for 022$2 and 034$2 preserve data and emit repetition review warnings. They are hash-pinned in `research/source-overrides.json`, not assertions that the official text has been amended.

`materials.json` adds 30 source-linked single-position checks for 008 and 30 corresponding 006 checks. Selection uses the official leader/06 and /07 criteria; 006 selects its own material independently through /00. The `when.leader` position map and `when.value_codes` operators express these conditions. Multi-position combinations and full prose dependencies are not implemented. Form-of-item positions are intentionally held for review because the overview and detailed pages conflict about fill characters. See the audit for the exact source conflict.
