# NER and analytical indexing — v7

## Method

The v7 NER layer was rebuilt from scratch across all reconstructed text views. It uses an expanded scholarly authority list and deterministic longest-surface matching. When two candidate entity forms overlap, the longest valid form is retained.

This method was chosen for the current build because the witness texts contain pre-reform / nonstandard Russian, OCR-derived forms, editorial reconstruction, and a relatively bounded set of historically salient entities. It is therefore described as a **hybrid authority-based NER pass**, not as a neural Russian NER model.

## Coverage

- reconstructed De Michelis text: 103 mentions
- K: 101
- A1: 101
- A2: 121
- N: 128
- B: 110

Total: 664 mentions.

By authority type:

- persons: 19 authorities / 237 mentions
- places: 20 authorities / 163 mentions
- organizations: 6 authorities / 202 mentions
- works: 12 authorities / 62 mentions

## Separate concept layer

The v7 build also indexes 19 controlled concepts (for example liberty/liberalism, state/government, finance/capital, press/public opinion, law/justice, war/coercion, revolution/anarchy, religion/theology, education, representation/elections, industry/monopoly, secrecy/hidden government, morality, socialism/Marxism, Darwinism, Nietzscheism, antisemitism, and Freemasonry).

These are **not** named entities and are not included in the NER totals.

## TEI

`tei/analysis/ner.xml` records the NER occurrences as a stand-off analytical layer, pointing to the authority record and to the witness/unit in which the occurrence appears.
