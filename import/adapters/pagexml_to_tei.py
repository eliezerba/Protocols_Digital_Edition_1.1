import sys
from pathlib import Path
from lxml import etree
from _common import *
if len(sys.argv)<5: raise SystemExit("usage: pagexml_to_tei.py input.xml output.xml WITNESS_ID TITLE")
src,out,wid,title=sys.argv[1:5]
t=etree.parse(src); ns=t.getroot().nsmap.get(None)
root,body=base_tei(wid,title,Path(src).name)
page=etree.SubElement(body,"{%s}div"%TEI,type="page")
pb=etree.SubElement(page,"{%s}pb"%TEI); pb.set('n','1')
regions=t.xpath('//*[local-name()="TextRegion"]') or [t.getroot()]
pi=0
for region in regions:
    lines=region.xpath('.//*[local-name()="TextLine"]')
    if not lines: continue
    pi+=1; p=etree.SubElement(page,"{%s}p"%TEI); p.set("{%s}id"%XML,f"{wid}.p{pi:04d}")
    first=True
    for line in lines:
        txt=' '.join(line.xpath('.//*[local-name()="Unicode"]/text()')).strip()
        if not txt: continue
        if not first: etree.SubElement(p,"{%s}lb"%TEI)
        if p.text is None: p.text=txt
        else:
            last=p[-1]; last.tail=(last.tail or '')+txt
        first=False
write(root,out)
