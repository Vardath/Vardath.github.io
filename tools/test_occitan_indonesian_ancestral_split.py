#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,random,statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DICT=ROOT/'data/phonetic-original-language-dictionary.json'
BENCH=ROOT/'data/phonetic-benchmark-summary.json'
OUTDIR=ROOT/'data/occitan-indonesian-ancestral-split-shards'
OUT=ROOT/'data/occitan-indonesian-ancestral-split.json'
N=20
CELLS=[f'{r}{c}' for r in 'ABCD' for c in range(1,5)]
OPS=['id','row_mirror','col_mirror','both_mirror','transpose','transpose_row','transpose_col','transpose_both']
ROMANCE={'oci','spa','osp','glg','ast','por','ita','fra','cat','arg','ron','scn','lmo','cos','frp','fax','vec','srd','fur'}

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
 a,b=divmod(i,16); ar,ac=divmod(a,4); br,bc=divmod(b,4); cell=lambda r,c:r*4+c
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

def inverse_transform(v,op):
 # idxop is a permutation; if y[f(i)]=x[i], then x[i]=y[f(i)].
 return [v[idxop(i,op)] for i in range(256)]

def best_forward(source,target):
 vals=[(score(transform(source,o),target),o) for o in OPS]
 return max(vals,key=lambda x:x[0])

def best_backward(source,target):
 vals=[(score(inverse_transform(source,o),target),o) for o in OPS]
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

def joint_parent(a,b):
 # Infer a common pre-split state using ONLY Occitan/Indonesian agreement, never root or target languages.
 best=None
 for oa in OPS:
  aa=inverse_transform(a,oa)
  for ob in OPS:
   bb=inverse_transform(b,ob)
   agree=score(aa,bb)
   latent=norm([(x+y)/2 for x,y in zip(aa,bb)])
   row=(agree,oa,ob,latent)
   if best is None or row[0]>best[0]: best=row
 return best

