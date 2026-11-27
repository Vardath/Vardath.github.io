"""Bounded deterministic difficulty tuning for generated Godot grid levels."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked as check_level
from deepthort_local.autonomous_gameplay import route, MAX_STEPS

SCHEMA='janus-grid-balancing-v1'
MAX_CANDIDATES=32

def checked(s):
    if not isinstance(s,dict) or set(s)!={'level','target_steps'}:
        raise ValueError('Expected level and target_steps')
    check_level(s['level'])
    if len(s['level']['collectibles'])>8 or type(s['target_steps']) is not int or not 1<=s['target_steps']<=MAX_STEPS:
        raise ValueError('Choose up to eight collectibles and a bounded target')
    return s

def balance(s):
    checked(s);level=s['level'];target=s['target_steps']
    baseline=len(route(level));best=copy.deepcopy(level);best_steps=baseline;tested=0
    occupied={tuple(level['start']),tuple(level['goal']),*map(tuple,level['walls']),*map(tuple,level['collectibles'])}
    # Vary exactly one collectible by one adjacent tile. Preserve level geometry,
    # objective count and all other gameplay rules. No unbounded optimization.
    if baseline!=target:
        for i,(x,y) in enumerate(level['collectibles']):
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if tested>=MAX_CANDIDATES:break
                if not 0<=nx<level['width'] or not 0<=ny<level['height'] or (nx,ny) in occupied:continue
                candidate=copy.deepcopy(level);candidate['collectibles'][i]=[nx,ny];tested+=1
                try:steps=len(route(candidate))
                except ValueError:continue
                if abs(steps-target)<abs(best_steps-target):
                    best=candidate;best_steps=steps
                if best_steps==target:break
            if best_steps==target or tested>=MAX_CANDIDATES:break
    check_level(best)
    if len(route(best))!=best_steps:raise ValueError('Candidate route recheck failed')
    return {'schema':SCHEMA,'metric':'deterministic greedy route input steps',
            'target_steps':target,'baseline_steps':baseline,'candidate_steps':best_steps,
            'target_met':best_steps==target,'improved':abs(best_steps-target)<abs(baseline-target),
            'candidates_evaluated':tested,'candidate_level':best,
            'human_difficulty_verified':False,'native_engine_executed':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Search at most 32 adjacent collectible relocations, preserve geometry and objective count, and write a candidate/report for the explicit route-length target. No original edits, external engine execution or human difficulty claims.')

def execute(root,plan):
    s,dst,_=validate(root,plan);result=balance(s)
    result['reviewed_spec_sha256']=plan['guards'][0]['expected']
    payload=(json.dumps(result,sort_keys=True,indent=2)+'\n').encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'grid_balance_candidate_reported','output':plan['output'],'sha256':digest,**result}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Invalid or unverified bounded grid balance candidate'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
