"""Bounded independent sphere trajectories with analytic floor impacts."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.scene_composition import number,vector
SCHEMA='janus-physics-simulation-v1'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'gravity','duration_seconds','fps','floor_y','bodies'}:
        raise ValueError('Expected gravity, time, floor and reviewed sphere bodies')
    if not number(s['gravity'],.01,100) or not number(s['duration_seconds'],.1,30) or not number(s['floor_y'],-1000,1000) or type(s['fps']) is not int or not 10<=s['fps']<=120:
        raise ValueError('Simulation time or physical parameters outside bound')
    frames=math.ceil(s['duration_seconds']*s['fps'])
    bodies=s['bodies']
    if not isinstance(bodies,list) or not 1<=len(bodies)<=8 or (frames+1)*len(bodies)>20000:
        raise ValueError('Simulation sample bound exceeded')
    names=set()
    for b in bodies:
        if not isinstance(b,dict) or set(b)!={'name','radius','position','velocity','restitution'}:raise ValueError('Invalid sphere record')
        name=b['name']
        if not isinstance(name,str) or not 1<=len(name)<=64 or not name.strip() or any(not 32<=ord(c)<=126 for c in name) or name.casefold() in names:
            raise ValueError('Use unique bounded names')
        names.add(name.casefold())
        if not number(b['radius'],.01,100) or not vector(b['position'],3,-1000,1100) or not vector(b['velocity'],3,-100,100) or not number(b['restitution'],0,1):
            raise ValueError('Invalid reviewed sphere parameters')
        if b['position'][1]<s['floor_y']+b['radius']:raise ValueError('Sphere begins below floor')
    return s
def impact_time(height,vy,g):
    if height==0 and vy<=0:return 0.
    root=math.sqrt(vy*vy+2*g*height)
    return 2*height/(root-vy) if vy<0 else (vy+root)/g
def trajectory(body,s,times):
    g=s['gravity'];floor=s['floor_y']+body['radius'];x,y,z=body['position'];vx,vy,vz=body['velocity']
    height=y-floor;restitution=body['restitution']
    # Analytic ballistic segments. Rest after low-energy floor contact; no inter-body collisions.
    impacts=[];samples=[];elapsed=0.;resting=False;max_violation=0.
    for t in times:
        remaining=t-elapsed
        while remaining>1e-12 and not resting:
            tau=impact_time(height,vy,g)
            if tau>remaining:
                height+=vy*remaining-.5*g*remaining*remaining;vy-=g*remaining
                elapsed=t;remaining=0.
            else:
                before=vy-g*tau
                if before>1e-9:raise ValueError('Impact must be descending')
                elapsed+=tau;remaining=max(0.,t-elapsed);height=0.
                after=-before*restitution
                if after*after/(2*g)<=1e-6:after=0.;resting=True
                if len(impacts)>=2048:raise ValueError('Impact count exceeds bound')
                impacts.append({'time':elapsed,'vertical_before':before,'vertical_after':after})
                if after*after>before*before+1e-8:raise ValueError('Impact gained energy')
                vy=after
        if resting:elapsed=t;vy=0.;height=0.
        max_violation=max(max_violation,-height)
        if height<-1e-8:raise ValueError('Sphere penetrated floor')
        height=max(0.,height)
        samples.append({'time':t,'position':[x+vx*t,floor+height,z+vz*t],'velocity':[vx,vy,vz]})
    # All returned values finite; exact sample times and restitution bounds checked.
    if any(not all(math.isfinite(v) for v in (*row['position'],*row['velocity'])) or row['position'][1]<floor-1e-8 for row in samples):
        raise ValueError('Invalid trajectory sample')
    return {'name':body['name'],'radius':body['radius'],'samples':samples,'impacts':impacts,
        'maximum_numerical_floor_violation':max_violation,'resting_at_end':resting}
def simulate(s):
    checked(s);duration=s['duration_seconds'];fps=s['fps']
    times=[min(i/fps,duration) for i in range(math.ceil(duration*fps)+1)]
    if times[-1]!=duration or any(a>=b for a,b in zip(times,times[1:])):raise ValueError('Invalid sample timeline')
    tracks=[trajectory(b,s,times) for b in s['bodies']]
    doc={'schema':'janus-physics-trajectory-v1','units':{'length':'metres','time':'seconds'},'settings':s,
        'tracks':tracks,'floor_collision_checked':True,'inter_body_collisions':False,
        'rotational_dynamics':False,'friction':False,'native_engine_verified':False,
        'scope':'Independent sphere centers with constant downward gravity, frictionless horizontal velocity and analytic floor restitution; no mutual contacts or rigid-body engine.'}
    raw=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    if len(raw)>guard.MAX_OUTPUT or json.loads(raw)!=doc:raise ValueError('Trajectory roundtrip failed')
    return raw,{'body_count':len(tracks),'sample_count':len(times)*len(tracks),'duration_seconds':duration,
        'impact_count':sum(len(t['impacts']) for t in tracks),'floor_collision_checked':True,'trajectory_roundtrip_verified':True,
        'inter_body_collisions':False,'native_engine_verified':False,'scope':doc['scope']}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Independent sphere trajectories with analytic floor collisions; no mutual contacts.')
def execute(root,plan):
    s,dst,_=validate(root,plan);payload,r=simulate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-physics-simulation-result-v1','status':'floor_trajectory_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed physics specification or trajectory output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
