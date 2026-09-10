#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'; BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/mirror-man-rome-origin-shards'; OUT=ROOT/'data/mirror-man-rome-origin.json'; N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}
# Rome/Vatican is operationalised as the attested Latin profile. Modern Rome is Italian; both are reported.
SOURCES=['lat','ita','oci','grc','sqi','ind','tur']

def norm(v):
 s=sum(v); return [x/s for x in v] if s else [0.0]*256

def cosine(a,b):
 d=sum(x*y for x,y in zip(a,b)); aa=sum(x*x for x in a); bb=sum(y*y for y in b)
 return d/math.sqrt(aa*bb) if aa and bb else 0.0

def jsd(a,b):
 m=[(x+y)/2 for x,y in zip(a,b)]
 def kl(x,y): return sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q)
 return .5*kl(a,m)+.5*kl(b,m)

def score(a,b): return .7*cosine(a,b)+.3*(1-min(1,jsd(a,b)))
def rc(i): return divmod(i,16)
def idx(r,c): return r*16+c
# Predeclared Mirror-Man operators on the 16x16 transition grid: row/column mirrors,
# transpose, 180 rotation, and their compositions. No target-specific fitted parameters.
def op_index(i,op):
 a,b=rc(i); ar,ac=divmod(a,4); br,bc=divmod(b,4)
 def cell(r,c): return r*4+c
 if op=='id': na,nb=a,b
 elif op=='row_mirror': na,nb=cell(3-ar,ac),cell(3-br,bc)
 elif op=='col_mirror': na,nb=cell(ar,3-ac),cell(br,3-bc)
 elif op=='both_mirror': na,nb=cell(3-ar,3-ac),cell(3-br,3-bc)
 elif op=='transpose': na,nb=b,a
 elif op=='transpose_row': na,nb=cell(3-br,bc),cell(3-ar,ac)
 elif op=='transpose_col': na,nb=cell(br,3-bc),cell(ar,3-ac)
 elif op=='transpose_both': na,nb=cell(3-br,3-bc),cell(3-ar,3-ac)
 return idx(na,nb)
OPS=['id','row_mirror','col_mirror','both_mirror','transpose','transpose_row','transpose_col','transpose_both']
def transform(v,op):
 z=[0.0]*256
 for i,x in enumerate(v): z[op_index(i,op)]+=x
 return z

def loadlangs():
 b=json.loads(BENCH.read_text(encoding='utf-8'))
 return {r['iso']:{'iso':r['iso'],'name':r['name'],'family':r.get('family',''),'p':norm(list(map(float,r['sample_counts'])))} for r in b['languages']}
def profile(paths):
 c=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]):
   if a in CELLS and b in CELLS:c[CELLS.index(a)*16+CELLS.index(b)]+=1
 return norm(c)
def best_from(source,target):
 vals=[(score(transform(source,op),target),op) for op in OPS]; return max(vals)
def shard(i):
 entries=json.loads(DICT.read_text(encoding='utf-8'))['entries']; chosen=[e for j,e in enumerate(entries) if j%N==i]
 root=profile([e['path'] for e in chosen]); langs=loadlangs(); rows=[]
 for iso,s in langs.items():
  # Exclude the source itself. Test whether one fixed Mirror-Man transform of source predicts every target profile.
  vals=[]
  for tiso,t in langs.items():
   if tiso==iso: continue
   bs,op=best_from(s['p'],t['p']); vals.append((bs,op,tiso,t['family']))
  nonrom=[x for x in vals if x[2] not in ROMANCE]
  rows.append({'iso':iso,'name':s['name'],'family':s['family'],'all_mean':statistics.mean(x[0] for x in vals),'nonromance_mean':statistics.mean(x[0] for x in nonrom),'operator_counts':dict((o,sum(x[1]==o for x in vals)) for o in OPS),'root_similarity':score(s['p'],root)})
 rows.sort(key=lambda x:x['nonromance_mean'],reverse=True)
 OUTDIR.mkdir(parents=True,exist_ok=True); (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps({'shard':i,'entries':len(chosen),'ranking':rows},indent=2),encoding='utf-8')
 print(json.dumps({'shard':i,'winner':rows[0]['name'],'rome_rank':next(j+1 for j,r in enumerate(rows) if r['iso']=='lat'),'italian_rank':next(j+1 for j,r in enumerate(rows) if r['iso']=='ita')}))
def merge():
 agg=defaultdict(list); meta={}
 for i in range(N):
  x=json.loads((OUTDIR/f'shard-{i:02d}.json').read_text())
  for rank,r in enumerate(x['ranking'],1): agg[r['iso']].append((rank,r)); meta[r['iso']]=r
 rows=[]
 for iso,xs in agg.items():
  rows.append({'iso':iso,'name':meta[iso]['name'],'family':meta[iso]['family'],'mean_rank':statistics.mean(x[0] for x in xs),'median_rank':statistics.median(x[0] for x in xs),'mean_nonromance_prediction':statistics.mean(x[1]['nonromance_mean'] for x in xs),'mean_all_prediction':statistics.mean(x[1]['all_mean'] for x in xs),'mean_root_similarity':statistics.mean(x[1]['root_similarity'] for x in xs),'top1_shards':sum(x[0]==1 for x in xs)})
 rows.sort(key=lambda x:x['mean_rank'])
 latin=next(r for r in rows if r['iso']=='lat'); italian=next(r for r in rows if r['iso']=='ita')
 verdict={'rome_latin_rank':latin['mean_rank'],'rome_latin_nonromance_prediction':latin['mean_nonromance_prediction'],'modern_rome_italian_rank':italian['mean_rank'],'modern_rome_italian_nonromance_prediction':italian['mean_nonromance_prediction'],'winner':rows[0]}
 verdict['supports_unique_rome_source']=latin['mean_rank']<=1.5 and latin['top1_shards']>=16
 result={'version':1,'test':'Mirror-Man Rome-origin falsification test','shards':N,'operators':OPS,'source_definition':'Rome/Vatican source is tested primarily as Latin; Italian is separately reported as modern Rome.','primary_prediction':'If all language profiles are derivative Mirror-Man splits from Rome, Latin should be the best or near-best source for predicting held-out non-Romance languages under the same predeclared operators across independent shards.','ranking':rows,'verdict':verdict,'boundary':'This tests the stated phonetic/grid prediction. It cannot by itself establish geography, chronology, population movement, or Vatican agency.'}
 OUT.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(verdict,indent=2))
def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args(); shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__':main()
