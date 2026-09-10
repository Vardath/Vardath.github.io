#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/reverse-family-convergence-shards'
OUT=ROOT/'data/reverse-family-convergence.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
OPS=['id','row_mirror','col_mirror','both_mirror','transpose','transpose_row','transpose_col','transpose_both']
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}
FOCAL={'oci','ind','lat','ita','grc','sqi','tur','spa','por','ron'}

def norm(v):
 s=sum(v); return [x/s for x in v] if s else [0.0]*256

def cosine(a,b):
 d=sum(x*y for x,y in zip(a,b)); aa=sum(x*x for x in a); bb=sum(y*y for y in b)
 return d/math.sqrt(aa*bb) if aa and bb else 0.0

def jsd(a,b):
 m=[(x+y)/2 for x,y in zip(a,b)]
 def kl(x,y): return sum(p*math.log2(p/q) for p,q in zip(x,y) if p and q)
 return .5*kl(a,m)+.5*kl(b,m)

def overlap(a,b,k=32):
 A=set(sorted(range(256),key=lambda i:a[i],reverse=True)[:k]); B=set(sorted(range(256),key=lambda i:b[i],reverse=True)[:k])
 return len(A&B)/k

def score(a,b): return .55*cosine(a,b)+.30*(1-min(1,jsd(a,b)))+.15*overlap(a,b)

def idxop(i,op):
 a,b=divmod(i,16); ar,ac=divmod(a,4); br,bc=divmod(b,4)
 cell=lambda r,c:r*4+c
 if op=='id': na,nb=a,b
 elif op=='row_mirror': na,nb=cell(3-ar,ac),cell(3-br,bc)
 elif op=='col_mirror': na,nb=cell(ar,3-ac),cell(br,3-bc)
 elif op=='both_mirror': na,nb=cell(3-ar,3-ac),cell(3-br,3-bc)
 elif op=='transpose': na,nb=b,a
 elif op=='transpose_row': na,nb=cell(3-br,bc),cell(3-ar,ac)
 elif op=='transpose_col': na,nb=cell(br,3-bc),cell(ar,3-ac)
 elif op=='transpose_both': na,nb=cell(3-br,3-bc),cell(3-ar,3-ac)
 return na*16+nb

def transform(v,op):
 z=[0.0]*256
 for i,x in enumerate(v): z[idxop(i,op)]+=x
 return z

def best_to_source(target,source):
 vals=[(score(transform(target,o),source),o) for o in OPS]
 return max(vals,key=lambda x:x[0])

def profile(paths):
 c=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]):
   if a in CELLS and b in CELLS: c[CELLS.index(a)*16+CELLS.index(b)]+=1
 return norm(c)

def langs():
 b=json.loads(BENCH.read_text(encoding='utf-8'))
 return {r['iso']:{'iso':r['iso'],'name':r['name'],'family':r.get('family','Unclassified') or 'Unclassified','p':norm(list(map(float,r['sample_counts'])))} for r in b['languages']}

def shard(i):
 entries=json.loads(DICT.read_text(encoding='utf-8'))['entries']
 chosen=[e for j,e in enumerate(entries) if j%N==i]
 root=profile([e['path'] for e in chosen])
 L=langs()
 sources={'root':root}
 for iso in ('oci','ind','lat'):
  if iso in L: sources[iso]=L[iso]['p']
 rows=[]
 for iso,t in L.items():
  if iso in sources: continue
  srow={}
  for sk,sp in sources.items():
   bs,op=best_to_source(t['p'],sp)
   direct=score(t['p'],sp)
   srow[sk]={'score':bs,'operator':op,'direct':direct,'gain':bs-direct}
  rows.append({'iso':iso,'name':t['name'],'family':t['family'],'scores':srow})
 fam=defaultdict(lambda:defaultdict(list))
 for r in rows:
  for sk,v in r['scores'].items(): fam[r['family']][sk].append(v['score'])
 famout={f:{sk:statistics.mean(v) for sk,v in d.items()} for f,d in fam.items()}
 out={'shard':i,'entries':len(chosen),'families':famout,'targets':rows}
 OUTDIR.mkdir(parents=True,exist_ok=True)
 (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 print(json.dumps({'shard':i,'entries':len(chosen),'families':len(famout)}))

def merge():
 shards=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)]
 fam=defaultdict(lambda:defaultdict(list)); targ=defaultdict(lambda:defaultdict(list)); opc=defaultdict(lambda:defaultdict(int)); gains=defaultdict(list)
 for x in shards:
  for f,d in x['families'].items():
   for sk,v in d.items(): fam[f][sk].append(v)
  for r in x['targets']:
   for sk,v in r['scores'].items():
    targ[r['iso']][sk].append(v['score']); opc[sk][v['operator']]+=1; gains[sk].append(v['gain'])
 famrows=[]
 for f,d in fam.items():
  m={k:statistics.mean(v) for k,v in d.items()}; winner=max(m,key=m.get)
  famrows.append({'family':f,'winner':winner,'scores':m,'root_minus_ind':m.get('root',0)-m.get('ind',0),'root_minus_oci':m.get('root',0)-m.get('oci',0)})
 famrows.sort(key=lambda r:r['family'])
 L=langs(); trows=[]
 for iso,d in targ.items():
  m={k:statistics.mean(v) for k,v in d.items()}; winner=max(m,key=m.get)
  trows.append({'iso':iso,'name':L[iso]['name'],'family':L[iso]['family'],'winner':winner,'scores':m})
 nonrom=[r for r in trows if r['iso'] not in ROMANCE]
 means={sk:statistics.mean([r['scores'][sk] for r in nonrom if sk in r['scores']]) for sk in ('root','oci','ind','lat')}
 rootwins=sum(r['winner']=='root' for r in famrows); ociwins=sum(r['winner']=='oci' for r in famrows); indwins=sum(r['winner']=='ind' for r in famrows); latwins=sum(r['winner']=='lat' for r in famrows)
 result={'version':1,'test':'Reverse-transform independent language families toward reconstructed root / Occitan / Indonesian / Latin','shards':N,'dictionary_entries':sum(x['entries'] for x in shards),'operators':OPS,'design':{'direction':'Each benchmark target language is reverse-transformed with each preregistered Mirror-Man operator and scored against four fixed candidate attractors: reconstructed root, Occitan, Indonesian and Latin.','convergence_question':'If unrelated families share a common root-like attractor, their best reverse transforms should converge preferentially toward the same candidate across shards and families.','controls':'Occitan, Indonesian and Latin are explicit competing attractors; direct untransformed similarity and transform gain are retained.','falsification':'The Occitan/root hypothesis weakens if unrelated families converge more consistently toward Indonesian or Latin, or if no candidate wins reproducibly.'},'verdict':{'nonromance_reverse_convergence_scores':means,'best_nonromance_attractor':max(means,key=means.get),'family_wins':{'root':rootwins,'oci':ociwins,'ind':indwins,'lat':latwins},'mean_transform_gain':{k:statistics.mean(v) for k,v in gains.items()},'root_beats_indonesian_nonromance':means['root']>means['ind'],'root_beats_occitan_nonromance':means['root']>means['oci']},'family_results':famrows,'focal_targets':[r for r in trows if r['iso'] in FOCAL],'operator_counts':{k:dict(v) for k,v in opc.items()},'boundary':'Structural phonetic-grid convergence is not by itself evidence of historical direction, ancestry, chronology or geography.'}
 OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result['verdict'],indent=2))

def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); s=sp.add_parser('shard'); s.add_argument('--id',type=int,required=True); sp.add_parser('merge'); a=ap.parse_args(); shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__': main()
