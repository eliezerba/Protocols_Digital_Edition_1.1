# Interface research and design rationale — v7

## Research patterns used

### Frankenstein Variorum

The Frankenstein Variorum treats textual variance as a navigational layer. One edition remains readable in full view, while degrees of variance are marked as hotspots; selecting a hotspot opens a critical-apparatus panel and provides direct links into the corresponding location in other editions. Its homepage heatmap is also an interactive route into heavily altered passages.

Source: https://frankensteinvariorum.org/method

**Adopted principle:** variation density should help the scholar decide *where to go next*. In v7 this becomes the home-page variance landscape and the internal protocol anatomy strip.

### Edition Visualization Technology (EVT)

EVT explicitly supports critical apparatuses, witness selection/exclusion, multiple recensions, a variance heat-map tool, named entities, and synchronized text/apparatus views.

Sources:
- https://github.com/evt-project/evt-demo
- https://github.com/evt-project/evt-viewer

**Adopted principle:** apparatus, witness choice, entity index, and structural views should remain synchronized rather than behave as unrelated pages.

### Juxta / Juxta Commons

Juxta provides complementary scales of comparison: a heat-map overlay, side-by-side comparison, and a global histogram showing where change clusters in the text.

Source: https://journalofdigitalhumanities.org/3-1/juxta-commons/

**Adopted principle:** the scholar needs both a local lexical comparison and a global map of change. v7 therefore separates word-level synopsis highlighting from the 22-locus variance landscape and witness-similarity matrix.

## Project-specific design decisions

### Witness color is not variant color

A persistent color identifies K, A1, A2, N, or B throughout the project. These colors never mean “addition” or “error.” Variant operations use a second visual vocabulary: addition, substitution, omission, and structural boundary.

This prevents a common ambiguity in multi-witness interfaces where the same color is asked to mean both *which text?* and *what kind of difference?*

### Structure cannot be normalized away

The principal difficulty of this tradition is that K, X, and Y organize the textual continuum into 22, 27, and 24 protocols. Therefore:

- the synopsis has an **organizing witness** independent from its visible columns;
- each witness column reports its own overlapping protocol labels;
- cross-witness boundaries remain visible inside the close-reading view;
- home-page structural ribbons act as navigation.

### Internal protocol anatomy

A long protocol should not appear as an undifferentiated block. The v7 anatomy layer uses De Michelis's lettered Joly-source loci where available because these are explicit textual landmarks already encoded in the edition. Where they are absent, the program creates neutral sentence groups. The interface labels them as textual blocks rather than inventing interpretive section titles.

### Distant reading must be reversible

A map or graph is useful only if it can return the scholar to evidence. Entity nodes, place dots, variance cells, co-occurrence nodes, and witness-frequency displays all link back to the entity index, witness, protocol, or synopsis.
