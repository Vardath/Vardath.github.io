#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from pathlib import Path
import man_grid_exact_engine as E
import man_grid_exact_data as D

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'data/man-grid-original-phonetics-v2-work/prepared.json.gz'
WORK=ROOT/'data/man-grid-phonetic-locality-v2-work'
OUT=ROOT/'data/man-grid-phonetic-locality-v2.json'
N=20;K=8

def load():
    with gzip.open(PREP,'rt',encoding='utf-8') as f:x=json.load(f)
    params={p:{**q} for p,q in x['params'].items()};return x,params

def layer_distance(a,b,spec):
    vals=[]
    for idx,l in enumerate([*spec['upper'],*spec['lower']]):
        x=(a['upper_left']+a['lower_left'])[idx];y=(b['upper_right']+b['lower_right'])[idx]
        import re
        mx=re.search(r'-R(\d+)-C(\d+)$',x);my=re.search(r'-R(\d+)-C(\d+)$',y);r1,c1=map(int,mx.groups());r2,c2=map(int,my.groups())
        rd=abs(r1-r2)/max(1,l['rows']-1);cd=abs(c1-c2)/max(1,l['columns']-1);vals.append((rd+cd)/2)
    return statistics.mean(vals),sum(1 for idx in range(10) if (a['upper_left']+a['lower_left'])[idx].replace('-L-','-')==(b['upper_right']+b['lower_right'])[idx].replace('-R-','-'))/10

def shard(i):
    x,params=load();spec=x['spec'];pids=sorted(params);owned=[p for p in pids if D.h64('exact-mg-test2',p)%N==i];real=[];control=[];same_real=[];same_control=[];pairs=0
    for p in owned:
        ranked=sorted((E.dist(params[p]['features'],params[q]['features']),q) for q in pids if q!=p)[:K]
        for fd,q in ranked:
            if p>=q:continue
            a=params[p]['grid'];b=params[q]['grid'];gd,sr=layer_distance(a,b,spec);real.append(gd);same_real.append(sr);pairs+=1
            r=pids[D.h64('exact-mg-test2-null',p,q)%len(pids)]
            if r==p:r=pids[(pids.index(r)+1)%len(pids)]
            nd,sc=layer_distance(a,params[r]['grid'],spec);control.append(nd);same_control.append(sc)
    out={'shard':i,'owned_segments':len(owned),'pairs':pairs,'real_grid_distances':real,'control_grid_distances':control,'real_same_coordinate_rates':same_real,'control_same_coordinate_rates':same_control}
    WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02d}.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8');print(json.dumps({'phase':'shard','shard':i,'owned_segments':len(owned),'pairs':pairs}),flush=True)

def effect(a,b):
    if len(a)<2 or len(b)<2:return None
    va=statistics.variance(a);vb=statistics.variance(b);sp=math.sqrt(((len(a)-1)*va+(len(b)-1)*vb)/(len(a)+len(b)-2));return (statistics.mean(b)-statistics.mean(a))/sp if sp else 0.0

def merge():
    x,params=load();ss=[json.loads((WORK/f'result-{i:02d}.json').read_text()) for i in range(N)];real=[z for s in ss for z in s['real_grid_distances']];ctrl=[z for s in ss for z in s['control_grid_distances']];sr=[z for s in ss for z in s['real_same_coordinate_rates']];sc=[z for s in ss for z in s['control_same_coordinate_rates']];advantages=[]
    for s in ss:
        if s['real_grid_distances'] and s['control_grid_distances']:advantages.append(statistics.mean(s['control_grid_distances'])-statistics.mean(s['real_grid_distances']))
    stability=sum(1 for z in advantages if z>0)/len(advantages) if advantages else 0.0
    result={'version':3,'test_id':2,'test':'Man Grid phonetic locality / shuffled-assignment control','status':'complete','shards':20,'independent_of_test1_reconstruction':True,'source':x['source'],'grid':{'cells':x['spec']['counts']['total_cells'],'all_rectangles_mirrored':True},'coverage':x['coverage'],'method':{'similar_pairs':f'for each shard-owned PHOIBLE segment, up to {K} nearest distinctive-feature neighbours; unordered pairs retained once','grid_metric':'mean normalized Manhattan row/column separation across all 10 mirrored layer coordinates, source on LEFT and target on RIGHT','control':'deterministic hash-shuffled target segment per real pair','engine':'same mapping rules as phonetic-man-grid-engine-core.js'},'summary':{'segments':len(params),'evaluated_pairs':len(real),'mean_real_structural_distance':statistics.mean(real) if real else None,'mean_shuffled_structural_distance':statistics.mean(ctrl) if ctrl else None,'effect_size_cohen_d_control_minus_real':effect(real,ctrl),'mean_real_same_mirrored_coordinate_rate':statistics.mean(sr) if sr else None,'mean_shuffled_same_mirrored_coordinate_rate':statistics.mean(sc) if sc else None,'shards_real_closer_than_shuffle':sum(1 for z in advantages if z>0),'shards_compared':len(advantages),'shard_agreement':stability,'supports_phonetic_locality':bool(real and ctrl and statistics.mean(real)<statistics.mean(ctrl))},'confidence':{'stability_fraction':stability,'interpretation':'descriptive stability across 20 genuinely partitioned source-segment shards; not a posterior probability'},'failures_missing_data':{'tone_segments_excluded_from_research_pair_pool':True,'marginal_inventory occurrences excluded':True},'assumptions':['PHOIBLE distinctive-feature distance is an external phonetic-similarity criterion','nearest-neighbour selection is fixed before examining Man Grid distances','LEFT/RIGHT side itself carries sibling-channel identity, so locality compares matched row/column structure across mirrored sides']}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'phase':'merge',**result['summary']}),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='phase',required=True);s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args();shard(a.id) if a.phase=='shard' else merge()
if __name__=='__main__':main()
