import json,re,shutil,zipfile,hashlib,math,html
from pathlib import Path
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from lxml import etree

ROOT=Path('/mnt/data/Protocols_Digital_Edition_v7')
SITE=ROOT/'site'; DATA=ROOT/'data'; DER=DATA/'derived'; WDIR=DATA/'witnesses'; TEI=ROOT/'tei'
WITS=['K','A1','A2','N','B']; ALL=['reconstructed']+WITS
NS='http://www.tei-c.org/ns/1.0'; XML='{http://www.w3.org/XML/1998/namespace}'

# ---------- core source views ----------
views={'reconstructed':json.load(open(SITE/'data'/'reconstructed.json',encoding='utf-8'))}
for w in WITS:
    views[w]=json.load(open(WDIR/f'{w}_structured.json',encoding='utf-8'))
structure=json.load(open(SITE/'data'/'structure.json',encoding='utf-8'))
app=json.load(open(SITE/'data'/'apparatus.json',encoding='utf-8'))
ops_by_wit={w:json.load(open(WDIR/f'{w}_applied_operations.json',encoding='utf-8')) for w in WITS}
syn_by_basis=json.load(open(SITE/'data'/'synopsis_by_basis.json',encoding='utf-8'))
project=json.load(open(SITE/'data'/'project.json',encoding='utf-8'))

# ---------- entities: expanded authority set for a fresh NER pass ----------
old_entities=json.load(open(SITE/'data'/'entities.json',encoding='utf-8'))
# enrich existing records without losing IDs or forms
entities={k:[] for k in ['persons','places','organizations','works']}
for typ,arr in old_entities.items():
    for e in arr:
        e=dict(e); e.setdefault('kind', {'persons':'person','places':'place','organizations':'organization','works':'work'}[typ]); e.setdefault('source','authority-seed')
        entities[typ].append(e)

def add_entity(typ,id,label,forms,**meta):
    if any(x['id']==id for x in entities[typ]):
        x=next(x for x in entities[typ] if x['id']==id)
        x['forms']=sorted(set(x.get('forms',[])+forms),key=lambda z:(-len(z),z))
        x.update(meta); return
    d={'id':id,'label':label,'forms':forms,'kind':{'persons':'person','places':'place','organizations':'organization','works':'work'}[typ],'source':'v7-rerun'}
    d.update(meta); entities[typ].append(d)

# Persons directly named in the witness texts but absent from the earlier authority set.
add_entity('persons','bourgeois','Léon Bourgeois',['Буржуа'],note='Named in the text as “Буржуа”.')
# Places / geopolitical names observed in the witnesses.
place_additions=[
 ('turkey','Turkey',['Турции','Турция'],38.9637,35.2433,'country'),
 ('asia-minor','Asia Minor',['Малой Азии','Малая Азия'],39.0,32.0,'region'),
 ('england','England',['Англия','Англии'],52.3555,-1.1743,'country'),
 ('germany','Germany',['Германия','Германии'],51.1657,10.4515,'country'),
]
for id,label,forms,lat,lon,subtype in place_additions:
    add_entity('places',id,label,forms,lat=lat,lon=lon,subtype=subtype)
# Coordinates and subtypes for existing place authority records.
coords={
'europe':(54.0,15.0,'continent'),'paris':(48.8566,2.3522,'city'),'greece':(39.0742,21.8243,'country'),
'italy':(41.8719,12.5674,'country'),'rome':(41.9028,12.4964,'city'),'madrid':(40.4168,-3.7038,'city'),
'london':(51.5074,-0.1278,'city'),'berlin':(52.52,13.405,'city'),'st-petersburg':(59.9311,30.3609,'city'),
'moscow':(55.7558,37.6173,'city'),'kyiv':(50.4501,30.5234,'city'),'odessa':(46.4825,30.7233,'city'),
'jerusalem':(31.7683,35.2137,'city'),'constantinople':(41.0082,28.9784,'city'),'france':(46.2276,2.2137,'country'),
'russia':(61.524,105.3188,'country')}
for e in entities['places']:
    if e['id'] in coords:
        e['lat'],e['lon'],e['subtype']=coords[e['id']]
