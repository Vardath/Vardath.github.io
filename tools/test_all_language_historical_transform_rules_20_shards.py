#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,hashlib,json,math,os,random,re,sqlite3,statistics,unicodedata,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
import reconstruct_original_language_all_dictionaries as core

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data'/'all-language-transform-rules'
DB=WORK/'prepared.sqlite'
META=WORK/'prepared-meta.json'
OUT=ROOT/'data'/'all-language-historical-transformation-rules.json'
RAW=os.environ.get('WIKTEXTRACT_URL','https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz')
N_SHARDS=20
CV_FOLDS=5
MIN_ROUTE=25
MAX_ROUTE=10000
DEL='__DEL__'
CELLS=tuple(core.CELLS)


def norm(s):
    s=unicodedata.normalize('NFKD',str(s or ''))
    return ''.join(c for c in s if not unicodedata.combining(c)).lower().strip()

def clean(s):
    s=re.sub(r'^\*+','',str(s or '').strip())
    s=re.sub(r'\([^)]*\)','',s)
    s=s.replace('[[','').replace(']]','')
    return re.split(r'[,;/]',s,1)[0].strip()

def path(s):
    z=[]
    for ch in clean(s):
        c=core.token_cell(ch)
        if c and (not z or z[-1]!=c): z.append(c)
    return tuple(z)

def ptxt(p): return ','.join(p)
def pparse(s): return tuple(x for x in str(s or '').split(',') if x)

def h64(*parts):
    b='\x1f'.join(map(str,parts)).encode('utf-8','ignore')
    return int.from_bytes(hashlib.sha256(b).digest()[:8],'big') & ((1<<63)-1)

def concepts(o):
    z=[]
    for g in core.get_glosses(o)[:8]:
        c=core.concept_key(g)
        if c and c not in z: z.append(c)
        if len(z)>=4: break
    return z

def inherited_source(t):
    n=str(t.get('name') or '').lower().strip()
    if n not in {'inh','inh+','inherited'}: return None
    a=t.get('args') or {}
    src=str(a.get('2') or a.get('source') or a.get('from') or '').strip()
    term=str(a.get('tr') or a.get('transliteration') or a.get('3') or a.get('term') or '').strip()
    if not src or not term: return None
    return src,clean(term)

def historical_name(name,code):
    q=(str(name or '')+' '+str(code or '')).lower()
    return any(x in q for x in ('proto-',' proto ','old ','middle ','ancient ','classical ','medieval ','-pro','reconstructed'))

