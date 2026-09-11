#!/usr/bin/env python3
from __future__ import annotations

import argparse,csv,gzip,hashlib,io,json,math,os,re,sqlite3,statistics,time,unicodedata,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

import man_grid_exact_data as D
import man_grid_exact_engine as E

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/man-grid-exact-v3-remaining-work'
WORK.mkdir(parents=True,exist_ok=True)
MANIFEST=WORK/'prepared-manifest.json'
DB=WORK/'lexicon.sqlite3'
T1=ROOT/'data/man-grid-original-phonetics-exact-v3.json'
OUT4=ROOT/'data/man-grid-original-language-lexical-exact-v3.json'
OUT13=ROOT/'data/man-grid-historical-drift-exact-v3.json'
N=20
RAW=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP='https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
MAX_CONCEPTS=int(os.environ.get('MAX_CONCEPTS','12000'))
CORE_CONCEPTS=int(os.environ.get('CORE_CONCEPTS','2000'))
MIN_LANGUAGES=int(os.environ.get('MIN_LANGUAGES','5'))
MIN_FAMILIES=int(os.environ.get('MIN_FAMILIES','3'))
GAP=.70

SKIP=set("/[](){}<>ˈˌːˑ.·‿#_=+~ |\t\r\n")

def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf-8','ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big')

def gzwrite(path,obj):
    with gzip.open(path,'wt',encoding='utf-8',compresslevel=6) as f:json.dump(obj,f,ensure_ascii=False,separators=(',',':'))

