# Documentary witness ingestion

1. Duplicate `tei/templates/documentary-witness-template.xml`.
2. Give the witness a persistent ID; do not reuse the provisional reconstruction file.
3. Transcribe diplomatically from the scan, retaining `pb` and, when useful, `lb`.
4. Encode historical source notes as `note type="source"`; do not mix them with modern apparatus.
5. Preserve uncertainty with `unclear`, loss with `gap`, editorial supply with `supplied`, and source corrections/additions with `add`/`del`.
6. If a normalized form is needed, retain both with `choice/orig/reg`.
7. Align to canonical loci only after the transcription is stable, using `anchor type="locus" corresp="../analysis/canonical_loci.xml#L####"`.
8. Validate: `python scripts/validate_documentary_witness.py path/to/witness.xml`.
9. Replace the provisional witness projection in the web data only after the documentary file passes validation and a spot collation.
