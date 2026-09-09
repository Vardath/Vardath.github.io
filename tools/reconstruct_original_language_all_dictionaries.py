#!/usr/bin/env python3
from __future__ import annotations

import csv, gzip, io, itertools, json, math, os, re, sqlite3, statistics, time, unicodedata, urllib.request
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/phonetic-all-dictionaries-reconstruction.json'
OUTMD=ROOT/'data/phonetic-all-dictionaries-reconstruction.md'
OUTDICT=ROOT/'data/phonetic-original-language-dictionary.json'
CACHE=ROOT/'.cache/all-dictionaries'; CACHE.mkdir(parents=True,exist_ok=True)
DB=CACHE/'lexicon.sqlite3'
RAW_URL=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP_BASE='https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/'
MIN_FAMILIES=int(os.environ.get('MIN_FAMILIES','3'))
MIN_LANGUAGES=int(os.environ.get('MIN_LANGUAGES','5'))
MAX_CONCEPTS=int(os.environ.get('MAX_CONCEPTS','12000'))
MAX_PATHS_PER_FAMILY=int(os.environ.get('MAX_PATHS_PER_FAMILY','24'))

CELLS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
PHONE={'A1':'i','A2':'a','A3':'u','A4':'ɑ','B1':'m','B2':'n','B3':'ŋ','B4':'r','C1':'f','C2':'s','C3':'x','C4':'h','D1':'p','D2':'t','D3':'k','D4':'ʔ'}
BASE=[('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),('place+manner',True,True,False),('reverse+place+manner',True,True,True)]
CLASSES=[x[0] for x in BASE]+['metathesis','acrophonic','clipblend','resegmentation']
COST={'identity':0.0,'metathesis':.008,'resegmentation':.012,'clipblend':.025,'acrophonic':.035,'reverse':.02,'place':.02,'manner':.02,'reverse+place':.03,'reverse+manner':.03,'place+manner':.03,'reverse+place+manner':.04}


def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).lower()
    return ''.join(c for c in s if not unicodedata.combining(c))

def concept_key(g):
    x=norm(g).strip()
    x=re.sub(r'\([^)]*\)',' ',x)
    x=re.sub(r'\[[^]]*\]',' ',x)
    x=re.sub(r'^(to|a|an|the)\s+','',x)
    x=x.split(';')[0].strip()
    x=re.sub(r'\s+',' ',x)
    if len(x)<2 or len(x)>90:return ''
    if any(x.startswith(z) for z in ('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')):return ''
    return x

def token_cell(tok):
    x=norm(tok).replace('ˈ','').replace('ˌ','').replace('ː','').replace(':','')
    if not x:return None
    if any(c in x for c in 'ieyɪɨɘeɛæ'):return 'A1'
    if any(c in x for c in 'aäɐ'):return 'A2'
    if any(c in x for c in 'uoʊɯʉ'):return 'A3'
    if any(c in x for c in 'ɑɔɒ'):return 'A4'
    if any(c in x for c in 'mwɱ'):return 'B1'
    if any(c in x for c in 'nrlɾɹɬ'):return 'B2'
    if any(c in x for c in 'ŋɲjɰ'):return 'B3'
    if any(c in x for c in 'fvwɸβ'):return 'C1'
    if any(c in x for c in 'sšzʃʒθðcçɕʑ'):return 'C2'
    if any(c in x for c in 'xɣχʁ'):return 'C3'
    if any(c in x for c in 'hħʕ'):return 'C4'
    if any(c in x for c in 'pbɓ'):return 'D1'
    if any(c in x for c in 'tdṭḍʈɖ'):return 'D2'
    if any(c in x for c in 'kgqɢɟ'):return 'D3'
    if 'ʔ' in x:return 'D4'
    return None

def ipa_path(ipa):
    s=str(ipa).strip('/[] ')
    out=[]
    # IPA data is sometimes whitespace-tokenized and sometimes compact. Broad character scan is intentional here.
    for ch in s:
        c=token_cell(ch)
        if c and (not out or out[-1]!=c):out.append(c)
    return tuple(out)

def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
@lru_cache(maxsize=3_000_000)
def sim(a,b):
    if not a or not b:return 0.0
    n,m=len(a),len(b);dp=list(range(m+1))
    for i in range(1,n+1):
        nd=[i]+[0]*m;ra,ca=feat(a[i-1])
        for j in range(1,m+1):
            rb,cb=feat(b[j-1]);sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
            nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+sub)
        dp=nd
    return max(0.0,1-dp[m]/max(n,m))