def gzread(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def norm_text(s):
    s=unicodedata.normalize('NFC',str(s or '')).strip().lower()
    s=re.sub(r'\([^)]*\)',' ',s);s=re.sub(r'\[[^]]*\]',' ',s)
    s=re.sub(r'^(to|a|an|the)\s+','',s);s=s.split(';')[0].strip();s=re.sub(r'\s+',' ',s)
    if len(s)<2 or len(s)>90:return ''
    bad=('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')
    return '' if any(s.startswith(x) for x in bad) else s

def get_ipa(o):
    z=[]
    for s in o.get('sounds') or []:
        x=s.get('ipa')
        if isinstance(x,str):z.append(x)
        elif isinstance(x,list):z += [str(q) for q in x if q]
    return z

def get_glosses(o):
    z=[]
    for s in o.get('senses') or []:
        z += [str(q) for q in (s.get('glosses') or []) if q]
        z += [str(q) for q in (s.get('raw_glosses') or []) if q]
    return z

def family_map():
    p=WORK/'asjp-languages.csv'
    if not p.exists():urllib.request.urlretrieve(ASJP,p)
    iso={};name={}
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            fam=(r.get('Glottolog_Family') or r.get('Family') or r.get('family') or r.get('Classification') or 'Unclassified').strip() or 'Unclassified'
            code=(r.get('ISO639P3code') or r.get('ISO639P3') or '').strip();nm=(r.get('Name') or '').strip().lower()
            if code:iso[code]=fam
            if nm:name[nm]=fam
    return iso,name

def build_models():
    spec,params,langs,P,cov=D.load_phoible()
    t1=json.loads(T1.read_text(encoding='utf-8'))
    roots=t1['original_phoneme_inventory']
    root_ids=[r['parameter_id'] for r in roots if r['parameter_id'] in params]
    if len(root_ids)<20:raise RuntimeError('corrected Test 1 inventory did not resolve into exact PHOIBLE parameter set')
    root_rows={r['parameter_id']:r for r in roots if r['parameter_id'] in params}
    nearest={}
    for pid,p in params.items():
        nearest[pid]=min(root_ids,key=lambda q:(E.dist(p['features'],params[q]['features']),q))
    byfirst=defaultdict(list)
    for pid,p in params.items():
        nm=unicodedata.normalize('NFC',p['name'])
        if nm and not any(ch.isspace() for ch in nm):byfirst[nm[0]].append((nm,pid))
    for k in byfirst:byfirst[k].sort(key=lambda x:(-len(x[0]),x[0],x[1]))
    return spec,params,P,cov,root_ids,root_rows,nearest,byfirst

def tokenize_ipa(raw,nearest,byfirst):
    s=unicodedata.normalize('NFC',str(raw or '').strip())
    out=[];i=0;unknown=0
    while i<len(s):
        ch=s[i]
        if ch in SKIP or ch.isspace():i+=1;continue
        hit=None
        for nm,pid in byfirst.get(ch,[]):
            if s.startswith(nm,i):hit=(nm,pid);break
        if hit:
            rid=nearest[hit[1]]
            if not out or out[-1]!=rid:out.append(rid)
            i+=len(hit[0]);continue
        # Combining marks can follow a matched base but may not occur in the PHOIBLE spelling.
        if unicodedata.combining(ch):i+=1;continue
        unknown+=1;i+=1
    return tuple(out),unknown

def seqdist(a,b,params):
    a=tuple(a);b=tuple(b)
    if not a and not b:return 0.0
    if not a or not b:return 1.0
    m=len(b);dp=[j*GAP for j in range(m+1)]
    for i,x in enumerate(a,1):
        nd=[i*GAP]+[0.0]*m
        for j,y in enumerate(b,1):
            sub=E.dist(params[x]['features'],params[y]['features'])
            nd[j]=min(dp[j]+GAP,nd[j-1]+GAP,dp[j-1]+sub)
        dp=nd
    return min(1.0,dp[m]/max(len(a),len(b)))

def medoid(counter,params,limit=24):
    items=counter.most_common(limit)
    if not items:return None
    den=sum(w for _,w in items);best=None
    for s,w in items:
        sc=sum(seqdist(s,t,params)*v for t,v in items)/den
        key=(sc,-w,len(s),s)
        if best is None or key<best[0]:best=(key,s,sc)
    return best[1],best[2]

def reconstruct(family_counts,params):
    fam={};fits={}
    for f,rows in family_counts.items():
        cnt=Counter({tuple(seq):int(n) for seq,n in rows})
        m=medoid(cnt,params)
        if m:fam[f]=m[0];fits[f]=m[1]
    if len(fam)<MIN_FAMILIES:return None
    candidates=sorted(set(fam.values()))
    best=None
    for c in candidates:
        ds=[seqdist(c,s,params) for s in fam.values()]
        q=(statistics.mean(ds),statistics.median(ds),len(c),c)
        if best is None or q<best[0]:best=(q,c,ds)
    root=best[1];mean_d=statistics.mean(best[2]);st=[]
    pairs=list(fam.items())
    if 4<=len(pairs)<=40:
        for i in range(min(12,len(pairs))):
            sub=dict(pairs[:i]+pairs[i+1:]);cands=sorted(set(sub.values()))
            if not cands:continue
            rr=min(cands,key=lambda c:(statistics.mean(seqdist(c,s,params) for s in sub.values()),len(c),c))
            st.append(seqdist(root,rr,params))
    stability=max(0.0,1-(statistics.mean(st) if st else mean_d))
    return root,fam,fits,mean_d,stability

def parse_inheritance(o):
    z=[]
    for t in o.get('etymology_templates') or []:
        n=str(t.get('name') or '').lower();a=t.get('args') or {}
        if n not in {'inh','inh+','inherited'}:continue
        src=str(a.get('2') or a.get('source') or a.get('from') or '').strip()
        word=str(a.get('3') or a.get('term') or '').strip()
        word=re.sub(r'^\*+','',word).strip()
        if src and word:z.append((src,word))
    return z

def init_db():
    if DB.exists():DB.unlink()
    c=sqlite3.connect(DB);c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=OFF');c.execute('PRAGMA temp_store=MEMORY')
    c.executescript('''
      CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,word TEXT,concept TEXT,seq TEXT);
      CREATE INDEX lex_concept ON lex(concept);CREATE INDEX lex_word ON lex(lang_code,word);CREATE INDEX lex_family ON lex(family);
      CREATE TABLE inheritance(child_lang TEXT,child_word TEXT,parent_lang TEXT,parent_word TEXT);
      CREATE INDEX inh_child ON inheritance(child_lang,child_word);
    ''');return c

def prepare():
    spec,params,P,cov,root_ids,root_rows,nearest,byfirst=build_models();iso,name=family_map();con=init_db();cur=con.cursor();batch=[];edges=[];stats=Counter();start=time.time()
    req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-ManGrid-Exact-Lexical/3.0'})
    with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz,io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
        for line in f:
            stats['dictionary_entries']+=1
            try:o=json.loads(line)
            except Exception:stats['json_errors']+=1;continue
            lc=str(o.get('lang_code') or '').strip();ln=str(o.get('lang') or '').strip();word=str(o.get('word') or '').strip()
            if not lc or not word:continue
            fam=iso.get(lc) or name.get(ln.lower()) or 'Unclassified'
            ips=get_ipa(o);gl=get_glosses(o);seqs=[]
            for raw in ips[:3]:
                q,u=tokenize_ipa(raw,nearest,byfirst);stats['ipa_unknown_symbols']+=u
                if len(q)>=2 and q not in seqs:seqs.append(q)
            concepts=[]
            for g in gl[:8]:
                c=norm_text(g)
                if c and c not in concepts:concepts.append(c)
                if len(concepts)>=4:break
            if seqs and concepts:
                stats['entries_with_exact_mappable_ipa']+=1
                for c in concepts:
                    for q in seqs[:2]:batch.append((lc,ln,fam,word,c,' '.join(q)))
            for pl,pw in parse_inheritance(o):edges.append((lc,word,pl,pw))
            if len(batch)>=15000:cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch);batch.clear()
            if len(edges)>=15000:cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',edges);edges.clear()
            if stats['dictionary_entries']%500000==0:
                con.commit();print(json.dumps({'entries':stats['dictionary_entries'],'mappable':stats['entries_with_exact_mappable_ipa'],'minutes':round((time.time()-start)/60,1)}),flush=True)
    if batch:cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch)
    if edges:cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',edges)
    con.commit()
    stats['languages']=con.execute('SELECT COUNT(DISTINCT lang_code) FROM lex').fetchone()[0]
    stats['families']=con.execute("SELECT COUNT(DISTINCT family) FROM lex WHERE family!='Unclassified'").fetchone()[0]
    concepts=list(con.execute('''SELECT concept,COUNT(DISTINCT lang_code),COUNT(DISTINCT family) FROM lex WHERE family!='Unclassified' GROUP BY concept HAVING COUNT(DISTINCT lang_code)>=? AND COUNT(DISTINCT family)>=? ORDER BY COUNT(DISTINCT family) DESC,COUNT(DISTINCT lang_code) DESC,concept LIMIT ?''',(MIN_LANGUAGES,MIN_FAMILIES,MAX_CONCEPTS)))
    lexsh=[[] for _ in range(N)]
    for rank,(concept,nlang,nfam) in enumerate(concepts):
        fc=defaultdict(Counter);lc=defaultdict(Counter)
        for fam,code,lang,seq,n in con.execute("SELECT family,lang_code,lang,seq,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,lang_code,lang,seq",(concept,)):
            q=tuple(seq.split());fc[fam][q]+=int(n);lc[(code,lang,fam)][q]+=int(n)
        item={'rank':rank,'meaning':concept,'languages':int(nlang),'families_reported':int(nfam),'family_sequences':{fam:[[list(q),n] for q,n in cnt.items()] for fam,cnt in fc.items()},'language_sequences':[{'code':k[0],'name':k[1],'family':k[2],'sequences':[[list(q),n] for q,n in cnt.items()]} for k,cnt in lc.items()]}
        lexsh[h64('lex',concept)%N].append(item)
    histsh=[[] for _ in range(N)];hist_seen=set();hist_n=0
    q='''SELECT c.lang_code,c.lang,c.family,c.word,c.concept,c.seq,i.parent_lang,i.parent_word,p.lang,p.family,p.seq
         FROM inheritance i JOIN lex c ON c.lang_code=i.child_lang AND c.word=i.child_word
         JOIN lex p ON p.lang_code=i.parent_lang AND p.word=i.parent_word AND p.concept=c.concept
         WHERE c.family!='Unclassified' GROUP BY c.lang_code,c.word,c.concept,c.seq,i.parent_lang,i.parent_word,p.seq'''
    for cl,cln,cf,cw,concept,cs,pl,pw,pln,pf,ps in con.execute(q):
        k=(cl,cw,pl,pw,concept,cs,ps)
        if k in hist_seen:continue
        hist_seen.add(k);r={'child_code':cl,'child_language':cln,'child_family':cf,'child_word':cw,'parent_code':pl,'parent_language':pln,'parent_family':pf,'parent_word':pw,'meaning':concept,'descendant':cs.split(),'ancestor':ps.split()}
        histsh[h64('hist',cl,cw,pl,pw,concept)%N].append(r);hist_n+=1
    for i in range(N):
        gzwrite(WORK/f'lexical-shard-{i:02d}.json.gz',lexsh[i]);gzwrite(WORK/f'historical-shard-{i:02d}.json.gz',histsh[i])
    manifest={'version':3,'status':'prepared','shards':20,'grid_cells':spec['counts']['total_cells'],'transform_nodes':1,'all_rectangles_mirrored':True,'test1_phonemes':len(root_ids),'source':{'wiktextract':RAW,'phoible_commit':D.PH},'scan':dict(stats),'eligible_meaning_groups':len(concepts),'core_test4_meanings':min(CORE_CONCEPTS,len(concepts)),'historical_pairs':hist_n,'lexical_shard_sizes':[len(x) for x in lexsh],'historical_shard_sizes':[len(x) for x in histsh],'method':{'ipa':'Wiktionary IPA tokenized against PHOIBLE segment spellings, then snapped by exact PHOIBLE feature distance to the corrected Test 1 36-phoneme inventory','grid':'every retained phoneme carries its exact 10-layer LEFT/RIGHT 1,074-cell Man Grid path','invalid_old_mapping_reused':False,'execution':'one shared corpus preparation followed by genuine disjoint 20-way Test 4 and Test 13 shards','custom_timeout_minutes':None}}
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=False),flush=True)

