#!/usr/bin/env python3
from __future__ import annotations

import csv, io, itertools, json, math, os, random, statistics, urllib.request
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / 'data/phonetic-benchmark-summary.json'
OUT = ROOT / 'data/phonetic-hierarchical-reconstruction.json'
OUTMD = ROOT / 'data/phonetic-hierarchical-reconstruction.md'
OUTDICT = ROOT / 'data/phonetic-original-language-dictionary.json'
CACHE = ROOT / '.cache' / 'asjp-v21'
CACHE.mkdir(parents=True, exist_ok=True)

ASJP_TAG = 'v21'
ASJP_BASE = f'https://raw.githubusercontent.com/lexibank/asjp/{ASJP_TAG}/cldf/'
ASJP_FILES = ('languages.csv','parameters.csv','forms.csv')
RNG = random.Random(137)

CELLS = ['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4']
PHONE = {'A1':'i','A2':'a','A3':'u','A4':'ɑ','B1':'m','B2':'n','B3':'ŋ','B4':'r','C1':'f','C2':'s','C3':'x','C4':'h','D1':'p','D2':'t','D3':'k','D4':'ʔ'}
BASE = [
 ('identity',False,False,False),('reverse',False,False,True),('place',True,False,False),
 ('reverse+place',True,False,True),('manner',False,True,False),('reverse+manner',False,True,True),
 ('place+manner',True,True,False),('reverse+place+manner',True,True,True)
]
CLASSES = [x[0] for x in BASE] + ['metathesis','acrophonic','clipblend','resegmentation']
BASE_COST = {'identity':0.0,'metathesis':.008,'resegmentation':.012,'clipblend':.025,'acrophonic':.035,
             'reverse':.02,'place':.02,'manner':.02,'reverse+place':.03,'reverse+manner':.03,
             'place+manner':.03,'reverse+place+manner':.04}

HISTORICAL_SEEDS = [
 ('Ancient Greek (to 1453)','Modern Greek (1453-)'),
 ('Old English (ca. 450-1100)','Middle English (1100-1500)'),
 ('Middle English (1100-1500)','English'),
 ('Old Spanish','Spanish'),('Old High German (ca. 750-1050)','German'),
 ('Middle Dutch (ca. 1050-1350)','Dutch'),('Old Russian','Russian'),
 ('Old French (842-ca. 1400)','French'),('Old Irish (to 900)','Middle Irish (900-1200)'),
 ('Middle Irish (900-1200)','Irish')
]


def q(x,n=5): return round(float(x),n)

def fetch(url, path):
    if path.exists() and path.stat().st_size > 1000: return path
    print('download',url,flush=True)
    req=urllib.request.Request(url,headers={'User-Agent':'Vardath-phonetic-research/2.0'})
    with urllib.request.urlopen(req,timeout=180) as r, path.open('wb') as w:
        while True:
            b=r.read(1024*1024)
            if not b: break
            w.write(b)
    return path

def get(row,*names):
    for n in names:
        v=row.get(n)
        if v not in (None,''): return str(v)
    return ''

def normtok(t):
    return t.strip().strip('/[](){}').replace('ˈ','').replace('ˌ','').replace('ː','').replace(':','')

def token_cell(tok):
    t=normtok(tok)
    if not t: return None
    # ASJP/CLTS forms are broad phonetic tokens. The mapping intentionally stays at the same
    # coarse 4x4 resolution as the public bridge, rather than pretending to recover fine IPA.
    x=t.lower()
    if any(c in x for c in 'ieyɪɨɘeɛæ'): return 'A1'
    if any(c in x for c in 'aäɐ'): return 'A2'
    if any(c in x for c in 'uoʊɯʉ'): return 'A3'
    if any(c in x for c in 'ɑɔɒ'): return 'A4'
    if any(c in x for c in 'mwɱ'): return 'B1'
    if any(c in x for c in 'nrlɾɹɬ'): return 'B2'
    if any(c in x for c in 'ŋɲjɰ'): return 'B3'
    if any(c in x for c in 'fvwɸβ'): return 'C1'
    if any(c in x for c in 'sšzʃʒθðcçɕʑ'): return 'C2'
    if any(c in x for c in 'xɣχʁ'): return 'C3'
    if any(c in x for c in 'hħʕ'): return 'C4'
    if any(c in x for c in 'pbɓ'): return 'D1'
    if any(c in x for c in 'tdṭḍʈɖtsdz'): return 'D2'
    if any(c in x for c in 'kgqɢɟ'): return 'D3'
    if 'ʔ' in x or x in ('7','?'): return 'D4'
    return None