def base_transform(p,pl,ma,rv):
    cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
    q=tuple('ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p)
    return q[::-1] if rv else q
@lru_cache(maxsize=1_500_000)
def variants(cls,p):
    p=tuple(p);n=len(p);out=[]
    for nm,pl,ma,rv in BASE:
        if cls==nm:return (base_transform(p,pl,ma,rv),)
    if cls=='metathesis':
        for i in range(n-1):q=list(p);q[i],q[i+1]=q[i+1],q[i];out.append(tuple(q))
    elif cls=='resegmentation':
        for k in range(1,n):out.append(p[k:]+p[:k])
    elif cls=='clipblend':
        for k in range(2,n):out += [p[:k],p[n-k:]]
        for l in range(1,n):
            for r in range(1,n-l+1):
                q=p[:l]+p[n-r:]
                if 2<=len(q)<n:out.append(q)
    elif cls=='acrophonic':
        for k in range(2,min(4,n)+1):
            for cuts in itertools.combinations(range(1,n),k-1):out.append(tuple(p[i] for i in (0,)+cuts))
    seen=set();z=[]
    for q in out or [p]:
        if q and q not in seen:seen.add(q);z.append(q)
    return tuple(z)

def bestfit(cand,target):
    best=(-1.0,'identity')
    for cls in CLASSES:
        s=max(sim(v,target) for v in variants(cls,cand))-COST[cls]
        if s>best[0]:best=(s,cls)
    return best

def medoid(counter):
    items=counter.most_common(MAX_PATHS_PER_FAMILY)
    if not items:return None
    den=sum(w for _,w in items);best=None
    for p,w in items:
        sc=sum(sim(p,q)*v for q,v in items)/den;key=(sc,w,-len(p),p)
        if best is None or key>best[0]:best=(key,p,sc)
    return best[1],best[2]

def reconstruct(fam_paths):
    reps=list(fam_paths.values());freq=Counter(reps);pool=[];seen=set()
    for p,_ in freq.most_common(40):
        for cls in ('identity','metathesis','resegmentation','clipblend','acrophonic'):
            for v in variants(cls,p):
                if 2<=len(v)<=12 and v not in seen:seen.add(v);pool.append(v)
    if not pool:return None
    median=statistics.median(map(len,reps));scores=[]
    for c in pool:
        fs=[];ops=[]
        for t in reps:
            s,op=bestfit(c,t);fs.append(s);ops.append(op)
        raw=statistics.mean(fs);score=raw-.012*abs(len(c)-median)
        scores.append((score,raw,c,ops,fs))
    scores.sort(reverse=True,key=lambda x:(x[0],x[1],-len(x[2]),x[2]));return scores[0]

def get_ipa(obj):
    vals=[]
    for s in obj.get('sounds') or []:
        x=s.get('ipa')
        if isinstance(x,str):vals.append(x)
        elif isinstance(x,list):vals += [str(y) for y in x if y]
    return vals

def get_glosses(obj):
    out=[]
    for s in obj.get('senses') or []:
        out += [str(x) for x in (s.get('glosses') or []) if x]
        out += [str(x) for x in (s.get('raw_glosses') or []) if x]
    return out

def family_map():
    url=ASJP_BASE+'languages.csv';p=CACHE/'asjp-languages.csv'
    if not p.exists():urllib.request.urlretrieve(url,p)
    iso2fam={};name2fam={}
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            fam=(r.get('Glottolog_Family') or r.get('Family') or r.get('family') or r.get('Classification') or 'Unclassified').strip() or 'Unclassified'
            iso=(r.get('ISO639P3code') or r.get('ISO639P3') or '').strip();name=(r.get('Name') or '').strip().lower()
            if iso:iso2fam[iso]=fam
            if name:name2fam[name]=fam
    return iso2fam,name2fam

def init_db():
    con=sqlite3.connect(DB);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=OFF');con.execute('PRAGMA temp_store=MEMORY')
    con.executescript('''DROP TABLE IF EXISTS lex; DROP TABLE IF EXISTS inheritance;
    CREATE TABLE lex(lang_code TEXT, lang TEXT, family TEXT, word TEXT, concept TEXT, path TEXT);
    CREATE INDEX lex_concept ON lex(concept); CREATE INDEX lex_word ON lex(lang_code,word);
    CREATE TABLE inheritance(child_lang TEXT, child_word TEXT, parent_lang TEXT, parent_word TEXT);
    CREATE INDEX inh_child ON inheritance(child_lang,child_word);''')
    return con

def parse_inheritance(obj):
    out=[]
    for t in obj.get('etymology_templates') or []:
        name=str(t.get('name') or '').lower();args=t.get('args') or {}
        if name not in ('inh','inh+','inherited'):continue
        parent=str(args.get('2') or args.get('source') or args.get('from') or '').strip()
        word=str(args.get('3') or args.get('term') or '').strip()
        if parent and word:out.append((parent,word))
    return out

def ingest_all():
    iso2fam,name2fam=family_map();con=init_db();cur=con.cursor();batch=[];eb=[]
    stats=Counter();langs=Counter();families=Counter();start=time.time()
    req=urllib.request.Request(RAW_URL,headers={'User-Agent':'Vardath-phonetic-research/3.0'})
    with urllib.request.urlopen(req,timeout=300) as resp, gzip.GzipFile(fileobj=resp) as gz, io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
        for line in f:
            stats['dictionary_entries']+=1
            try:o=json.loads(line)
            except Exception:stats['json_errors']+=1;continue
            lc=str(o.get('lang_code') or '').strip();ln=str(o.get('lang') or '').strip();word=str(o.get('word') or '').strip()
            if not lc or not word:continue
            langs[(lc,ln)]+=1
            fam=iso2fam.get(lc) or name2fam.get(ln.lower()) or 'Unclassified';families[fam]+=1
            ips=get_ipa(o);gs=get_glosses(o)
            if ips and gs:
                paths=[]
                for ipa in ips:
                    p=ipa_path(ipa)
                    if len(p)>=2:paths.append(p)
                if paths:
                    stats['entries_with_mappable_ipa']+=1
                    concepts=[]
                    for g in gs[:6]:
                        c=concept_key(g)
                        if c and c not in concepts:concepts.append(c)
                    for c in concepts[:4]:
                        for p in paths[:2]:batch.append((lc,ln,fam,word,c,' '.join(p)))
            for pl,pw in parse_inheritance(o):eb.append((lc,word,pl,pw))
            if len(batch)>=10000:
                cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch);batch.clear()
            if len(eb)>=10000:
                cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',eb);eb.clear()
            if stats['dictionary_entries']%250000==0:
                con.commit();print(json.dumps({'entries':stats['dictionary_entries'],'languages':len(langs),'mappable':stats['entries_with_mappable_ipa'],'minutes':round((time.time()-start)/60,1)}),flush=True)
    if batch:cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch)
    if eb:cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',eb)
    con.commit();stats['languages']=len(langs);stats['families_seen']=len(families)
    return con,stats,langs

