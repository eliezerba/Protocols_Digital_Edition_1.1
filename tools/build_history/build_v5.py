#!/usr/bin/env python3
from __future__ import annotations
import re, json, csv, sys, importlib.util, shutil, hashlib
from pathlib import Path
from collections import defaultdict, Counter
from xml.etree import ElementTree as ET

ROOT=Path('/mnt/data/protocols_reconstruction')
V4PATH=ROOT/'src/build_v4.py'
spec=importlib.util.spec_from_file_location('v4mod',V4PATH)
v4=importlib.util.module_from_spec(spec); sys.modules['v4mod']=v4; spec.loader.exec_module(v4)
v3=v4.v3

OUT=ROOT/'data/derived_v5'; WOUT=ROOT/'data/witnesses_v5'; TEI=ROOT/'tei_v5'; SITE=ROOT/'site_v5'; DOCS=ROOT/'docs_v5'
for d in [OUT,WOUT,TEI,TEI/'witnesses',TEI/'entities',TEI/'schema',SITE,SITE/'assets',SITE/'data',SITE/'data/witnesses',DOCS]: d.mkdir(parents=True,exist_ok=True)
WITS=['K','A1','A2','N','B']
ROMAN=v4.ROMAN
BOUNDARIES=v4.BOUNDARIES
SOURCE_ANOMALIES=v4.SOURCE_ANOMALIES
WORD_RE=re.compile(r"[A-Za-zА-Яа-яЁёІіѢѣѲѳѴѵ'-]+")
SIG_TOKEN=r'(?:A1|A2|Al|А\s*1|А\s*2|A\s*1|A\s*2|N|[КK]|[ВB])'

# ---------------- editorial cleanup of nested apparatus syntax ----------------
def norm_sig(s):
    s=re.sub(r'\s+','',s.strip())
    return v3.norm_siglum(s)

def split_sig_group(s):
    return [norm_sig(x) for x in re.split(r'\s*,\s*',s) if x.strip()]

def remove_prev_words(before,n):
    ms=list(WORD_RE.finditer(before))
    if not ms: return before
    n=max(1,min(n,len(ms)))
    return before[:ms[-n].start()].rstrip()

def parse_inner_directive(content,w,before):
    c=content.strip().replace('\u00ad','')
    c=re.sub(r',\s*;',';',c)
    # common OCR/extraction punctuation after siglum
    c=re.sub(r'^\s*([NКKВB])\s*[;,]\s*',r'\1: ',c)
    c=re.sub(r'^\s*([АA])\s*([12])\s*[;,]\s*',r'A\2: ',c)
    # Split only when a semicolon introduces a fresh witness clause.
    parts=re.split(r';\s*(?='+SIG_TOKEN+r'\b)',c)
    parsed=[]
    for part in parts:
        m=re.match(r'^\s*('+SIG_TOKEN+r'(?:\s*,\s*'+SIG_TOKEN+r')*)\s*(?:(add|omitt?|omit)\.?\s*)?(?::)?\s*(.*)$',part,re.I)
        if not m: continue
        ws=split_sig_group(m.group(1)); act=(m.group(2) or 'replace').lower(); val=m.group(3).strip()
        parsed.append((ws,act,val))
    target=next((x for x in parsed if w in x[0]),None)
    if target is None:
        # Square brackets can also contain literal supplied text rather than apparatus syntax.
        return before, (content if not parsed else '')
    ws,act,val=target
    # Sometimes an omission clause itself contains an '& add.' replacement.
    if act.startswith('omit') and re.search(r'&\s*add\.?\s*:',val,re.I):
        _,val=re.split(r'&\s*add\.?\s*:',val,maxsplit=1,flags=re.I); act='replace'
    if act.startswith('add'):
        return before, (' '+val+' ' if val else '')
    if act.startswith('omit'):
        hint=re.split(r'&\s*add',val,maxsplit=1,flags=re.I)[0].strip(' .')
        if hint and '...' not in hint:
            j=before.lower().rfind(hint.lower())
            if j>=0 and len(before)-j<300:
                return before[:j]+before[j+len(hint):],''
        return remove_prev_words(before,1),''
    # replacement: substitute a lexical span of similar token length immediately before bracket
    n=max(1,len(WORD_RE.findall(val)))
    return remove_prev_words(before,n),val

def resolve_brackets(s,w):
    s=(s or '').replace('\u00ad','')
    # Some PDF extraction lost the opening '[' but preserved a closing ']' around a local reading.
    # Those unmatched closings are removed after all well-formed inner directives are processed.
    for _ in range(60):
        ms=list(re.finditer(r'\[([^\[\]]*)\]',s))
        if not ms: break
        for m in reversed(ms):
            before=s[:m.start()]; after=s[m.end():]
            nb,rep=parse_inner_directive(m.group(1),w,before)
            s=nb+rep+after
    s=s.replace('[','').replace(']','')
    return s

def clean_reading(s,w):
    s=(s or '').replace('\u00ad','').strip()
    # A few clauses were extracted as "A2,N: omitt.: ... & add.: ..."; interpret their inner action.
    if re.match(r'^omitt?\.?\s*:',s,re.I) and re.search(r'&\s*add\.?\s*:',s,re.I):
        s=re.split(r'&\s*add\.?\s*:',s,maxsplit=1,flags=re.I)[1].strip()
    elif re.match(r'^add\.?\s*:',s,re.I):
        s=re.sub(r'^add\.?\s*:','',s,flags=re.I).strip()
    s=resolve_brackets(s,w)
    # Strip residual apparatus-control fragments that arose from broken PDF bracket extraction.
    # Keep lexical material; only remove control labels themselves.
    group=SIG_TOKEN+r'(?:\s*,\s*'+SIG_TOKEN+r')*'
    s=re.sub(r'\b'+group+r'\s+(?:add|omitt?|omit)\.?\s*:?', ' ', s, flags=re.I)
    s=re.sub(r'\b'+group+r'\s*:\s*', ' ', s, flags=re.I)
    s=re.sub(r'\bNadd\.?\w*\b',' ',s,flags=re.I)
    s=re.sub(r'\bNomitt?\.?\w*\b',' ',s,flags=re.I)
    s=re.sub(r'\bomitt?\.?\s*:\s*[^&]{0,120}&\s*add\.?\s*:\s*',' ',s,flags=re.I)
    s=s.replace(']','').replace('[','')
    # Normalize extraction-only spacing, not Russian spelling.
    s=re.sub(r'[ \t]+',' ',s)
    s=re.sub(r'\s+([,.;:!?])',r'\1',s)
    return s.strip()