def path_from_segments(s):
    if not s: return ()
    # CLDF list-valued fields are normally space-separated. Fall back to characters for compact ASJP strings.
    toks=s.split() if ' ' in s.strip() else list(s.strip())
    out=[]
    for t in toks:
        c=token_cell(t)
        if c and (not out or out[-1] != c): out.append(c)
    return tuple(out)

def feat(c): return ('ABCD'.index(c[0]), int(c[1])-1)

@lru_cache(maxsize=2_000_000)
def sim(a,b):
    n,m=len(a),len(b)
    if not n or not m: return 0.0
    dp=list(range(m+1))
    for i in range(1,n+1):
        nd=[i]+[0]*m
        ra,ca=feat(a[i-1])
        for j in range(1,m+1):
            rb,cb=feat(b[j-1])
            sub=0.0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6.0
            nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+sub)
        dp=nd
    return max(0.0,1.0-dp[m]/max(n,m))

def base_transform(p,pl,ma,rv):
    cm=[2,1,0,3] if pl else [0,1,2,3]; rm=[0,3,2,1] if ma else [0,1,2,3]
    qv=tuple('ABCD'[rm['ABCD'.index(c[0])]]+str(cm[int(c[1])-1]+1) for c in p)
    return qv[::-1] if rv else qv

@lru_cache(maxsize=1_000_000)
def variants(cls,p):
    p=tuple(p); n=len(p); out=[]
    for nm,pl,ma,rv in BASE:
        if cls==nm: return (base_transform(p,pl,ma,rv),)
    if cls=='metathesis':
        for i in range(n-1):
            qv=list(p);qv[i],qv[i+1]=qv[i+1],qv[i];out.append(tuple(qv))
    elif cls=='resegmentation':
        for k in range(1,n): out.append(p[k:]+p[:k])
    elif cls=='clipblend':
        for k in range(2,n): out += [p[:k],p[n-k:]]
        for l in range(1,n):
            for r in range(1,n-l+1):
                qv=p[:l]+p[n-r:]
                if 2<=len(qv)<n: out.append(qv)
    elif cls=='acrophonic':
        for k in range(2,min(4,n)+1):
            for cuts in itertools.combinations(range(1,n),k-1): out.append(tuple(p[i] for i in (0,)+cuts))
    z=[];seen=set()
    for x in out or [p]:
        if x and x not in seen: seen.add(x);z.append(x)
    return tuple(z)

def pathvec(p):
    v=np.zeros(272,dtype=np.float32)
    for c in p: v[CELLS.index(c)] += 1
    for a,b in zip(p,p[1:]): v[16+CELLS.index(a)*16+CELLS.index(b)] += 1
    n=np.linalg.norm(v)
    return v/n if n else v