def prepare():
    WORK.mkdir(parents=True,exist_ok=True)
    if DB.exists(): DB.unlink()
    con=sqlite3.connect(DB)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=OFF')
    con.execute('CREATE TABLE pairs(route TEXT, desc TEXT, anc TEXT, meaning TEXT, dp TEXT, ap TEXT, dform TEXT, aform TEXT, h INTEGER, fold INTEGER, PRIMARY KEY(route,meaning,dp,ap))')
    con.execute('CREATE INDEX idx_route ON pairs(route)')
    con.execute('CREATE INDEX idx_route_h ON pairs(route,h)')
    names={}; stats=Counter(); batch=[]
    req=urllib.request.Request(RAW,headers={'User-Agent':'Vardath-all-language-transform/1.0'})
    with urllib.request.urlopen(req) as resp,gzip.GzipFile(fileobj=resp) as gz:
        import io
        f=io.TextIOWrapper(gz,encoding='utf-8',errors='replace')
        for line in f:
            stats['dictionary_entries']+=1
            try:o=json.loads(line)
            except Exception:
                stats['json_errors']+=1; continue
            lc=str(o.get('lang_code') or '').strip()
            if not lc: continue
            if lc not in names and o.get('lang'): names[lc]=str(o.get('lang'))
            dform=clean(o.get('word')); dp=path(dform)
            if len(dp)<2: continue
            cs=concepts(o)
            if not cs: continue
            for t in o.get('etymology_templates') or []:
                q=inherited_source(t)
                if not q: continue
                src,aform=q; ap=path(aform)
                if len(ap)<2 or src==lc: continue
                route=src+'>'+lc
                for meaning in cs:
                    hh=h64(route,meaning,ptxt(dp),ptxt(ap),dform,aform)
                    batch.append((route,lc,src,meaning,ptxt(dp),ptxt(ap),dform,aform,hh,hh%CV_FOLDS))
                    if len(batch)>=5000:
                        con.executemany('INSERT OR IGNORE INTO pairs VALUES(?,?,?,?,?,?,?,?,?,?)',batch); con.commit(); batch=[]
            if stats['dictionary_entries']%1000000==0:
                n=con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0]
                print(json.dumps({'entries':stats['dictionary_entries'],'pairs':n}),flush=True)
    if batch:
        con.executemany('INSERT OR IGNORE INTO pairs VALUES(?,?,?,?,?,?,?,?,?,?)',batch); con.commit()
    total=con.execute('SELECT COUNT(*) FROM pairs').fetchone()[0]
    routes=con.execute('SELECT COUNT(DISTINCT route) FROM pairs').fetchone()[0]
    descs=con.execute('SELECT COUNT(DISTINCT desc) FROM pairs').fetchone()[0]
    ancs=con.execute('SELECT COUNT(DISTINCT anc) FROM pairs').fetchone()[0]
    eligible=con.execute('SELECT COUNT(*) FROM (SELECT route,COUNT(*) n FROM pairs GROUP BY route HAVING n>=?)',(MIN_ROUTE,)).fetchone()[0]
    stats.update({'pairs':total,'routes':routes,'descendant_languages':descs,'ancestor_languages':ancs,'eligible_routes':eligible,'languages_named':len(names)})
    meta={'version':1,'source_audit':dict(stats),'language_names':names,'design':{
        'scope':'Every entry in the complete English Wiktionary Wiktextract stream is scanned. Every explicit inherited ancestor→descendant word relation with a usable meaning and 4×4 gate path is admitted; historical and proto-language codes are not excluded.',
        'route':'One exact ancestor-language-code → descendant-language-code pair.',
        'minimum_route_pairs':MIN_ROUTE,'maximum_pairs_tested_per_route':MAX_ROUTE,'route_shards':N_SHARDS,'cross_validation_folds_per_route':CV_FOLDS,
        'primary_test':'For each language route, learn context-sensitive ancestor→descendant and descendant→ancestor gate transformations on four folds and test reverse reconstruction on the unseen fifth fold.',
        'rule_model':'Context-conditioned substitution/deletion rules plus boundary-conditioned insertions, backed off to cell-level rules. Rules must meet fixed support/confidence thresholds; otherwise identity is preserved.',
        'null':'Learn the same reverse model after deterministically rotating ancestor targets among meanings within the training set.',
        'meaning_control':'Compare the matched historical ancestor with a wrong-meaning ancestor under the full fixed Man-grid operator family.',
        'all_languages_boundary':'Languages without an explicit inherited historical form cannot yield a transformation rule, but they are still scanned; no language or language family is hard-coded into or excluded from the test.',
        'representation':'Historical spellings are mapped through the same fixed 4×4 gate encoder. This measures reproducible structural sound/spelling drift; it is not a claim that every spelling is an exact historical IPA transcription.',
        'no_custom_timeout':True}}
    META.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    con.close()
    print(json.dumps({'phase':'prepare',**dict(stats)},ensure_ascii=False),flush=True)

def cell_cost(a,b):
    ra,ca=core.feat(a); rb,cb=core.feat(b)
    return (abs(ra-rb)+abs(ca-cb))/6

def align(src,tgt):
    a=tuple(src); b=tuple(tgt); n=len(a); m=len(b); gap=.75
    dp=[[0.]*(m+1) for _ in range(n+1)]; bt=[[None]*(m+1) for _ in range(n+1)]
    for i in range(1,n+1): dp[i][0]=i*gap; bt[i][0]='D'
    for j in range(1,m+1): dp[0][j]=j*gap; bt[0][j]='I'
    pref={'M':0,'D':1,'I':2}
    for i in range(1,n+1):
        for j in range(1,m+1):
            opts=[(dp[i-1][j-1]+cell_cost(a[i-1],b[j-1]),'M'),(dp[i-1][j]+gap,'D'),(dp[i][j-1]+gap,'I')]
            dp[i][j],bt[i][j]=min(opts,key=lambda x:(x[0],pref[x[1]]))
    out=[]; i=n; j=m
    while i or j:
        q=bt[i][j]
        if q=='M': out.append((a[i-1],b[j-1])); i-=1; j-=1
        elif q=='D': out.append((a[i-1],None)); i-=1
        else: out.append((None,b[j-1])); j-=1
    return list(reversed(out))

