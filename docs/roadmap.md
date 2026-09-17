# Roadmap and release policy

These are planned milestones, not claims about existing functionality. Correct
transport and auditable rules precede broader mappings and automated repair.

## 0.1 series: reproducible foundation

Maintain the current conversion, API, CLI, profile, presentations, fixtures,
regression tests, and documentation. Fix correctness defects before expanding
semantic coverage. The published artifact must include its rules, schema, and
stylesheets and pass an installed-package demonstration.

Acceptance gates: local quality checks, documented demonstration, regression
suite, reproducible build instructions, and remote CI results once hosted.

## Next: verified bibliographic coverage

1. Obtain complete authorized primary-source access and reconcile all source
   entries with KS X 6006-0:2023 and subsequent official changes.
2. Review each field's repeatability, indicators, subfield codes, and application
   level; attach source identifiers and independent positive/negative fixtures.
3. Add material-specific 006/007/008 layouts, Korean code tables, cross-field
   dependencies, and documented exceptions without importing MARC 21 assumptions.
4. Generate coverage documentation from the registry and expose rule provenance
   in downstream reports. Consider Schematron export only where semantics map
   exactly to the registry implementation.

Acceptance gate: rule-by-rule review and traceable tests, not merely a greater
number of rules. Obtain reusable datasets with documented rights before claiming
representative production coverage.

## Next: interoperability and operational reliability

- Add independent official LC XSD and MODS XSD compatibility checks when approved
  redistribution or reliable acquisition is available; never reorder records to
  manufacture a pass.
- Review DC/MODS crosswalks with cataloguers and add a machine-readable per-record
  mapping-loss report.
- Measure process RSS and throughput on increasing input sizes and diverse records;
  retain reproducible benchmark environment metadata.
- Add explicit quarantine and checkpoint strategies for recoverable record errors,
  preserving original bytes and an audit trail. No silent repair.
- Review XML provenance attributes and optional transport metadata with a clear
  preservation policy before accepting them.

## Later: separate profiles and semantic adapters

Create separately verified authority and holdings profiles, retaining the generic
ordered model. Introduce reviewed BIBFRAME/RDF/JSON-LD mappings with identity,
provenance, and graph validation policies; add SHACL only after the target graph
model is defined. An HTTP API, browser inspector, or KOLIS-NET quality pipeline
should wrap the library and issue model, not duplicate conversion logic.

Legacy ONIX/OAI MARC/MARC DTD ingestion requires a concrete user need, versioned
input specifications, fixture rights, and documented mapping loss. LC parity
inventory alone is not justification to claim an untested adapter.

## Versioning

Use semantic versioning for the package. While pre-1.0, minor releases may change
public APIs; record changes and migration guidance in the changelog. Patch
releases should preserve documented APIs and fix defects. Rule-profile identity
and source revision are distinct from software version: adding a rule may change
validation results even when the transport API stays stable. Record both in
institutional job manifests and rerun representative regression datasets before
upgrading. Namespace changes require a separate ADR and explicit migration.

No package publication, GitHub visibility, or repository ownership is assumed by
this roadmap.
