import sys
from pathlib import Path
from lxml import etree
from _common import *
if len(sys.argv)<5: raise SystemExit("usage: alto_to_tei.py input.xml output.xml WITNESS_ID TITLE")
src,out,wid,title=sys.argv[1:5]
t=etree.parse(src)
root,body=base_tei(wid,title,Path(src).name)
pages=t.xpath('//*[local-name()="Page"]')
for pageno,page in enumerate(pages,1):
    etree.SubElement(body,"{%s}pb"%TEI,n=str(pageno))
    for bi,block in enumerate(page.xpath('.//*[local-name()="TextBlock"]'),1):
        p=etree.SubElement(body,"{%s}p"%TEI); p.set("{%s}id"%XML,f"{wid}.p{pageno:04d}.{bi:03d}")
        first=True
        for line in block.xpath('.//*[local-name()="TextLine"]'):
            words=line.xpath('.//*[local-name()="String"]/@CONTENT'); txt=' '.join(words).strip()
            if not txt: continue
            if not first: etree.SubElement(p,"{%s}lb"%TEI)
            if p.text is None: p.text=txt
            else: p[-1].tail=(p[-1].tail or '')+txt
            first=False
write(root,out)
