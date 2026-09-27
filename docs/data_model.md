# Data model

Canonical scholarly interchange is TEI P5. `edition.xml` carries the reconstructed text and stand-off critical apparatus. Each witness has its own TEI file and own protocol segmentation. `witnesses.xml` is the witness authority list; `relations.xml` expresses descent and contamination/open-tradition relations; `entities/*.xml` are authority registers; `corpus.xml` is the XInclude manifest. JSON under `site_v5/data` is a generated web projection, not the source of truth.
