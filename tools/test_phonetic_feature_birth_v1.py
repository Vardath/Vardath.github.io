#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E, man_grid_exact_data as D

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/phonetic-feature-birth-v1-work'
PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data/phonetic-feature-birth-v1.json'
SHARDS=20
RES=list(range(2,24))
CAND=list(range(3,22))
BOUND=[22,23]
PRIMARY=[f for f in E.FEATURES if f in E.PRIMARY]
PI=[E.FEATURES.index(f) for f in PRIMARY]
HELD=[f for f in E.FEATURES if f not in E.PRIMARY and f not in {'tone','stress'}]
HI=[E.FEATURES.index(f) for f in HELD]
CATEGORIES={
 'timing_release':['short','long','delayedRelease'],
 'secondary_manner':['approximant','tap','trill','nasal','lateral'],
 'lip_coronal_detail':['round','labiodental','anterior','distributed','strident'],
 'tongue_root_tension':['tense','retractedTongueRoot','advancedTongueRoot'],
 'laryngeal_source':['periodicGlottalSource','epilaryngealSource','spreadGlottis','constrictedGlottis','fortis'],
 'airstream_special':['raisedLarynxEjective','loweredLarynxImplosive','click'],
}

def dumpgz(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 with gzip.open(p,'wt',encoding='utf8') as f:json.dump(x,f,separators=(',',':'))
def loadgz(p):
 with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)
def sub(v,I):return [v[i] for i in I]
def fit(params):
 pv=[sub(q['features'],PI) for q in params.values()]; full=[q['features'] for q in params.values()]
 m=E.centroid(pv); C0=E.covariance(pv,m); d=len(m)
 a,l=E.eig(C0,[math.sin((i+1)*1.731)+.5 for i in range(d)])
 C1=[[C0[i][j]-l*a[i]*a[j] for j in range(d)] for i in range(d)]
 b,_=E.eig(C1,[math.cos((i+1)*2.117)+.25 for i in range(d)],a)
 def orient(ax,k):
  score=0.0
  for fv,v in zip(full,pv):
   g=lambda n:fv[E.FEATURES.index(n)]
   target=(g('back')-g('front')+.5*g('dorsal')-.45*g('labial')) if k=='x' else (g('syllabic')+.65*g('sonorant')+.25*g('continuant')-.5*g('consonantal'))
   score+=E.dot(v,ax)*target
  return [-x for x in ax] if score<0 else ax
 a,b=orient(a,'x'),orient(b,'y');xs=[];ys=[]
 for z in pv:
  q=[z[i]-m[i] for i in range(d)];xs.append(E.dot(q,a));ys.append(E.dot(q,b))
 return {'mean':m,'x':a,'y':b,'x0':E.pct(xs,.01),'x1':E.pct(xs,.99),'y0':E.pct(ys,.01),'y1':E.pct(ys,.99)}
def project(v,p):
 z=[sub(v,PI)[i]-p['mean'][i] for i in range(len(PI))]
 x=(E.dot(z,p['x'])-p['x0'])/((p['x1']-p['x0']) or 1.0);y=(E.dot(z,p['y'])-p['y0'])/((p['y1']-p['y0']) or 1.0)
 return [max(0,min(.999999,x)),max(0,min(.999999,y))]
def cell(c,n):return [int(c[0]*n),int(c[1]*n)]
def signp(k,n):return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def prepare():
 _,params,_,_,cov=D.load_phoible(); P=fit(params); ids=sorted(params)
 rec={pid:{'f':params[pid]['features'],'c':project(params[pid]['features'],P),'fold':D.h64('feature-birth-fold',pid)%SHARDS} for pid in ids}
 x={'version':1,'source':{'dataset':'PHOIBLE','commit':D.PH},'segments':len(ids),'coverage':cov,'resolutions':RES,'candidate':CAND,'boundary':BOUND,'primary':PRIMARY,'heldout':HELD,'categories':CATEGORIES,'projection':P,'records':rec,'protocol':{
  'question':'Which held-out phonetic features become newly predictable at each successive square resolution?',
  'birth_definition':'Feature information is born at n when moving from (n-1)x(n-1) to nxn reduces held-out prediction error more than a coordinate-shuffled null, replicated across held-out folds.',
  'cross_validation':'20 deterministic held-out segment folds. Cell feature means are learned from 19 folds and evaluated on the untouched fold.',
  'null':'Within each fold, the same phonetic records keep their features while their articulatory coordinates are deterministically permuted across segment IDs.',
  'independence':'Only the 11 broad primary place/manner features define the 2D grid. The 24 tested features are withheld from projection and cell placement.',
  'support':'A birth step requires positive mean null-adjusted gain, positive mean real gain, >=15/20 fold wins, and one-sided sign p<0.05.',
  'interpretation':'Birth means first/strongest resolvability in this codec, not biological or historical invention of the articulatory feature.'}}
 dumpgz(PREP,x);print({'segments':len(ids),'heldout':len(HELD),'folds':SHARDS})

def predict(records,coords,train_ids,test_ids,n):
 # Train a mean value for each held-out feature in each occupied cell.
 sums=defaultdict(lambda:[0.0]*len(HI)); counts=defaultdict(int); global_sum=[0.0]*len(HI)
 for pid in train_ids:
  key=tuple(cell(coords[pid],n)); fv=records[pid]['f'];counts[key]+=1
  for j,ix in enumerate(HI):sums[key][j]+=fv[ix];global_sum[j]+=fv[ix]
 g=[x/len(train_ids) for x in global_sum]
 err=[0.0]*len(HI); used=0; fallback=0
 for pid in test_ids:
  key=tuple(cell(coords[pid],n)); fv=records[pid]['f']; c=counts.get(key,0);mu=[sums[key][j]/c for j in range(len(HI))] if c else g
  fallback+=not bool(c);used+=1
  for j,ix in enumerate(HI):err[j]+=abs(fv[ix]-mu[j])/2.0
 return {'mae':[x/used for x in err],'test':used,'fallback':fallback}