def word_level_historical_audit(con):
    # Validate inherited-from links when both daughter and cited source forms have mappable phonetics.
    q='''SELECT c.lang_code,c.word,p.parent_lang,p.parent_word,c.path,s.path FROM inheritance p JOIN lex c ON c.lang_code=p.child_lang AND c.word=p.child_word JOIN lex s ON s.lang_code=p.parent_lang AND s.word=p.parent_word GROUP BY c.lang_code,c.word,p.parent_lang,p.parent_word,c.path,s.path LIMIT 250000'''
    op=Counter();scores=[];n=0
    for cl,cw,pl,pw,cp,pp in con.execute(q):
        a=tuple(pp.split());b=tuple(cp.split());s,o=bestfit(a,b);op[o]+=1;scores.append(s);n+=1
    return {'matched_inheritance_edges':n,'mean_best_fit':round(statistics.mean(scores),5) if scores else 0,'operator_usage':dict(op)}
def reconstruct_all(con):
    concepts=[]
    q='''SELECT concept,COUNT(DISTINCT lang_code) nlang,COUNT(DISTINCT family) nfam FROM lex WHERE family!='Unclassified' GROUP BY concept HAVING nlang>=? AND nfam>=? ORDER BY nfam DESC,nlang DESC LIMIT ?'''
    concepts=list(con.execute(q,(MIN_LANGUAGES,MIN_FAMILIES,MAX_CONCEPTS)))
    entries=[];start=time.time()
    for ix,(concept,nlang,nfam) in enumerate(concepts,1):
        famc=defaultdict(Counter)
        for fam,path,n in con.execute("SELECT family,path,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,path",(concept,)):
            famc[fam][tuple(path.split())]+=n
        fam_paths={};fam_fit={}
        for fam,cnt in famc.items():
            m=medoid(cnt)
            if m:fam_paths[fam]=m[0];fam_fit[fam]=round(m[1],4)
        if len(fam_paths)<MIN_FAMILIES:continue
        r=reconstruct(fam_paths)
        if not r:continue
        score,raw,cand,ops,fs=r
        # leave-one-family-out stability for manageable family counts
        stab=[]
        if 4<=len(fam_paths)<=40:
            items=list(fam_paths.items())
            for i in range(min(len(items),12)):
                rr=reconstruct(dict(items[:i]+items[i+1:]))
                if rr:stab.append(sim(rr[2],cand))
        stability=statistics.mean(stab) if stab else raw
        conf=.40*raw+.25*min(1,len(fam_paths)/8)+.20*stability+.15*min(1,nlang/25)
        evidence=[]
        for (fam,p),o,s in zip(fam_paths.items(),ops,fs):evidence.append({'family':fam,'path':list(p),'operator':o,'fit':round(s,4),'within_family_medoid_fit':fam_fit[fam]})
        entries.append({'meaning':concept,'form':''.join(PHONE[c] for c in cand),'ipa':'/'+''.join(PHONE[c] for c in cand)+'/','path':list(cand),'languages':nlang,'families':len(fam_paths),'fit':round(raw,4),'stability':round(stability,4),'confidence':round(conf,4),'evidence':evidence})
        if ix%100==0:print(json.dumps({'reconstructed':ix,'of':len(concepts),'minutes':round((time.time()-start)/60,1)}),flush=True)
    entries.sort(key=lambda x:(-x['confidence'],-x['families'],-x['languages'],x['meaning']))
    return entries,len(concepts)
