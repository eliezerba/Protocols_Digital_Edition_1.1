# Protocols Digital Research Edition - 2.3 (provisional)

Version 2.3 is a **temporary De Michelis-based research environment built on the target architecture**. It is intended for internal scholarly use while documentary witness scans/transcriptions are prepared.

## What is authoritative in this release

- Cesare G. De Michelis's reconstructed Russian text is the current **reference reconstruction**.
- De Michelis's numbered critical apparatus is preserved.
- Historical asterisk source notes are being separated from the running text as their own annotation layer.
- K, A1, A2, N and B are **provisional continuous reconstructions derived from De Michelis's apparatus**. They are not documentary transcriptions and are expected to be replaced later.

## Research functions

- close reading with non-parallel witness structure;
- configurable synopsis (choose organizing structure, visible witnesses and order);
- textual difference highlighting;
- search;
- entity index and distant-reading views;
- TEI downloads;
- interactive De Michelis transmission model;
- contextual Guide;
- source-note inspector for historical `* / **` notes;
- provenance/status labels distinguishing reconstruction from provisional derived witnesses.

## Architecture

Read **`docs/SYSTEM_ARCHITECTURE_v0.1.md`** first. It defines the target model: Work / Witness / Reconstruction / Locus / Reading / Note / Alignment / Entity / Concept / Hypothesis, with stable identifiers and replaceable witness layers.

`docs/architecture-manifest.json` maps the current 2.1 files to those target roles.

## TEI

The TEI package is in `tei/` and can also be downloaded from the interface. New in 2.1: `tei/analysis/source_notes.xml`.

## Known limitations

- The witness texts remain apparatus-derived scaffolding.
- The K provenance indicator is currently unit-level for explicitly long omissions (`usque ad`); span-level provenance is planned.
- The current transmission graph is **De Michelis's model**, not the final project stemma.
- Source notes have been extracted where the paired asterisk-note block is unambiguous; documentary witnesses will provide final verification.
- De Michelis apparatus anomalies 380 and 2502 remain unresolved.

## GitHub Pages

Upload the contents of this folder to the repository root and enable **Settings -> Pages -> Deploy from a branch -> main -> /(root)**. No build step is required.

The site remains an internal experimental interface and retains the password gate configured in the project.


## 2.1 corrections
- Exhaustive separation of historical `(*)` / `(**)` source notes from Protocol II.
- Printed-heading-based protocol segmentation correction.
- Span-level provisional provenance of De Michelis against apparatus-derived K.
See `docs/release_notes_2.1.md`.


## Version 2.2 additions

- **3,603 canonical loci** independent of witness protocol numbering (`research/canonical_loci.json`, `tei/analysis/canonical_loci.xml`).
- Documentary witness TEI template + Relax NG validator (`tei/templates/`, `tei/schema/documentary-witness.rng`).
- Research annotation workspace and selection-based annotation from Close Reading.
- Research annotations remain local to the browser until exported as JSON/TEI.
- Architecture document updated to `docs/SYSTEM_ARCHITECTURE_v0.2.md`.


## Version 2.3 additions

- Detailed contextual Help catalogue inside the interface, including explicit status/limitations for provisional or not-yet-final functions.
- Mandatory cumulative `docs/PROJECT_HISTORY_AND_DECISIONS.md` — update this file in every release.
- `docs/WITNESS_INGESTION_CONTRACT.md` for externally transcribed witnesses (including eScriptorium PAGE/ALTO workflows).
- Conservative PAGE XML / ALTO / TXT / TEI import adapters.
- Synthetic ingestion smoke test and canonical-locus/ID consistency checker.
- **No documentary witnesses were ingested in 2.3.**
