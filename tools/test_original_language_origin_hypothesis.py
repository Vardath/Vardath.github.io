#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,random,statistics
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/original-language-origin-hypothesis-shards'
OUT=ROOT/'data/original-language-origin-hypothesis.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}
FOCAL={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','lat','grc','ang','got'}


def profile(paths):
 c=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]):
   if a in CELLS and b in CELLS:c[CELLS.index(a)*16+CELLS.index(b)]+=1
 s=sum(c);return [x/s for x in c] if s else c

def norm(v):
 s=sum(v);return [x/s for x in v] if s else [0.0]*256

def cosine(a,b):
 d=sum(x*y for x,y in zip(a,b));aa=sum(x*x for x in a);bb=sum(y*y for y in b)
 return d/math.sqrt(aa*bb) if aa and bb else 0.0

def jsd(a,b):
 m=[(x+y)/2 for x,y in zip(a,b)]
 def kl(x,y):return sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q)
 return .5*kl(a,m)+.5*kl(b,m)

def overlap(a,b,k=32):
 A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]);B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k]);return len(A&B)/k

def score(a,b):
 co=cosine(a,b);jd=jsd(a,b);ov=overlap(a,b)
 return .55*co+.30*(1-min(1,jd))+.15*ov,co,jd,ov

def feat(c):return ('ABCD'.index(c[0]),int(c[1])-1)
@lru_cache(maxsize=2_000_000)
def sim(a,b):
 a=list(a);b=list(b);n=len(a);m=len(b)
 if not n or not m:return 0.0
 dp=list(range(m+1))
 for i in range(1,n+1):
  nd=[i]+[0]*m;ra,ca=feat(a[i-1])
  for j in range(1,m+1):
   rb,cb=feat(b[j-1]);sub=0 if a[i-1]==b[j-1] else (abs(ra-rb)+abs(ca-cb))/6
   nd[j]=min(dp[j]+1,nd[j-1]+1,dp[j-1]+sub)
  dp=nd
 return max(0,1-dp[m]/max(n,m))

def medoid(paths):
 if not paths:return ()
 if len(paths)==1:return tuple(paths[0])
 best=None
 for p in paths:
  p=tuple(p);v=statistics.mean(sim(p,tuple(q)) for q in paths)
  key=(v,-len(p),p)
  if best is None or key>best[0]:best=(key,p)
 return best[1]

def languages():
 b=json.loads(BENCH.read_text(encoding='utf-8'));out=[]
 for r in b['languages']:
  out.append((r,norm(list(map(float,r['sample_counts'])))))
 return out

def shard(i):
 entries=json.loads(DICT.read_text(encoding='utf-8'))['entries'];chosen=[e for j,e in enumerate(entries) if j%N==i]
 p=profile([e['path'] for e in chosen]);ranking=[]
 for r,q in languages():
  s,co,jd,ov=score(p,q);ranking.append({'iso':r['iso'],'name':r['name'],'family':r.get('family',''),'score':s,'cosine':co,'jsd':jd,'top32_overlap':ov})
 ranking.sort(key=lambda x:x['score'],reverse=True)
 held=defaultdict(lambda:{'sum':0.0,'n':0})
 for e in chosen:
  ev=[x for x in e.get('evidence',[]) if x.get('family') and x.get('path')]
  fams={x['family']:tuple(x['path']) for x in ev}
  if len(fams)<4:continue
  for fam,target in fams.items():
   others=[p for f,p in fams.items() if f!=fam]
   if len(others)<3:continue
   pred=medoid(others);held[fam]['sum']+=sim(pred,target);held[fam]['n']+=1
 out={'shard':i,'entries':len(chosen),'ranking':ranking,'heldout_family':{f:{'mean_similarity':v['sum']/v['n'],'n':v['n']} for f,v in held.items() if v['n']}}
 OUTDIR.mkdir(parents=True,exist_ok=True);(OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'shard':i,'entries':len(chosen),'winner':ranking[0]['name'],'winner_score':ranking[0]['score'],'heldout_families':len(held)}))

