# Import adapters

These are deliberately conservative boundary converters. They create a first-pass TEI shell from incoming transcription files. They do not collate, normalize, or align the witness. Review the TEI before using canonical loci.

Usage examples:

```bash
python import/adapters/txt_to_tei.py input.txt output.xml WIT1 "Witness title"
python import/adapters/pagexml_to_tei.py page.xml output.xml WIT1 "Witness title"
python import/adapters/alto_to_tei.py alto.xml output.xml WIT1 "Witness title"
python import/adapters/tei_direct.py input.xml output.xml WIT1
```
