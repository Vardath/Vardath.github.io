#!/usr/bin/env python3
"""20-way stability test: reconstructed original language vs attested languages."""
from __future__ import annotations
import argparse,json,math,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/original-language-nearest-current-shards'; OUT=ROOT/'data/original-language-nearest-current.json'; N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]

def profile(paths):
 c=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]): c[CELLS.index(a)*16+CELLS.index(b)]+=1
 s=sum(c); return [x/s for x in c] if s else c

def norm(v):
 s=sum(v); return [x/s for x in v] if s else [0.0]*256

def cosine(a,b):
 d=sum(x*y for x,y in zip(a,b)); aa=sum(x*x for x in a); bb=sum(y*y for y in b); return d/math.sqrt(aa*bb) if aa and bb else 0

def jsd(a,b):
 m=[(x+y)/2 for x,y in zip(a,b)]
 def kl(x,y): return sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q)
 return .5*kl(a,m)+.5*kl(b,m)

def overlap(a,b,k=32):
 A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]); B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k]); return len(A&B)/k

def languages():
 b=json.loads(BENCH.read_text(encoding='utf-8')); out=[]
 for r in b['languages']:
  v=norm(list(map(float,r['sample_counts'])))
  out.append((r,v))
 return out

def shard(i):
 d=json.loads(DICT.read_text(encoding='utf-8'))['entries']; chosen=[e for j,e in enumerate(d) if j%N==i]; p=profile([e['path'] for e in chosen]); scores=[]
 for r,q in languages():
  co=cosine(p,q); jd=jsd(p,q); ov=overlap(p,q); score=.55*co+.30*(1-min(1,jd))+.15*ov
  scores.append({'iso':r['iso'],'name':r['name'],'family':r.get('family',''),'cosine':co,'jsd':jd,'top32_overlap':ov,'score':score})
 scores.sort(key=lambda x:x['score'],reverse=True); OUTDIR.mkdir(parents=True,exist_ok=True); (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'entries':len(chosen),'ranking':scores},ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'shard':i,'entries':len(chosen),'winner':scores[0]}))

def merge():
 by=defaultdict(list); meta={}; total=0
 for i in range(N):
  x=json.loads((OUTDIR/f'shard-{i:02d}.json').read_text(encoding='utf-8')); total+=x['entries']
  for rank,r in enumerate(x['ranking'],1): by[r['iso']].append((rank,r)); meta[r['iso']]=r
 final=[]
 for iso,xs in by.items():
  ranks=[x[0] for x in xs]; ss=[x[1]['score'] for x in xs]; r=meta[iso]
  final.append({'iso':iso,'name':r['name'],'family':r['family'],'mean_score':statistics.mean(ss),'score_sd':statistics.pstdev(ss),'mean_rank':statistics.mean(ranks),'median_rank':statistics.median(ranks),'top1_shards':sum(z==1 for z in ranks),'top5_shards':sum(z<=5 for z in ranks),'top10_shards':sum(z<=10 for z in ranks)})
 final.sort(key=lambda x:(x['mean_rank'],-x['mean_score'],x['score_sd'])); OUT.write_text(json.dumps({'version':2,'test':'20-shard reconstructed-original-language nearest attested language','dictionary_entries':total,'shards':N,'ranking':final,'interpretation':'Nearest phonetic/gate-profile proxy only; similarity does not establish descent or historical identity.'},ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'winner':final[0],'languages':len(final)}))

def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); s=sp.add_parser('shard'); s.add_argument('--id',type=int,required=True); sp.add_parser('merge'); a=ap.parse_args(); shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__': main()