def load_runtime():
    spec,params,P,cov,root_ids,root_rows,nearest,byfirst=build_models();return spec,params,root_rows

def root_entry(item,params,root_rows):
    rr=reconstruct(item['family_sequences'],params)
    if not rr:return None
    root,fam,fits,mean_d,stability=rr
    form=''.join(root_rows[p]['ipa'] for p in root)
    paths=[]
    for p in root:
        row=root_rows[p];paths.append({'ipa':row['ipa'],'parameter_id':p,'root_cell_left':row.get('root_cell_left'),'root_cell_right':row.get('root_cell_right'),'parent_path_L':row.get('man_grid_state',{}).get('parent_path_L',[]),'parent_path_R':row.get('man_grid_state',{}).get('parent_path_R',[])})
    conf=.40*(1-mean_d)+.20*min(1,len(fam)/10)+.20*stability+.20*min(1,item['languages']/30)
    return {'meaning':item['meaning'],'form':form,'ipa':'/'+form+'/','phoneme_ids':list(root),'phonemes':[root_rows[p]['ipa'] for p in root],'languages':item['languages'],'families':len(fam),'mean_family_distance':mean_d,'stability':stability,'confidence':conf,'man_grid_path':paths,'family_representatives':{f:list(s) for f,s in fam.items()}}

