"""Seeded, connected grid level generation for the reviewed Godot game scaffold."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked as game_checked

SCHEMA='janus-game-level-v1'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','width','height','cell_size','seed','wall_percent','collectible_count','minimum_goal_distance'}:
        raise ValueError('Expected seeded grid level settings')
    if not isinstance(s['title'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}',s['title']):raise ValueError('Invalid game title')
    w,h,c,seed,p,k,d=(s[x] for x in ('width','height','cell_size','seed','wall_percent','collectible_count','minimum_goal_distance'))
    if any(type(x) is not int for x in (w,h,c,seed,p,k,d)) or not 5<=w<=32 or not 5<=h<=24 or c not in (24,32,40) or w*c>1280 or h*c+48>960 or not 0<=seed<2**32 or not 0<=p<=45 or not 1<=k<=32 or not 1<=d<=w+h-2:
        raise ValueError('Invalid level generation bounds')
    if w*h-w*h*p//100<k+2:raise ValueError('Not enough open cells for objectives')
    return s

def distances(start,open_cells):
    seen={start:0};q=deque([start])
    while q:
        x,y=q.popleft()
        for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if p in open_cells and p not in seen:
                seen[p]=seen[(x,y)]+1;q.append(p)
    return seen

def generate(s):
    checked(s);w,h,seed=s['width'],s['height'],s['seed']
    cells={(x,y) for y in range(h) for x in range(w)}
    start=(0,0);goal=(w-1,h-1)
    def rank(p,purpose):
        return (hashlib.sha256(f'{seed}:{purpose}:{p[0]}:{p[1]}'.encode('ascii')).digest(),p)
    open_cells=set(cells);wall_count=w*h*s['wall_percent']//100
    for p in sorted(cells-{start,goal},key=lambda v:rank(v,'wall')):
        if len(cells)-len(open_cells)>=wall_count:break
        candidate=open_cells-{p}
        if len(distances(start,candidate))==len(candidate):open_cells=candidate
    dist=distances(start,open_cells)
    if len(dist)!=len(open_cells) or len(cells)-len(open_cells)!=wall_count or dist[goal]<s['minimum_goal_distance']:
        raise ValueError('Could not meet exact connected-level constraints')
    candidates=sorted(open_cells-{start,goal},key=lambda v:rank(v,'item'))
    level={k:s[k] for k in ('title','width','height','cell_size')}
    level.update(start=list(start),goal=list(goal),walls=[list(v) for v in sorted(cells-open_cells)],
                 collectibles=[list(v) for v in candidates[:s['collectible_count']]])
    game_checked(level)
    payload=(json.dumps(level,sort_keys=True,indent=2)+'\n').encode('utf-8')
    if json.loads(payload)!=level:raise ValueError('Level JSON roundtrip failed')
    return payload,{'seed':seed,'walls':wall_count,'open_cells':len(open_cells),
        'goal_shortest_path_steps':dist[goal],'collectibles':len(level['collectibles']),
        'all_open_cells_connected':True,'all_objectives_reachable':True,'native_playtest_verified':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    _,r=generate(s)
    return plan,dict(s,observations=r,scope='Deterministic connected grid level compatible with the reviewed game project generator; no engine execution.')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-game-level-result-v1','status':'connected_level_generated','output':plan['output'],
        'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid or unsatisfied reviewed level constraints'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
