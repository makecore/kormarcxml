# ADR 002: Python library, lxml, and an independent CLI

Status: accepted for 0.1.0. Date: 2026-09-16.

## Context

The project needs an auditable ISO 2709 codec, XML Schema support, streaming XML,
straightforward institutional integration, and a small maintainable toolkit.
It must not inherit MARC 21 semantic assumptions through its implementation.

## Options considered

| Option | Strengths for this project | Costs/tradeoffs |
|---|---|---|
| Python + lxml | Compact readable core; mature XML/XSD APIs; easy data-pipeline integration; packaging for common desktop/server environments | Interpreter overhead; native XML allocations need separate memory measurement |
| Java + JAXP/Saxon ecosystem | Established XML tooling and strong deployment options for institutional Java services | Larger initial build/dependency surface and less convenient small-script integration |
| Rust XML ecosystem | Strong memory safety and potential throughput advantages | More implementation work for the selected XML validation/transformation requirements |
| JavaScript/TypeScript XML tools | Natural browser/service integration | Additional decisions needed for equivalent XML Schema and secure streaming behavior |

This is an engineering selection for this repository, not a benchmark proving
one language superior. Historical LC implementation language is not a requirement.

## Decision

Use Python 3.11+ for the ordered model, explicit ISO 2709 codec, rules engine, and
CLI. Use lxml for XML parsing, writing, XSD validation, and escaped presentation.
Keep API modules independent of `argparse` and command-line file handling.

Use pytest for behavior/regression tests, Ruff for lint and formatting, mypy for
static checks, setuptools/build for distributable packages, and GitHub Actions
for a Windows/macOS/Linux matrix. Use pymarc as an independent structural test
oracle; it does not define KORMARC semantics or perform production conversion.
Development dependencies and build-tool versions are pinned; runtime compatibility
is declared in `pyproject.toml`.

## Consequences

The core can be reused in scripts or services without spawning a CLI. Institutional
rules are JSON resources rather than duplicated validator code. Streaming paths
bound retained records, although total memory measurements must include native
libxml2 allocations separately. Desktop installations depend on compatible wheels
or a functioning native build environment; CI is intended to detect portability
regressions, and remote results must be checked after publication.

A separate rules engine was selected instead of claiming XSD can represent all
KORMARC semantics. Schematron is a potential export/interop feature, not a runtime
dependency or an already implemented validator.
