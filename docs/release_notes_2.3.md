# Version 2.3 — documentation and witness-ingestion readiness

Version 2.3 deliberately does **not** ingest documentary witnesses. It completes the preparation needed before externally transcribed witness files arrive.

## In-system documentation
- Expanded Help into a contextual catalogue covering every major page, panel, data layer, and function.
- Each topic states what it does and whether it is working, provisional, experimental, a hypothesis, or planned.
- Known non-final functions are documented explicitly rather than left ambiguous.
- Added direct links from Method/Help to cumulative project documentation.

## Required cumulative project record
- Added `docs/PROJECT_HISTORY_AND_DECISIONS.md`.
- This file is a mandatory release artifact and must be updated in every future version.
- It records standing editorial/architectural decisions, version changes, provisional components, and the boundary of the current phase.

## Witness-ingestion readiness
- Added `docs/WITNESS_INGESTION_CONTRACT.md`.
- Added conservative adapters for PAGE XML, ALTO XML, plain text, and direct TEI.
- Added a synthetic witness package and smoke test.
- Added an automated project consistency checker.
- Import remains separate from canonical-locus alignment.

## Not done in 2.3
- No real witness from the shared folders was ingested.
- No final collation was attempted.
- No new stemma was asserted.
- No reconstruction of future witness files was attempted.
