import sys
from pathlib import Path
from _common import *
import re
if len(sys.argv)<5: raise SystemExit("usage: txt_to_tei.py input.txt output.xml WITNESS_ID TITLE")
src,out,wid,title=sys.argv[1:5]
root,body=base_tei(wid,title,Path(src).name)
for i,para in enumerate(re.split(r"\n\s*\n",Path(src).read_text(encoding="utf-8").strip()),1):
    if para.strip():
        p=etree.SubElement(body,"{%s}p"%TEI); p.set("{%s}id"%XML,f"{wid}.p{i:04d}"); p.text=para.strip()
write(root,out)
