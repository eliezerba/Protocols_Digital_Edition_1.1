# Protocols — Digital Critical Edition 1.1

Experimental internal research edition of the *Protocols of the Sages of Zion*, reconstructed from Cesare G. De Michelis's printed critical apparatus. This repository is designed to serve **both as the complete scholarly package and as the GitHub Pages site**: no separate website/research/TEI repositories are required.

## Deploy to GitHub Pages

1. Create a repository and upload **the contents of this folder to the repository root**.
2. In GitHub: **Settings → Pages → Build and deployment → Deploy from a branch**.
3. Select `main` and `/ (root)`.
4. The site opens with the project's client-side internal-access gate.

No build step, npm install, server, or GitHub Action is required.

## Repository structure

- `index.html` — GitHub Pages entry point.
- `assets/` — the complete static research interface and its compact generated dataset.
- `tei/` — canonical TEI P5 corpus: reconstructed edition, five witness texts, apparatus, witness metadata, relations, authority files, NER stand-off layer, ODD and Schematron.
- `downloads/Protocols_TEI_1.1.zip` — one-click TEI package used by the web interface.
- `research/` — compact audit trail: editorial decisions, source anomalies, build summary, and structural map.
- `docs/` — editorial/data-model/design/NER documentation.
- `tools/build_history/` — historical pipeline stages retained for provenance; they are **not required for deployment** and still reflect earlier staging-directory names.
- `.nojekyll` — ensures GitHub Pages serves the repository as a plain static site.
- `VERSION` — release number.

## What is deliberately not duplicated

Earlier working packages contained both a large JavaScript data bundle and parallel JSON copies of the same generated data, plus a second copy of the TEI inside a `site/` directory. Release 1.0 removed those duplicates. Release 1.1 adds a contextual in-site guide without changing the scholarly data layer. The browser uses `assets/data.js`; the scholarly source layer is `tei/`.

The original De Michelis PDF, page renders, OCR scratch files, temporary extraction files, and other working artifacts are not included. They are not required to run or inspect the edition and would make the Git repository unnecessarily large.

## Scholarly status

This is an experimental internal research version. The continuous witness texts are reverse reconstructions from De Michelis's apparatus rather than fresh diplomatic transcriptions of the historical printed witnesses. The audit trail is preserved in `research/editorial_decisions.csv`. Two source anomalies remain explicitly documented (notes 380 and 2502).

Witness structures are retained independently:

- K: 22 protocols
- A1: 27 protocols
- B: 27 protocols
- A2: 24 protocols
- N: 24 protocols

The interface supports witness reading, structure-aware synopsis, variant highlighting, textual-tradition mapping, search, named-entity indexes, entity atlas/geography/network views, protocol anatomy, and TEI downloads.

## Access gate

The GitHub Pages version uses a **client-side password gate** suitable for an internal demonstration. It is not server-side authentication: static files remain technically retrievable by someone who knows their direct URLs. For genuinely confidential deployment, use hosting with server-side authentication.


## 1.1 interface guide

A persistent circular **i / Guide** control in the top navigation opens a context-sensitive explanation of the current view and a map of the complete research environment. It is intended to orient first-time scholarly users without interrupting normal reading.
