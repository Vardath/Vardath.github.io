#!/usr/bin/env python3
from __future__ import annotations
import argparse,gzip,json,math,statistics
from collections import defaultdict
from pathlib import Path
import man_grid_v2_core as C

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
    spec,params,langs,P=C.load_phoible()
    branches,eligible,axis=C.assign_branches(langs,params)
    payload={
      'version':2,'spec':spec,'projection':P,'features':C.FEATURES,'eligible_families':eligible,
      'sibling_axis':axis,
      'params':{p:{'name':q['name'],'class':q['class'],'features':q['features'],'grid':q['grid']} for p,q in params.items()},
      'langs':{lid:{'name':l['name'],'iso':l['iso'],'family':l['family'],'branch':branches.get(lid),'inventory':sorted(l['inventory'])} for lid,l in langs.items() if branches.get(lid)},
      'source':{'dataset':'PHOIBLE CLDF','commit':C.PH,'marginal_segments_excluded':True,'tone_segments_excluded':True},
      'design':{
        'grid':'exact 691-cell Man Grid from data/man-grid-structure-v1.json',
        'flow':'D5 -> D4 -> D3 -> D2 -> D1 -> transformative circle -> U5 -> U4 -> U3 -> U2 -> U1',
        'phonetic_coordinates':'two unsupervised principal axes from the complete PHOIBLE distinctive-feature vectors; quantized independently at each exact grid resolution',
        'sibling_split':'languages are centered within family and split left/right by the first global axis of within-family inventory-centroid variation; no modern language is preselected as an anchor',
        'ancestor_sound':'mutual-nearest left/right branch sounds are midpointed in full PHOIBLE feature space; family-balanced midpoint evidence is accumulated in lower D5 cells',
        'control':'same branch procedure with right branches deterministically rotated to a different family inside each execution shard',
        'shards':N
      }
    }
    dumpgz(PREP,payload)
    print(json.dumps({'phase':'prepare','languages':len(payload['langs']),'segments':len(params),'eligible_families':len(eligible),'shards':N}),flush=True)


def unpack():
    x=loadgz(PREP)
    params={p:{**q} for p,q in x['params'].items()}
    langs={lid:{**l,'inventory':set(l['inventory'])} for lid,l in x['langs'].items()}
    return x,params,langs


def fam_struct(fam,lids,langs,params):
    L=[x for x in lids if langs[x]['branch']=='L'];R=[x for x in lids if langs[x]['branch']=='R']
    if not L or not R:return None
    A=C.consensus_inventory(L,langs,.5);B=C.consensus_inventory(R,langs,.5)
    pairs=C.mutual_pairs(A,B,params)
    return {'L':L,'R':R,'A':A,'B':B,'pairs':pairs}


