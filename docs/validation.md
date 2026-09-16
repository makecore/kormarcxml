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
3. Content: `validate(record, level=3)` additionally checks Leader/09, the 005
   calendar timestamp, the 008 entered-date fill prohibition, and 082$m codes.
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

| Element | Implemented checks | Still outside coverage |
|---|---|---|
| Leader | 24 characters; /09 blank, a, z | Other coded positions and material dependencies |
| 005 | 14 characters; real YYYYMMDDhhmmss timestamp | Institutional update policy |
| 006 | 14 characters | Material-specific /01–13 codes |
| 008 | 40 characters; no fill character in /00–05 | Remaining coded positions, dates and country/language code tables |
| 020 | Field repeatability | Indicators, subfield rules and ISBN content |
| 082 | Both indicator enumerations; full subfield set and repeatability; $m a/b | Edition dependencies and conditional $m/$a exception |
| 245 | Field nonrepeatability; $a/$b/$d/$e repeatability | Remaining subfields; indicators; mandatory conditions |
| 300 | Field repeatability | Remaining field rules |
| 370 | Blank indicators; full subfield set and repeatability | Conditional obligation and geographic authority control |
| 688 | Field repeatability; both indicators; closed subfield set and repeatability; indicator 2 / $2 condition | Authority reconciliation and conditional obligation |
| 700 | Field repeatability; first indicator 0/1/3 | Second indicator, name/subfield semantics |
| 940 | Field repeatability; both indicators; full subfield set and repeatability | Text/content interpretation |

The 005 and 006 lengths are **KORMARC-specific**, not the MARC 21 lengths of
16 and 18. Repeated 245$a and responsibility in 245$d must not be interpreted
using MARC 21 rules. 082 second indicator 1 represents NLK assignment.

All included field facts come from the official NLK pages recorded in the JSON.
Access during development: 2026-09-16. Some full-page fetches failed with HTTP
417; indexed official-source excerpts were used where available. Comprehensive
page-by-page verification, obligation levels, and national code lists remain a
release limitation. See the research inventory for the complete research status.

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
