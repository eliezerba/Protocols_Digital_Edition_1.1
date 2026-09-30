from pathlib import Path
from lxml import etree
TEI="http://www.tei-c.org/ns/1.0"
XML="http://www.w3.org/XML/1998/namespace"
def base_tei(wid,title,source):
    root=etree.Element("{%s}TEI"%TEI,nsmap={None:TEI}); root.set("{%s}id"%XML,wid)
    h=etree.SubElement(root,"{%s}teiHeader"%TEI); fd=etree.SubElement(h,"{%s}fileDesc"%TEI)
    ts=etree.SubElement(fd,"{%s}titleStmt"%TEI); etree.SubElement(ts,"{%s}title"%TEI).text=title
    ps=etree.SubElement(fd,"{%s}publicationStmt"%TEI); etree.SubElement(ps,"{%s}p"%TEI).text="Internal documentary witness transcription"
    sd=etree.SubElement(fd,"{%s}sourceDesc"%TEI); etree.SubElement(sd,"{%s}p"%TEI).text=f"Imported from {source}"
    text=etree.SubElement(root,"{%s}text"%TEI); body=etree.SubElement(text,"{%s}body"%TEI)
    return root,body
def write(root,out):
    Path(out).write_bytes(etree.tostring(root,encoding="utf-8",xml_declaration=True,pretty_print=True))