def shard(i):
    x,params,langs=unpack();P=x['projection'];spec=x['spec']
    by=defaultdict(list)
    for lid,l in langs.items():by[l['family']].append(lid)
    fams=[f for f in x['eligible_families'] if C.h64('mgv2-original-phonetics',f)%N==i]
    structs={f:fam_struct(f,by[f],langs,params) for f in fams}
    structs={f:s for f,s in structs.items() if s and s['pairs']}
    obs=[];real_d=[]
    for fam,s in structs.items():
        best={}
        for a,b,d in s['pairs']:
            va=params[a]['features'];vb=params[b]['features'];mid=[(u+v)/2 for u,v in zip(va,vb)]
            g=C.grid_paths(mid,P,spec);cell=g['lower'][0]  # D5 fine ancestral cell
            q=(d,a,b,mid,g)
            if cell not in best or q[0]<best[cell][0]:best[cell]=q
        for cell,(d,a,b,mid,g) in best.items():
            real_d.append(d)
            obs.append({'family':fam,'cell':cell,'left':a,'right':b,'left_ipa':params[a]['name'],'right_ipa':params[b]['name'],'distance':d,'mid':mid,'grid':g})
    # unrelated-family null: rotate each family's right consensus to the next family in this shard.
    control=[];ordered=sorted(structs)
    if len(ordered)>1:
        for j,f in enumerate(ordered):
            g=ordered[(j+1)%len(ordered)]
            A=structs[f]['A'];B=structs[g]['B']
            for a,b,d in C.mutual_pairs(A,B,params):control.append(d)
    out={'shard':i,'families':len(structs),'family_names':ordered,'observations':obs,'real_pair_distances':real_d,'control_pair_distances':control}
    WORK.mkdir(parents=True,exist_ok=True);(WORK/f'result-{i:02d}.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'phase':'shard','shard':i,'families':len(structs),'observations':len(obs),'real_pairs':len(real_d),'control_pairs':len(control)}),flush=True)


def merge():
    x,params,langs=unpack();P=x['projection'];spec=x['spec']
    shards=[json.loads((WORK/f'result-{i:02d}.json').read_text(encoding='utf-8')) for i in range(N)]
    obs=[o|{'shard':s['shard']} for s in shards for o in s['observations']]
    eligible=sum(s['families'] for s in shards)
    groups=defaultdict(list)
    for o in obs:groups[o['cell']].append(o)
    minfam=max(6,math.ceil(max(1,eligible)*.015));minsh=5
    candidates=[]
    all_vectors={p:q['features'] for p,q in params.items()}
    for cell,rows in groups.items():
        fams={r['family'] for r in rows};shs={r['shard'] for r in rows}
        if len(fams)<minfam or len(shs)<minsh:continue
        mean=C.centroid([r['mid'] for r in rows]);pid=min(all_vectors,key=lambda p:(C.dist(mean,all_vectors[p]),params[p]['name']))
        grid=C.grid_paths(mean,P,spec)
        survival=0
        for leftout in range(N):
            rr=[r for r in rows if r['shard']!=leftout]
            if len({r['family'] for r in rr})>=minfam and len({r['shard'] for r in rr})>=minsh:survival+=1
        if survival<16:continue
        candidates.append({
          'ipa':params[pid]['name'],'parameter_id':pid,'root_cell':cell,'root_path':grid['lower'],'sibling_left_path':grid['upper_left'],'sibling_right_path':grid['upper_right'],
          'family_support':len(fams),'shard_support':len(shs),'leave_one_shard_out_survival':survival,
          'mean_sibling_feature_distance':statistics.mean(r['distance'] for r in rows),'prototype_feature_distance':C.dist(mean,params[pid]['features']),
          'examples':[{'family':r['family'],'left':r['left_ipa'],'right':r['right_ipa']} for r in sorted(rows,key=lambda z:(z['distance'],z['family']))[:8]]
        })
    # A phoneme inventory contains unique sounds; when adjacent ancestral cells choose the same IPA, keep the stronger cell.
    candidates.sort(key=lambda r:(-r['family_support'],-r['shard_support'],r['prototype_feature_distance'],r['ipa']))
    uniq=[];seen=set()
    for r in candidates:
        if r['ipa'] in seen:continue
        seen.add(r['ipa']);uniq.append(r)
    real=[d for s in shards for d in s['real_pair_distances']];control=[d for s in shards for d in s['control_pair_distances']]
    rm=statistics.mean(real) if real else None;cm=statistics.mean(control) if control else None
    result={
      'version':2,'test':'Original phonetic sounds through the exact Man Grid — 20 shards','status':'complete','shards':N,
      'correction':'This test replaces the earlier ChatGPT-built A1-D4/16-state original-phonetics reconstruction. The earlier implementation did not use the actual Man Grid and is not treated as an exact-Man-Grid result.',
      'source':x['source'],'grid':{'cells':spec['counts']['total_cells'],'upper':spec['upper'],'transform':spec['transform'],'lower':spec['lower']},'design':x['design'],
      'summary':{'languages':len(langs),'families':eligible,'segments_considered':len(params),'candidate_phonemes':len(uniq),'minimum_family_support_per_root_cell':minfam,'minimum_shard_support':minsh,'real_sibling_pairs':len(real),'unrelated_control_pairs':len(control),'mean_real_sibling_feature_distance':rm,'mean_unrelated_control_feature_distance':cm,'real_siblings_closer_than_unrelated_control':bool(rm is not None and cm is not None and rm<cm)},
      'original_phoneme_inventory':uniq,
      'boundary':'This is an experimental family-balanced phonetic reconstruction under the exact Man Grid bifurcation hypothesis. It reconstructs feature-space prototypes supported across unrelated language families; it is not direct historical attestation of a single prehistoric language.'
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':'merge',**result['summary'],'top_phonemes':[x['ipa'] for x in uniq[:40]]},ensure_ascii=False),flush=True)


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='phase',required=True);sp.add_parser('prepare');s=sp.add_parser('shard');s.add_argument('--id',type=int,required=True);sp.add_parser('merge');a=ap.parse_args()
    if a.phase=='prepare':prepare()
    elif a.phase=='shard':shard(a.id)
    else:merge()
if __name__=='__main__':main()
