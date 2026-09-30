from pathlib import Path
import json, sys, re
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
issues=[]
# Canonical locus JSON
p=ROOT/'research/canonical_loci.json'; data=json.loads(p.read_text(encoding='utf-8'))
loci=data.get('loci',data if isinstance(data,list) else [])
ids=[x.get('id') for x in loci]
if len(ids)!=len(set(ids)): issues.append('duplicate canonical locus IDs')
if any(not re.fullmatch(r'L\d{4,}',x or '') for x in ids): issues.append('malformed canonical locus ID')
# XML IDs across project TEI: duplicates within a file are always invalid; report cross-file duplicates informationally only for local IDs.
for f in (ROOT/'tei').rglob('*.xml'):
    try: t=etree.parse(str(f))
    except Exception as e: issues.append(f'XML parse failure {f.relative_to(ROOT)}: {e}'); continue
    vals=t.xpath('//@xml:id',namespaces={'xml':'http://www.w3.org/XML/1998/namespace'})
    if len(vals)!=len(set(vals)): issues.append(f'duplicate xml:id within {f.relative_to(ROOT)}')
# Current structure mappings
for x in loci:
    maps=x.get('mappings',{})
    if 'reconstructed' not in maps: issues.append(f"{x.get('id')}: missing reconstructed mapping")
report={'version':'2.3','canonical_loci':len(loci),'issues':issues,'ok':not issues}
out=ROOT/'research/consistency_report.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if not issues else 1)
