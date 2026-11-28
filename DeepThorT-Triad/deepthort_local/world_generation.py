"""Reviewed deterministic region worlds built from the existing connected levels."""
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
from deepthort_local.level_generation import generate as generate_level
from deepthort_local.game_project_generation import checked as check_level

SCHEMA='janus-procedural-world-v1'
KEYS={'title','columns','rows','seed','region_width','region_height','cell_size','wall_percent','collectible_count','extra_links'}

def checked(s):
    if not isinstance(s,dict) or set(s)!=KEYS:
        raise ValueError('Expected world generation settings')
    if not isinstance(s['title'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,59}',s['title']):
        raise ValueError('Invalid world title')
    c,r,seed,w,h,cell,p,k,extra=(s[x] for x in ('columns','rows','seed','region_width','region_height','cell_size','wall_percent','collectible_count','extra_links'))
    if any(type(x) is not int for x in (c,r,seed,w,h,cell,p,k,extra)) or not (2<=c<=4 and 2<=r<=4 and 0<=seed<2**32 and 5<=w<=16 and 5<=h<=12 and cell in (24,32,40) and 0<=p<=40 and 1<=k<=16 and 0<=extra<=(c-1)*(r-1)):
        raise ValueError('Invalid world bounds')
    if w*h-w*h*p//100<k+2:
        raise ValueError('Too few cells for objectives')
    return s

def generate(s):
    checked(s)
    c,r,seed=s['columns'],s['rows'],s['seed']
    ids=list(range(c*r))
    def score(purpose, *values):
        return hashlib.sha256((':'.join(map(str,(seed,purpose,*values)))).encode('ascii')).digest()
    regions=[]
    for i in ids:
        x,y=i%c,i//c
        biome=('plains','forest','rocky','wetland')[score('biome',i)[0]%4]
        local_seed=(seed+i*2654435761)%(2**32)
        spec={'title':f"{s['title']} Region {i+1}",'width':s['region_width'],'height':s['region_height'],
              'cell_size':s['cell_size'],'seed':local_seed,'wall_percent':s['wall_percent'],
              'collectible_count':s['collectible_count'],'minimum_goal_distance':s['region_width']+s['region_height']-2}
        raw,receipt=generate_level(spec)
        level=check_level(json.loads(raw))
        if not receipt['all_objectives_reachable']:
            raise ValueError('Invalid region objectives')
        regions.append({'id':i,'coordinate':[x,y],'biome':biome,'seed':local_seed,'level':level})
    edges=[(i,i+1) for i in ids if i%c<c-1]+[(i,i+c) for i in ids if i//c<r-1]
    edges.sort(key=lambda e:(score('route',*e),e))
    groups=list(ids)
    links=[];spares=[]
    for a,b in edges:
        if groups[a]==groups[b]:
            spares.append((a,b));continue
        old,new=groups[b],groups[a]
        groups=[new if g==old else g for g in groups]
        links.append((a,b))
    links=sorted(links+spares[:s['extra_links']])
    adjacency={i:set() for i in ids}
    for a,b in links:
        if a==b or b in adjacency[a] or abs(a%c-b%c)+abs(a//c-b//c)!=1:
            raise ValueError('Invalid region link')
        adjacency[a].add(b);adjacency[b].add(a)
    seen={0};queue=deque([0])
    while queue:
        for j in adjacency[queue.popleft()]-seen:
            seen.add(j);queue.append(j)
    if seen!=set(ids) or len(links)!=len(ids)-1+s['extra_links']:
        raise ValueError('World connectivity verification failed')
    world={'schema':SCHEMA,'title':s['title'],'seed':seed,'columns':c,'rows':r,
           'start_region':0,'regions':regions,'links':[list(e) for e in links]}
    payload=(json.dumps(world,sort_keys=True,indent=2)+'\n').encode('utf-8')
    if json.loads(payload)!=world:raise ValueError('World JSON roundtrip failed')
    return payload,{'regions':len(regions),'links':len(links),'all_regions_connected':True,
                    'all_region_objectives_reachable':True,'native_playtest_verified':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    _,r=generate(s)
    return plan,dict(s,observations=r,scope='Editable world graph and independent connected grid level specifications; no engine integration or travel simulation.')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-procedural-world-result-v1','status':'connected_world_generated','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid or unsatisfied reviewed world constraints'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
