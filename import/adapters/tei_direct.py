import sys, shutil
from pathlib import Path
from lxml import etree
if len(sys.argv)<4: raise SystemExit("usage: tei_direct.py input.xml output.xml WITNESS_ID")
src,out,wid=sys.argv[1:4]
t=etree.parse(src); root=t.getroot(); ns=root.nsmap.get(None)
if root.tag.split('}')[-1] != 'TEI': raise SystemExit('input root is not TEI')
root.set('{http://www.w3.org/XML/1998/namespace}id',wid)
Path(out).write_bytes(etree.tostring(root,encoding='utf-8',xml_declaration=True,pretty_print=True))
