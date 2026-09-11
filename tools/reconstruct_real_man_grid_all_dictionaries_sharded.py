#!/usr/bin/env python3
"""20-shard all-language reconstruction through the source-traced Man Grid.

This is the corrected replacement experiment for the old A1-D4 / 16-state reconstruction.
No 4x4 cells, 16x16 transition matrix, row/column mirrors, transpose, metathesis or old
language-transformation rules are used. IPA segments are projected to continuous points on
the 716x910 source trace by real_man_grid_core; the only predeclared transform is the live
tool's vertical fold x' = 2*axis-x.
"""
from __future__ import annotations

import argparse,csv,gzip,json,os,re,sqlite3,statistics,time,unicodedata,urllib.request
from collections import Counter,defaultdict
from pathlib import Path

import real_man_grid_core as mg

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'real-man-grid-all-dictionaries-shards';WORK.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'data'/'real-man-grid-all-dictionaries-reconstruction.json'
OUTMD=ROOT/'data'/'real-man-grid-all-dictionaries-reconstruction.md'
OUTDICT=ROOT/'data'/'real-man-grid-original-language-dictionary.json'
CACHE=ROOT/'.cache'/'real-man-grid-all-dictionaries';CACHE.mkdir(parents=True,exist_ok=True)
DB=CACHE/'lexicon.sqlite3'
RAW_URL=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
ASJP='https://raw.githubusercontent.com/lexibank/asjp/v21/cldf/languages.csv'
N=int(os.environ.get('N_SHARDS','20'));MIN_FAMILIES=int(os.environ.get('MIN_FAMILIES','3'));MIN_LANGUAGES=int(os.environ.get('MIN_LANGUAGES','5'));MAX_CONCEPTS=int(os.environ.get('MAX_CONCEPTS','12000'));MAX_PATHS=int(os.environ.get('MAX_PATHS_PER_FAMILY','18'))
SEP='␟'


def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).lower()
    return ''.join(c for c in s if not unicodedata.combining(c))

def concept_key(g):
    x=norm(g).strip();x=re.sub(r'\([^)]*\)',' ',x);x=re.sub(r'\[[^]]*\]',' ',x);x=re.sub(r'^(to|a|an|the)\s+','',x);x=x.split(';')[0].strip();x=re.sub(r'\s+',' ',x)
    if len(x)<2 or len(x)>90:return ''
    bad=('alternative form of ','inflection of ','plural of ','past participle of ','misspelling of ','obsolete spelling of ')
    return '' if any(x.startswith(z) for z in bad) else x

def get_ipa(o):
    out=[]
    for s in o.get('sounds') or []:
        x=s.get('ipa')
        if isinstance(x,str):out.append(x)
        elif isinstance(x,list):out.extend(str(y) for y in x if y)
    return out

def get_glosses(o):
    out=[]
    for s in o.get('senses') or []:
        out.extend(str(x) for x in (s.get('glosses') or []) if x);out.extend(str(x) for x in (s.get('raw_glosses') or []) if x)
    return out

def parse_inheritance(o):
    out=[]
    for t in o.get('etymology_templates') or []:
        if str(t.get('name') or '').lower() not in ('inh','inh+','inherited'):continue
        a=t.get('args') or {};pl=str(a.get('2') or a.get('source') or a.get('from') or '').strip();pw=str(a.get('3') or a.get('term') or '').strip()
        if pl and pw:out.append((pl,pw))
    return out

def family_map():
    p=CACHE/'asjp-languages.csv'
    if not p.exists():urllib.request.urlretrieve(ASJP,p)
    i2f={};n2f={}
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            fam=(r.get('Glottolog_Family') or r.get('Family') or r.get('family') or r.get('Classification') or 'Unclassified').strip() or 'Unclassified'
            iso=(r.get('ISO639P3code') or r.get('ISO639P3') or '').strip();name=(r.get('Name') or '').strip().lower()
            if iso:i2f[iso]=fam
            if name:n2f[name]=fam
    return i2f,n2f

