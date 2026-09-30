# Project History and Editorial / Architectural Decisions

**Maintenance rule:** this file is a required release artifact. Every new version must update (1) the version log, (2) any new or reversed architectural/editorial decisions, (3) the list of provisional components, and (4) the next-stage boundary. A release is incomplete if this file is not updated.

## Project purpose

The project is an internal digital research edition/workbench for studying the textual formation, rewriting, editorship, structure, and transmission of *The Protocols of the Elders of Zion*. The current phase deliberately uses Cesare G. De Michelis's reconstructed text and apparatus as scaffolding while documentary witnesses are transcribed outside the system and prepared for later ingestion.

The project is **not** treating the De Michelis reconstruction as a documentary witness, and it is **not** treating the apparatus-derived K/A1/A2/N/B projections as final transcriptions.

## Standing decisions

### D1. Separate reconstruction from documentary witness
De Michelis is represented as a reconstruction/reference text. A documentary witness is a transcription tied directly to a historical printed/manuscript source. These are different entity types and must remain visibly distinct in the UI and TEI.

### D2. Stable canonical loci are independent of witness numbering
The 22/24/27 protocol structures cannot serve as universal identifiers. Stable locus IDs provide a witness-independent alignment layer. A witness maps to loci; loci do not inherit the witness's protocol numbering.

### D3. Import and alignment are separate stages
A witness is first ingested diplomatically and validated. Only after the transcription is stable is it aligned to canonical loci. Alignment errors must never silently change the transcription.

### D4. Preserve three distinct note systems
De Michelis numbered critical apparatus, Joly source-parallel markers, and historical asterisk source notes are separate data layers. They must never be merged in transcription or interface.

### D5. Research annotation is not documentary annotation
Interpretive claims (economic discourse, editorial voice, possible Sharapov/Boutmy relation, etc.) are stand-off research annotations. They are separated from historical notes, transcription, and critical apparatus.

### D6. Transmission diagrams are hypotheses
The current De Michelis transmission model is displayed as a model/hypothesis, not as the project's final stemma. The architecture permits multiple versioned hypotheses.

### D7. Current witness reconstructions are scaffolding
K/A1/A2/N/B in the present interface are derived from De Michelis's apparatus. They are useful for testing comparison, search, alignment, and UI, but will be replaced by documentary transcriptions.

### D8. Documentary transcription remains diplomatic
Future witness ingestion preserves pagination, lineation when supplied, punctuation, historical notes, uncertainty, additions/deletions, and source references. Normalization is an additional layer, not a replacement for the diplomatic text.

### D9. Contextual documentation is part of the scholarly interface
Every major panel, concept, and function must have accessible contextual help stating what it does, its evidentiary status, and whether it is working, provisional, experimental, or planned. Known limitations should be visible inside the system, not only in developer documentation.

### D10. Ingestion adapters are boundary tools, not canonical formats
PAGE XML / ALTO / TXT may be accepted as incoming transcription formats (for example from eScriptorium), but the project's canonical textual representation remains TEI.

## Version log

### 1.0 — initial integrated research edition
- Consolidated De Michelis reconstruction, apparatus-derived witness views, edition/synopsis/search/entity/distant-reading interfaces, and TEI package.
- Established the internal experimental publication model.

### 1.1 — contextual guide
- Added an in-system guide and contextual orientation.
- Retained client-side password/noindex experimental deployment model.

### 2.0 — target architecture introduced
- Separated Work / Witness / Reconstruction / Locus / Reading / Note / Alignment / Entity / Concept / Transmission Hypothesis.
- Recast De Michelis as reconstruction/reference rather than K.
- Marked apparatus-derived witnesses as provisional.
- Separated historical source-note layer and made the transmission graph explicitly hypothetical.

### 2.1 — textual cleanup and provenance
- Separated the historical `(*)` / `(**)` source notes from running text.
- Corrected protocol segmentation/boundary punctuation against printed headings.
- Added span-level provisional K provenance to the De Michelis reconstruction.

### 2.2 — pre-witness research infrastructure
- Created stable canonical loci and mappings across non-parallel witness structures.
- Added documentary-witness TEI template, Relax NG validation, and ingestion guidance.
- Added local-first research annotations and a Research workspace.

### 2.3 — documentation and ingestion readiness
- Replaced the limited guide concept with a detailed contextual help catalogue covering every major panel/function and explicitly labelling working/provisional/experimental/planned features.
- Added this mandatory cumulative Project History and Decisions file and exposed it inside the Method/Help interface.
- Added a formal witness-ingestion contract for externally transcribed witnesses.
- Added import adapters for PAGE XML, ALTO XML, plain text, and direct TEI.
- Added a synthetic witness smoke test and consistency checks for canonical loci/IDs.
- No documentary witness has been ingested; 2.3 remains a De Michelis-based temporary system.

## Current provisional / experimental components (2.3)

- K/A1/A2/N/B continuous text projections: **provisional, apparatus-derived**.
- K provenance against De Michelis: **provisional until documentary K is ingested**.
- Entity recognition / concept indexing: **experimental; recompute against documentary witnesses**.
- Distant-reading visualizations: **experimental; current witness-level comparisons inherit provisional text limitations**.
- De Michelis transmission graph: **hypothesis/model, not final project stemma**.
- Research annotations: **local-browser persistence only**; export required for preservation.
- Documentary witness ingestion: **infrastructure ready, no real witness ingested**.

## Boundary of the current phase

Version 2.3 completes preparation for receiving witness files transcribed outside the system. The next phase should begin with a real documentary witness file. At that point the workflow is: import -> diplomatic TEI validation -> metadata review -> human alignment to canonical loci -> synopsis/search/index regeneration. The current phase should not attempt to reconstruct or correct the future witnesses before those files arrive.
