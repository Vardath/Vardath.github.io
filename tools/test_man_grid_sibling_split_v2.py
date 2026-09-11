#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E
import man_grid_exact_data as D

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'data/man-grid-original-phonetics-v2-work/prepared.json.gz'
WORK=ROOT/'data/man-grid-sibling-split-v2-work'
OUT=ROOT/'data/man-grid-sibling-split-v2.json'
N=20

def load():
    with gzip.open(PREP,'rt',encoding='utf-8') as f:x=json.load(f)
    params={p:{**q} for p,q in x['params'].items()};langs={lid:{**l,'inventory':set(l['inventory'])} for lid,l in x['langs'].items()};return x,params,langs

def family_sets(x,langs):
    by=defaultdict(list)
    for lid,l in langs.items():by[l['family']].append(lid)
    out={}
    for fam in x['eligible_families']:
        L=[z for z in by[fam] if langs[z]['branch']=='L'];R=[z for z in by[fam] if langs[z]['branch']=='R']
        if len(L)>=2 and len(R)>=2:out[fam]={'L':L,'R':R}
    return out

def parent_inventory(A,B,params):
    out=set()
    for a,b,_ in D.mutual_pairs(A,B,params):
        m=[(u+v)/2 for u,v in zip(params[a]['features'],params[b]['features'])]
        p=min(params,key=lambda q:(E.dist(m,params[q]['features']),q));out.add(p)
    return out

def holdout(branch,fam,side):
    return min(branch,key=lambda lid:(D.h64('exact-mg-test3-holdout',fam,side,lid),lid))

def shard(i):
    x,params,langs=load();fs=family_sets(x,langs);ordered=sorted(fs);owned=[f for f in ordered if D.h64('exact-mg-test3',f)%N==i];rows=[]
    for fam in owned:
        L=fs[fam]['L'];R=fs[fam]['R'];hl=holdout(L,fam,'L');hr=holdout(R,fam,'R');tl=[z for z in L if z!=hl];tr=[z for z in R if z!=hr]
        A=D.consensus_inventory(tl,langs,.5);B=D.consensus_inventory(tr,langs,.5);parent=parent_inventory(A,B,params)
        dl=E.inventory_distance(parent,langs[hl]['inventory'],params);dr=E.inventory_distance(parent,langs[hr]['inventory'],params)
        if dl is None or dr is None or not parent:continue
        real=(dl+dr)/2;branch_base=[]
        bl=E.inventory_distance(A,langs[hl]['inventory'],params);br=E.inventory_distance(B,langs[hr]['inventory'],params)
        if bl is not None and br is not None:branch_base=[bl,br]
        other=ordered[(ordered.index(fam)+1)%len(ordered)] if len(ordered)>1 else fam
        if other==fam and len(ordered)>1:other=ordered[(ordered.index(fam)+2)%len(ordered)]
        OR=fs[other]['R'];oh=holdout(OR,other,'R');ot=[z for z in OR if z!=oh];OB=D.consensus_inventory(ot,langs,.5);null_parent=parent_inventory(A,OB,params)
        nl=E.inventory_distance(null_parent,langs[hl]['inventory'],params);nr=E.inventory_distance(null_parent,langs[hr]['inventory'],params);null=(nl+nr)/2 if nl is not None and nr is not None and null_parent else None
        rows.append({'family':fam,'languages_total':len(L)+len(R),'left_holdout':langs[hl]['name'],'right_holdout':langs[hr]['name'],'training_left_languages':len(tl),'training_right_languages':len(tr),'parent_segments':len(parent),'real_shared_parent_holdout_distance':real,'mismatched_parent_holdout_distance':null,'branch_specific_holdout_distance':statistics.mean(branch_base) if branch_base else None,'real_beats_mismatch':bool(null is not None and real<null),'parent_ipa':sorted(params[p]['name'] for p in parent)})
    out={'shard':i,'families':len(rows),'family_results':rows};WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02d}.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8');print(json.dumps({'phase':'shard','shard':i,'families':len(rows)}),flush=True)

def paired_effect(real,null):
    d=[b-a for a,b in zip(real,null)]
    return statistics.mean(d)/(statistics.stdev(d) or 1.0) if len(d)>1 else None

def merge():
    x,params,langs=load();ss=[json.loads((WORK/f'result-{i:02d}.json').read_text(encoding='utf-8')) for i in range(N)];rows=[r|{'shard':s['shard']} for s in ss for r in s['family_results'] if r['mismatched_parent_holdout_distance'] is not None];real=[r['real_shared_parent_holdout_distance'] for r in rows];null=[r['mismatched_parent_holdout_distance'] for r in rows];base=[r['branch_specific_holdout_distance'] for r in rows if r['branch_specific_holdout_distance'] is not None];shard_adv=[]
    for s in ss:
        rr=[r for r in s['family_results'] if r['mismatched_parent_holdout_distance'] is not None]
        if rr:shard_adv.append(statistics.mean(r['mismatched_parent_holdout_distance']-r['real_shared_parent_holdout_distance'] for r in rr))
    agree=sum(1 for z in shard_adv if z>0);result={'version':3,'test_id':3,'test':'Parent to two sibling phonetic systems falsification','status':'complete','shards':20,'independent_of_test1_reconstruction':True,'source':x['source'],'grid':{'cells':x['spec']['counts']['total_cells'],'all_rectangles_mirrored':True},'coverage':x['coverage'],'method':{'family_requirement':'at least two LEFT and two RIGHT branch languages after data-driven within-family split','cross_validation':'one deterministic held-out language from each sibling branch; parent inferred only from remaining branch inventories','parent':'mutual-nearest training LEFT/RIGHT sounds midpointed in full features and snapped to nearest PHOIBLE sound through the exact engine','falsification_control':'same LEFT training branch paired with a deterministically rotated unrelated family RIGHT branch; both parents scored on the original family two held-out languages','extra_baseline':'each branch training consensus predicts its own held-out branch independently'},'summary':{'families_tested':len(rows),'heldout_languages':2*len(rows),'mean_real_shared_parent_holdout_distance':statistics.mean(real) if real else None,'mean_mismatched_parent_holdout_distance':statistics.mean(null) if null else None,'paired_effect_size_standardized_advantage':paired_effect(real,null) if real else None,'families_real_parent_beats_mismatch':sum(1 for r in rows if r['real_beats_mismatch']),'family_success_rate':sum(1 for r in rows if r['real_beats_mismatch'])/len(rows) if rows else None,'mean_branch_specific_holdout_distance':statistics.mean(base) if base else None,'shards_real_parent_beats_mismatch':agree,'shards_compared':len(shard_adv),'shard_agreement':agree/len(shard_adv) if shard_adv else None,'supports_one_parent_two_siblings_against_unrelated_control':bool(real and statistics.mean(real)<statistics.mean(null))},'confidence':{'stability_fraction':agree/len(shard_adv) if shard_adv else None,'interpretation':'cross-family shard stability of held-out predictive advantage; not historical certainty'},'family_results':sorted(rows,key=lambda r:(r['real_shared_parent_holdout_distance']-r['mismatched_parent_holdout_distance'],r['family'])),'failures_missing_data':{'families_without_two_languages_per_sibling_branch_excluded':True,'unclassified_families_excluded':True},'assumptions':['the unsupervised branch split is a provisional test partition, not a known historical split','a feature midpoint snapped to an attested segment is a candidate parent phoneme representation','the transformative circle is not given a fitted transformation in this independent falsification test']}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'phase':'merge',**result['summary']},ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='phase',required=True);s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();shard(a.id) if a.phase=='shard' else merge()
if __name__=='__main__':main()