def shard(i):
 x=loadgz(PREP);records=x['records'];ids=sorted(records);test=[p for p in ids if records[p]['fold']==i];train=[p for p in ids if records[p]['fold']!=i]
 coords={p:records[p]['c'] for p in ids}
 # Deterministic null permutation, unique per fold.
 order=sorted(ids,key=lambda p:(D.h64('feature-birth-null',i,p),p)); shuffled={pid:coords[src] for pid,src in zip(ids,order)}
 out={'shard':i,'n_test':len(test),'real':{},'null':{}}
 for n in RES:
  out['real'][str(n)]=predict(records,coords,train,test,n)
  out['null'][str(n)]=predict(records,shuffled,train,test,n)
 WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02}.json').write_text(json.dumps(out,separators=(',',':')))
 print({'shard':i,'test':len(test)})

def merge():
 x=loadgz(PREP); shards=[json.loads((WORK/f'result-{i:02}.json').read_text()) for i in range(SHARDS)]
 feats={}; births=defaultdict(list)
 for j,f in enumerate(HELD):
  trajectory=[];sig=[]
  for n in range(3,24):
   rg=[];ng=[];ag=[]
   for s in shards:
    rprev=s['real'][str(n-1)]['mae'][j];rnow=s['real'][str(n)]['mae'][j];nprev=s['null'][str(n-1)]['mae'][j];nnow=s['null'][str(n)]['mae'][j]
    a=rprev-rnow;b=nprev-nnow;rg.append(a);ng.append(b);ag.append(a-b)
   wins=sum(v>0 for v in ag);p=signp(wins,len(ag));row={'n':n,'real_gain':statistics.mean(rg),'null_gain':statistics.mean(ng),'adjusted_gain':statistics.mean(ag),'fold_wins':wins,'sign_p':p}
   row['supported']=row['real_gain']>0 and row['adjusted_gain']>0 and wins>=15 and p<.05
   trajectory.append(row)
   if n in CAND and row['supported']:sig.append(n)
  onset=min(sig) if sig else None
  pool=[r for r in trajectory if r['n'] in CAND and r['supported']]
  peak=max(pool,key=lambda r:r['adjusted_gain'])['n'] if pool else None
  peakrow=next((r for r in trajectory if r['n']==peak),None)
  feats[f]={'onset':onset,'peak':peak,'peak_adjusted_gain':peakrow['adjusted_gain'] if peakrow else None,'significant_steps':sig,'trajectory':trajectory}
  if peak is not None:births[str(peak)].append(f)
 cats={}
 for name,members in CATEGORIES.items():
  traj=[];sig=[]
  idx=[HELD.index(f) for f in members]
  for n in range(3,24):
   vals=[];reals=[]
   for s in shards:
    aa=[];rr=[]
    for j in idx:
     rg=s['real'][str(n-1)]['mae'][j]-s['real'][str(n)]['mae'][j];ng=s['null'][str(n-1)]['mae'][j]-s['null'][str(n)]['mae'][j]
     aa.append(rg-ng);rr.append(rg)
    vals.append(statistics.mean(aa));reals.append(statistics.mean(rr))
   wins=sum(v>0 for v in vals);p=signp(wins,len(vals));row={'n':n,'real_gain':statistics.mean(reals),'adjusted_gain':statistics.mean(vals),'fold_wins':wins,'sign_p':p}
   row['supported']=row['real_gain']>0 and row['adjusted_gain']>0 and wins>=15 and p<.05;traj.append(row)
   if n in CAND and row['supported']:sig.append(n)
  onset=min(sig) if sig else None;pool=[r for r in traj if r['n'] in CAND and r['supported']];peak=max(pool,key=lambda r:r['adjusted_gain'])['n'] if pool else None
  cats[name]={'members':members,'onset':onset,'peak':peak,'significant_steps':sig,'trajectory':traj}
 # Aggregate per-resolution held-out error and null-adjusted gain for overview.
 overview=[]
 for n in RES:
  r=statistics.mean(statistics.mean(s['real'][str(n)]['mae']) for s in shards);q=statistics.mean(statistics.mean(s['null'][str(n)]['mae']) for s in shards)
  overview.append({'n':n,'real_mae':r,'null_mae':q})
 out={'version':1,'status':'complete','test':'phonetic information birth across successive square grids','source':x['source'],'segments':x['segments'],'shards':SHARDS,'features':{'grid_and_matching':PRIMARY,'heldout_tested':HELD,'categories':CATEGORIES},'method':x['protocol'],'feature_births_by_peak_resolution':dict(sorted(births.items(),key=lambda kv:int(kv[0]))),'feature_results':feats,'category_results':cats,'overview':overview,'boundary':'Resolutions 22 and 23 are boundary continuation checks only; candidate birth assignments are restricted to 3x3 through 21x21.'}
 OUT.write_text(json.dumps(out,indent=2));print(json.dumps({'features_with_supported_birth':sum(v['peak'] is not None for v in feats.values()),'peak_groups':out['feature_births_by_peak_resolution']},indent=2))

def main():
 a=argparse.ArgumentParser();s=a.add_subparsers(dest='cmd',required=True);s.add_parser('prepare');q=s.add_parser('shard');q.add_argument('--id',type=int,required=True);s.add_parser('merge');z=a.parse_args()
 if z.cmd=='prepare':prepare()
 elif z.cmd=='shard':shard(z.id)
 else:merge()
if __name__=='__main__':main()