# Organizations and works explicitly named in the reconstructed witnesses.
add_entity('organizations','zion-chancellery','“Central Chancellery of Zion” (rhetorical institution in the text)',
           ['Сионской Главной Канцелярии','Сионская Главная Канцелярия','сионской главной канцеляри','сионская главная канцелярия'])
add_entity('organizations','world-freemasons','World Alliance / Society of Freemasons (as named in titles)',
           ['всемирного союза Франмасонов','Всемирного общества Фран-Масонов','всемирного общества Фран-Масонов'])
add_entity('organizations','world-zionists','World Union of Zionists (as named in the text)',
           ['всемирный союз сионистов','Всемирный союз сионистов'])
add_entity('works','orach-chaim','Orach Chaim (as cited in the text)',['Орах-Хамм','Орах-Хаим','Орах-Хайм'])
add_entity('works','even-haezer','Even HaEzer (as cited in the text)',['Эбен-Гаэзер','Эбен-Гайзер'])
add_entity('works','aram-haim','“Aram-Haim” (citation as printed/reconstructed)',['Арам-Хайм'],note='Preserved as the reconstructed witness reads it; not silently normalized.')
add_entity('works','libre-parole','La Libre Parole',['Libre Parole'])

# Add observed surface variants for several seeded entities.
extras={
 'god':['Божеской','Божеских','Божеским','Божии','Божиих'],
 'zion':['Сионские','Сионской','сионская','сионской'],
 'freemasonry':['фран-масонские','франмасонские','масонства','масонство','масонских','масонские'],
 'talmud':['талмудических','талмудистов'],
 'russia':['Россиею'],
 'france':['Франциею'],
}
for typ,arr in entities.items():
    for e in arr:
        if e['id'] in extras: e['forms']=sorted(set(e.get('forms',[])+extras[e['id']]),key=lambda z:(-len(z),z))

# ---------- controlled concepts for distant reading (not NER) ----------
concepts=[
 {'id':'liberty','label':'Liberty / liberalism','patterns':[r'свобод\w*',r'либерализ\w*']},
 {'id':'power','label':'Power / rule','patterns':[r'власт\w*',r'правлен\w*',r'царств\w*']},
 {'id':'state','label':'State / government','patterns':[r'государств\w*',r'правительств\w*',r'администрац\w*']},
 {'id':'finance','label':'Finance / capital','patterns':[r'капитал\w*',r'банк\w*',r'кредит\w*',r'золот\w*',r'деньг\w*',r'за[её]м\w*',r'займ\w*']},
 {'id':'press','label':'Press / public opinion','patterns':[r'пресс\w*',r'газет\w*',r'журнал\w*',r'общественн\w*\s+мнени\w*']},
 {'id':'law','label':'Law / justice','patterns':[r'закон\w*',r'суд\w*',r'право\w*']},
 {'id':'war','label':'War / coercion','patterns':[r'войн\w*',r'оруж\w*',r'насили\w*',r'террор\w*']},
 {'id':'revolution','label':'Revolution / anarchy','patterns':[r'революц\w*',r'анарх\w*',r'переворот\w*']},
 {'id':'religion','label':'Religion / theology','patterns':[r'религи\w*',r'вер[аыеуой]\w*',r'бог\w*',r'духовен\w*']},
 {'id':'education','label':'Education / formation','patterns':[r'образован\w*',r'воспитан\w*',r'учеб\w*',r'школ\w*']},
 {'id':'parliament','label':'Representation / elections','patterns':[r'парламент\w*',r'выбор\w*',r'конституц\w*',r'республик\w*',r'представительств\w*']},
 {'id':'industry','label':'Industry / monopoly','patterns':[r'промышлен\w*',r'монопол\w*']},
 {'id':'secrecy','label':'Secrecy / hidden government','patterns':[r'тайн\w*',r'секрет\w*',r'незрим\w*',r'невидим\w*']},
 {'id':'morality','label':'Morality','patterns':[r'морал\w*',r'нрав\w*']},
 {'id':'socialism','label':'Socialism / Marxism','patterns':[r'социал\w*',r'марксизм\w*']},
 {'id':'darwinism','label':'Darwinism','patterns':[r'дарвинизм\w*']},
 {'id':'nietzscheism','label':'Nietzscheism','patterns':[r'нитцшеизм\w*',r'нитшейзм\w*']},
 {'id':'antisemitism','label':'Antisemitism','patterns':[r'антисемит\w*',r'антисемизм\w*']},
 {'id':'masonry','label':'Freemasonry','patterns':[r'масон\w*',r'франмасон\w*',r'фран-масон\w*']},
]