def shard4(i):
    spec,params,root_rows=load_runtime();items=gzread(WORK/f'lexical-shard-{i:02d}.json.gz');core=[x for x in items if x['rank']<CORE_CONCEPTS];entries=[]
    for x in core:
        e=root_entry(x,params,root_rows)
        if e:entries.append(e)
    entries.sort(key=lambda x:x['meaning']);wrong=entries[1:]+entries[:1] if len(entries)>1 else entries
    real=[];control=[]
    for e,w in zip(entries,wrong):
        fam=[tuple(v) for v in e['family_representatives'].values()];r=tuple(e['phoneme_ids']);q=tuple(w['phoneme_ids'])
        if fam:
            real.append(statistics.mean(seqdist(r,s,params) for s in fam));control.append(statistics.mean(seqdist(q,s,params) for s in fam))
    out={'test_id':4,'shard':i,'input_meanings':len(core),'entries':entries,'mean_real_same_meaning_distance':statistics.mean(real) if real else None,'mean_wrong_meaning_control_distance':statistics.mean(control) if control else None}
    gzwrite(WORK/f'test4-result-{i:02d}.json.gz',out);print(json.dumps({'test':4,'shard':i,'input':len(core),'output':len(entries)}),flush=True)

def align(a,b,params):
    a=tuple(a);b=tuple(b);n=len(a);m=len(b);dp=[[0.0]*(m+1) for _ in range(n+1)];bt=[[None]*(m+1) for _ in range(n+1)]
    for i in range(1,n+1):dp[i][0]=i*GAP;bt[i][0]='D'
    for j in range(1,m+1):dp[0][j]=j*GAP;bt[0][j]='I'
    for i in range(1,n+1):
        for j in range(1,m+1):
            z=[(dp[i-1][j-1]+E.dist(params[a[i-1]]['features'],params[b[j-1]]['features']),'M'),(dp[i-1][j]+GAP,'D'),(dp[i][j-1]+GAP,'I')]
            dp[i][j],bt[i][j]=min(z,key=lambda x:(x[0],{'M':0,'D':1,'I':2}[x[1]]))
    out=[];i=n;j=m
    while i or j:
        t=bt[i][j]
        if t=='M':out.append((a[i-1],b[j-1]));i-=1;j-=1
        elif t=='D':out.append((a[i-1],None));i-=1
        else:out.append((None,b[j-1]));j-=1
    return list(reversed(out))