def historical_audit(bench):
    langs=bench['languages']; names=[x['name'] for x in langs]; fam=[x.get('family','Unclassified') for x in langs]
    P=np.array([x['sample_counts'] for x in langs],dtype=float)
    P=P/np.where(P.sum(1,keepdims=True)>0,P.sum(1,keepdims=True),1)
    def unit(x):
        n=np.linalg.norm(x);return x/(n or 1)
    U=np.array([unit(x) for x in P])
    smaps=[]
    for nm,pl,ma,rv in BASE:
        cm=[2,1,0,3] if pl else [0,1,2,3];rm=[0,3,2,1] if ma else [0,1,2,3]
        idx=[]
        for a in range(16):
            for b in range(16):
                aa=rm[a//4]*4+cm[a%4];bb=rm[b//4]*4+cm[b%4]
                if rv: aa,bb=bb,aa
                idx.append(aa*16+bb)
        smaps.append(np.array(idx,dtype=int))
    nameix={n:i for i,n in enumerate(names)}; audits=[]; opcount=Counter()
    for older,newer in HISTORICAL_SEEDS:
        if older not in nameix or newer not in nameix: continue
        i,j=nameix[older],nameix[newer]
        scores=[]
        for oi,(nm,*_) in enumerate(BASE):
            t=np.zeros(256);t[smaps[oi]]=P[i]; scores.append(float(np.dot(unit(t),U[j])))
        oi=int(np.argmax(scores));best=scores[oi];op=BASE[oi][0];opcount[op]+=1
        candidates=[k for k,f in enumerate(fam) if f==fam[j] and k!=j]
        ranked=[]
        for k in candidates:
            bs=0.0
            for mi in smaps:
                t=np.zeros(256);t[mi]=P[k];bs=max(bs,float(np.dot(unit(t),U[j])))
            ranked.append((bs,k))
        ranked.sort(reverse=True); rank=1+next((r for r,(_,k) in enumerate(ranked) if k==i),len(ranked))
        best_alt=ranked[0][0] if ranked else 0.0
        audits.append({'older':older,'newer':newer,'family':fam[j],'identity_similarity':q(float(np.dot(U[i],U[j]))),
                       'best_similarity':q(best),'best_operator':op,'accepted_predecessor_rank_within_family':rank,
                       'same_family_candidates':len(ranked),'best_same_family_similarity':q(best_alt),
                       'accepted_minus_best_margin':q(best-best_alt),
                       'interpretation':'supports accepted chain strongly' if rank<=3 else ('compatible but non-unique' if rank<=10 else 'phonetic profile alone does not strongly select accepted chain')})
    total=sum(opcount.values())
    prior={c:(opcount[c]+1)/(total+len(CLASSES)) for c in CLASSES}
    return audits,prior


def load_asjp():
    files={n:fetch(ASJP_BASE+n,CACHE/n) for n in ASJP_FILES}
    with files['parameters.csv'].open(encoding='utf-8-sig',newline='') as f:
        params={get(r,'ID','id'):get(r,'Name','name','Concepticon_Gloss') for r in csv.DictReader(f)}
    langs={}
    with files['languages.csv'].open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            lid=get(r,'ID','id');
            if not lid: continue
            langs[lid]={'id':lid,'name':get(r,'Name','name'),'glottocode':get(r,'Glottocode','glottocode'),
                        'iso':get(r,'ISO639P3code','ISO639P3','iso'),
                        'family':get(r,'Glottolog_Family','Family','family','Classification') or 'Unclassified'}
    by=defaultdict(Counter); mapped=raw=0
    with files['forms.csv'].open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            lid=get(r,'Language_ID','languageReference','Language'); pid=get(r,'Parameter_ID','parameterReference','Parameter')
            if lid not in langs or pid not in params: continue
            seg=get(r,'Segments','segments') or get(r,'Form','form','Value')
            p=path_from_segments(seg);raw+=1
            if len(p)<2: continue
            mapped+=1; by[(params[pid],langs[lid]['family'])][p]+=1
    return langs,params,by,raw,mapped

def medoid(counter,limit=14):
    items=counter.most_common(limit)
    if not items:return None
    best=None
    for p,w in items:
        sw=sum(sim(p,q)*v for q,v in items)/sum(v for _,v in items)
        key=(sw,w,-len(p),p)
        if best is None or key>best[0]: best=(key,p,sw)
    return best[1],best[2]

@lru_cache(maxsize=1_000_000)
def bestfit(cand,target,prior_key):
    prior=dict(prior_key)
    best=(-1.0,'identity')
    for cls in CLASSES:
        s=max(sim(v,target) for v in variants(cls,cand))-BASE_COST[cls] + .006*math.log(max(prior.get(cls,1e-6),1e-6))
        if s>best[0]: best=(s,cls)
    return best

def reconstruct_concept(family_paths,prior):
    items=list(family_paths.items())
    reps=[p for _,p in items]
    centroid=np.mean(np.array([pathvec(p) for p in reps]),axis=0); cn=np.linalg.norm(centroid) or 1
    freq=Counter(reps)
    seeds=[p for p,_ in freq.most_common(32)]
    pool=[];seen=set()
    for p in seeds:
        for cls in ('identity','metathesis','resegmentation','clipblend','acrophonic'):
            for v in variants(cls,p):
                if 2<=len(v)<=10 and v not in seen:seen.add(v);pool.append(v)
    # cheap geometric shortlist, then exact operator-aware scoring over all independent families
    ranked=sorted(pool,key=lambda p:float(np.dot(pathvec(p),centroid)/cn)-.004*abs(len(p)-statistics.median(map(len,reps))),reverse=True)[:36]
    pk=tuple(sorted(prior.items())); scores=[]
    for c in ranked:
        fs=[];ops=[]
        for t in reps:
            s,op=bestfit(c,t,pk);fs.append(s);ops.append(op)
        raw=statistics.mean(fs); score=raw-.012*abs(len(c)-statistics.median(map(len,reps)))
        scores.append((score,raw,c,ops,fs))
    scores.sort(reverse=True,key=lambda x:(x[0],x[1],-len(x[2]),x[2]));best=scores[0]
    # Bootstrap the already exact shortlist: measures whether family resampling changes the preferred candidate.
    wins=0; boot=24
    if len(reps)>=8:
        for _ in range(boot):
            ix=[RNG.randrange(len(reps)) for __ in reps]
            b=max(scores,key=lambda z:sum(z[4][i] for i in ix)/len(ix))
            wins += sim(b[2],best[2])>=.85
    else:wins=boot
    return best, wins/boot

def main():
    bench=json.loads(BENCH.read_text(encoding='utf-8'))
    audits,prior=historical_audit(bench)
    print('historical chains',len(audits),flush=True)
    langs,params,by,raw,mapped=load_asjp()
    print('ASJP varieties',len(langs),'concepts',len(params),'forms',raw,'mapped',mapped,flush=True)
    fams=sorted({x['family'] for x in langs.values() if x['family']!='Unclassified'})
    concepts=defaultdict(dict); medoid_fit=defaultdict(dict)
    for (concept,fam),cnt in by.items():
        if fam=='Unclassified':continue
        m=medoid(cnt)
        if m: concepts[concept][fam]=m[0];medoid_fit[concept][fam]=m[1]
    rootg=set()
    try:
        r=json.loads((ROOT/'data/phonetic-proto-reconstruction.json').read_text(encoding='utf-8'))
        rootg={g['gate'] for g in (r.get('refined_roots',{}).get('family_balanced',{}).get('top_gates') or r.get('latent_root',{}).get('top_gates') or [])[:64]}
    except Exception:pass
    entries=[]
    for ci,(concept,fpaths) in enumerate(sorted(concepts.items()),1):
        if len(fpaths)<8: continue
        best,bstab=reconstruct_concept(fpaths,prior);score,fit,cand,ops,fs=best
        gs=[a+'→'+b for a,b in zip(cand,cand[1:])];hits=[g for g in gs if g in rootg]
        ev=[]
        for (fam,p),op,sc in sorted(zip(fpaths.items(),ops,fs),key=lambda z:-z[2])[:24]:
            ev.append({'family':fam,'path':list(p),'representative':'/'+''.join(PHONE[x] for x in p)+'/','best_from_candidate_operator':op,'candidate_fit':q(sc),'within_family_medoid_fit':q(medoid_fit[concept][fam])})
        coverage=len(fpaths)/max(1,len(fams)); conf=.45*fit+.30*bstab+.25*min(1,coverage*2.5)
        entries.append({'meaning':concept,'form':''.join(PHONE[x] for x in cand),'ipa':'/'+''.join(PHONE[x] for x in cand)+'/',
                        'path':list(cand),'families':len(fpaths),'fit':q(fit),'loo_stability':q(bstab),'confidence':q(conf),
                        'family_coverage':q(coverage),'root_gate_overlap':q(len(hits)/max(1,len(gs))),'root_gate_hits':hits,
                        'evidence':ev,'method':'ASJP all-variety -> family medoid -> operator-aware deep medoid'})
        if ci%10==0:print('concept',ci,'entries',len(entries),flush=True)
    entries.sort(key=lambda x:(-x['confidence'],-x['families'],x['meaning']))
    result={
      'version':3,'title':'Hierarchical original-language reconstruction experiment',
      'research_boundary':'This is a candidate latent reconstruction from broad phonetic/semantic data. A strong fit can challenge or support a phonetic historical chain, but cannot by itself overturn documentary chronology, morphology, borrowing evidence, archaeology, or established comparative sound laws.',
      'sources':{'ASJP':'lexibank/asjp v21','ASJP_varieties':len(langs),'ASJP_concepts':len(params),'ASJP_forms':raw,'mapped_forms':mapped,
                 'WikiPron_PHOBLE_benchmark':str(BENCH.relative_to(ROOT)),'benchmark_languages':len(bench['languages'])},
      'historical_regression_audit':{'known_chain_links':audits,'learned_reverse_operator_prior':prior,
          'note':'Accepted chains are treated as hypotheses to audit. Rank asks whether the accepted older stage is selected by the bridge among same-family alternatives; poor rank is a flag for deeper lexical investigation, not automatic proof the historical chain is wrong.'},
      'dictionary_summary':{'entries':len(entries),'mean_confidence':q(statistics.mean([x['confidence'] for x in entries]) if entries else 0),
                            'mean_families':q(statistics.mean([x['families'] for x in entries]) if entries else 0)},
      'entries':entries
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # Keep the public dictionary endpoint compatible with the existing phonetics-page UI.
    pub={'version':3,'title':'Candidate original-language dictionary','method':{'source':'ASJP v21 + existing WikiPron/PHOIBLE bridge + audited historical regression prior','concept_inventory':len(params),'minimum_independent_families':8,'research_boundary':result['research_boundary']},
         'summary':{'entries':len(entries),'five_family_entries':sum(x['families']>=5 for x in entries),'four_or_more':sum(x['families']>=4 for x in entries),'mean_confidence':result['dictionary_summary']['mean_confidence']},'entries':entries}
    OUTDICT.write_text(json.dumps(pub,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Hierarchical original-language reconstruction','',result['research_boundary'],'',f"- ASJP varieties: {len(langs):,}",f"- ASJP source forms: {raw:,}",f"- mapped forms: {mapped:,}",f"- historical chain links audited: {len(audits)}",f"- reconstructed dictionary entries: {len(entries)}",'', '## Historical regression audit','']
    for a in audits: lines.append(f"- {a['older']} → {a['newer']}: rank {a['accepted_predecessor_rank_within_family']}/{a['same_family_candidates']}, best operator {a['best_operator']}, {a['interpretation']}")
    lines += ['', '## Candidate dictionary','']
    for e in entries: lines.append(f"- **{e['meaning']}** {e['ipa']} — {e['families']} families, fit {e['fit']:.3f}, stability {e['loo_stability']:.3f}, confidence {e['confidence']:.3f}")
    OUTMD.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'historical_links':len(audits),'asjp_varieties':len(langs),'asjp_forms':raw,'mapped_forms':mapped,'dictionary_entries':len(entries),'mean_confidence':result['dictionary_summary']['mean_confidence']},indent=2),flush=True)

if __name__=='__main__': main()
