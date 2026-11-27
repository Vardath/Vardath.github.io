"""Transfer reviewed local rotation tracks between explicitly corresponding skeletons."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import skeletal_animation as animation,character_rigging as rig,scene_composition as scene
from deepthort_local.mesh_geometry import dot,cross
SCHEMA='janus-animation-retargeting-v1'
EXTRA=('mesh','.obj')

def normalized(q):
    length=math.sqrt(dot(q,q))
    return [x/length for x in q]
def multiply(a,b):
    c=cross(a[:3],b[:3])
    return [a[3]*b[i]+b[3]*a[i]+c[i] for i in range(3)]+[a[3]*b[3]-dot(a[:3],b[:3])]
def rotate_basis(q,b):
    b=normalized(b);q=normalized(q)
    return normalized(multiply(multiply(b,q),[-b[0],-b[1],-b[2],b[3]]))
def transform(s):
    if not isinstance(s,dict) or set(s)!={'mesh','max_position_error','joints','source_joints','source_tracks','mapping','name'}:
        raise ValueError('Expected target mesh and skeleton, source skeleton/tracks and explicit mapping')
    target=animation.rig_spec(s)
    rig.checked(target)
    rig.checked(dict(target,joints=s['source_joints']))
    src=s['source_joints'];dst=s['joints']
    animation.tracks_checked(s['source_tracks'],len(src))
    mapping=s['mapping']
    if not isinstance(mapping,list) or not 1<=len(mapping)<=min(len(src),len(dst)):raise ValueError('Invalid mapping size')
    m={};used=set()
    for row in mapping:
        if not isinstance(row,dict) or set(row)!={'source','target','basis_xyzw'}:raise ValueError('Invalid mapping row')
        a,b,q=row['source'],row['target'],row['basis_xyzw']
        if type(a) is not int or type(b) is not int or not 0<=a<len(src) or not 0<=b<len(dst) or a in m or b in used:
            raise ValueError('Mapping must be one to one')
        if not scene.vector(q,4,-1,1) or abs(dot(q,q)-1)>1e-6:raise ValueError('Expected normalized basis quaternion')
        m[a]=(b,q);used.add(b)
    for a,(b,_) in m.items():
        sp,tp=src[a]['parent'],dst[b]['parent']
        if sp is None:
            if tp is not None:raise ValueError('Root correspondence mismatch')
        elif sp not in m or m[sp][0]!=tp:raise ValueError('Mapped parent correspondence required')
    tracks=[]
    for t in s['source_tracks']:
        a=t['joint']
        if a not in m:raise ValueError('Source track missing target mapping')
        b,q=m[a]
        tracks.append({'joint':b,'times':list(t['times']),
            'rotations_xyzw':[rotate_basis(x,q) for x in t['rotations_xyzw']]})
    result=dict(target,name=s['name'],tracks=tracks)
    animation.checked(result)
    return result
def checked(s):
    transform(s)
    return s
def retarget(raw,s):
    t=transform(s);payload,r=animation.animate(raw,t)
    return payload,{**r,'mapped_joints':len(s['mapping']),'source_track_count':len(s['source_tracks']),
        'target_track_count':len(t['tracks']),'parent_correspondence_verified':True,
        'basis_conjugation_applied':True,'automatic_correspondence_verified':False,
        'foot_contact_verified':False,'proportion_compensation_verified':False,
        'scope':'Explicit one-to-one hierarchy and local rotation basis transfer only; no IK, translation, root motion, contact or native playback acceptance.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
    validate(root,plan)
    return plan,dict(s,scope='Transfer local rotations via explicit joint correspondence and basis; no IK or automatic discovery.')
def execute(root,plan):
    s,dst,path=validate(root,plan)
    out,r=retarget(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-animation-retargeting-result-v1','status':'retargeted_animation_structure_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed target mesh, source tracks or joint correspondence'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