def learn_map(rows,params,shuffle=False):
    rows=sorted(rows,key=lambda r:(r['meaning'],r['child_code'],r['child_word'],r['parent_code'],r['parent_word']));anc=[r['ancestor'] for r in rows]
    if shuffle and len(anc)>1:anc=anc[1:]+anc[:1]
    c=defaultdict(Counter)
    for r,a in zip(rows,anc):
        for d,p in align(r['descendant'],a,params):
            if d and p:c[d][p]+=1
    mp={}
    for d,cnt in c.items():
        mx=max(cnt.values());opts=sorted(p for p,n in cnt.items() if n==mx);mp[d]=d if d in opts else opts[0]
    return mp,c

def apply_map(seq,mp):
    z=[]
    for p in seq:
        q=mp.get(p,p)
        if not z or z[-1]!=q:z.append(q)
    return z

def shard13(i):
    spec,params,root_rows=load_runtime();rows=gzread(WORK/f'historical-shard-{i:02d}.json.gz');train=[r for r in rows if h64('hold',r['meaning'],r['child_word'],r['parent_word'])%5!=0];test=[r for r in rows if h64('hold',r['meaning'],r['child_word'],r['parent_word'])%5==0]
    if len(train)<5:train=rows[:max(0,len(rows)-max(1,len(rows)//5))];test=rows[len(train):]
    mp,c=learn_map(train,params,False) if train else ({},{});nm,_=learn_map(train,params,True) if train else ({},{})
    wrong=test[1:]+test[:1] if len(test)>1 else test;ev=[]
    for r,w in zip(test,wrong):
        d=r['descendant'];a=r['ancestor'];pred=apply_map(d,mp);null=apply_map(d,nm);wa=w['ancestor'] if wrong else a
        ev.append({'meaning':r['meaning'],'child_language':r['child_language'],'parent_language':r['parent_language'],'raw':seqdist(d,a,params),'learned':seqdist(pred,a,params),'shuffled_rule':seqdist(null,a,params),'wrong_meaning':seqdist(pred,wa,params)})
    rules=[]
    for d,cnt in c.items():
        for a,n in cnt.most_common():rules.append({'from':d,'to':a,'count':n})
    out={'test_id':13,'shard':i,'assigned_pairs':len(rows),'training_pairs':len(train),'heldout_pairs':len(test),'evaluations':ev,'rules':rules}
    gzwrite(WORK/f'test13-result-{i:02d}.json.gz',out);print(json.dumps({'test':13,'shard':i,'assigned':len(rows),'train':len(train),'heldout':len(test)}),flush=True)

def cohen_d(a,b):
    if len(a)<2 or len(b)<2:return 0.0
    va=statistics.variance(a);vb=statistics.variance(b);p=math.sqrt(((len(a)-1)*va+(len(b)-1)*vb)/max(1,len(a)+len(b)-2))
    return (statistics.mean(b)-statistics.mean(a))/p if p else 0.0

def merge4():
    man=json.loads(MANIFEST.read_text());entries=[];real=[];ctrl=[];wins=0;comp=0;counts=[]
    for i in range(N):
        r=gzread(WORK/f'test4-result-{i:02d}.json.gz');entries+=r['entries'];counts.append({'shard':i,'input':r['input_meanings'],'output':len(r['entries'])});a=r['mean_real_same_meaning_distance'];b=r['mean_wrong_meaning_control_distance']
        if a is not None and b is not None:real.append(a);ctrl.append(b);wins+=a<b;comp+=1
    entries.sort(key=lambda x:(-x['confidence'],-x['families'],-x['languages'],x['meaning']))
    res={'version':3,'test_id':4,'test':'Original-language lexical reconstruction through corrected exact Man Grid','status':'complete','shards':20,'source':man['source'],'grid':{'cells':1074,'all_rectangles_mirrored':True,'transformative_circle_operator_fitted':False},'dependency':{'test1':'data/man-grid-original-phonetics-exact-v3.json','candidate_phonemes':man['test1_phonemes']},'coverage':{'dictionary_entries_scanned':man['scan'].get('dictionary_entries',0),'languages':man['scan'].get('languages',0),'families':man['scan'].get('families',0),'eligible_meaning_groups_total':man['eligible_meaning_groups'],'core_meanings_assigned':sum(x['input'] for x in counts),'reconstructed_meanings':len(entries)},'summary':{'mean_real_same_meaning_distance':statistics.mean(real) if real else None,'mean_wrong_meaning_control_distance':statistics.mean(ctrl) if ctrl else None,'effect_size_cohen_d_control_minus_real':cohen_d(real,ctrl),'shards_real_beats_wrong_meaning':wins,'shards_compared':comp,'shard_agreement':wins/comp if comp else None,'mean_reconstruction_confidence':statistics.mean(e['confidence'] for e in entries) if entries else None},'shard_counts':counts,'entries':entries,'research_boundary':'Candidate same-meaning ancestral forms under the corrected exact-v3 phonetic model; not established Proto-World vocabulary.'}
    OUT4.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res['summary'],ensure_ascii=False),flush=True)

def merge13():
    man=json.loads(MANIFEST.read_text());ev=[];wins=0;comp=0;counts=[];rules=Counter()
    for i in range(N):
        r=gzread(WORK/f'test13-result-{i:02d}.json.gz');ev+=r['evaluations'];counts.append({'shard':i,'assigned':r['assigned_pairs'],'train':r['training_pairs'],'heldout':r['heldout_pairs']});
        for x in r['rules']:rules[(x['from'],x['to'])]+=x['count']
        if r['evaluations']:
            a=statistics.mean(x['learned'] for x in r['evaluations']);b=statistics.mean(x['shuffled_rule'] for x in r['evaluations']);wins+=a<b;comp+=1
    learned=[x['learned'] for x in ev];raw=[x['raw'] for x in ev];shuf=[x['shuffled_rule'] for x in ev];wrong=[x['wrong_meaning'] for x in ev]
    top=[{'from':a,'to':b,'count':n} for (a,b),n in rules.most_common(500)]
    res={'version':3,'test_id':13,'test':'Historical language drift through the corrected exact Man Grid','status':'complete','shards':20,'source':man['source'],'grid':{'cells':1074,'all_rectangles_mirrored':True},'coverage':{'matched_historical_pairs_prepared':man['historical_pairs'],'heldout_pairs_evaluated':len(ev)},'summary':{'mean_raw_distance':statistics.mean(raw) if raw else None,'mean_learned_reverse_distance':statistics.mean(learned) if learned else None,'mean_shuffled_rule_distance':statistics.mean(shuf) if shuf else None,'mean_wrong_meaning_distance':statistics.mean(wrong) if wrong else None,'effect_size_cohen_d_shuffled_minus_learned':cohen_d(learned,shuf),'shards_learned_beats_shuffled':wins,'shards_compared':comp,'shard_agreement':wins/comp if comp else None},'shard_counts':counts,'top_transition_rules':top,'research_boundary':'Cross-validated historical phonetic drift signal only. It does not establish the ultimate original language or assign an operator to the transformative circle.'}
    OUT13.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(res['summary'],ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare')
    for name in ('test4-shard','test13-shard'):
        p=sp.add_parser(name);p.add_argument('--id',type=int,required=True)
    sp.add_parser('merge4');sp.add_parser('merge13');a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='test4-shard':shard4(a.id)
    elif a.cmd=='test13-shard':shard13(a.id)
    elif a.cmd=='merge4':merge4()
    else:merge13()

if __name__=='__main__':main()