def init_db():
    con=sqlite3.connect(DB);con.execute('PRAGMA journal_mode=WAL');con.execute('PRAGMA synchronous=OFF');con.execute('PRAGMA temp_store=MEMORY')
    con.executescript('DROP TABLE IF EXISTS lex;DROP TABLE IF EXISTS inheritance;CREATE TABLE lex(lang_code TEXT,lang TEXT,family TEXT,word TEXT,concept TEXT,path TEXT);CREATE INDEX lex_concept ON lex(concept);CREATE INDEX lex_word ON lex(lang_code,word);CREATE TABLE inheritance(child_lang TEXT,child_word TEXT,parent_lang TEXT,parent_word TEXT);CREATE INDEX inh_child ON inheritance(child_lang,child_word);')
    return con

def encode_tokens(tokens):return SEP.join(tokens)
def decode_tokens(s):return tuple(x for x in str(s).split(SEP) if x)
def token_path(tokens,enc):return [enc.coords[t] for t in tokens if t in enc.coords]

def scan_all(enc):
    i2f,n2f=family_map();con=init_db();cur=con.cursor();batch=[];eb=[];stats=Counter();langs=set();fams=set();start=time.time()
    req=urllib.request.Request(RAW_URL,headers={'User-Agent':'Vardath-real-man-grid-reconstruction/1.0'})
    with urllib.request.urlopen(req,timeout=300) as resp,gzip.GzipFile(fileobj=resp) as gz:
        import io
        with io.TextIOWrapper(gz,encoding='utf-8',errors='replace') as f:
            for line in f:
                stats['dictionary_entries']+=1
                try:o=json.loads(line)
                except Exception:stats['json_errors']+=1;continue
                lc=str(o.get('lang_code') or '').strip();ln=str(o.get('lang') or '').strip();word=str(o.get('word') or '').strip()
                if not lc or not word:continue
                langs.add((lc,ln));fam=i2f.get(lc) or n2f.get(ln.lower()) or 'Unclassified';fams.add(fam)
                ipas=[]
                for ipa in get_ipa(o):
                    tok=tuple(enc.tokenize(ipa))
                    if len(tok)>=2 and tok not in ipas:ipas.append(tok)
                if ipas:
                    concepts=[]
                    for g in get_glosses(o)[:8]:
                        c=concept_key(g)
                        if c and c not in concepts:concepts.append(c)
                    if concepts:
                        stats['entries_with_mappable_ipa']+=1
                        for c in concepts[:4]:
                            for tok in ipas[:2]:batch.append((lc,ln,fam,word,c,encode_tokens(tok)))
                for pl,pw in parse_inheritance(o):eb.append((lc,word,pl,pw))
                if len(batch)>=12000:cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch);batch.clear()
                if len(eb)>=12000:cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',eb);eb.clear()
                if stats['dictionary_entries']%500000==0:
                    con.commit();print(json.dumps({'scan':stats['dictionary_entries'],'languages':len(langs),'mappable':stats['entries_with_mappable_ipa'],'minutes':round((time.time()-start)/60,1)}),flush=True)
    if batch:cur.executemany('INSERT INTO lex VALUES(?,?,?,?,?,?)',batch)
    if eb:cur.executemany('INSERT INTO inheritance VALUES(?,?,?,?)',eb)
    con.commit();stats['languages']=len(langs);stats['families_seen']=len(fams)
    return con,dict(stats)

def historical_audit(con,enc,limit=50000):
    q='''SELECT c.path,s.path FROM inheritance p JOIN lex c ON c.lang_code=p.child_lang AND c.word=p.child_word JOIN lex s ON s.lang_code=p.parent_lang AND s.word=p.parent_word GROUP BY c.path,s.path LIMIT ?'''
    scores=[];fold=0
    for cp,pp in con.execute(q,(limit,)):
        child=token_path(decode_tokens(cp),enc);parent=token_path(decode_tokens(pp),enc)
        if not child or not parent:continue
        sc,op=mg.best_orientation(parent,child,enc);scores.append(sc);fold+=op=='fold'
    return {'matched_edges':len(scores),'mean_best_identity_or_fold':statistics.mean(scores) if scores else 0.0,'fold_best_count':fold,'identity_best_count':len(scores)-fold}

