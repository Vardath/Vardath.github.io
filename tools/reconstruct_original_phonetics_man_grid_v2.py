#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_exact_engine as E
import man_grid_exact_data as D

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'data/man-grid-original-phonetics-v2-work'
PREP=WORK/'prepared.json.gz'
OUT=ROOT/'data/man-grid-original-phonetics-v2.json'
N=20

def dumpgz(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(path,'wt',encoding='utf-8',compresslevel=6) as f:json.dump(obj,f,ensure_ascii=False,separators=(',',':'))
def loadgz(path):
    with gzip.open(path,'rt',encoding='utf-8') as f:return json.load(f)

def prepare():
    spec,params,langs,P,coverage=D.load_phoible();branches,eligible,axis=D.assign_branches(langs,params)
    payload={'version':3,'spec':spec,'projection':P,'features':E.FEATURES,'coverage':coverage,'eligible_families':eligible,'sibling_axis':axis,
      'params':{p:{'name':q['name'],'class':q['class'],'features':q['features'],'grid':q['grid']} for p,q in params.items()},
      'langs':{lid:{'name':l['name'],'iso':l['iso'],'family':l['family'],'branch':branches.get(lid),'inventory':sorted(l['inventory'])} for lid,l in langs.items() if branches.get(lid)},
      'source':{'dataset':'PHOIBLE CLDF','commit':D.PH,'marginal_segments_excluded':True,'tone_segments_excluded_from_research_inventory':True,'projection_fit_to_all_phoible_parameters':True},
      'design':{'grid':'exact 1,074-cell mirrored Man Grid + transformative circle from data/man-grid-structure-v1.json','engine_parity':'Python research mapping ports phonetic-man-grid-engine-core.js: same raw PHOIBLE feature vectors, PCA seeds/orientation, 1st/99th-percentile bounds, y inversion, per-layer quantisation, weighted feature distance and L/R mirror addressing','rectangles':'U1 4x4, U2 7x5, U3 10x5, U4 7x4, U5 5x5, D1 6x5, D2 11x5, D3 17x4, D4 21x5, D5 25x5; every layer exists on LEFT and RIGHT','sibling_split':'within-family inventory centroids are split by a global within-family residual axis; no modern language is preselected','ancestor_sound':'mutual-nearest LEFT/RIGHT branch sounds are midpointed in full PHOIBLE feature space; candidate roots are aggregated by mirrored D5 row/column coordinate and retain both L and R addresses','control':'for each real family, replace its RIGHT branch with a deterministically rotated unrelated family RIGHT branch','shards':20}}
    dumpgz(PREP,payload);print(json.dumps({'phase':'prepare','coverage':coverage,'eligible_families':len(eligible),'shards':N}),flush=True)

def unpack():
    x=loadgz(PREP);params={p:{**q} for p,q in x['params'].items()};langs={lid:{**l,'inventory':set(l['inventory'])} for lid,l in x['langs'].items()};return x,params,langs

def fam_struct(fam,lids,langs,params):
    L=[x for x in lids if langs[x]['branch']=='L'];R=[x for x in lids if langs[x]['branch']=='R']
    if not L or not R:return None
    A=D.consensus_inventory(L,langs,.5);B=D.consensus_inventory(R,langs,.5);pairs=D.mutual_pairs(A,B,params)
    return {'L':L,'R':R,'A':A,'B':B,'pairs':pairs}

def root_key(g):
    p=g['lower_left'][-1]
    return p.replace('-L-','-')

def shard(i):
    x,params,langs=unpack();P=x['projection'];spec=x['spec'];by=defaultdict(list)
    for lid,l in langs.items():by[l['family']].append(lid)
    all_struct={f:fam_struct(f,by[f],langs,params) for f in x['eligible_families']};all_struct={f:s for f,s in all_struct.items() if s and s['pairs']};ordered=sorted(all_struct)
    fams=[f for f in ordered if D.h64('exact-mg-test1',f)%N==i];obs=[];real=[];control=[]
    for fam in fams:
        s=all_struct[fam];best={}
        for a,b,d in s['pairs']:
            va=params[a]['features'];vb=params[b]['features'];mid=[(u+v)/2 for u,v in zip(va,vb)];g=E.grid_paths(mid,P,spec);k=root_key(g);q=(d,a,b,mid,g)
            if k not in best or q[0]<best[k][0]:best[k]=q
        for k,(d,a,b,mid,g) in best.items():
            real.append(d);obs.append({'family':fam,'root_coordinate':k,'root_cell_left':g['lower_left'][-1],'root_cell_right':g['lower_right'][-1],'left':a,'right':b,'left_ipa':params[a]['name'],'right_ipa':params[b]['name'],'distance':d,'mid':mid,'parent_paths':{'L':g['all_left'],'R':g['all_right']},'left_languages':[langs[z]['name'] for z in s['L'][:6]],'right_languages':[langs[z]['name'] for z in s['R'][:6]]})
        if len(ordered)>1:
            j=ordered.index(fam);other=ordered[(j+1)%len(ordered)]
            if other==fam:other=ordered[(j+2)%len(ordered)]
            for a,b,d in D.mutual_pairs(s['A'],all_struct[other]['B'],params):control.append(d)
    out={'shard':i,'families':len(fams),'family_names':fams,'observations':obs,'real_pair_distances':real,'control_pair_distances':control}
    WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02d}.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'phase':'shard','shard':i,'families':len(fams),'observations':len(obs),'real_pairs':len(real),'control_pairs':len(control)}),flush=True)

