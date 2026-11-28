"""Generate a reviewed, editable and fixture-executed NPC behaviour bundle."""
from __future__ import annotations
import argparse
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.game_project_generation import checked as check_level
from deepthort_local.npc_behaviour_runtime import Controller,route

SCHEMA='janus-grid-npc-behaviour-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'level','patrol','detection_distance','player_trace'}:
        raise ValueError('Expected level, patrol, detection distance and player trace')
    level=check_level(s['level']);w,h=level['width'],level['height'];walls=set(map(tuple,level['walls']))
    def point(p):
        if not isinstance(p,list) or len(p)!=2 or any(type(v) is not int for v in p) or not (0<=p[0]<w and 0<=p[1]<h) or tuple(p) in walls:
            raise ValueError('Invalid NPC or player cell')
        return tuple(p)
    patrol,trace,radius=s['patrol'],s['player_trace'],s['detection_distance']
    if not isinstance(patrol,list) or not 2<=len(patrol)<=16 or not isinstance(trace,list) or not 1<=len(trace)<=128 or type(radius) is not int or not 1<=radius<=32:
        raise ValueError('NPC behaviour exceeds bounds')
    cells=list(map(point,patrol))
    if len(set(cells))!=len(cells) or any(route(cells[0],p,w,h,walls) is None for p in cells[1:]):
        raise ValueError('Patrol must have distinct connected waypoints')
    for p in trace:
        if p is not None:point(p)
    return s

def generate(s):
    checked(s);controller=Controller(s);trace=[];previous=tuple(s['patrol'][0])
    walls=set(map(tuple,s['level']['walls']))
    for player in s['player_trace']:
        row=controller.step(player)
        x,y=row['position']
        if (x,y) in walls or not (0<=x<controller.w and 0<=y<controller.h) or abs(x-previous[0])+abs(y-previous[1])>1:
            raise ValueError('Invalid NPC movement')
        previous=(x,y);trace.append(row)
    runtime=Path(__file__).with_name('npc_behaviour_runtime.py').read_bytes()
    encode=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode('utf-8')
    entries={'behaviour.json':encode(s),'trace.json':encode(trace),'npc_controller.py':runtime,
             'README.txt':b'Python 3 grid NPC controller. Load behaviour.json; instantiate npc_controller.Controller(spec); call step(player_cell_or_None) each tick. trace.json records the supplied fixture. Adapt movement and rendering to your engine. Detection uses traversable path distance, not line of sight. No engine integration or native playtest verified.\n'}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(entries.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
    payload=buf.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() or set(z.namelist())!=set(entries) or any(z.read(n)!=v for n,v in entries.items()):
            raise ValueError('NPC bundle verification failed')
    return payload,{'ticks':len(trace),'modes':sorted({row['mode'] for row in trace}),
                    'movement_verified':True,'native_playtest_verified':False}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    _,r=generate(s)
    return plan,{'observations':r,'patrol':s['patrol'],'detection_distance':s['detection_distance'],'scope':'Portable Python NPC controller and verified fixture movement; no native engine integration.'}
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=generate(s);sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-grid-npc-result-v1','status':'npc_behaviour_generated','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid or unsatisfied reviewed NPC constraints'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
