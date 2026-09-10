#!/usr/bin/env python3
"""Compare the reconstructed original-language dictionary to attested language profiles.

Execution is deliberately 20-way sharded. Each dictionary entry is assigned by
stable index modulo 20, so every shard receives 600 entries when the candidate
dictionary contains 12,000 entries. Each shard builds a 256 directed-gate
profile and compares it with the existing canonical WikiPron benchmark
profiles. Merge aggregates the 20 independent rankings, emphasizing stability
across shards rather than a single aggregate similarity.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
LANGS=ROOT/'data/phonetic-benchmark-languages.csv'
OUTDIR=ROOT/'data/original-language-nearest-current-shards'
OUT=ROOT/'data/original-language-nearest-current.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
GATES=[f'{a}→{b}' for a in CELLS for b in CELLS]
GI={g:i for i,g in enumerate(GATES)}

def profile(paths):
    c=[0.0]*256
    for p in paths:
        for a,b in zip(p,p[1:]): c[GI[f'{a}→{b}']]+=1
    s=sum(c)
    return [x/s for x in c] if s else c

def cosine(a,b):
    dot=sum(x*y for x,y in zip(a,b)); aa=sum(x*x for x in a); bb=sum(y*y for y in b)
    return dot/math.sqrt(aa*bb) if aa and bb else 0.0

def jsd(a,b):
    m=[(x+y)/2 for x,y in zip(a,b)]
    def kl(x,y): return sum(p*math.log(p/q,2) for p,q in zip(x,y) if p>0 and q>0)
    return .5*kl(a,m)+.5*kl(b,m)

def top_overlap(a,b,k=32):
    A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]); B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k])
    return len(A&B)/k

def load_languages():
    rows=[]
    with LANGS.open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            if r.get('canonical')!='True': continue
            # benchmark CSV does not store the 256-vector, only summary fields;
            # derive an attested gate-presence proxy from the benchmark's stable
            # gate data when available in the companion summary.
            rows.append(r)
    summary=json.loads((ROOT/'data/phonetic-benchmark-summary.json').read_text(encoding='utf-8'))
    # Global gate prevalence is not language-specific, so use per-language gate
    # vectors if a gate-profile companion exists. Fail loudly rather than fake it.
    candidates=[ROOT/'data/phonetic-benchmark-language-gates.json',ROOT/'data/phonetic-language-gate-profiles.json']
    gp=next((p for p in candidates if p.exists()),None)
    if gp is None:
        raise RuntimeError('Missing per-language 256-gate profile dataset; generate it from the benchmark before comparison.')
    raw=json.loads(gp.read_text(encoding='utf-8'))
    profiles=raw.get('languages',raw)
    out=[]
    for r in rows:
        keys=[r.get('iso'),r.get('canonical'),r.get('name')]
        x=next((profiles.get(k) for k in keys if k and k in profiles),None)
        if x is None: continue
        if isinstance(x,dict):
            v=[float(x.get(g,0)) for g in GATES]
        else: v=list(map(float,x))
        s=sum(v); v=[z/s for z in v] if s else v
        out.append((r,v))
    return out

def run_shard(i):
    d=json.loads(DICT.read_text(encoding='utf-8'))['entries']
    chosen=[e for j,e in enumerate(d) if j%N==i]
    p=profile([e['path'] for e in chosen])
    langs=load_languages(); scores=[]
    for r,q in langs:
        co=cosine(p,q); jd=jsd(p,q); ov=top_overlap(p,q)
        combined=.55*co+.30*(1-min(1,jd))+.15*ov
        scores.append({'iso':r['iso'],'name':r['name'],'family':r.get('family',''),'cosine':co,'jsd':jd,'top32_overlap':ov,'score':combined})
    scores.sort(key=lambda x:x['score'],reverse=True)
    OUTDIR.mkdir(parents=True,exist_ok=True)
    (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'entries':len(chosen),'ranking':scores},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'shard':i,'entries':len(chosen),'languages':len(scores),'winner':scores[0] if scores else None}))

def merge():
    by=defaultdict(list); meta={}
    for i in range(N):
        x=json.loads((OUTDIR/f'shard-{i:02d}.json').read_text(encoding='utf-8'))
        for rank,r in enumerate(x['ranking'],1):
            by[r['iso']].append((rank,r)); meta[r['iso']]=r
    final=[]
    for iso,xs in by.items():
        ranks=[x[0] for x in xs]; ss=[x[1]['score'] for x in xs]
        r=meta[iso]
        final.append({'iso':iso,'name':r['name'],'family':r['family'],'shards':len(xs),'mean_score':statistics.mean(ss),'score_sd':statistics.pstdev(ss),'mean_rank':statistics.mean(ranks),'median_rank':statistics.median(ranks),'top1_shards':sum(z==1 for z in ranks),'top5_shards':sum(z<=5 for z in ranks),'top10_shards':sum(z<=10 for z in ranks)})
    final.sort(key=lambda x:(x['mean_rank'],-x['mean_score'],x['score_sd']))
    result={'version':1,'test':'20-shard reconstructed-original-language nearest attested language','dictionary_entries':sum(json.loads((OUTDIR/f'shard-{i:02d}.json').read_text())['entries'] for i in range(N)),'shards':N,'ranking':final,'interpretation':'Nearest phonetic/gate-profile proxy only; similarity does not establish descent or historical identity.'}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'winner':final[0] if final else None,'languages':len(final)}))

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); s=sp.add_parser('shard'); s.add_argument('--id',type=int,required=True); sp.add_parser('merge'); a=ap.parse_args()
    run_shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__': main()