def shard(i):
 entries=json.loads(DICT.read_text(encoding='utf-8'))['entries']
 chosen=[e for j,e in enumerate(entries) if j%N==i]
 root=profile([e['path'] for e in chosen])
 L=langs(); oci=L['oci']['p']; ind=L['ind']['p']; lat=L['lat']['p']
 jf,oo,oi,latent=joint_parent(oci,ind)
 o2i=best_forward(oci,ind); i2o=best_forward(ind,oci)
 occitan_back=best_backward(oci,root); indonesian_back=best_backward(ind,root)
 latent_root=score(latent,root); oci_root=score(oci,root); ind_root=score(ind,root); lat_root=score(lat,root)
 # Hold out 1/20 of canonical languages on each shard for prediction; candidate parent was inferred without them.
 target_keys=sorted(L)
 held=[iso for j,iso in enumerate(target_keys) if j%N==i and iso not in {'oci','ind'}]
 pred={'latent':[],'root':[],'oci':[],'ind':[],'lat':[]}
 fam=defaultdict(lambda:defaultdict(list))
 for iso in held:
  t=L[iso]
  srcs={'latent':latent,'root':root,'oci':oci,'ind':ind,'lat':lat}
  for k,p in srcs.items():
   s,_=best_forward(p,t['p']); pred[k].append(s); fam[t['family']][k].append(s)
 # Deterministic unrelated-pair control: 50 pairs, parent inferred the same way, then scored to shard root.
 # Keep control operator names separate so they cannot overwrite the focal Occitan backward result.
 pool=[x for x in sorted(L) if x not in {'oci','ind'}]
 rng=random.Random(9173+i)
 controls=[]
 for _ in range(50):
  a,b=rng.sample(pool,2); ag,ctrl_oa,ctrl_ob,lp=joint_parent(L[a]['p'],L[b]['p'])
  controls.append(score(lp,root))
 pct=sum(x<=latent_root for x in controls)/len(controls)
 out={'shard':i,'entries':len(chosen),'joint_parent':{'agreement':jf,'occitan_inverse_operator':oo,'indonesian_inverse_operator':oi,'root_score':latent_root},
      'bidirectional':{'occitan_to_indonesian':{'score':o2i[0],'operator':o2i[1]},'indonesian_to_occitan':{'score':i2o[0],'operator':i2o[1]},
                       'occitan_backward_to_root':{'score':occitan_back[0],'operator':occitan_back[1]},'indonesian_backward_to_root':{'score':indonesian_back[0],'operator':indonesian_back[1]}},
      'direct_root_scores':{'latent':latent_root,'oci':oci_root,'ind':ind_root,'lat':lat_root},
      'heldout_prediction':{k:(statistics.mean(v) if v else None) for k,v in pred.items()},
      'family_prediction':{f:{k:statistics.mean(v) for k,v in d.items()} for f,d in fam.items()},
      'control':{'n':len(controls),'mean_random_pair_parent_root_score':statistics.mean(controls),'occitan_indonesian_parent_percentile':pct}}
 # Fail loudly at shard time if a numeric score/operator pair is corrupted.
 for label in ('occitan_to_indonesian','indonesian_to_occitan','occitan_backward_to_root','indonesian_backward_to_root'):
  row=out['bidirectional'][label]
  if not isinstance(row['score'],(int,float)) or row['operator'] not in OPS:
   raise TypeError(f'Corrupt bidirectional result for {label}: {row!r}')
 OUTDIR.mkdir(parents=True,exist_ok=True); (OUTDIR/f'shard-{i:02d}.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 print(json.dumps({'shard':i,'joint_parent':out['joint_parent'],'bidirectional':out['bidirectional'],'direct_root_scores':out['direct_root_scores'],'control':out['control']}))

def merge():
 xs=[json.loads((OUTDIR/f'shard-{i:02d}.json').read_text()) for i in range(N)]
 # Validate every shard before aggregating so future schema/type regressions identify the exact shard/field.
 for x in xs:
  for label in ('occitan_to_indonesian','indonesian_to_occitan','occitan_backward_to_root','indonesian_backward_to_root'):
   row=x['bidirectional'][label]
   if not isinstance(row.get('score'),(int,float)) or row.get('operator') not in OPS:
    raise TypeError(f"Shard {x.get('shard')} corrupt {label}: {row!r}")
 means=lambda path: statistics.mean(path(x) for x in xs)
 op_o=defaultdict(int); op_i=defaultdict(int); op_or=defaultdict(int); op_ir=defaultdict(int)
 for x in xs:
  op_o[x['joint_parent']['occitan_inverse_operator']]+=1; op_i[x['joint_parent']['indonesian_inverse_operator']]+=1
  op_or[x['bidirectional']['occitan_backward_to_root']['operator']]+=1; op_ir[x['bidirectional']['indonesian_backward_to_root']['operator']]+=1
 pred=defaultdict(list); fam=defaultdict(lambda:defaultdict(list))
 for x in xs:
  for k,v in x['heldout_prediction'].items():
   if v is not None: pred[k].append(v)
  for f,d in x['family_prediction'].items():
   for k,v in d.items(): fam[f][k].append(v)
 pmean={k:statistics.mean(v) for k,v in pred.items()}
 famout=[]
 for f,d in fam.items():
  m={k:statistics.mean(v) for k,v in d.items()}; famout.append({'family':f,'winner':max(m,key=m.get),'scores':m})
 famout.sort(key=lambda r:r['family'])
 verdict={
  'joint_parent_agreement':means(lambda x:x['joint_parent']['agreement']),
  'joint_parent_root_score':means(lambda x:x['joint_parent']['root_score']),
  'occitan_direct_root_score':means(lambda x:x['direct_root_scores']['oci']),
  'indonesian_direct_root_score':means(lambda x:x['direct_root_scores']['ind']),
  'latin_direct_root_score':means(lambda x:x['direct_root_scores']['lat']),
  'occitan_to_indonesian_score':means(lambda x:x['bidirectional']['occitan_to_indonesian']['score']),
  'indonesian_to_occitan_score':means(lambda x:x['bidirectional']['indonesian_to_occitan']['score']),
  'occitan_backward_to_root_score':means(lambda x:x['bidirectional']['occitan_backward_to_root']['score']),
  'indonesian_backward_to_root_score':means(lambda x:x['bidirectional']['indonesian_backward_to_root']['score']),
  'joint_parent_occitan_inverse_operator_counts':dict(op_o),'joint_parent_indonesian_inverse_operator_counts':dict(op_i),
  'occitan_backward_root_operator_counts':dict(op_or),'indonesian_backward_root_operator_counts':dict(op_ir),
  'heldout_prediction_scores':pmean,'best_heldout_predictor':max(pmean,key=pmean.get),
  'random_pair_parent_root_mean':means(lambda x:x['control']['mean_random_pair_parent_root_score']),
  'joint_parent_mean_control_percentile':means(lambda x:x['control']['occitan_indonesian_parent_percentile'])}
 verdict['joint_parent_closer_to_root_than_both_children']=verdict['joint_parent_root_score']>max(verdict['occitan_direct_root_score'],verdict['indonesian_direct_root_score'])
 verdict['joint_parent_beats_reconstructed_root_on_heldout_languages']=pmean.get('latent',0)>pmean.get('root',0)
 result={'version':2,'test':'Occitan + Indonesian backward-through-Man-grid common-ancestor / split test','shards':N,'dictionary_entries':sum(x['entries'] for x in xs),'operators':OPS,
 'design':{'ancestral_inference':'A latent pre-split profile is inferred solely by inverse-transforming Occitan and Indonesian under all 8x8 operator pairs and choosing the pair with maximum mutual agreement. The reconstructed root and held-out languages are not used to select that parent.',
 'bidirectional':'Occitan->Indonesian and Indonesian->Occitan are measured explicitly; each is also inverse-transformed independently toward the reconstructed root.',
 'heldout':'Canonical benchmark languages are partitioned deterministically across 20 shards and used only after parent inference.',
 'null':'Each shard compares the Occitan+Indonesian inferred parent against 50 deterministic random language-pair inferred parents for closeness to that shard reconstructed root.',
 'falsification':'The stronger ancient-parent split hypothesis requires the inferred joint parent to outperform both children against the reconstructed root and ideally outperform the reconstructed root itself on held-out languages, while also being exceptional versus random-pair parents.'},
 'verdict':verdict,'family_results':famout,'boundary':'A positive result is structural evidence for a shared latent phonetic-grid state under this operator model; it does not by itself establish chronology, geography, or historical descent.'}
 OUT.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(verdict,indent=2))

def main():
 ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); s=sp.add_parser('shard'); s.add_argument('--id',type=int,required=True); sp.add_parser('merge'); a=ap.parse_args(); shard(a.id) if a.cmd=='shard' else merge()
if __name__=='__main__': main()
