<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <title>Protocols documentary witness constraints</title>
  <pattern id="identity"><rule context="tei:TEI"><assert test="@xml:id">Every documentary witness must have @xml:id.</assert></rule></pattern>
  <pattern id="protocols"><rule context="tei:div[@type='protocol']"><assert test="@xml:id and @n">Every protocol div must have stable @xml:id and @n.</assert></rule></pattern>
  <pattern id="pages"><rule context="tei:pb"><assert test="@n">Page breaks must carry the source page number in @n.</assert></rule></pattern>
  <pattern id="notes"><rule context="tei:note[@type='source']"><assert test="@xml:id">Historical source notes require stable IDs.</assert></rule></pattern>
  <pattern id="locus"><rule context="tei:anchor[@type='locus']"><assert test="@corresp">Locus anchors must point to the canonical locus map with @corresp.</assert></rule></pattern>
</schema>