# Witness Ingestion Contract v1

This contract defines what the system expects **after** a witness has been transcribed externally (for example in eScriptorium). Version 2.3 prepares this path but does not ingest the real witnesses.

## 1. Accepted incoming forms

The import layer accepts:

- PAGE XML (`*.xml`, PAGE namespace)
- ALTO XML (`*.xml`, ALTO namespace)
- plain UTF-8 text (`*.txt`)
- TEI P5 (`*.xml`)

Incoming formats are transport formats. **Canonical project text is TEI P5.**

## 2. Minimal witness metadata

Each witness must have a persistent project ID and metadata record containing, where known:

- `id` — persistent project identifier
- `siglum`
- `title`
- `date`
- `place`
- `edition_or_publication`
- `source_repository_or_url`
- `language`
- `transcription_status`
- `input_format`
- `source_file`

Unknown values may be left empty. Do not invent metadata.

## 3. What must survive import

When present in the incoming file, preserve:

- page boundaries
- line boundaries
- paragraph/division boundaries
- original punctuation and spelling
- historical asterisk/source notes
- uncertain or illegible readings
- additions/deletions/corrections
- source page/image identifiers

## 4. Two-stage rule

**Stage A — transcription ingestion** creates a diplomatic witness TEI and validates it.  
**Stage B — alignment** maps that stable witness text to canonical loci.

No importer is permitted to alter the transcription merely to improve alignment.

## 5. Folder contract

Recommended incoming package:

```text
incoming/<witness-id>/
  metadata.json
  transcription.xml   # or transcription.txt
  images/              # optional; original page images if supplied
```

Processed project representation:

```text
tei/witnesses/documentary/<witness-id>.xml
research/ingestion/<witness-id>-report.json
research/alignments/<witness-id>-loci.json
```

## 6. eScriptorium

If eScriptorium exports PAGE XML or ALTO, retain the original export unchanged and convert it through the adapter. The adapter output is a **first-pass TEI shell**, not a reviewed diplomatic edition. Human review remains required before locus alignment.

## 7. Acceptance checks

A witness is ready for alignment only if:

1. XML is well formed (if XML input).
2. Resulting TEI passes the documentary-witness validator.
3. page count / page markers are plausible relative to the source package.
4. no imported source-note markers have disappeared.
5. metadata contains at least project ID, siglum, source file, and transcription status.
6. an ingestion report has been generated.

## 8. Things explicitly deferred until after ingestion

- collation against other witnesses
- NER/concept recomputation
- historical stemma decisions
- textual normalization beyond an explicitly separate normalized layer
- correction of the source transcription on the basis of De Michelis