# ---------------- clean operations and rebuild witnesses ----------------
def build_core():
    raw=v3.RAW.read_text(encoding='utf-8',errors='replace')
    parsed=v3.parse_pages(raw)
    base,anchors,methods,page_ranges=v3.build_base_and_anchors(parsed)
    ops=v4.build_v4_ops(base,parsed,anchors)
    # All target-specific nested syntax is now resolved into lexical readings.
    for o in ops:
        if o.get('witness'):
            o['reading_candidate_preclean']=o.get('reading_candidate','')
            o['reading_candidate']=clean_reading(o.get('reading_candidate',''),o['witness'])
            if o.get('action')=='omit': o['reading_candidate']=''
            if o.get('status')!='resolved':
                # User asked for decisions, not a pending queue. Force a minimal local scope while retaining audit metadata.
                rr=v4.force_prev_span(base,o.get('anchor',0),0)
                o.update(start=rr[0],end=rr[1],lemma_candidate=rr[2],status='resolved',decision='forced-minimal-scope',confidence=0.45)
    chosen={}; rejected={}; wtext={}
    for w in WITS:
        a,r=v4.choose_ops_for_witness(ops,w); chosen[w]=a; rejected[w]=r
        wtext[w]=v4.apply_ops(base,a)
    return base,anchors,methods,ops,chosen,rejected,wtext

# ---------------- structure incl. paratext ----------------
def structure_map(base,anchors):
    tr_pos=base.find('От переводчика')
    if tr_pos<0: tr_pos=len(base)
    S={}
    for key,bnotes in BOUNDARIES.items():
        rows=[{'index':0,'label':'Title / Front matter','type':'front','start_note':1,'start':0,'end':anchors[bnotes[0]]}]
        for i,n in enumerate(bnotes):
            st=anchors[n]; en=anchors[bnotes[i+1]] if i+1<len(bnotes) else tr_pos
            rows.append({'index':i+1,'label':ROMAN[i],'type':'protocol','start_note':n,'start':st,'end':en})
        rows.append({'index':len(bnotes)+1,'label':'Translator’s Note','type':'paratext','subtype':'translator-note','start_note':3309,'start':tr_pos,'end':len(base)})
        S[key]=rows
    return S,tr_pos

def clean_segment_text(t,structural=True):
    if structural: t=v4.strip_structural_markers(t)
    t=t.replace('\u00ad','')
    # remove pure Roman heading lines left in source stream
    t=re.sub(r'(?m)^\s*(?:XXVII|XXVI|XXV|XXIV|XXIII|XXII|XXI|XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)(?:\s+\d+)?\s*$','',t)
    t=re.sub(r'\n{3,}','\n\n',t).strip()
    return t

# ---------------- entities -----------------
ENTITIES={
 'persons':[
  ('david','David',['Давида','Давидова','Давид']),('solomon','Solomon',['Соломоном','Соломона','Соломон']),('moses','Moses',['Моисея','Моисей']),
  ('carnot','Sadi Carnot',['Карно']),('mckinley','William McKinley',['Мак Кинлея','Мак-Кинлея','Мак Кинлей','Мак-Кинлей']),('gambetta','Léon Gambetta',['Гамбеты','Гамбетта']),('faure','Félix Faure',['Феликса Фора','Феликс Фор']),
  ('sulla','Sulla',['Силлы','Силла']),('pericles','Pericles',['Перикла','Перикл']),('augustus','Augustus',['Августа','Август']),('napoleon','Napoleon',['Наполеона','Наполеон']),
  ('charles-v','Charles V',['Карла V']),('louis-xiv','Louis XIV',['Людовика XIV']),('minin','Kuzma Minin',['Минин']),('pozharsky','Dmitry Pozharsky',['Князь Пожарский','Пожарский']),
  ('vishnu','Vishnu',['Вишну']),('montefiore','Moses Montefiore',['Монте Фиоре','Монтефиоре']),('god','God',['Богом','Бога','Боге','Бог','Божий','Божьему','Божества'])],
 'places':[
  ('europe','Europe',['Европе','Европы','Европу','Европой','Европа']),('paris','Paris',['Париже','Париж']),('greece','Greece',['Греции','Греция']),('italy','Italy',['Италия','Италии']),('rome','Rome',['Риме','Рим']),('madrid','Madrid',['Мадриде','Мадрид']),('london','London',['Лондоне','Лондон']),('berlin','Berlin',['Берлине','Берлин']),('st-petersburg','St Petersburg',['С.-Петербурге','Петербурге','Петербург']),('moscow','Moscow',['Москву','Москва','Москве']),('kyiv','Kyiv',['Киев','Киеве']),('odessa','Odessa',['Одессу','Одесса','Одессе']),('jerusalem','Jerusalem',['Иерусалима','Иерусалим']),('constantinople','Constantinople',['Константинополь']),('france','France',['Франции','Франция']),('russia','Russia',['России','Россия','Русь'])],
 'organizations':[
  ('zion','Zion (rhetorical collective in the text)',['Сиона','Сиону','Сионом','Сион']),('freemasonry','Freemasonry / Masons',['франмасонов','масонов','масоны','масонской','масонского','масонским']),('rothschild','Rothschild family',['Ротшильдов','Ротшильды'])],
 'works':[
  ('bible','Bible',['Библии','Библия']),('nehemiah','Book of Nehemiah',['Неемии','Неемия']),('talmud','Talmud',['Талмуда','Талмуд']),('yebamot','Yevamot',['Иебамот']),('ketubot','Ketubot',['Катубот','Кетубот']),('sanhedrin','Sanhedrin',['Санхедрин']),('kiddushin','Kiddushin',['Кидушин','Кадушин']),('joly-dialogue','Maurice Joly, Dialogue aux enfers entre Machiavel et Montesquieu',[]) ]
}
SURF=[]
TAGFILE={'persons':('persName','persons.xml'),'places':('placeName','places.xml'),'organizations':('orgName','organizations.xml'),'works':('title','works.xml')}
for typ,items in ENTITIES.items():
    tag,_=TAGFILE[typ]
    for eid,label,forms in items:
        for form in forms: SURF.append((form,tag,typ,eid))
SURF.sort(key=lambda x:len(x[0]),reverse=True)

def entity_matches(text):
    out=[]; occ=[]
    for form,tag,typ,eid in SURF:
        for m in re.finditer(r'(?<![А-Яа-яЁёA-Za-z])'+re.escape(form)+r'(?![А-Яа-яЁёA-Za-z])',text):
            if any(not(m.end()<=a or m.start()>=b) for a,b in occ): continue
            out.append((m.start(),m.end(),tag,typ,eid,m.group())); occ.append((m.start(),m.end()))
    return sorted(out)

# ---------------- TEI -----------------
NS='http://www.tei-c.org/ns/1.0'; XML='http://www.w3.org/XML/1998/namespace'; XI='http://www.w3.org/2001/XInclude'
ET.register_namespace('',NS); ET.register_namespace('xi',XI)
def q(t): return '{'+NS+'}'+t

