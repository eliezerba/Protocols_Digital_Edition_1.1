#!/usr/bin/env python3
from pathlib import Path
import sys
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
NS={'tei':'http://www.tei-c.org/ns/1.0'}
XML='{http://www.w3.org/XML/1998/namespace}'
if len(sys.argv)<2:
    print('usage: python scripts/validate_documentary_witness.py FILE.xml')
    raise SystemExit(2)
path=Path(sys.argv[1])
errors=[]
try:
    doc=etree.parse(str(path))
except Exception as e:
    print('INVALID XML:',e); raise SystemExit(1)
# broad structural RNG
rng=etree.RelaxNG(etree.parse(str(ROOT/'tei/schema/documentary-witness.rng')))
if not rng.validate(doc):
    errors.extend(str(x) for x in rng.error_log)
r=doc.getroot()
if r.tag!='{http://www.tei-c.org/ns/1.0}TEI': errors.append('Root element must be TEI in the TEI namespace.')
if not r.get(XML+'id'): errors.append('TEI root requires xml:id.')
if doc.find('.//tei:teiHeader',NS) is None: errors.append('teiHeader is required.')
if doc.find('.//tei:text/tei:body',NS) is None: errors.append('text/body is required.')
for x in doc.xpath('//tei:div[@type="protocol"]',namespaces=NS):
    if not x.get(XML+'id') or not x.get('n'): errors.append('Every protocol div requires xml:id and n.')
for x in doc.xpath('//tei:pb',namespaces=NS):
    if not x.get('n'): errors.append('Every pb requires @n with the source page number.')
for x in doc.xpath('//tei:note[@type="source"]',namespaces=NS):
    if not x.get(XML+'id'): errors.append('Every historical source note requires xml:id.')
for x in doc.xpath('//tei:anchor[@type="locus"]',namespaces=NS):
    c=x.get('corresp','')
    if not c or '#L' not in c: errors.append('Every locus anchor requires @corresp to canonical_loci.xml#L####.')
ids=doc.xpath('//@xml:id',namespaces={'xml':'http://www.w3.org/XML/1998/namespace'})
if len(ids)!=len(set(ids)): errors.append('xml:id values must be unique within the witness file.')
if errors:
    print('INVALID')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('VALID')