def make_examples(rows,forward=False,shuffle=False):
    rows=sorted(rows,key=lambda r:(r['meaning'],r['h']))
    src=[r['ap'] if forward else r['dp'] for r in rows]
    tgt=[r['dp'] if forward else r['ap'] for r in rows]
    if shuffle and len(tgt)>1: tgt=tgt[1:]+tgt[:1]
    return list(zip(src,tgt))

def learn(rows,forward=False,shuffle=False):
    ctx=defaultdict(Counter); base=defaultdict(Counter); ins=defaultdict(Counter)
    for src,tgt in make_examples(rows,forward,shuffle):
        si=0
        for s,t in align(src,tgt):
            if s is None:
                prev=src[si-1] if si>0 else '^'; nxt=src[si] if si<len(src) else '$'
                if t: ins[(prev,nxt)][t]+=1
            else:
                prev=src[si-1] if si>0 else '^'; nxt=src[si+1] if si+1<len(src) else '$'
                q=t if t is not None else DEL
                ctx[(prev,s,nxt)][q]+=1; base[s][q]+=1; si+=1
    return {'ctx':ctx,'base':base,'ins':ins}

def choice(counter,identity=None,min_support=8,min_conf=.55):
    if not counter: return None,0,0
    sup=sum(counter.values()); mx=max(counter.values()); opts=sorted(k for k,v in counter.items() if v==mx)
    q=identity if identity in opts else opts[0]
    return (q,sup,mx/sup) if sup>=min_support and mx/sup>=min_conf else (None,sup,mx/sup)

def predict(src,model):
    src=tuple(src); out=[]
    for i,c in enumerate(src):
        prev=src[i-1] if i else '^'; nxt=src[i+1] if i+1<len(src) else '$'
        q,_,_=choice(model['ctx'].get((prev,c,nxt)),c,8,.55)
        if q is None: q,_,_=choice(model['base'].get(c),c,10,.60)
        if q is None: q=c
        if q!=DEL and (not out or out[-1]!=q): out.append(q)
        iq,_,_=choice(model['ins'].get((c,nxt)),None,8,.65)
        if iq and iq!=DEL and (not out or out[-1]!=iq): out.append(iq)
    return tuple(out) or src

def ci(vals,seed,reps=1600):
    if not vals:return [None,None]
    rng=random.Random(seed); n=len(vals); arr=[]
    for _ in range(reps): arr.append(sum(vals[rng.randrange(n)] for _ in range(n))/n)
    arr.sort(); return [arr[int(.025*reps)],arr[int(.975*reps)-1]]

def rule_rows(model,limit=24):
    rows=[]
    for (prev,s,nxt),c in model['ctx'].items():
        q,sup,conf=choice(c,s,12,.60)
        if q is None or q==s: continue
        typ='deletion' if q==DEL else 'substitution'
        score=sup*conf
        rows.append({'type':typ,'source':s,'target':None if q==DEL else q,'left':prev,'right':nxt,'support':sup,'confidence':conf,'score':score})
    for (prev,nxt),c in model['ins'].items():
        q,sup,conf=choice(c,None,12,.65)
        if q is None:continue
        rows.append({'type':'insertion','source':None,'target':q,'left':prev,'right':nxt,'support':sup,'confidence':conf,'score':sup*conf})
    rows.sort(key=lambda r:(-r['score'],-r['confidence'],-r['support'],str(r)))
    return rows[:limit]

def read_route(con,route):
    rows=[]
    for desc,anc,meaning,dp,ap,dform,aform,h,fold in con.execute('SELECT desc,anc,meaning,dp,ap,dform,aform,h,fold FROM pairs WHERE route=? ORDER BY h LIMIT ?',(route,MAX_ROUTE)):
        rows.append({'desc':desc,'anc':anc,'meaning':meaning,'dp':pparse(dp),'ap':pparse(ap),'dform':dform,'aform':aform,'h':h,'fold':fold})
    return rows

