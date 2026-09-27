import json,re,shutil,zipfile,hashlib
from pathlib import Path
ROOT=Path('/mnt/data/Protocols_Digital_Edition_v6')
SITE=ROOT/'site'; DATA=ROOT/'data'; DER=DATA/'derived'; WDIR=DATA/'witnesses'
WITS=['K','A1','A2','N','B']
base=(DER/'reconstructed_base.txt').read_text(encoding='utf-8')
struct=json.load(open(SITE/'data'/'structure.json',encoding='utf-8'))
entities=json.load(open(SITE/'data'/'entities.json',encoding='utf-8'))
ops={w:json.load(open(WDIR/f'{w}_applied_operations.json',encoding='utf-8')) for w in WITS}

def clean(t):
    t=t.replace('\u00ad','')
    t=re.sub(r'\[\[PROTOCOL ([^\]]+)\]\]', r'\n', t)
    t=re.sub(r'(?m)^\s*(?:XXVII|XXVI|XXV|XXIV|XXIII|XXII|XXI|XX|XIX|XVIII|XVII|XVI|XV|XIV|XIII|XII|XI|X|IX|VIII|VII|VI|V|IV|III|II|I)(?:\s+\d+)?\s*$', '', t)
    t=re.sub(r'\n{3,}','\n\n',t)
    return t.strip()

def apply_range(w,st,en):
    txt=base[st:en]
    relevant=[]
    for o in ops[w]:
        a=o.get('start',0); b=o.get('end',a)
        # retain only edits fully contained in window; structural boundaries are note anchors,
        # so cross-boundary edits are exceptional and are left to the adjacent alignment note.
        if a>=st and b<=en:
            relevant.append(o)
    for o in sorted(relevant,key=lambda x:(x.get('start',0),x.get('end',0)),reverse=True):
        a=o.get('start',0)-st; b=o.get('end',o.get('start',0))-st
        rep='' if o.get('action')=='omit' else o.get('reading_candidate','')
        txt=txt[:a]+rep+txt[b:]
    return clean(txt)

def own_sections(w,st,en):
    out=[]
    for s in struct[w]:
        if s['end']>st and s['start']<en:
            out.append({'index':s['index'],'label':s['label'],'type':s['type'],'start_note':s.get('start_note')})
    return out

syn_by_basis={}
for basis in ['reconstructed']+WITS:
    rows=[]
    for i,s in enumerate(struct[basis]):
        st,en=s['start'],s['end']
        row={'index':i,'label':s['label'],'type':s['type'],'start_note':s.get('start_note'),'start':st,'end':en,'basis':basis,'witnesses':{}}
        for w in ['reconstructed']+WITS:
            tx=clean(base[st:en]) if w=='reconstructed' else apply_range(w,st,en)
            row['witnesses'][w]={'text':tx,'sections': own_sections(w if w!='reconstructed' else 'reconstructed',st,en)}
        rows.append(row)
    syn_by_basis[basis]=rows
(SITE/'data'/'synopsis_by_basis.json').write_text(json.dumps(syn_by_basis,ensure_ascii=False),encoding='utf-8')

# Entity occurrence index across the actual structured witness views.
views={'reconstructed':json.load(open(SITE/'data'/'reconstructed.json',encoding='utf-8'))}
for w in WITS:
    views[w]=json.load(open(WDIR/f'{w}_structured.json',encoding='utf-8'))
forms=[]
for typ,arr in entities.items():
    for e in arr:
        for f in e.get('forms',[]):
            forms.append((len(f),typ,e['id'],e['label'],f))
forms.sort(reverse=True)
occ=[]; freq={}
for wit,segs in views.items():
    freq[wit]={}
    for seg in segs:
        t=seg.get('text','')
        occupied=[]
        for _,typ,eid,label,form in forms:
            for m in re.finditer(r'(?<![А-Яа-яЁёA-Za-z])'+re.escape(form)+r'(?![А-Яа-яЁёA-Za-z])',t,re.I):
                if any(not(m.end()<=a or m.start()>=b) for a,b in occupied): continue
                occupied.append((m.start(),m.end()))
                freq[wit][eid]=freq[wit].get(eid,0)+1
                lo=max(0,m.start()-75); hi=min(len(t),m.end()+75)
                snippet=re.sub(r'\s+',' ',t[lo:hi]).strip()
                occ.append({'witness':wit,'unit_index':seg['index'],'unit_label':seg['label'],'unit_type':seg['type'],'type':typ,'entity':eid,'label':label,'form':m.group(),'snippet':snippet})
idx={'occurrences':occ,'frequency':freq}
(SITE/'data'/'entity_index.json').write_text(json.dumps(idx,ensure_ascii=False),encoding='utf-8')

# Co-occurrence at structural-unit level.
co={}
for wit,segs in views.items():
    for seg in segs:
        ids=set(o['entity'] for o in occ if o['witness']==wit and o['unit_index']==seg['index'])
        ids=sorted(ids)
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                k=a+'|'+b; co[k]=co.get(k,0)+1
(SITE/'data'/'entity_cooccurrence.json').write_text(json.dumps(co,ensure_ascii=False),encoding='utf-8')

# Copy TEI into web-visible subtree; create package downloads.
shutil.rmtree(SITE/'tei',ignore_errors=True); shutil.copytree(ROOT/'tei',SITE/'tei')
(SITE/'downloads').mkdir(exist_ok=True)
for name,folder in [('Protocols_TEI_v6.zip',ROOT/'tei')]:
    zp=SITE/'downloads'/name
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file(): z.write(p,p.relative_to(folder.parent))

# Inject additions into data.js so file:// usage still works without fetch/CORS.
data_js=(SITE/'assets'/'data.js').read_text(encoding='utf-8')
m=re.match(r'window\.PROTOCOLS_DATA=(.*);\s*$',data_js,re.S)
D=json.loads(m.group(1))
D['synopsisByBasis']=syn_by_basis
D['entityIndex']=idx
D['entityCooccurrence']=co
D['teiDownloads']={
 'package':'downloads/Protocols_TEI_v6.zip',
 'edition':'tei/edition.xml',
 'K':'tei/witnesses/K.xml','A1':'tei/witnesses/A1.xml','A2':'tei/witnesses/A2.xml','N':'tei/witnesses/N.xml','B':'tei/witnesses/B.xml',
 'witnesses':'tei/witnesses.xml','relations':'tei/relations.xml','persons':'tei/entities/persons.xml','places':'tei/entities/places.xml','organizations':'tei/entities/organizations.xml','works':'tei/entities/works.xml'
}
D['project']['version']='v6'
(SITE/'assets'/'data.js').write_text('window.PROTOCOLS_DATA='+json.dumps(D,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')

print('synopsis rows', {k:len(v) for k,v in syn_by_basis.items()})
print('entity occurrences',len(occ),'co pairs',len(co))