def main():
    con,stats,langs=ingest_all();hist=word_level_historical_audit(con);entries,eligible=reconstruct_all(con)
    summary={'version':3,'source':{'dataset':'English Wiktionary via Wiktextract/Kaikki raw all-language dump','url':RAW_URL,'scope':'Every dictionary entry in the dump is scanned; entries with usable IPA and English glosses enter the man-grid lexical reconstruction.'},'method':{'coordinate_system':'16-state A1-D4 man-grid phonetic bridge','historical_validation':'Wiktionary inherited-from etymology links are backtracked through the same grid when both forms have phonetics','minimum_independent_families':MIN_FAMILIES,'minimum_languages':MIN_LANGUAGES,'max_concepts':MAX_CONCEPTS},'scan':dict(stats),'historical_word_regression':hist,'eligible_meaning_groups':eligible,'dictionary_entries':len(entries),'research_boundary':'This is a model-derived deep ancestral candidate dictionary. It can test consistency with documented historical chains but phonetic fit alone does not establish or overturn a historical relationship.'}
    OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    OUTDICT.write_text(json.dumps({'version':3,'title':'Candidate original-language dictionary — all-language reconstruction','method':summary['method'],'summary':{'entries':len(entries),'languages_scanned':stats['languages'],'dictionary_entries_scanned':stats['dictionary_entries'],'eligible_meaning_groups':eligible},'entries':entries},ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# All-language full-dictionary man-grid reconstruction','',f"Dictionary entries scanned: **{stats['dictionary_entries']:,}**",f"Languages encountered: **{stats['languages']:,}**",f"Entries with usable IPA+meaning: **{stats['entries_with_mappable_ipa']:,}**",f"Matched historical inheritance edges: **{hist['matched_inheritance_edges']:,}**",f"Eligible cross-family meaning groups: **{eligible:,}**",f"Reconstructed dictionary entries: **{len(entries):,}**",'', 'The run scans the complete English-Wiktionary Wiktextract all-language dictionary dump. Only entries with usable pronunciation evidence are permitted to influence phonetic reconstruction.']
    OUTMD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