def test_route(route,rows,seed):
    gains=[]; nullg=[]; flexg=[]; rawv=[]; learnedv=[]; nullv=[]; wins=losses=ties=0; used=0
    op=Counter()
    for f in range(CV_FOLDS):
        train=[r for r in rows if r['fold']!=f]; test=[r for r in rows if r['fold']==f]
        if len(train)<20 or not test: continue
        rev=learn(train,False,False); nul=learn(train,False,True)
        wrong=[r['ap'] for r in sorted(test,key=lambda r:(r['meaning'],r['h']))]
        if len(wrong)>1: wrong=wrong[1:]+wrong[:1]
        elif train: wrong=[train[0]['ap']]
        ordered=sorted(test,key=lambda r:(r['meaning'],r['h']))
        for k,r in enumerate(ordered):
            raw=core.sim(r['dp'],r['ap']); learned=core.sim(predict(r['dp'],rev),r['ap']); nv=core.sim(predict(r['dp'],nul),r['ap'])
            fs,fo=core.bestfit(r['dp'],r['ap']); ws,_=core.bestfit(r['dp'],wrong[k])
            rawv.append(raw); learnedv.append(learned); nullv.append(nv); gains.append(learned-raw); nullg.append(learned-nv); flexg.append(fs-ws); op[fo]+=1; used+=1
            if learned>raw:wins+=1
            elif learned<raw:losses+=1
            else:ties+=1
    if not used:return None
    fwd=learn(rows,True,False)
    gci=ci(gains,seed+1); nci=ci(nullg,seed+2); fci=ci(flexg,seed+3)
    return {'route':route,'ancestor_code':rows[0]['anc'],'descendant_code':rows[0]['desc'],'n_total_available':len(rows),'n_tested':used,
        'raw_similarity':statistics.mean(rawv),'learned_reverse_similarity':statistics.mean(learnedv),'learned_gain':statistics.mean(gains),'learned_gain_bootstrap_95':gci,
        'shuffled_rule_similarity':statistics.mean(nullv),'learned_minus_shuffled':statistics.mean(nullg),'learned_minus_shuffled_bootstrap_95':nci,
        'matched_minus_wrong_meaning_flexible':statistics.mean(flexg),'matched_minus_wrong_bootstrap_95':fci,
        'reverse_wins':wins,'reverse_losses':losses,'reverse_ties':ties,'operator_counts':dict(op),'forward_rules':rule_rows(fwd),
        'positive':bool(used>=20 and gci[0] is not None and gci[0]>0 and nci[0] is not None and nci[0]>0)}

def shard(i):
    meta=json.loads(META.read_text(encoding='utf-8')); con=sqlite3.connect(DB)
    route_counts=list(con.execute('SELECT route,COUNT(*) n FROM pairs GROUP BY route HAVING n>=? ORDER BY route',(MIN_ROUTE,)))
    chosen=[(r,n) for r,n in route_counts if h64(r)%N_SHARDS==i]
    out=[]
    for j,(route,n) in enumerate(chosen):
        rows=read_route(con,route); z=test_route(route,rows,200000+i*10000+j*17)
        if z: out.append(z)
        if (j+1)%25==0: print(json.dumps({'shard':i,'routes_done':j+1,'routes_total':len(chosen)}),flush=True)
    con.close(); p=WORK/f'result-{i:02d}.json'; p.write_text(json.dumps({'shard':i,'routes':out},ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'phase':'shard','shard':i,'routes':len(out),'positive':sum(r['positive'] for r in out)}),flush=True)

def route_boot(routes,key,seed,reps=3000):
    if not routes:return [None,None]
    rng=random.Random(seed); arr=[]; n=len(routes)
    for _ in range(reps):
        sample=[routes[rng.randrange(n)] for _ in range(n)]; den=sum(r['n_tested'] for r in sample)
        arr.append(sum(r[key]*r['n_tested'] for r in sample)/den if den else 0)
    arr.sort(); return [arr[int(.025*reps)],arr[int(.975*reps)-1]]