def cohen_d(real,control):
    if len(real)<2 or len(control)<2:return None
    vr=statistics.variance(real);vc=statistics.variance(control);pooled=math.sqrt(((len(real)-1)*vr+(len(control)-1)*vc)/(len(real)+len(control)-2))
    return (statistics.mean(control)-statistics.mean(real))/pooled if pooled else 0.0

def merge():
    x,params,langs=unpack();P=x['projection'];spec=x['spec'];shards=[json.loads((WORK/f'result-{i:02d}.json').read_text(encoding='utf-8')) for i in range(N)]
    obs=[o|{'shard':s['shard']} for s in shards for o in s['observations']];eligible=sum(s['families'] for s in shards);groups=defaultdict(list)
    for o in obs:groups[o['root_coordinate']].append(o)
    minfam=max(6,math.ceil(max(1,eligible)*.015));minsh=5;candidates=[];vectors={p:q['features'] for p,q in params.items()}
    for key,rows in groups.items():
        fams={r['family'] for r in rows};shs={r['shard'] for r in rows}
        if len(fams)<minfam or len(shs)<minsh:continue
        mean=E.centroid([r['mid'] for r in rows]);ranked=sorted(((E.dist(mean,v),p) for p,v in vectors.items()),key=lambda z:(z[0],params[z[1]]['name']));pid=ranked[0][1];g=E.grid_paths(mean,P,spec)
        survival=sum(1 for leftout in range(N) if len({r['family'] for r in rows if r['shard']!=leftout})>=minfam and len({r['shard'] for r in rows if r['shard']!=leftout})>=minsh)
        if survival<16:continue
        confidence=.4*min(1,len(fams)/(minfam*2))+.3*len(shs)/N+.3*survival/N
        candidates.append({'ipa':params[pid]['name'],'parameter_id':pid,'features':params[pid]['features'],'root_coordinate':key,'root_cell':g['lower_left'][-1],'root_cell_left':g['lower_left'][-1],'root_cell_right':g['lower_right'][-1],'man_grid_state':{'parent_path_L':g['all_left'],'parent_path_R':g['all_right']},'family_support':len(fams),'shard_support':len(shs),'leave_one_shard_out_survival':survival,'support_confidence':round(confidence,4),'mean_sibling_feature_distance':statistics.mean(r['distance'] for r in rows),'prototype_feature_distance':E.dist(mean,params[pid]['features']),'competing_candidates':[{'ipa':params[p]['name'],'distance':d} for d,p in ranked[1:4]],'examples':[{'family':r['family'],'left_ipa':r['left_ipa'],'right_ipa':r['right_ipa'],'left_languages':r['left_languages'],'right_languages':r['right_languages']} for r in sorted(rows,key=lambda z:(z['distance'],z['family']))[:8]]})
    candidates.sort(key=lambda r:(-r['family_support'],-r['shard_support'],-r['leave_one_shard_out_survival'],r['prototype_feature_distance'],r['ipa']));uniq=[];seen=set()
    for r in candidates:
        if r['ipa'] not in seen:seen.add(r['ipa']);uniq.append(r)
    real=[d for s in shards for d in s['real_pair_distances']];control=[d for s in shards for d in s['control_pair_distances']];rm=statistics.mean(real) if real else None;cm=statistics.mean(control) if control else None;effects=[]
    for s in shards:
        if s['real_pair_distances'] and s['control_pair_distances']:effects.append(statistics.mean(s['control_pair_distances'])-statistics.mean(s['real_pair_distances']))
    result={'version':3,'test_id':1,'test':'Original phonetic reconstruction through the exact mirrored Man Grid','status':'complete','shards':20,'correction':'This corrected run replaces ChatGPT implementations that used the A1-D4/16-state proxy and later the traced-image coordinate model. Those are implementation errors and are not evidence from the correct Man Grid.','source':x['source'],'grid':{'cells':spec['counts']['total_cells'],'transform_nodes':1,'upper':spec['upper'],'lower':spec['lower'],'all_rectangles_mirrored':True},'design':x['design'],'coverage':x['coverage'],'summary':{'languages':len(langs),'families':eligible,'segments_considered':len(params),'candidate_phonemes':len(uniq),'minimum_family_support_per_root_coordinate':minfam,'minimum_shard_support':minsh,'real_sibling_pairs':len(real),'unrelated_control_pairs':len(control),'mean_real_sibling_feature_distance':rm,'mean_unrelated_control_feature_distance':cm,'effect_size_cohen_d_control_minus_real':cohen_d(real,control),'shards_with_real_closer_than_control':sum(1 for e in effects if e>0),'shards_compared':len(effects),'mean_shard_advantage':statistics.mean(effects) if effects else None,'real_siblings_closer_than_unrelated_control':bool(rm is not None and cm is not None and rm<cm)},'original_phoneme_inventory':uniq,'failures_missing_data':{'unclassified_families_excluded':True,'inventories_under_10_segments_excluded':True,'marginal_segments_excluded':True,'tone_segments_excluded_from_reconstruction_inventory':True},'assumptions':['PHOIBLE distinctive features are a usable phonetic representation','within-family residual inventory variation can define two provisional sibling channels','feature midpoints are only candidate parent states, not attested ancestral forms','the transformative circle has no learned operator in Test 1; no circle behaviour is assumed beyond the mirrored coordinate hypothesis'],'boundary':'Experimental reconstruction under a falsifiable Man Grid hypothesis; candidate sounds are feature-space prototypes supported across families, not direct attestation of a single prehistoric language.'}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'phase':'merge',**result['summary'],'top_phonemes':[z['ipa'] for z in uniq[:40]]},ensure_ascii=False),flush=True)

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='phase',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
    {'prepare':prepare,'merge':merge}.get(a.phase,lambda:shard(a.id))()
if __name__=='__main__':main()