# ---------- fresh NER pass ----------
# longest-form first, non-overlapping per structural unit
entity_forms=[]
for typ,arr in entities.items():
    for e in arr:
        for f in e.get('forms',[]):
            if f.strip(): entity_forms.append((len(f),typ,e['id'],e['label'],f,e))
entity_forms.sort(key=lambda x:(-x[0],x[4]))

def sentence_windows(text):
    # 2-sentence windows are a useful co-occurrence scale for this rhetorical prose.
    spans=[]; start=0
    parts=list(re.finditer(r'(?<=[.!?…])\s+',text))
    bounds=[0]+[m.end() for m in parts]+[len(text)]
    sents=[]
    for a,b in zip(bounds,bounds[1:]):
        if b>a: sents.append((a,b))
    for i in range(0,len(sents),2):
        spans.append((sents[i][0],sents[min(i+1,len(sents)-1)][1],i//2))
    if not spans: spans=[(0,len(text),0)]
    return spans

def win_for(pos,windows):
    for a,b,i in windows:
        if a<=pos<b:return i
    return windows[-1][2] if windows else 0

occ=[]; freq={w:{} for w in ALL}; by_unit=defaultdict(list)
for wit,segs in views.items():
    for seg in segs:
        t=seg.get('text',''); occupied=[]; wins=sentence_windows(t)
        for _,typ,eid,label,form,eobj in entity_forms:
            pat=re.compile(r'(?<![А-Яа-яЁёA-Za-z])'+re.escape(form)+r'(?![А-Яа-яЁёA-Za-z])',re.I)
            for m in pat.finditer(t):
                if any(not(m.end()<=a or m.start()>=b) for a,b in occupied): continue
                occupied.append((m.start(),m.end()))
                freq[wit][eid]=freq[wit].get(eid,0)+1
                lo=max(0,m.start()-95); hi=min(len(t),m.end()+115)
                snippet=re.sub(r'\s+',' ',t[lo:hi]).strip()
                o={'witness':wit,'unit_index':seg['index'],'unit_label':seg['label'],'unit_type':seg['type'],
                   'type':typ,'entity':eid,'label':label,'form':m.group(),'start':m.start(),'end':m.end(),
                   'context_window':win_for(m.start(),wins),'snippet':snippet,'method':'authority+surface','confidence':1.0}
                occ.append(o); by_unit[(wit,seg['index'])].append(o)

# entity differential: presence and counts by witness
entity_matrix=[]
for typ,arr in entities.items():
    for e in arr:
        counts={w:freq[w].get(e['id'],0) for w in ALL}
        if sum(counts.values()):
            entity_matrix.append({'id':e['id'],'label':e['label'],'type':typ,'counts':counts,'spread':max(counts.values())-min(counts.values())})
entity_matrix.sort(key=lambda x:(-x['spread'],-sum(x['counts'].values()),x['label']))

# co-occurrence at 2-sentence window level, not whole protocol
co=Counter()
for wit,segs in views.items():
    for seg in segs:
        buckets=defaultdict(set)
        for o in by_unit[(wit,seg['index'])]: buckets[o['context_window']].add(o['entity'])
        for ids in buckets.values():
            ids=sorted(ids)
            for i,a in enumerate(ids):
                for b in ids[i+1:]: co[a+'|'+b]+=1

# ---------- concept indexing ----------
concept_freq={w:{c['id']:0 for c in concepts} for w in ALL}
concept_units=[]
for wit,segs in views.items():
    for seg in segs:
        row={'witness':wit,'unit_index':seg['index'],'unit_label':seg['label'],'counts':{}}
        for c in concepts:
            n=0
            for p in c['patterns']: n+=len(re.findall(p,seg['text'],re.I))
            if n:
                row['counts'][c['id']]=n; concept_freq[wit][c['id']]+=n
        concept_units.append(row)

# ---------- protocol anatomy ----------
marker_re=re.compile(r'\(([A-Za-zА-Яа-яЁё]{1,3})\)')
conf_map={'а':'a','А':'a','с':'c','С':'c','е':'e','Е':'e','о':'o','О':'o','р':'p','Р':'p','х':'x','Х':'x','Ь':'b','ь':'b'}
def marker_norm(raw): return ''.join(conf_map.get(ch,ch.lower()) for ch in raw)

def split_blocks(text):
    ms=list(marker_re.finditer(text)); blocks=[]; prev=0; num=1
    for m in ms:
        en=m.end()
        if en-prev<45: continue
        chunk=text[prev:en].strip()
        if chunk:
            blocks.append({'index':len(blocks),'start':prev,'end':en,'label':marker_norm(m.group(1)),'marker_raw':m.group(1),'text':chunk})
        prev=en
    tail=text[prev:].strip()
    if tail: blocks.append({'index':len(blocks),'start':prev,'end':len(text),'label':f'§{len(blocks)+1}','marker_raw':'','text':tail})
    if len(blocks)<2:
        # fallback: sentence-based chunks, around 500-850 chars, no semantic claim
        sents=list(re.finditer(r'.+?(?:[.!?…](?=\s|$)|$)',text,re.S))
        blocks=[]; st=0; buf=''
        for m in sents:
            if len(buf)>600:
                en=m.start(); chunk=text[st:en].strip()
                if chunk: blocks.append({'index':len(blocks),'start':st,'end':en,'label':f'§{len(blocks)+1}','marker_raw':'','text':chunk})
                st=m.start(); buf=''
            buf+=m.group()
        chunk=text[st:].strip()
        if chunk: blocks.append({'index':len(blocks),'start':st,'end':len(text),'label':f'§{len(blocks)+1}','marker_raw':'','text':chunk})
    return blocks

def concept_counts(text):
    out={}
    for c in concepts:
        n=sum(len(re.findall(p,text,re.I)) for p in c['patterns'])
        if n: out[c['id']]=n
    return out

def global_boundaries(wit,seg):
    st,en=seg.get('start',0),seg.get('end',0); out=[]
    if en<=st:return out
    for ow in WITS:
        if ow==wit: continue
        for s in structure.get(ow,[]):
            if s.get('type')!='protocol': continue
            p=s.get('start',-1)
            if st<p<en:
                out.append({'witness':ow,'label':s['label'],'position':(p-st)/(en-st)})
    return sorted(out,key=lambda x:x['position'])

anatomy={}
for wit,segs in views.items():
    anatomy[wit]=[]
    for seg in segs:
        blocks=split_blocks(seg['text']) if seg['type']=='protocol' else [{'index':0,'start':0,'end':len(seg['text']),'label':'front','marker_raw':'','text':seg['text']}]
        # relevant witness operations. reconstructed gets all operations for density of disagreement.
        if wit=='reconstructed':
            rel=[o for o in app if seg.get('start',0)<=o.get('start',-1)<seg.get('end',0)]
        else:
            rel=[o for o in ops_by_wit[wit] if seg.get('start',0)<=o.get('start',-1)<seg.get('end',0)]
        total_len=max(1,len(seg['text']))
        for b in blocks:
            ents=Counter(o['entity'] for o in by_unit[(wit,seg['index'])] if b['start']<=o['start']<b['end'])
            cc=concept_counts(b['text'])
            # operation positions are in base coordinates; map proportionally within the section.
            vc=0
            for o in rel:
                p=(o.get('start',seg.get('start',0))-seg.get('start',0))/max(1,seg.get('end',1)-seg.get('start',0))
                if b['start']/total_len<=p<max((b['end']/total_len),0.0001): vc+=1
            b['word_count']=len(re.findall(r'[А-Яа-яЁёA-Za-z]+',b['text']))
            b['entity_ids']=[x for x,_ in ents.most_common(8)]
            b['concepts']=[{'id':x,'count':n} for x,n in sorted(cc.items(),key=lambda kv:-kv[1])[:4]]
            b['variant_count']=vc
            b['incipit']=re.sub(r'\s+',' ',b['text'])[:115]
            del b['text']
        anatomy[wit].append({'index':seg['index'],'label':seg['label'],'type':seg['type'],'start_note':seg.get('start_note'),
                             'blocks':blocks,'boundaries':global_boundaries(wit if wit!='reconstructed' else 'K',seg),
                             'variant_count':len(rel),'word_count':len(re.findall(r'[А-Яа-яЁёA-Za-z]+',seg['text']))})

# ---------- variation landscape and witness similarity ----------
def ntoks(s): return re.findall(r'[А-Яа-яЁёA-Za-z0-9]+',s.lower().replace('ё','е'))
landscape=[]
for i,row in enumerate(syn_by_basis['reconstructed']):
    if row['type']!='protocol': continue
    base_t=ntoks(row['witnesses']['reconstructed']['text'])
    diffs={}
    for w in WITS:
        oth=ntoks(row['witnesses'][w]['text'])
        ratio=SequenceMatcher(a=base_t,b=oth,autojunk=False).ratio() if (base_t or oth) else 1.0
        diffs[w]=round(1-ratio,4)
    landscape.append({'unit_index':i,'label':row['label'],'start_note':row.get('start_note'),'diffs':diffs,'mean':round(sum(diffs.values())/len(diffs),4),
                      'entities':len(set(o['entity'] for o in occ if o['witness']=='reconstructed' and o['unit_index']==i))})

sim={a:{} for a in WITS}
for a in WITS:
    for b in WITS:
        if a==b: sim[a][b]=1.0; continue
        scores=[]
        # compare by reconstructed structural windows to avoid assuming common protocol numbering
        for row in syn_by_basis['reconstructed']:
            if row['type']!='protocol': continue
            ta=ntoks(row['witnesses'][a]['text']); tb=ntoks(row['witnesses'][b]['text'])
            scores.append(SequenceMatcher(a=ta,b=tb,autojunk=False).ratio())
        sim[a][b]=round(sum(scores)/max(1,len(scores)),4)

# ---------- write web data ----------
V7=SITE/'data'/'v7'; V7.mkdir(parents=True,exist_ok=True)
json.dump(entities,open(SITE/'data'/'entities.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
json.dump({'occurrences':occ,'frequency':freq,'matrix':entity_matrix},open(V7/'ner_index.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({'pairs':dict(co)},open(V7/'knowledge_graph.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump({'concepts':concepts,'frequency':concept_freq,'units':concept_units},open(V7/'concept_index.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(anatomy,open(V7/'protocol_anatomy.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(landscape,open(V7/'variance_landscape.json','w',encoding='utf-8'),ensure_ascii=False)
json.dump(sim,open(V7/'witness_similarity.json','w',encoding='utf-8'),ensure_ascii=False)
ner_meta={'version':'v7','method':'Fresh corpus-wide hybrid NER: expanded scholarly authority lists + longest-surface matching; overlap resolution by longest match. Concepts are indexed separately and are not treated as named entities.',
          'entity_counts':{k:len(v) for k,v in entities.items()},'occurrences':len(occ),
          'by_witness':{w:sum(freq[w].values()) for w in ALL},
          'by_type':{typ:sum(1 for o in occ if o['type']==typ) for typ in entities}}
json.dump(ner_meta,open(V7/'ner_meta.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)

# ---------- TEI authority files ----------
TEI_NS={'tei':NS}
def E(tag,*args,**kwargs): return etree.Element('{%s}%s'%(NS,tag),*args,**kwargs)
def sub(parent,tag,text=None,**attrs):
    el=etree.SubElement(parent,'{%s}%s'%(NS,tag),**attrs)
    if text is not None: el.text=str(text)
    return el

def write_authority(typ,filename):
    root=E('TEI',nsmap={None:NS}); root.set(XML+'id',f'authority-{typ}')
    hdr=sub(root,'teiHeader'); fd=sub(hdr,'fileDesc'); ts=sub(fd,'titleStmt'); sub(ts,'title',f'Named entity authority: {typ}')
    ps=sub(fd,'publicationStmt'); sub(ps,'p','Internal research edition; NER authority rerun in v7.')
    sd=sub(fd,'sourceDesc'); sub(sd,'p','Authority entries derived from the reconstructed witness corpus and editorial review.')
    text=sub(root,'text'); body=sub(text,'body')
    if typ=='persons': lst=sub(body,'listPerson')
    elif typ=='places': lst=sub(body,'listPlace')
    elif typ=='organizations': lst=sub(body,'listOrg')
    else: lst=sub(body,'listBibl')
    for e in entities[typ]:
        if typ=='persons': item=sub(lst,'person'); item.set(XML+'id',e['id']); sub(item,'persName',e['label'])
        elif typ=='places':
            item=sub(lst,'place'); item.set(XML+'id',e['id']); sub(item,'placeName',e['label'])
            if 'lat' in e:
                loc=sub(item,'location'); sub(loc,'geo',f"{e['lat']} {e['lon']}")
        elif typ=='organizations': item=sub(lst,'org'); item.set(XML+'id',e['id']); sub(item,'orgName',e['label'])
        else: item=sub(lst,'bibl'); item.set(XML+'id',e['id']); sub(item,'title',e['label'])
        note=sub(item,'note'); note.text='Surface forms: '+', '.join(e.get('forms',[]))
        if e.get('note'): note.text += '. '+e['note']
    path=TEI/'entities'/filename; path.parent.mkdir(parents=True,exist_ok=True)
    etree.ElementTree(root).write(str(path),encoding='utf-8',xml_declaration=True,pretty_print=True)

write_authority('persons','persons.xml'); write_authority('places','places.xml'); write_authority('organizations','organizations.xml'); write_authority('works','works.xml')

# Stand-off NER ledger: all witness occurrences, preserving char offsets and links back to witness structural units.
root=E('TEI',nsmap={None:NS}); root.set(XML+'id','ner-v7')
hdr=sub(root,'teiHeader'); fd=sub(hdr,'fileDesc'); ts=sub(fd,'titleStmt'); sub(ts,'title','Corpus-wide named entity recognition ledger (v7)')
sub(fd,'publicationStmt'); fd.find('{%s}publicationStmt'%NS).append(E('p')); fd.find('{%s}publicationStmt/{%s}p'%(NS,NS)).text='Internal scholarly research edition.'
sd=sub(fd,'sourceDesc'); sub(sd,'p',ner_meta['method'])
stand=sub(root,'standOff'); la=sub(stand,'listAnnotation'); la.set('type','named-entities')
for i,o in enumerate(occ,1):
    an=sub(la,'annotation'); an.set(XML+'id',f'ner-{i}'); an.set('type',o['type'])
    target=f"../witnesses/{o['witness']}.xml#{o['witness']}-protocol-{o['unit_index']:02d}" if o['witness']!='reconstructed' and o['unit_type']=='protocol' else f"../witnesses/{o['witness']}.xml"
    sub(an,'ptr',target=target)
    refpath={'persons':'../entities/persons.xml#','places':'../entities/places.xml#','organizations':'../entities/organizations.xml#','works':'../entities/works.xml#'}[o['type']]+o['entity']
    rs=sub(an,'rs',o['form'],type=o['type'],ref=refpath)
    sub(an,'note',f"unit={o['unit_label']}; offsets={o['start']}:{o['end']}; method={o['method']}")
(TEI/'analysis').mkdir(exist_ok=True)
etree.ElementTree(root).write(str(TEI/'analysis'/'ner.xml'),encoding='utf-8',xml_declaration=True,pretty_print=True)

# Add NER ledger to corpus manifest if not already present.
corpus=TEI/'corpus.xml'
try:
    txt=corpus.read_text(encoding='utf-8')
    if 'analysis/ner.xml' not in txt:
        # place include before closing group/text/TEI; xinclude namespace already in file in v6.
        insert='\n    <xi:include href="analysis/ner.xml" parse="xml"/>\n'
        if '</teiCorpus>' in txt: txt=txt.replace('</teiCorpus>',insert+'</teiCorpus>')
        elif '</TEI>' in txt: txt=txt.replace('</TEI>',insert+'</TEI>')
        corpus.write_text(txt,encoding='utf-8')
except Exception:
    pass

# ---------- sync TEI to site and create v7 package ----------
shutil.rmtree(SITE/'tei',ignore_errors=True); shutil.copytree(TEI,SITE/'tei')
(SITE/'downloads').mkdir(exist_ok=True)
zip_path=SITE/'downloads'/'Protocols_TEI_v7.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in TEI.rglob('*'):
        if p.is_file(): z.write(p,p.relative_to(TEI.parent))

# ---------- inject v7 data into file:// compatible data.js ----------
data_js=(SITE/'assets'/'data.js').read_text(encoding='utf-8')
m=re.match(r'window\.PROTOCOLS_DATA=(.*);\s*$',data_js,re.S); D=json.loads(m.group(1))
D['entities']=entities
D['nerIndex']={'occurrences':occ,'frequency':freq,'matrix':entity_matrix}
D['knowledgeGraph']={'pairs':dict(co)}
D['conceptIndex']={'concepts':concepts,'frequency':concept_freq,'units':concept_units}
D['anatomy']=anatomy
D['varianceLandscape']=landscape
D['witnessSimilarity']=sim
D['nerMeta']=ner_meta
D['witnessStyles']={
 'reconstructed':{'label':'De Michelis','color':'#1D2730','short':'DM'},
 'K':{'label':'K · 1903','color':'#286B5F','short':'K'},
 'A1':{'label':'A1 · 1905','color':'#B85F3B','short':'A1'},
 'B':{'label':'B · 1905–06','color':'#7A4F85','short':'B'},
 'A2':{'label':'A2 · 1905','color':'#3C6FA8','short':'A2'},
 'N':{'label':'N · 1905','color':'#B47E20','short':'N'},
}
D['teiDownloads']['package']='downloads/Protocols_TEI_v7.zip'
D['teiDownloads']['ner']='tei/analysis/ner.xml'
D['project']['version']='v7'
D['project']['ner']=ner_meta
(SITE/'assets'/'data.js').write_text('window.PROTOCOLS_DATA='+json.dumps(D,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')

# ---------- write build report ----------
report={'ner':ner_meta,'landscape_units':len(landscape),'anatomy_sections':{w:len(v) for w,v in anatomy.items()},'concepts':len(concepts),'tei_ner_annotations':len(occ)}
json.dump(report,open(ROOT/'data'/'derived'/'build_report_v7.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