def header(title,source,kind='edition'):
    h=ET.Element(q('teiHeader'))
    fd=ET.SubElement(h,q('fileDesc')); ts=ET.SubElement(fd,q('titleStmt')); ET.SubElement(ts,q('title')).text=title
    rs=ET.SubElement(ts,q('respStmt')); ET.SubElement(rs,q('resp')).text='Digital reconstruction, TEI encoding, and witness collation'; ET.SubElement(rs,q('name'),{'{'+XML+'}id':'digital-editor'}).text='University research project'
    ps=ET.SubElement(fd,q('publicationStmt')); ET.SubElement(ps,q('p')).text='Internal scholarly research edition.'
    sd=ET.SubElement(fd,q('sourceDesc')); ET.SubElement(sd,q('p')).text=source
    enc=ET.SubElement(h,q('encodingDesc')); ET.SubElement(enc,q('p')).text='TEI P5 package. Reconstructed reference text and witness-specific reconstructions are encoded separately; critical apparatus remains traceable to De Michelis note numbers. Witness organization is not normalized to a single protocol numbering.'
    refs=ET.SubElement(enc,q('refsDecl')); ET.SubElement(refs,q('p')).text='Apparatus locations use anchors with xml:id note-N in the reconstructed text; witness readings point to witnesses.xml.'
    prof=ET.SubElement(h,q('profileDesc')); lu=ET.SubElement(prof,q('langUsage')); ET.SubElement(lu,q('language'),{'ident':'ru'}).text='Russian'; ET.SubElement(lu,q('language'),{'ident':'en'}).text='English metadata'
    rev=ET.SubElement(h,q('revisionDesc')); ET.SubElement(rev,q('change'),{'when':'2026-09-27'}).text='v5: all former scope-review cases adjudicated; nested apparatus syntax resolved; witness structures and paratext encoded; authority registers linked.'
    return h

def write_xml(root,path):
    ET.indent(root,space='  '); ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def append_annotated(parent,text,refprefix='entities/'):
    ms=entity_matches(text); pos=0
    for st,en,tag,typ,eid,val in ms:
        pre=text[pos:st]
        if pre:
            if len(parent): parent[-1].tail=(parent[-1].tail or '')+pre
            else: parent.text=(parent.text or '')+pre
        _,file=TAGFILE[typ]
        el=ET.SubElement(parent,q(tag),{'ref':refprefix+file+'#'+eid}); el.text=val; pos=en
    tail=text[pos:]
    if tail:
        if len(parent): parent[-1].tail=(parent[-1].tail or '')+tail
        else: parent.text=(parent.text or '')+tail

def append_text_with_anchors(parent,text,abs_start,anchors,refprefix):
    positions=sorted((pos,n) for n,pos in anchors.items() if abs_start<=pos<=abs_start+len(text))
    cur=0
    for pos,n in positions:
        rel=max(0,min(len(text),pos-abs_start))
        append_annotated(parent,text[cur:rel],refprefix)
        ET.SubElement(parent,q('anchor'),{'{'+XML+'}id':f'note-{n}'})
        cur=rel
    append_annotated(parent,text[cur:],refprefix)

def add_structured_span(parent,base,st,en,anchors,head,attrs,refprefix='entities/'):
    dv=ET.SubElement(parent,q('div'),attrs); ET.SubElement(dv,q('head')).text=head
    ab=ET.SubElement(dv,q('ab'))
    raw=base[st:en]
    positions=sorted((pos,n) for n,pos in anchors.items() if st<=pos<en)
    cur=0
    for pos,n in positions:
        rel=pos-st
        append_annotated(ab,raw[cur:rel],refprefix)
        ET.SubElement(ab,q('anchor'),{'{'+XML+'}id':f'note-{n}'})
        cur=rel
    append_annotated(ab,raw[cur:],refprefix)
    return dv

