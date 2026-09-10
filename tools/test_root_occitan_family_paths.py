#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/root-occitan-family-paths-shards'
OUT=ROOT/'data/root-occitan-family-paths.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}
OPS=['id','row_mirror','col_mirror','both_mirror','transpose','transpose_row','transpose_col','transpose_both']
FOCAL=['oci','ind','lat','ita','grc','sqi','tur','spa','por','ron']

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

def score(a,b):return .55*cosine(a,b)+.30*(1-min(1,jsd(a,b)))+.15*overlap(a,b)

def idxop(i,op):
 a,b=divmod(i,16);ar,ac=divmod(a,4);br,bc=divmod(b,4)
 cell=lambda r,c:r*4+c
 if op=='id':na,nb=a,b
 elif op=='row_mirror':na,nb=cell(3-ar,ac),cell(3-br,bc)
 elif op=='col_mirror':na,nb=cell(ar,3-ac),cell(br,3-bc)
 elif op=='both_mirror':na,nb=cell(3-ar,3-ac),cell(3-br,3-bc)
 elif op=='transpose':na,nb=b,a
 elif op=='transpose_row':na,nb=cell(3-br,bc),cell(3-ar,ac)
 elif op=='transpose_col':na,nb=cell(br,3-bc),cell(ar,3-ac)
 elif op=='transpose_both':na,nb=cell(3-br,3-bc),cell(3-ar,3-ac)
 return na*16+nb

def transform(v,op):
 z=[0.0]*256
 for i,x in enumerate(v):z[idxop(i,op)]+=x
 return z

def best(source,target):
 vals=[(score(transform(source,o),target),o) for o in OPS]
 return max(vals,key=lambda x:x[0])

def profile(paths):
 c=[0.0]*256
 for p in paths:
  for a,b in zip(p,p[1:]):
   if a in CELLS and b in CELLS:c[CELLS.index(a)*16+CELLS.index(b)]+=1
 return norm(c)

def langs():
 b=json.loads(BENCH.read_text(encoding='utf-8'))
 return {r['iso']:{'iso':r['iso'],'name':r['name'],'family':r.get('family','Unclassified') or 'Unclassified','p':norm(list(map(float,r['sample_counts'])))} for r in b['languages']}

def shard(i):
 entries=json.loads(DICT.read_text(encoding='utf-8'))['entries']
 chosen=[e for j,e in enumerate(entries) if j%N==i]
 root=profile([e['path'] for e in chosen])
 L=langs(); sources={'root':{'name':'Reconstructed root','family':'model','p':root}}
 for iso in ['oci','ind','lat','ita']:
  if iso in L:sources[iso]=L[iso]
 rows=[]
 for tiso,t in L.items():
  sr={}
  for sk,s in sources.items():
   if sk==tiso:continue
   bs,op=best(s['p'],t['p']);sr[sk]={'score':bs,'operator':op,'identity_score':score(s['p'],t['p']),'gain':bs-score(s['p'],t['p'])}
  rows.append({'iso':tiso,'name':t['name'],'family':t['family'],'scores':sr})
 # Root -> Occitan conserved-state check and two-leg Occitan mediation summary.
 root_occ=best(root,L['oci']['p']) if 'oci' in L else (0,'')
 fam=defaultdict(lambda:defaultdict(list))
 for r in rows:
  for sk,v in r['scores'].items():fam[r['family']][sk].append(v['score'])
 famout={f:{sk:statistics.mean(v) for sk,v in d.items()} for f,d in fam.items()}
 overall={}
 for sk in sources:
  vals=[r['scores'][sk]['score'] for r in rows if sk in r['scores'] and r['iso'] not in ROMANCE]
  overall[sk]=statistics.mean(vals) if vals else None
 out={'shard':i,'entries':len(chosen),'root_to_occitan':{'score':root_occ[0],'operator':root_occ[1]},'nonromance_prediction':overall,'family_prediction':famout,'targets':rows}
 OUTDIR.mkdir(parents=True,exist_ok=True);(OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 print(json.dumps({'shard':i,'entries':len(chosen),'root_to_occitan':out['root_to_occitan'],'nonromance_prediction':overall}))

def merge():
 shards=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)]
 keys=['root','oci','ind','lat','ita']
 nr={k:[] for k in keys};ro=[];rop=defaultdict(int);fam=defaultdict(lambda:defaultdict(list));target=defaultdict(lambda:defaultdict(list));opcounts=defaultdict(lambda:defaultdict(int))
 for x in shards:
  ro.append(x['root_to_occitan']['score']);rop[x['root_to_occitan']['operator']]+=1
  for k,v in x['nonromance_prediction'].items():
   if v is not None:nr[k].append(v)
  for f,d in x['family_prediction'].items():
   for k,v in d.items():fam[f][k].append(v)
  for r in x['targets']:
   for k,v in r['scores'].items():
    target[r['iso']][k].append(v['score']);opcounts[k][v['operator']]+=1
 nonrom={k:statistics.mean(v) for k,v in nr.items() if v}
 famout=[]
 for f,d in fam.items():
  m={k:statistics.mean(v) for k,v in d.items()};winner=max(m,key=m.get)
  famout.append({'family':f,'winner':winner,'scores':m})
 famout.sort(key=lambda x:x['family'])
 trows=[]
 L=langs()
 for iso,d in target.items():
  m={k:statistics.mean(v) for k,v in d.items()};winner=max(m,key=m.get)
  trows.append({'iso':iso,'name':L[iso]['name'],'family':L[iso]['family'],'winner':winner,'scores':m})
 focal=[r for r in trows if r['iso'] in FOCAL]
 verdict={'root_to_occitan_mean_best_operator_score':statistics.mean(ro),'root_to_occitan_operator_counts':dict(rop),'best_nonromance_source':max(nonrom,key=nonrom.get),'nonromance_scores':nonrom,'occitan_beats_indonesian_nonromance':nonrom.get('oci',0)>nonrom.get('ind',0),'occitan_beats_latin_nonromance':nonrom.get('oci',0)>nonrom.get('lat',0),'family_wins':dict((k,sum(r['winner']==k for r in famout)) for k in keys)}
 result={'version':1,'test':'Reconstructed root -> Occitan-like conserved state -> Mirror-Man family paths','shards':N,'dictionary_entries':sum(x['entries'] for x in shards),'operators':OPS,'design':{'root':'Independent reconstructed dictionary gate-transition profile, recomputed per deterministic shard.','conserved_state':'Occitan is tested as the proposed surviving root-like state; Indonesian, Latin and Italian are explicit competitors.','prediction':'Each source is transformed by the same eight preregistered Mirror-Man operators; the best operator predicts each canonical target language. Results are aggregated by broad language family and on non-Romance targets.','falsification':'If Occitan is uniquely privileged as a conserved branching state, it should consistently beat competitors out of family, not merely resemble the reconstructed root.'},'verdict':verdict,'family_results':famout,'focal_targets':focal,'operator_counts':{k:dict(v) for k,v in opcounts.items()},'boundary':'This is a structural phonetic-grid experiment. It does not by itself establish geographic or chronological origin.'}
 OUT.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(verdict,indent=2))

def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True);s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__':main()