def merge():
 bylang=defaultdict(list);meta={};held=defaultdict(lambda:{'sum':0.0,'n':0});shards=[]
 for i in range(N):
  x=json.loads((OUTDIR/f'shard-{i:02d}.json').read_text(encoding='utf-8'));shards.append(x)
  for rank,r in enumerate(x['ranking'],1):
   bylang[r['iso']].append((rank,r['score']));meta[r['iso']]=r
  for fam,v in x['heldout_family'].items():
   held[fam]['sum']+=v['mean_similarity']*v['n'];held[fam]['n']+=v['n']
 ranking=[]
 for iso,xs in bylang.items():
  ranks=[z[0] for z in xs];ss=[z[1] for z in xs];r=meta[iso]
  ranking.append({'iso':iso,'name':r['name'],'family':r['family'],'mean_score':statistics.mean(ss),'score_sd':statistics.pstdev(ss),'mean_rank':statistics.mean(ranks),'median_rank':statistics.median(ranks),'top1_shards':sum(z==1 for z in ranks),'top5_shards':sum(z<=5 for z in ranks),'top10_shards':sum(z<=10 for z in ranks),'romance_set':iso in ROMANCE})
 ranking.sort(key=lambda x:(x['mean_rank'],-x['mean_score']))
 romans=[r for r in ranking if r['iso'] in ROMANCE];others=[r for r in ranking if r['iso'] not in ROMANCE]
 rom_mean=statistics.mean(r['mean_score'] for r in romans);non_mean=statistics.mean(r['mean_score'] for r in others)
 vals=[r['mean_score'] for r in ranking];k=len(romans);rng=random.Random(137);hits=0;draws=10000
 for _ in range(draws):
  if statistics.mean(rng.sample(vals,k))>=rom_mean:hits+=1
 enrichment={'languages_in_set':k,'romance_mean_score':rom_mean,'non_romance_mean_score':non_mean,'difference':rom_mean-non_mean,'random_same_size_draws':draws,'empirical_p_ge_romance':(hits+1)/(draws+1),'top20_romance_count':sum(r['romance_set'] for r in ranking[:20]),'top50_romance_count':sum(r['romance_set'] for r in ranking[:50])}
 heldrank=[{'family':f,'mean_heldout_similarity':v['sum']/v['n'],'comparisons':v['n']} for f,v in held.items() if v['n']]
 heldrank.sort(key=lambda x:x['mean_heldout_similarity'],reverse=True)
 focal=[r for r in ranking if r['iso'] in FOCAL]
 occ=next((r for r in ranking if r['iso']=='oci'),None);lat=next((r for r in ranking if r['iso']=='lat'),None);osp=next((r for r in ranking if r['iso']=='osp'),None)
 interpretation=[]
 if enrichment['empirical_p_ge_romance']<=.01:interpretation.append('Romance languages are significantly enriched for high similarity under the 20-shard gate-profile test.')
 else:interpretation.append('Romance enrichment is not statistically strong under the same-size random-group control.')
 if occ and lat:
  interpretation.append(f"Occitan ranks {occ['mean_rank']:.2f} on average versus Latin {lat['mean_rank']:.2f}; the reconstruction is therefore more similar to the tested modern Occitan profile than to the tested Latin profile.")
 if osp and occ:interpretation.append(f"Old Spanish mean rank {osp['mean_rank']:.2f} versus Occitan {occ['mean_rank']:.2f}.")
 interpretation.append('This experiment can identify a Romance/Indo-European structural signal but cannot by itself establish that Latin or any Romance language is the historical ancestor of all human languages. The reconstructed dictionary was built from multilingual evidence, so the held-out-family lane is included as a circularity check.')
 result={'version':1,'test':'20-shard origin-hypothesis stress test','dictionary_entries':sum(x['entries'] for x in shards),'shards':N,'design':{'lane_1':'Repeat independent 600-entry gate-profile comparisons against all 348 canonical WikiPron language profiles.','lane_2':'Test whether a predeclared Romance set is enriched versus 10,000 random same-size language sets.','lane_3':'For each reconstructed meaning, hold one broad family out of its evidence, predict a medoid path from the remaining families, and score the held-out family. This prevents the target family from directly defining its own prediction.','primary_boundary':'Similarity is structural evidence, not proof of genealogical origin.'},'ranking':ranking,'romance_enrichment':enrichment,'heldout_family_ranking':heldrank,'focal_languages':focal,'interpretation':interpretation}
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'winner':ranking[0],'romance_enrichment':enrichment,'heldout_top':heldrank[:5],'interpretation':interpretation},ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
 shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__':main()