def merge():
    meta=json.loads(META.read_text(encoding='utf-8')); names=meta['language_names']; routes=[]
    for i in range(N_SHARDS): routes+=json.loads((WORK/f'result-{i:02d}.json').read_text(encoding='utf-8'))['routes']
    routes.sort(key=lambda r:r['route']); tested=sum(r['n_tested'] for r in routes)
    def wm(k): return sum(r[k]*r['n_tested'] for r in routes)/tested if tested else None
    for r in routes:
        r['ancestor_name']=names.get(r['ancestor_code'],r['ancestor_code']); r['descendant_name']=names.get(r['descendant_code'],r['descendant_code'])
        r['historical_ancestor']=historical_name(r['ancestor_name'],r['ancestor_code']); r['historical_descendant']=historical_name(r['descendant_name'],r['descendant_code'])
        for q in r['forward_rules']:
            def lab(c): return c if c in {'^','$',None} else f"{c}({core.PHONE.get(c,c)})"
            q['english']=('delete '+lab(q['source']) if q['type']=='deletion' else ('insert '+lab(q['target']) if q['type']=='insertion' else lab(q['source'])+' → '+lab(q['target'])))+' when between '+lab(q['left'])+' and '+lab(q['right'])
    pos=[r for r in routes if r['positive']]
    ruleagg=defaultdict(lambda:{'routes':0,'support':0,'confidence_sum':0.0,'examples':[]})
    for r in pos:
        seen=set()
        for q in r['forward_rules']:
            sig=(q['type'],q['source'],q['target'],q['left'],q['right'])
            a=ruleagg[sig]; a['support']+=q['support']; a['confidence_sum']+=q['confidence']
            if sig not in seen:a['routes']+=1;seen.add(sig)
            if len(a['examples'])<5:a['examples'].append(r['ancestor_name']+' → '+r['descendant_name'])
    universal=[]
    for sig,a in ruleagg.items():
        typ,src,tgt,left,right=sig
        universal.append({'type':typ,'source':src,'target':tgt,'left':left,'right':right,'routes':a['routes'],'total_support':a['support'],'mean_route_confidence':a['confidence_sum']/max(1,a['routes']),'examples':a['examples']})
    universal.sort(key=lambda x:(-x['routes'],-x['total_support'],-x['mean_route_confidence']))
    anc_hubs=Counter(r['ancestor_name'] for r in routes); desc_hubs=Counter(r['descendant_name'] for r in routes)
    ranked=sorted(routes,key=lambda r:(-r['learned_gain'],-r['learned_minus_shuffled'],-r['n_tested']))
    historical=[r for r in routes if r['historical_ancestor'] or r['historical_descendant']]
    result={'version':1,'test':'All-language historical transformation-rule discovery — complete Wiktextract scan, 20 route shards, 5-fold held-out testing per route',
        'source_audit':meta['source_audit'],'design':meta['design'],'tested_routes':len(routes),'tested_pairs':tested,'positive_routes':len(pos),'positive_route_fraction':len(pos)/len(routes) if routes else 0,
        'historical_or_proto_routes_tested':len(historical),
        'overall':{'raw_similarity':wm('raw_similarity'),'learned_reverse_similarity':wm('learned_reverse_similarity'),'learned_gain':wm('learned_gain'),'learned_gain_route_bootstrap_95':route_boot(routes,'learned_gain',30101),
                   'learned_minus_shuffled':wm('learned_minus_shuffled'),'learned_minus_shuffled_route_bootstrap_95':route_boot(routes,'learned_minus_shuffled',30102),
                   'matched_minus_wrong_meaning_flexible':wm('matched_minus_wrong_meaning_flexible'),'matched_minus_wrong_route_bootstrap_95':route_boot(routes,'matched_minus_wrong_meaning_flexible',30103)},
        'top_reverse_recoverable_routes':ranked[:50],
        'top_historical_or_proto_routes':sorted(historical,key=lambda r:(-r['learned_gain'],-r['n_tested']))[:75],
        'universal_forward_rule_candidates':universal[:75],
        'ancestor_hubs':[{'language':k,'routes':v} for k,v in anc_hubs.most_common(40)],'descendant_hubs':[{'language':k,'routes':v} for k,v in desc_hubs.most_common(40)],
        'all_routes':routes,
        'verdict':{'supports_learnable_historical_transformation_rules_overall':bool(routes and route_boot(routes,'learned_gain',40101)[0]>0 and route_boot(routes,'learned_minus_shuffled',40102)[0]>0),
                   'positive_routes':len(pos),'tested_routes':len(routes),
                   'boundary':'A positive route means recurring historical transformation structure can be learned on unseen inherited word pairs in the fixed 4×4 encoding. It does not by itself prove a particular ultimate ancestor, date, migration, or genealogy beyond the inherited relations used as source evidence.'}}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':'merge','tested_routes':len(routes),'tested_pairs':tested,'positive_routes':len(pos),'overall':result['overall'],'verdict':result['verdict']},ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True); sub.add_parser('prepare'); s=sub.add_parser('shard'); s.add_argument('--id',type=int,required=True); sub.add_parser('merge'); a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