def family_medoid(rows,enc):
    paths=[]
    for s,n in rows:
        p=token_path(decode_tokens(s),enc)
        paths.extend([p]*min(int(n),4))
    if not paths:return None
    if len(paths)>MAX_PATHS:paths=paths[:MAX_PATHS]
    return mg.medoid(paths,enc,allow_fold=False)

def prepare():
    encoder=mg.build_encoder(force=True);enc=mg.Encoder(encoder);con,stats=scan_all(enc);hist=historical_audit(con,enc)
    q='''SELECT concept,COUNT(DISTINCT lang_code),COUNT(DISTINCT family) FROM lex WHERE family!='Unclassified' GROUP BY concept HAVING COUNT(DISTINCT lang_code)>=? AND COUNT(DISTINCT family)>=? ORDER BY COUNT(DISTINCT family) DESC,COUNT(DISTINCT lang_code) DESC LIMIT ?'''
    concepts=list(con.execute(q,(MIN_LANGUAGES,MIN_FAMILIES,MAX_CONCEPTS)))
    shards=[[] for _ in range(N)]
    for ix,(concept,nlang,nfam) in enumerate(concepts):
        famrows=defaultdict(list)
        for fam,path,cnt in con.execute("SELECT family,path,COUNT(*) FROM lex WHERE concept=? AND family!='Unclassified' GROUP BY family,path ORDER BY family,COUNT(*) DESC",(concept,)):
            if len(famrows[fam])<MAX_PATHS:famrows[fam].append([path,int(cnt)])
        shards[ix%N].append({'meaning':concept,'languages':int(nlang),'families_reported':int(nfam),'family_paths':dict(famrows)})
    manifest={'version':1,'test':'all-language original-language reconstruction through source-traced Man Grid','shards':N,'eligible_meaning_groups':len(concepts),'scan':stats,'historical_identity_or_fold_audit':hist,'geometry':{'width':encoder['width'],'height':encoder['height'],'axis':encoder['axis'],'trace_segments':encoder['trace_segments'],'trace_file':encoder['trace_file']},'phonetic_overlay':{'source':'PHOIBLE feature vectors only','method':encoder['embedding'],'phoible_commit':encoder['phoible_commit']},'allowed_transform':['identity','tool_fold'],'forbidden':['A1-D4 cells','16-state proxy','16x16 transitions','row mirror','column mirror','transpose','old learned language rules']}
    (WORK/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for i,x in enumerate(shards):
        with gzip.open(WORK/f'shard-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,separators=(',',':'))
    print(json.dumps({'phase':'prepare','eligible':len(concepts),'sizes':[len(x) for x in shards],'scan':stats,'historical':hist}),flush=True)

def reconstruct_one(item,enc):
    fam={};within={}
    for name,rows in item['family_paths'].items():
        m=family_medoid(rows,enc)
        if m:fam[name]=m[0];within[name]=m[1]
    if len(fam)<MIN_FAMILIES:return None
    r=mg.latent_barycenter(fam,enc,iterations=2)
    if not r:return None
    cand,ops,fits=r;raw=statistics.mean(fits.values());direct=statistics.mean(mg.sim(cand,p) for p in fam.values())
    # deterministic leave-one-family-out reconstruction for up to six families
    loo=[]
    keys=sorted(fam)
    for k in keys[:min(6,len(keys))]:
        sub={a:b for a,b in fam.items() if a!=k}
        if len(sub)<MIN_FAMILIES:continue
        rr=mg.latent_barycenter(sub,enc,iterations=1)
        if rr:loo.append(mg.best_orientation(rr[0],fam[k],enc)[0])
    tokens=[enc.nearest_segment(p) for p in cand]
    return {'meaning':item['meaning'],'tokens':tokens,'ipa':'/'+''.join(tokens)+'/','coordinates':[[round(x,3),round(y,3)] for x,y in cand],'languages':item['languages'],'families':len(fam),'mean_family_fit':round(raw,6),'mean_direct_fit':round(direct,6),'fold_gain':round(raw-direct,6),'fold_family_count':sum(v=='fold' for v in ops.values()),'identity_family_count':sum(v=='identity' for v in ops.values()),'loo_mean':round(statistics.mean(loo),6) if loo else None,'family_evidence':[{'family':k,'within_family_medoid_fit':round(within[k],6),'orientation':ops[k],'fit':round(fits[k],6)} for k in sorted(fam)]}

def shard(i):
    enc=mg.Encoder();
    with gzip.open(WORK/f'shard-{i:02d}.json.gz','rt',encoding='utf-8') as f:items=json.load(f)
    out=[]
    for j,item in enumerate(items,1):
        r=reconstruct_one(item,enc)
        if r:out.append(r)
        if j%25==0:print(json.dumps({'shard':i,'processed':j,'of':len(items),'reconstructed':len(out)}),flush=True)
    with gzip.open(WORK/f'result-{i:02d}.json.gz','wt',encoding='utf-8') as f:json.dump({'shard':i,'input':len(items),'entries':out},f,ensure_ascii=False,separators=(',',':'))
    print(json.dumps({'phase':'shard','shard':i,'input':len(items),'output':len(out)}),flush=True)

def merge():
    manifest=json.loads((WORK/'manifest.json').read_text(encoding='utf-8'));entries=[];counts=[]
    for i in range(N):
        with gzip.open(WORK/f'result-{i:02d}.json.gz','rt',encoding='utf-8') as f:r=json.load(f)
        entries.extend(r['entries']);counts.append({'shard':i,'input':r['input'],'output':len(r['entries'])})
    entries.sort(key=lambda x:(-x['mean_family_fit'],-x['families'],-x['languages'],x['meaning']))
    fits=[e['mean_family_fit'] for e in entries];loo=[e['loo_mean'] for e in entries if e['loo_mean'] is not None];gains=[e['fold_gain'] for e in entries]
    summary={'version':1,'test':manifest['test'],'dictionary_entries':len(entries),'shards':N,'shard_counts':counts,'scan':manifest['scan'],'historical_identity_or_fold_audit':manifest['historical_identity_or_fold_audit'],'geometry':manifest['geometry'],'phonetic_overlay':manifest['phonetic_overlay'],'allowed_transform':manifest['allowed_transform'],'metrics':{'mean_family_fit':statistics.mean(fits) if fits else 0,'median_family_fit':statistics.median(fits) if fits else 0,'mean_leave_one_family_out':statistics.mean(loo) if loo else 0,'mean_fold_gain':statistics.mean(gains) if gains else 0,'entries_using_fold':sum(e['fold_family_count']>0 for e in entries)},'boundary':'Source-traced Man Grid geometry is used directly. PHOIBLE supplies an experimental phonetic overlay because the manuscript cells are unlabeled; these results test that explicit model, not a claim about the manuscript author’s intended phonetic labels.'}
    OUT.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    OUTDICT.write_text(json.dumps({'version':1,'title':'Candidate original-language dictionary — source-traced Man Grid 20-shard reconstruction','method':summary,'entries':entries},ensure_ascii=False,indent=2),encoding='utf-8')
    OUTMD.write_text('\n'.join(['# Source-traced Man Grid all-language reconstruction','',f"Dictionary entries: **{len(entries):,}**",f"Raw Wiktionary entries scanned: **{manifest['scan'].get('dictionary_entries',0):,}**",f"Languages encountered: **{manifest['scan'].get('languages',0):,}**",f"Mean family fit: **{summary['metrics']['mean_family_fit']:.6f}**",f"Mean leave-one-family-out fit: **{summary['metrics']['mean_leave_one_family_out']:.6f}**",'', 'No 4x4/16-state or 16x16 transition representation is used.']),encoding='utf-8')
    print(json.dumps({'phase':'merge','entries':len(entries),'metrics':summary['metrics'],'historical':summary['historical_identity_or_fold_audit']},indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
