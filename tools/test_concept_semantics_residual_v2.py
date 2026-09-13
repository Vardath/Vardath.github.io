#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_exact_data as D
import test_concept_semantics_v1 as V1

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/concept-semantics-residual-v2-work'
PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data/concept-semantics-residual-v2.json'
BASE_RESULT=ROOT/'data/concept-semantics-v1.json'
SHARDS=20
GRID=20
PRIMARY_THRESH=.25
SENS_THRESH=[.15,.25,.35]
NEG=15
NEG_SEARCH=80
MIN_CASES=20
MIN_FAMILIES=8
MIN_HALF_FAMILIES=4


def dumpgz(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(p,'wt',encoding='utf8') as f: json.dump(x,f,separators=(',',':'))

def loadgz(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)

def signp(k,n):
    return sum(math.comb(n,i) for i in range(k,n+1))/2**n if n else 1.0

def bh_q(ps):
    m=len(ps);out=[1.0]*m;order=sorted(range(m),key=lambda i:ps[i]);prev=1.0
    for rank in range(m,0,-1):
        i=order[rank-1];q=min(prev,ps[i]*m/rank,1.0);out[i]=q;prev=q
    return out

def rawdist(a,b):
    return V1.edit(a,b,None,None,True)

def agg():
    return {'cases':0,'auc_real':0.0,'auc_label':0.0,'auc_random':0.0,'auc_raw':0.0,
            'top1_real':0.0,'top1_label':0.0,'top1_random':0.0,'top1_raw':0.0}

def addagg(a,m):
    a['cases']+=1
    for k,v in m.items():a[k]+=v

def avgagg(a):
    n=a['cases']
    return {k:(v/n if k!='cases' and n else v) for k,v in a.items()}

def prepare():
    # Rebuild the exact pinned v1 lexical evidence using the committed v1 protocol.
    V1.prepare()
    x=V1.loadgz(V1.PREP)
    base=json.loads(BASE_RESULT.read_text(encoding='utf8'))
    survivors=[r['concept_id'] for r in base.get('semantic_supported',[])]
    survivors=[c for c in survivors if c in x['concepts']]
    if len(survivors)!=27: raise RuntimeError(f'expected 27 frozen v1 FDR survivors, found {len(survivors)}')
    order=sorted(survivors,key=lambda c:(D.h64('residual-v2-shard',c),c))
    concept_shard={c:i%SHARDS for i,c in enumerate(order)}
    shard_sizes=[sum(1 for c in survivors if concept_shard[c]==i) for i in range(SHARDS)]
    if min(shard_sizes)<1: raise RuntimeError(f'empty shard in {shard_sizes}')
    out={'version':2,'source':x['source'],'phones':x['phones'],'languages':x['languages'],'forms':x['forms'],
         'concept_labels':x['concept_labels'],'plan':x['plan'],'survivors':survivors,
         'concept_shard':concept_shard,'shard_sizes':shard_sizes,
         'thresholds':SENS_THRESH,'primary_threshold':PRIMARY_THRESH,
         'protocol':{
          'question':'Which of the 27 v1 FDR concept survivors remain after removing cross-family lexical forms that are still too close in raw phone sequence?',
          'status':'Robustness test on previously selected concepts; not an independent discovery sample.',
          'frozen_survivors':'Exactly the 27 semantic FDR survivors from data/concept-semantics-v1.json.',
          'grid':'20x20 fixed from the prior pooled family-blocked peak; no per-concept grid selection.',
          'existing_controls':'Different target/reference families; 2000 km reference threshold; same non-empty NorthEuraLex cognacy label excluded for the true concept; NorthEuraLex Loan=true excluded where available.',
          'new_lexical_transmission_filter':'Before candidate scoring, every reference form whose normalized raw-phone edit distance to the target is <= the threshold is removed, for true and false concepts alike.',
          'primary_threshold':PRIMARY_THRESH,
          'sensitivity_thresholds':SENS_THRESH,
          'negative_candidates':f'Up to {NEG_SEARCH} deterministically hashed candidate concepts are searched to obtain {NEG} wrong concepts with at least two surviving reference forms.',
          'eligibility':f'>={MIN_CASES} cases across >={MIN_FAMILIES} target families.',
          'replication':'Target families are deterministically split into two disjoint hash halves; support requires positive semantic advantage in both halves with >=4 families per half.',
          'statistics':'One-sided family sign tests, BH-FDR across the 27 frozen survivors separately at each lexical-similarity threshold.',
          'semantic_support':'Positive real-grid AUC minus pseudo-label AUC, q<0.05, and positive effect in both family halves.',
          'geometry_support':'Positive real-grid AUC minus random-cell AUC, q<0.05, and positive effect in both family halves.',
          'interpretation_boundary':'Survival would show robustness to near-identical cross-family word forms; it would not by itself distinguish ancient inheritance, convergent sound symbolism, or undocumented borrowing.'
         }}
    dumpgz(PREP,out)
    print(json.dumps({'survivors':len(survivors),'shard_sizes':shard_sizes,'thresholds':SENS_THRESH},indent=2))

def filtered_refs(tgt,forms,thr,true_cog=None):
    out=[]
    for f in forms:
        if true_cog and f.get('cog') and f.get('cog')==true_cog: continue
        seq=f['seq']
        if rawdist(tgt,seq)<=thr: continue
        out.append(seq)
    return out

def make_case(x,lid,concept,thr,cache):
    target=x['forms'].get(lid,{}).get(concept)
    if not target:return None
    pool=V1.pool_for(x,lid,2000,cache)
    tcog=target.get('cog') or ''
    true_refs=filtered_refs(target['seq'],pool.get(concept,[]),thr,tcog)
    if len(true_refs)<2:return None
    avail=[c for c in pool if c!=concept]
    ordered=sorted(avail,key=lambda c:(D.h64('residual-v2-neg',thr,lid,concept,c),c))[:NEG_SEARCH]
    neg=[];negrefs=[]
    for c in ordered:
        rr=filtered_refs(target['seq'],pool.get(c,[]),thr,None)
        if len(rr)>=2:
            neg.append(c);negrefs.append(rr)
            if len(neg)==NEG:break
    if len(neg)<NEG:return None
    pseudo=1+(D.h64('residual-v2-pseudo',thr,lid,concept)%NEG)
    return target['seq'],[true_refs]+negrefs,pseudo

def concept_row(label,byfam):
    famrows=[];total=agg()
    halves={0:[],1:[]}
    for fam,a in sorted(byfam.items()):
        aa=avgagg(a);famrows.append((fam,aa))
        total['cases']+=a['cases']
        for k in total:
            if k!='cases':total[k]+=a[k]
        halves[D.h64('residual-family-half',fam)%2].append(aa)
    overall=avgagg(total)
    sem=[];geo=[]
    for fam,a in famrows:
        ds=a['auc_real']-a['auc_label'];dg=a['auc_real']-a['auc_random']
        if abs(ds)>1e-12:sem.append(ds)
        if abs(dg)>1e-12:geo.append(dg)
    def havg(rows,key1,key2):
        return statistics.mean(r[key1]-r[key2] for r in rows) if rows else None
    half_sem={str(h):havg(rows,'auc_real','auc_label') for h,rows in halves.items()}
    half_geo={str(h):havg(rows,'auc_real','auc_random') for h,rows in halves.items()}
    eligible=overall['cases']>=MIN_CASES and len(famrows)>=MIN_FAMILIES and all(len(halves[h])>=MIN_HALF_FAMILIES for h in (0,1))
    return {'label':label,'cases':overall['cases'],'target_families':len(famrows),'half_family_counts':{str(h):len(halves[h]) for h in (0,1)},
            'metrics':overall,'semantic_auc_advantage':overall.get('auc_real',0)-overall.get('auc_label',0),
            'geometry_auc_advantage':overall.get('auc_real',0)-overall.get('auc_random',0),
            'semantic_half_advantage':half_sem,'geometry_half_advantage':half_geo,
            'semantic_family_wins':sum(d>0 for d in sem),'semantic_family_nonzero':len(sem),'semantic_p':signp(sum(d>0 for d in sem),len(sem)),
            'geometry_family_wins':sum(d>0 for d in geo),'geometry_family_nonzero':len(geo),'geometry_p':signp(sum(d>0 for d in geo),len(geo)),
            'eligible':eligible}

def shard(i):
    x=loadgz(PREP);concepts=[c for c in x['survivors'] if x['concept_shard'][c]==i]
    if not concepts:raise RuntimeError(f'empty shard {i}')
    real=V1.qlookup(x['phones'],GRID,False);rand=V1.qlookup(x['phones'],GRID,True)
    cache={};out={'shard':i,'concept_count':len(concepts),'thresholds':{}}
    for thr in SENS_THRESH:
        rows={}
        for c in concepts:
            byfam=defaultdict(agg)
            for lid,L in x['languages'].items():
                q=make_case(x,lid,c,thr,cache)
                if q:addagg(byfam[L['family']],V1.eval_case(q,real,rand))
            rows[c]=concept_row(x['concept_labels'].get(c,c),byfam)
        out['thresholds'][str(thr)]=rows
    WORK.mkdir(parents=True,exist_ok=True)
    (WORK/f'result-{i:02}.json').write_text(json.dumps(out,separators=(',',':')))
    print({'shard':i,'concepts':len(concepts)})

def merge():
    x=loadgz(PREP);shards=[json.loads((WORK/f'result-{i:02}.json').read_text()) for i in range(SHARDS)]
    results={}
    for thr in SENS_THRESH:
        rows={}
        for s in shards: rows.update(s['thresholds'][str(thr)])
        ids=sorted(rows);eligible=[c for c in ids if rows[c]['eligible']]
        sq=bh_q([rows[c]['semantic_p'] for c in eligible]);gq=bh_q([rows[c]['geometry_p'] for c in eligible])
        for c,q in zip(eligible,sq):rows[c]['semantic_q']=q
        for c,q in zip(eligible,gq):rows[c]['geometry_q']=q
        supported=[];geometry=[]
        for c in eligible:
            r=rows[c];hs=r['semantic_half_advantage'];hg=r['geometry_half_advantage']
            r['semantic_supported']=r['semantic_auc_advantage']>0 and r['semantic_q']<.05 and hs['0'] is not None and hs['1'] is not None and hs['0']>0 and hs['1']>0
            r['geometry_supported']=r['geometry_auc_advantage']>0 and r['geometry_q']<.05 and hg['0'] is not None and hg['1'] is not None and hg['0']>0 and hg['1']>0
            if r['semantic_supported']:supported.append(c)
            if r['geometry_supported']:geometry.append(c)
        pooled=agg()
        for c in eligible:
            r=rows[c]['metrics'];n=r['cases'];pooled['cases']+=n
            for k in pooled:
                if k!='cases':pooled[k]+=r[k]*n
        results[str(thr)]={'eligible':len(eligible),'semantic_supported':supported,'geometry_supported':geometry,
                           'both_supported':sorted(set(supported)&set(geometry)),'pooled':avgagg(pooled),'concepts':rows}
    primary=results[str(PRIMARY_THRESH)]
    summary={'frozen_survivors':len(x['survivors']),'primary_threshold':PRIMARY_THRESH,'primary_eligible':primary['eligible'],
             'primary_semantic_supported':len(primary['semantic_supported']),'primary_geometry_supported':len(primary['geometry_supported']),
             'primary_both_supported':len(primary['both_supported']),
             'semantic_survivor_labels':[primary['concepts'][c]['label'] for c in primary['semantic_supported']],
             'geometry_survivor_labels':[primary['concepts'][c]['label'] for c in primary['geometry_supported']],
             'sensitivity_counts':{t:{'eligible':r['eligible'],'semantic':len(r['semantic_supported']),'geometry':len(r['geometry_supported']),'both':len(r['both_supported'])} for t,r in results.items()}}
    out={'version':2,'status':'complete','test':'27-concept residual semantics after near-identical cross-family lexical-form exclusion',
         'source':x['source'],'shards':SHARDS,'shard_sizes':x['shard_sizes'],'protocol':x['protocol'],'summary':summary,'results':results}
    OUT.write_text(json.dumps(out,indent=2),encoding='utf8')
    print(json.dumps(summary,indent=2))

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('prepare');q=sp.add_parser('shard');q.add_argument('--id',type=int,required=True);sp.add_parser('merge')
    a=ap.parse_args()
    if a.cmd=='prepare':prepare()
    elif a.cmd=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