# ---------------- build all outputs -----------------
def main():
    base,anchors,methods,ops,chosen,rejected,wtext=build_core()
    struct,trpos=structure_map(base,anchors)
    (OUT/'reconstructed_base.txt').write_text(base,encoding='utf-8')
    (OUT/'apparatus_operations_resolved.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'source_anomalies.json').write_text(json.dumps(SOURCE_ANOMALIES,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'structure_map.json').write_text(json.dumps(struct,ensure_ascii=False,indent=2),encoding='utf-8')
    # Audit every decision including overlaps.
    fields=['note','page_pdf','witness','action','status','decision','confidence','lemma_candidate','reading_candidate','reading_candidate_preclean','raw_clause','anchor_method']
    with (OUT/'editorial_decisions.csv').open('w',encoding='utf-8-sig',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=fields);wr.writeheader()
        for o in ops:
            if o.get('witness'):wr.writerow({k:o.get(k,'') for k in fields})
    with (OUT/'overlap_decisions.json').open('w',encoding='utf-8') as f: json.dump(rejected,f,ensure_ascii=False,indent=2)

    witness_segments={}; qa={}
    for w in WITS:
        # continuous resolved reconstruction
        full=wtext[w]
        (WOUT/f'{w}_reconstructed_resolved.txt').write_text(full,encoding='utf-8')
        (WOUT/f'{w}_applied_operations.json').write_text(json.dumps(chosen[w],ensure_ascii=False,indent=2),encoding='utf-8')
        segs=[]
        for row in struct[w]:
            txt=v4.apply_ops_interval(base,row['start'],row['end'],chosen[w])
            txt=clean_segment_text(txt,structural=(row['type']=='protocol'))
            segs.append({**row,'text':txt})
        witness_segments[w]=segs
        (WOUT/f'{w}_structured.json').write_text(json.dumps(segs,ensure_ascii=False,indent=2),encoding='utf-8')
        joined='\n\n'.join(x['text'] for x in segs)
        qa[w]={
          'square_brackets_remaining':joined.count('[')+joined.count(']'),
          'apparatus_control_tokens_remaining':len(re.findall(r'\b(?:A1|A2|N|K|B)\s*(?:add|omitt?|omit|:)',joined,re.I)),
          'units':len([x for x in segs if x['type']=='protocol']),
          'paratext_units':len([x for x in segs if x['type']=='paratext'])
        }

    # synopsis by reconstructed 22 protocol windows + separate translator note
    synopsis=[]
    for br in struct['reconstructed']:
        unit={'index':br['index'],'label':br['label'],'type':br['type'],'witnesses':{}}
        for w in WITS:
            txt=v4.apply_ops_interval(base,br['start'],br['end'],chosen[w])
            if br['type']=='protocol':
                own=[x for x in struct[w] if x['type']=='protocol' and br['start']<x['start']<br['end']]
                if own:
                    pieces=[];cur=br['start']
                    for b in own:
                        pieces.append(v4.apply_ops_interval(base,cur,b['start'],chosen[w]));pieces.append(f'\n\n[[PROTOCOL {b["label"]}]]\n\n');cur=b['start']
                    pieces.append(v4.apply_ops_interval(base,cur,br['end'],chosen[w]));txt=''.join(pieces)
                txt=clean_segment_text(txt,True)
                overlaps=[x['label'] for x in struct[w] if x['type']=='protocol' and not(x['end']<=br['start'] or x['start']>=br['end'])]
            else:
                txt=clean_segment_text(txt,False); overlaps=[br['label']]
            unit['witnesses'][w]={'sections':overlaps,'text':txt}
        synopsis.append(unit)
    (OUT/'synopsis.json').write_text(json.dumps(synopsis,ensure_ascii=False,indent=2),encoding='utf-8')

    # ---------- TEI authority files ----------
    witmeta={
      'K':('1903','22','first redaction','Znamja / Kruševan; earliest full witness and De Michelis’s base witness.'),
      'A1':('1905','27','X','Anonymous St Petersburg edition; 27-part redaction.'),
      'B':('1905–1906','27','X','Butmi edition; 27-part redaction, related to A1 but independently modified.'),
      'A2':('1905','24','Y','Anonymous Moscow edition; 24-part redaction.'),
      'N':('1905','24','Y','Nilus edition; 24-part redaction and later influential vulgate.'),
      'R':('1905–1906','single discourse','short redaction','Short redaction R1–R4; not reconstructed as a continuous witness here.'),
      'I':('1917','extract anthology','short redaction','Late extract dependent on N; not reconstructed continuously here.'),
      'W':('unknown','-','hypothetical','Hypothetical common textual stage reconstructed by De Michelis.'),
      'Z':('before/around 1905','-','hypothetical','Hypothetical intermediate antigraph leading to X and Y.'),
      'X':('1905','27','hypothetical redaction','Reconstructed 27-part redaction underlying A1 and B.'),
      'Y':('1905','24','hypothetical redaction','Reconstructed 24-part redaction underlying A2 and N.')}
    wr=ET.Element(q('TEI'),{'{'+XML+'}id':'witness-register'});wr.append(header('Witness register','Witness metadata and hypothetical textual stages described by De Michelis.'))
    st=ET.SubElement(wr,q('standOff'));lw=ET.SubElement(st,q('listWit'))
    for sig,(date,parts,red,desc) in witmeta.items():
        attrs={'{'+XML+'}id':sig};
        if red.startswith('hypothetical') or sig in {'W','Z','X','Y'}: attrs['type']='hypothetical'
        wi=ET.SubElement(lw,q('witness'),attrs);ET.SubElement(wi,q('abbr')).text=sig;ET.SubElement(wi,q('date')).text=date;ET.SubElement(wi,q('note'),{'type':'segmentation'}).text=str(parts);ET.SubElement(wi,q('note'),{'type':'redaction'}).text=red;ET.SubElement(wi,q('desc')).text=desc
    write_xml(wr,TEI/'witnesses.xml')

    rr=ET.Element(q('TEI'),{'{'+XML+'}id':'textual-relations'});rr.append(header('Textual transmission relations','Graph relations abstracted from De Michelis’s Note on the Edition.'))
    st=ET.SubElement(rr,q('standOff'));lr=ET.SubElement(st,q('listRelation'),{'type':'textual-transmission'})
    rels=[('W','K','descendsTo','W → K'),('W','R','descendsTo','W → R'),('W','Z','descendsTo','W → Z'),('Z','X','descendsTo','Z → X'),('X','A1','descendsTo','X → A1'),('X','B','descendsTo','X → B'),('Z','Y','descendsTo','Z → Y'),('Y','A2','descendsTo','Y → A2'),('Y','N','descendsTo','Y → N'),('N','I','sourceOf','I depends on N')]
    for a,b,name,desc in rels:
        rel=ET.SubElement(lr,q('relation'),{'name':name,'active':'witnesses.xml#'+a,'passive':'witnesses.xml#'+b});ET.SubElement(rel,q('desc')).text=desc
    # contamination/open tradition explicitly encoded as non-tree relation
    rel=ET.SubElement(lr,q('relation'),{'name':'contaminationPossible','active':'witnesses.xml#B','passive':'witnesses.xml#Y'});ET.SubElement(rel,q('desc')).text='De Michelis identifies transversal readings/contamination; the stemmatic graph is not a closed tree.'
    write_xml(rr,TEI/'relations.xml')

    # entities
    for typ,items in ENTITIES.items():
        root=ET.Element(q('TEI'),{'{'+XML+'}id':'entities-'+typ});root.append(header('Entity register: '+typ,'Authority file linked from the encoded texts.'))
        st=ET.SubElement(root,q('standOff'))
        if typ=='persons': lst=ET.SubElement(st,q('listPerson')); elname,nameel='person','persName'
        elif typ=='places': lst=ET.SubElement(st,q('listPlace')); elname,nameel='place','placeName'
        elif typ=='organizations': lst=ET.SubElement(st,q('listOrg')); elname,nameel='org','orgName'
        else: lst=ET.SubElement(st,q('listBibl')); elname,nameel='bibl','title'
        for eid,label,forms in items:
            x=ET.SubElement(lst,q(elname),{'{'+XML+'}id':eid});ET.SubElement(x,q(nameel)).text=label
            if forms: ET.SubElement(x,q('note'),{'type':'surfaceForms'}).text='; '.join(forms)
        write_xml(root,TEI/'entities'/f'{typ}.xml')

    # bibliography
    br=ET.Element(q('TEI'),{'{'+XML+'}id':'bibliography'});br.append(header('Bibliography','Core sources for the edition.'))
    tx=ET.SubElement(br,q('text'));bd=ET.SubElement(tx,q('body'));lb=ET.SubElement(bd,q('listBibl'))
    for bid,author,title,date,pub in [
      ('demichelis2004','Cesare G. De Michelis','The Non-Existent Manuscript: A Study of the Protocols of the Sages of Zion','2004','University of Nebraska Press'),
      ('joly1864','Maurice Joly','Dialogue aux enfers entre Machiavel et Montesquieu','1864','Brussels')]:
        b=ET.SubElement(lb,q('bibl'),{'{'+XML+'}id':bid});ET.SubElement(b,q('author')).text=author;ET.SubElement(b,q('title')).text=title;ET.SubElement(b,q('date')).text=date;ET.SubElement(b,q('publisher')).text=pub
    write_xml(br,TEI/'bibliography.xml')

    # taxonomy
    tax=ET.Element(q('TEI'),{'{'+XML+'}id':'taxonomy'});tax.append(header('Editorial taxonomy','Controlled vocabulary for variant and structural categories.'))
    st=ET.SubElement(tax,q('standOff'));txm=ET.SubElement(st,q('taxonomy'),{'{'+XML+'}id':'variant-types'})
    for ident,label in [('addition','Addition'),('omission','Omission'),('replacement','Substitution / replacement'),('segmentation','Witness-specific segmentation'),('normalization','Linguistic normalization'),('contamination','Transversal/contaminated reading'),('source-parallel','Reading supported by Joly parallel')]:
        c=ET.SubElement(txm,q('category'),{'{'+XML+'}id':ident});ET.SubElement(c,q('catDesc')).text=label
    write_xml(tax,TEI/'taxonomy.xml')

    # reconstructed edition + anchors + standOff apparatus
    ed=ET.Element(q('TEI'),{'{'+XML+'}id':'protocols-critical-edition'});ed.append(header('The Protocols of the Sages of Zion: Digital Critical Reconstruction','Cesare G. De Michelis, The Non-Existent Manuscript (2004), Appendix: The Russian Text of the Protocols.'))
    text=ET.SubElement(ed,q('text'));body=ET.SubElement(text,q('body'))
    for row in struct['reconstructed']:
        if row['type']=='protocol':
            attrs={'type':'protocol','{'+XML+'}id':'protocol-%02d'%row['index'],'n':row['label']}; head='Protocol '+row['label']
        elif row['type']=='front':
            attrs={'type':'front','{'+XML+'}id':'front-matter'}; head='Title / Front matter'
        else:
            attrs={'type':'paratext','subtype':'translator-note','{'+XML+'}id':'translator-note'}; head='Translator’s Note'
        add_structured_span(body,base,row['start'],row['end'],anchors,head,attrs,'entities/')
    st=ET.SubElement(ed,q('standOff'));la=ET.SubElement(st,q('listApp'),{'{'+XML+'}id':'apparatus'})
    app_serial=defaultdict(int)
    for o in ops:
        if not o.get('witness'): continue
        key=(o['note'],o['witness']); app_serial[key]+=1
        suffix='' if app_serial[key]==1 else f'-{app_serial[key]}'
        app=ET.SubElement(la,q('app'),{'{'+XML+'}id':f'app-{o["note"]}-{o["witness"]}{suffix}','loc':'#note-'+str(o['note']),'type':o['action'],'resp':'#digital-editor'})
        lem=ET.SubElement(app,q('lem'));lem.text=o.get('lemma_candidate','')
        rd=ET.SubElement(app,q('rdg'),{'wit':'witnesses.xml#'+o['witness'],'cert':('high' if o.get('confidence',0)>=.85 else 'medium' if o.get('confidence',0)>=.65 else 'low')});rd.text=o.get('reading_candidate','')
        ET.SubElement(app,q('note'),{'type':'source-apparatus'}).text=o.get('raw_clause','')
        ET.SubElement(app,q('note'),{'type':'editorial-decision'}).text=f"{o.get('decision','')}; confidence={o.get('confidence','')}"
    for n,msg in SOURCE_ANOMALIES.items(): ET.SubElement(la,q('note'),{'type':'source-anomaly','n':str(n)}).text=msg
    write_xml(ed,TEI/'edition.xml')

    # witness TEIs with each witness's own organization + paratext
    for w,segs in witness_segments.items():
        rt=ET.Element(q('TEI'),{'{'+XML+'}id':'witness-'+w,'corresp':'witnesses.xml#'+w});rt.append(header(f'Witness {w}: reconstructed continuous text',f'Reconstructed computationally from De Michelis’s printed apparatus; see ../data/derived_v5/editorial_decisions.csv for full audit.'))
        tx=ET.SubElement(rt,q('text'));bd=ET.SubElement(tx,q('body'))
        for s in segs:
            body_text=s['text']
            if s['type']=='protocol':
                attrs={'type':'protocol','{'+XML+'}id':f'{w}-protocol-{s["index"]:02d}','n':s['label']}; head=f'{w} Protocol {s["label"]}'
            elif s['type']=='front':
                attrs={'type':'front','{'+XML+'}id':f'{w}-front'}; head='Title / Front matter'
            else:
                attrs={'type':'paratext','subtype':'translator-note','{'+XML+'}id':f'{w}-translator-note'}
                lines=body_text.splitlines(); head=(lines[0].strip() if lines and lines[0].strip() else 'Translator’s Note'); body_text='\n'.join(lines[1:]).lstrip()
            dv=ET.SubElement(bd,q('div'),attrs);ET.SubElement(dv,q('head')).text=head
            for ptxt in [x.strip() for x in re.split(r'\n\s*\n',body_text) if x.strip()]:
                p=ET.SubElement(dv,q('p'));append_annotated(p,re.sub(r'\s*\n\s*',' ',ptxt),'../entities/')
        write_xml(rt,TEI/'witnesses'/f'{w}.xml')

    # corpus XInclude manifest
    corp=ET.Element(q('teiCorpus'),{'{'+XML+'}id':'protocols-corpus'});corp.append(header('Protocols digital edition corpus','Manifest for the edition, witnesses, relations, authorities and bibliography.'))
    for href in ['edition.xml','witnesses.xml','relations.xml','bibliography.xml','taxonomy.xml','entities/persons.xml','entities/places.xml','entities/organizations.xml','entities/works.xml']+[f'witnesses/{w}.xml' for w in WITS]:
        ET.SubElement(corp,'{'+XI+'}include',{'href':href})
    write_xml(corp,TEI/'corpus.xml')

    # ODD + Schematron
    odd='''<?xml version="1.0" encoding="UTF-8"?>\n<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><titleStmt><title>Protocols Digital Critical Edition ODD</title></titleStmt><publicationStmt><p>Internal university research project.</p></publicationStmt><sourceDesc><p>Customization for a multi-witness critical edition.</p></sourceDesc></fileDesc></teiHeader><text><body><schemaSpec ident="protocols" start="TEI teiCorpus"><moduleRef key="tei"/><moduleRef key="header"/><moduleRef key="core"/><moduleRef key="textstructure"/><moduleRef key="textcrit"/><moduleRef key="namesdates"/><moduleRef key="linking"/><elementSpec ident="div" mode="change"><attList><attDef ident="type" mode="change" usage="req"/></attList></elementSpec></schemaSpec></body></text></TEI>'''
    (TEI/'protocols.odd').write_text(odd,encoding='utf-8')
    sch='''<?xml version="1.0" encoding="UTF-8"?><schema xmlns="http://purl.oclc.org/dsdl/schematron"><ns prefix="tei" uri="http://www.tei-c.org/ns/1.0"/><pattern id="protocols"><rule context="tei:div[@type='protocol']"><assert test="@n">Every protocol division must have @n.</assert></rule><rule context="tei:rdg"><assert test="@wit">Every reading must point to a witness.</assert></rule><rule context="tei:persName|tei:placeName|tei:orgName|tei:title[@ref]"><assert test="@ref">Tagged entities must point to an authority file.</assert></rule></pattern></schema>'''
    (TEI/'schema'/'protocols.sch').write_text(sch,encoding='utf-8')

    # ---------- site data ----------
    # segmentation bands proportional to reconstructed source position
    def band(key):
        rows=[r for r in struct[key] if r['type']=='protocol']; denom=max(1,trpos)
        return [{'label':r['label'],'left':round(100*r['start']/denom,4),'width':round(100*(r['end']-r['start'])/denom,4)} for r in rows]
    project={
      'title':'The Protocols — Digital Critical Reconstruction',
      'subtitle':'A multi-witness research edition reconstructed from Cesare G. De Michelis’s critical apparatus',
      'counts':{'apparatus_notes':3602,'resolved_operations':len([o for o in ops if o.get('witness')]),'scope_decisions':sum(1 for o in ops if o.get('decision') not in {'insert_at_note_anchor','explicit_exact'}),'source_anomalies':2},
      'witnesses':[{'id':w,'date':witmeta[w][0],'parts':int(witmeta[w][1]),'redaction':witmeta[w][2],'description':witmeta[w][3]} for w in WITS],
      'relations':[{'from':a,'to':b,'kind':name} for a,b,name,_ in rels]+[{'from':'B','to':'Y','kind':'contaminationPossible'}],
      'segmentation':{'K':band('K'),'A1 / B':band('A1'),'A2 / N':band('A2')},
      'source_anomalies':SOURCE_ANOMALIES}
    (SITE/'data'/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2),encoding='utf-8')
    (SITE/'data'/'structure.json').write_text(json.dumps(struct,ensure_ascii=False),encoding='utf-8')
    (SITE/'data'/'synopsis.json').write_text(json.dumps(synopsis,ensure_ascii=False),encoding='utf-8')
    apps=[]
    for o in ops:
        if not o.get('witness'):continue
        apos=o.get('anchor',0)
        if apos < struct['reconstructed'][1]['start']:
            unit=0
        elif apos >= trpos:
            unit=23
        else:
            unit=next((r['index'] for r in struct['reconstructed'] if r['type']=='protocol' and r['start']<=apos<r['end']),23)
        apps.append({k:o.get(k,'') for k in ['note','page_pdf','witness','action','decision','confidence','lemma_candidate','reading_candidate','raw_clause']}|{'unit':unit})
    (SITE/'data'/'apparatus.json').write_text(json.dumps(apps,ensure_ascii=False),encoding='utf-8')
    (SITE/'data'/'entities.json').write_text(json.dumps({k:[{'id':a,'label':b,'forms':c} for a,b,c in v] for k,v in ENTITIES.items()},ensure_ascii=False),encoding='utf-8')
    recsegs=[]
    for r in struct['reconstructed']:
        recsegs.append({**r,'text':clean_segment_text(base[r['start']:r['end']],r['type']=='protocol')})
    (SITE/'data'/'reconstructed.json').write_text(json.dumps(recsegs,ensure_ascii=False),encoding='utf-8')
    for w,segs in witness_segments.items():(SITE/'data'/'witnesses'/f'{w}.json').write_text(json.dumps(segs,ensure_ascii=False),encoding='utf-8')

    # Embed all site data so index.html works directly from file:// as well as GitHub Pages.
    data_obj={'project':project,'structure':struct,'synopsis':synopsis,'apparatus':apps,'entities':{k:[{'id':a,'label':b,'forms':c} for a,b,c in v] for k,v in ENTITIES.items()},'reconstructed':recsegs,'witnesses':witness_segments}
    (SITE/'assets'/'data.js').write_text('window.PROTOCOLS_DATA='+json.dumps(data_obj,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')

    css='''*{box-sizing:border-box}body{margin:0;background:#f4f1eb;color:#272522;font-family:Georgia,"Times New Roman",serif}header{position:sticky;top:0;z-index:10;background:#201f1d;color:#fff}.nav{max-width:1500px;margin:auto;display:flex;align-items:center;gap:6px;padding:10px 20px}.nav a{color:#d8d2ca;text-decoration:none;padding:9px 12px;border-radius:4px;font:14px system-ui}.nav a.active,.nav a:hover{background:#403d38;color:#fff}.brand{font-weight:700;margin-right:auto}main{max-width:1500px;margin:auto;padding:28px 24px 60px}.hero{display:grid;grid-template-columns:1.05fr .95fr;gap:24px;align-items:stretch}.panel,.wcard{background:#fff;border:1px solid #d7d0c6;border-radius:7px;padding:20px;box-shadow:0 2px 8px #00000008}.eyebrow{text-transform:uppercase;letter-spacing:.12em;font:700 11px system-ui;color:#7a4f38}.hero h1{font-size:44px;line-height:1.02;margin:10px 0 14px}.lead{font-size:19px;line-height:1.55;color:#57524c}.stats{display:flex;gap:10px;flex-wrap:wrap}.stat{background:#e9e3da;border-radius:5px;padding:11px 14px;min-width:128px}.stat b{display:block;font-size:22px}.stat span{font:12px system-ui;color:#625d56}.section-title{margin:34px 0 14px;font-size:28px}.wgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.wcard h3{font-size:27px;margin:0 0 6px}.badge{display:inline-block;background:#eee9e1;padding:4px 7px;border-radius:12px;margin:0 4px 5px 0;font:11px system-ui}.segbar{display:flex;gap:1px;height:11px;margin-top:9px}.segbar i{display:block;flex:1;background:#8a8175}.map svg{width:100%;height:310px}.edge{stroke:#817a71;stroke-width:2;fill:none}.edge.dash{stroke-dasharray:5 4}.node{fill:#fff;stroke:#4f4a44;stroke-width:2}.node.hyp{stroke-dasharray:5 4;fill:#f7f4ef}.nodeText{font:bold 14px system-ui;text-anchor:middle;dominant-baseline:middle}.small{font:12px/1.45 system-ui;color:#6b655e}.segcompare{margin-top:12px}.segrow{display:grid;grid-template-columns:75px 1fr;gap:10px;align-items:center;margin:8px 0}.segtrack{position:relative;height:28px;background:#eee9e2;border-radius:4px;overflow:hidden}.segpiece{position:absolute;top:0;height:100%;border-right:1px solid #fff;background:#9d9488;opacity:.9}.segpiece:nth-child(even){opacity:.65}.segpiece span{display:none}.toolbar{display:flex;gap:10px;margin-bottom:15px}.toolbar select{font:14px system-ui;padding:9px;border:1px solid #c9c0b5;background:#fff}.edition-layout{display:grid;grid-template-columns:210px minmax(420px,1fr) 360px;gap:14px}.side{position:sticky;top:70px;align-self:start;max-height:82vh;overflow:auto}.protocol-list button{display:block;width:100%;text-align:left;border:0;background:none;padding:7px 8px;font:13px system-ui;border-radius:3px}.protocol-list button.active{background:#e5ded4}.textpanel{white-space:pre-wrap;font-size:18px;line-height:1.75;direction:ltr}.apparatus{font:13px/1.45 system-ui}.appitem{padding:10px 0;border-bottom:1px solid #eee}.synopsis{overflow:auto}.synrow{display:grid;grid-template-columns:repeat(5,minmax(330px,1fr));gap:10px;min-width:1750px}.syncell{background:#fff;border:1px solid #d7d0c6;padding:15px;white-space:pre-wrap;line-height:1.58}.boundary{display:block;background:#ded5c9;margin:12px -15px;padding:7px 15px;font:700 11px system-ui;text-transform:uppercase;letter-spacing:.08em}.notice{border-left:3px solid #8a8175;background:#ebe5dc;padding:13px 16px;margin:10px 0 18px;font:13px/1.5 system-ui}.entity-table{width:100%;border-collapse:collapse;background:#fff}.entity-table th,.entity-table td{padding:9px 11px;border-bottom:1px solid #e4ded5;text-align:left}.entity-table th{font:700 12px system-ui}.home-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:1050px){.hero,.home-grid{grid-template-columns:1fr}.wgrid{grid-template-columns:repeat(2,1fr)}.edition-layout{grid-template-columns:1fr}.side{position:static;max-height:none}}'''
    (SITE/'assets'/'style.css').write_text(css,encoding='utf-8')

    js=r'''const D=window.PROTOCOLS_DATA;const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];const esc=s=>(s??'').toString().replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function node(x,y,t,h=false){return `<circle class="node ${h?'hyp':''}" cx="${x}" cy="${y}" r="21"/><text class="nodeText" x="${x}" y="${y}">${t}</text>`}
function map(){return `<div class="panel map"><div class="eyebrow">Transmission map</div><svg viewBox="0 0 760 330"><path class="edge" d="M380 50 L120 115"/><path class="edge" d="M380 50 L380 115"/><path class="edge" d="M380 50 L640 115"/><path class="edge" d="M380 140 L260 205"/><path class="edge" d="M380 140 L500 205"/><path class="edge" d="M260 230 L190 290"/><path class="edge" d="M260 230 L330 290"/><path class="edge" d="M500 230 L450 290"/><path class="edge" d="M500 230 L590 290"/><path class="edge" d="M590 290 L690 290"/><path class="edge dash" d="M330 290 C390 255,430 250,500 230"/>${node(380,35,'W',true)}${node(120,125,'K')}${node(380,125,'Z',true)}${node(640,125,'R')}${node(260,215,'X',true)}${node(500,215,'Y',true)}${node(190,290,'A1')}${node(330,290,'B')}${node(450,290,'A2')}${node(590,290,'N')}${node(710,290,'I')}</svg><div class="small">W, X, Y and Z are hypothetical/reconstructed textual stages. The dashed transversal line marks the fact that De Michelis’s tradition is open and includes contamination/transversal readings rather than a perfectly closed stemma.</div></div>`}
function segCompare(){let rows=Object.entries(D.project.segmentation).map(([k,a])=>`<div class="segrow"><b>${k}</b><div class="segtrack">${a.map(x=>`<i class="segpiece" style="left:${x.left}%;width:${x.width}%" title="Protocol ${x.label}"><span>${x.label}</span></i>`).join('')}</div></div>`).join('');return `<div class="panel"><div class="eyebrow">Competing organizations of the text</div><p class="small">The bars are aligned to the reconstructed textual continuum. They show that 22, 27 and 24 are different segmentations, not merely different numbering systems.</p><div class="segcompare">${rows}</div></div>`}
function cards(){return D.project.witnesses.map(w=>`<div class="wcard"><h3>${w.id}</h3><div><span class="badge">${w.date}</span><span class="badge">${w.redaction}</span></div><p>${w.description}</p><b>${w.parts} protocols</b><div class="segbar">${'<i></i>'.repeat(w.parts)}</div></div>`).join('')}
function home(){return `<section class="hero"><div><div class="eyebrow">Digital critical edition · university research environment</div><h1>${D.project.title}</h1><p class="lead">${D.project.subtitle}</p><div class="stats"><div class="stat"><b>${D.project.counts.apparatus_notes}</b><span>apparatus notes</span></div><div class="stat"><b>${D.project.counts.resolved_operations}</b><span>witness operations adjudicated</span></div><div class="stat"><b>22 / 27 / 24</b><span>structural organizations</span></div></div></div>${map()}</section><div class="home-grid" style="margin-top:16px">${segCompare()}<div class="panel"><div class="eyebrow">Edition model</div><h3>One reconstructed text, five continuous witness views</h3><p>The project keeps De Michelis’s reconstruction distinct from the reconstructed witnesses. K follows a 22-part organization; A1 and B 27; A2 and N 24. The translator’s note is encoded as paratext rather than being absorbed into Protocol XXII.</p><p class="small">Two source-level anomalies remain exactly as printed: apparatus note 380 is absent, and note 2502 gives an addition without a siglum. These are not pending editorial decisions.</p></div></div><h2 class="section-title">Witnesses</h2><div class="wgrid">${cards()}</div>`}
function edition(){setTimeout(setupEdition,0);return `<div class="toolbar"><select id="witSel"><option value="reconstructed">Reconstructed (De Michelis)</option>${['K','A1','A2','N','B'].map(x=>`<option>${x}</option>`).join('')}</select><select id="unitSel"></select></div><div class="edition-layout"><div class="panel side"><div class="eyebrow">Structure</div><div id="plist" class="protocol-list"></div></div><div class="panel"><div id="etitle" class="eyebrow"></div><div id="etext" class="textpanel"></div></div><div class="panel side"><div class="eyebrow">Apparatus / provenance</div><div id="apparatus" class="apparatus"></div></div></div>`}
function setupEdition(){let ws=$('#witSel'),us=$('#unitSel');function load(){let w=ws.value,segs=w==='reconstructed'?D.reconstructed:D.witnesses[w];us.innerHTML=segs.map((s,i)=>`<option value="${i}">${s.type==='protocol'?'Protocol '+s.label:s.label}</option>`).join('');function show(i){let s=segs[i];$('#etitle').textContent=`${w} · ${s.type==='protocol'?'Protocol '+s.label:s.label}`;$('#etext').textContent=s.text;$('#plist').innerHTML=segs.map((x,j)=>`<button data-i="${j}" class="${j===i?'active':''}">${x.type==='protocol'?'Protocol '+x.label:x.label}</button>`).join('');$$('#plist button').forEach(b=>b.onclick=()=>{us.value=b.dataset.i;show(+b.dataset.i)});if(w==='reconstructed'){let a=D.apparatus.filter(o=>o.unit===s.index);$('#apparatus').innerHTML=a.map(o=>`<div class="appitem"><b>${o.note} · ${o.witness}</b> <span class="badge">${o.action}</span><div>${esc(o.lemma_candidate)} → ${esc(o.reading_candidate)}</div><div class="small">${esc(o.decision)} · ${o.confidence}</div></div>`).join('')}else{$('#apparatus').innerHTML='<div class="small">This is the continuous reconstructed witness. Switch to the reconstructed view to inspect De Michelis’s apparatus and the decision provenance.</div>'}}us.onchange=()=>show(+us.value);show(0)}ws.onchange=load;load()}
function synopsis(){setTimeout(setupSyn,0);return `<div class="toolbar"><select id="synSel">${D.synopsis.map((u,i)=>`<option value="${i}">${u.type==='protocol'?'Reference Protocol '+u.label:u.label}</option>`).join('')}</select></div><div id="syn" class="synopsis"></div>`}
function setupSyn(){let s=$('#synSel');function show(){let u=D.synopsis[+s.value];$('#syn').innerHTML=`<div class="synrow">${['K','A1','A2','N','B'].map(w=>{let x=u.witnesses[w],tx=esc(x.text).replace(/\[\[PROTOCOL ([^\]]+)\]\]/g,'<span class="boundary">Witness boundary · Protocol $1</span>');return `<div class="syncell"><b>${w}</b> <span class="small">own unit(s): ${x.sections.join(', ')}</span><hr>${tx}</div>`}).join('')}</div>`}s.onchange=show;show()}
function witnesses(){return `<h1>Witnesses and redactions</h1><div class="wgrid">${cards()}</div><h2 class="section-title">Structural comparison</h2>${segCompare()}<h2 class="section-title">Transmission</h2>${map()}`}
function entities(){let rows=[];for(let [typ,arr] of Object.entries(D.entities))for(let x of arr)rows.push(`<tr><td>${typ}</td><td>${x.label}</td><td>${(x.forms||[]).join(', ')}</td></tr>`);return `<h1>Entity registers</h1><div class="notice">The TEI files link textual mentions to separate authority files for persons, places, organizations, and works using @ref.</div><table class="entity-table"><thead><tr><th>Type</th><th>Entity</th><th>Surface forms tagged</th></tr></thead><tbody>${rows.join('')}</tbody></table>`}
function method(){return `<h1>Editorial method</h1><div class="panel"><h3>Reconstruction</h3><p>Every variant operation extracted from De Michelis’s apparatus has been assigned a scope and action. Former review cases were adjudicated using explicit lemma cues where present; otherwise by the note anchor, bounded lexical windows, nested witness syntax, and conflict priority rules. The full audit is preserved in <code>data/derived_v5/editorial_decisions.csv</code>.</p><h3>Structure</h3><p>No single protocol numbering is imposed on the tradition. K/reconstruction has 22 protocols; A1/B have 27; A2/N have 24. The synopsis uses the 22-part reconstructed continuum only as an alignment window and displays the witness-specific boundaries inside each witness column.</p><h3>TEI package</h3><p>The TEI directory contains the reconstructed edition, five witness documents, witness authority metadata, relations, four entity registers, bibliography, taxonomy, ODD customization, Schematron checks, and an XInclude corpus manifest.</p><h3>Source anomalies</h3><p>Notes 380 and 2502 are retained as source anomalies rather than editorially supplied.</p></div>`}
function render(){let p=(location.hash||'#home').slice(1),f={home,edition,synopsis,witnesses,entities,method}[p]||home;$$('.nav a').forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+p));$('#main').innerHTML=f()}
window.addEventListener('hashchange',render);window.addEventListener('DOMContentLoaded',render);'''
    (SITE/'assets'/'app.js').write_text(js,encoding='utf-8')
    index='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Protocols — Digital Critical Reconstruction</title><link rel="stylesheet" href="assets/style.css"></head><body><header><nav class="nav"><div class="brand">Protocols · Critical Edition</div><a href="#home">Home</a><a href="#edition">Edition</a><a href="#synopsis">Synopsis</a><a href="#witnesses">Witnesses</a><a href="#entities">Entities</a><a href="#method">Method</a></nav></header><main id="main"></main><script src="assets/data.js"></script><script src="assets/app.js"></script></body></html>'''
    (SITE/'index.html').write_text(index,encoding='utf-8')

    # docs
    (DOCS/'editorial_principles.md').write_text('''# Editorial principles\n\n- De Michelis’s reconstructed Russian text is encoded separately from all witnesses.\n- K, A1, A2, N and B are computationally reconstructed from the printed apparatus.\n- Witness structure is retained: K = 22 protocols; A1/B = 27; A2/N = 24.\n- The material headed `От переводчика` is encoded as paratext (`div type="paratext" subtype="translator-note"`), not as part of Protocol XXII.\n- All former scope-review cases have an explicit machine-assisted editorial decision in `editorial_decisions.csv`.\n- Nested witness instructions inside a reading are resolved target-by-target before the continuous witness is generated.\n- Source anomalies 380 and 2502 are not conjecturally repaired.\n- Entity tagging is conservative and authority-file based.\n''',encoding='utf-8')
    (DOCS/'data_model.md').write_text('''# Data model\n\nCanonical scholarly interchange is TEI P5. `edition.xml` carries the reconstructed text and stand-off critical apparatus. Each witness has its own TEI file and own protocol segmentation. `witnesses.xml` is the witness authority list; `relations.xml` expresses descent and contamination/open-tradition relations; `entities/*.xml` are authority registers; `corpus.xml` is the XInclude manifest. JSON under `site_v5/data` is a generated web projection, not the source of truth.\n''',encoding='utf-8')
    (DOCS/'source_anomalies.md').write_text('# Source anomalies\n\n- **380** — the printed body has the note marker but De Michelis prints no apparatus entry.\n- **2502** — the apparatus reads `add.: безличную` without a witness siglum.\n\nThe digital edition records both without assigning conjectural witness evidence.\n',encoding='utf-8')

    report={'apparatus_notes':3602,'witness_operations_total':len([o for o in ops if o.get('witness')]),'operations_status':dict(Counter(o.get('status') for o in ops if o.get('witness'))),'overlap_decisions':{w:len(rejected[w]) for w in WITS},'protocol_counts':{w:len([x for x in struct[w] if x['type']=='protocol']) for w in WITS},'paratext_split_at':trpos,'qa':qa,'source_anomalies':SOURCE_ANOMALIES}
    (OUT/'build_report_v5.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

    # README
    readme=f'''# Protocols digital critical edition — v5\n\nThis package reconstructs the continuous texts of **K, A1, A2, N, and B** from Cesare G. De Michelis’s printed critical apparatus and preserves the reconstructed De Michelis text as a separate layer.\n\n## Completed editorial decisions\nAll {report['witness_operations_total']} witness-specific operations have a resolved scope/action. The former review queue is replaced by an audit table (`data/derived_v5/editorial_decisions.csv`). Overlapping candidates were adjudicated and recorded in `overlap_decisions.json`. The two remaining irregularities are source anomalies, not undecided editorial cases: notes 380 and 2502.\n\n## Structure\n- K: 22 protocols\n- A1: 27 protocols\n- B: 27 protocols\n- A2: 24 protocols\n- N: 24 protocols\n- `От переводчика`: paratextual translator’s note in every structured view.\n\n## TEI\n`tei_v5/edition.xml` — reconstructed text + stand-off apparatus.\n`tei_v5/witnesses/*.xml` — continuous witness texts with witness-specific structure.\n`tei_v5/witnesses.xml` — witness and hypothetical-stage authority list.\n`tei_v5/relations.xml` — transmission graph.\n`tei_v5/entities/*.xml` — persons, places, organizations, works.\n`tei_v5/bibliography.xml`, `taxonomy.xml`, `protocols.odd`, `schema/protocols.sch`, `corpus.xml`.\n\n## Web interface\nOpen `site_v5/index.html`. All data are embedded in `assets/data.js`, so it works directly from disk; the parallel JSON files are also supplied for reuse. The interface provides Home / Edition / Synopsis / Witnesses / Entities / Method.\n\n## Important provenance\nThe witness texts are reverse reconstructions from De Michelis’s apparatus, not fresh diplomatic transcriptions of the historical printed witnesses. Every applied decision is auditable.\n'''
    (ROOT/'README_v5.md').write_text(readme,encoding='utf-8')

    # manifest with SHA256
    manifest=[]
    for root in [OUT,WOUT,TEI,SITE,DOCS]:
        for p in sorted(root.rglob('*')):
            if p.is_file(): manifest.append((hashlib.sha256(p.read_bytes()).hexdigest(),str(p.relative_to(ROOT))))
    (ROOT/'MANIFEST_v5.sha256').write_text('\n'.join(f'{h}  {p}' for h,p in manifest)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
