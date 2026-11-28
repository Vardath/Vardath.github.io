"""Bounded calibrated rectified stereo point reconstruction from local photographs."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.texture_pixels import decode

SCHEMA='janus-calibrated-stereo-v1'
MAX_WORK=25_000_000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'left','right','focal_px','baseline_m','min_disparity','max_disparity','step','max_error','min_margin'}:
        raise ValueError('Expected rectified stereo pair and explicit calibration/matching controls')
    if any(not isinstance(s[k],str) for k in ('left','right')) or s['left'].casefold()==s['right'].casefold():
        raise ValueError('Select two distinct PNGs')
    for k,lo,hi in (('focal_px',20,5000),('baseline_m',.001,10)):
        v=s[k]
        if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Invalid '+k)
    for k,lo,hi in (('min_disparity',1,64),('max_disparity',2,64),('step',4,32),('max_error',0,30),('min_margin',1,100)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid '+k)
    if s['min_disparity']>=s['max_disparity']:raise ValueError('Invalid disparity range')
    return s

def gray(raw):
    w,h,mode,data=decode(raw,('L','RGB'))
    if not 24<=w<=640 or not 12<=h<=480:raise ValueError('Use 24–640 by 12–480 pixel photographs')
    if mode=='RGB':data=bytes((77*r+150*g+29*b+128)//256 for r,g,b in zip(data[::3],data[1::3],data[2::3]))
    return w,h,data

def patch(data,w,x,y):
    return b''.join(data[(y+j)*w+x-2:(y+j)*w+x+3] for j in range(-2,3))

def match(template,other,w,x,y,s,direction):
    candidates=[]
    for d in range(s['min_disparity'],s['max_disparity']+1):
        q=x+direction*d
        if not 2<=q<w-2:continue
        sample=patch(other,w,q,y)
        error=sum(abs(a-b) for a,b in zip(template,sample))
        candidates.append((error,d))
    candidates.sort()
    if len(candidates)<2 or candidates[0][0]>25*s['max_error'] or candidates[1][0]-candidates[0][0]<25*s['min_margin']:
        return None
    return candidates[0]

def reconstruct(left,right,s):
    s=checked(s);w,h,a=gray(left);rw,rh,b=gray(right)
    if (w,h)!=(rw,rh):raise ValueError('Stereo dimensions differ')
    xs=range(2+s['max_disparity'],w-2,s['step']);ys=range(2,h-2,s['step'])
    total=len(xs)*len(ys)
    if not total or total*2*(s['max_disparity']-s['min_disparity']+1)*25>MAX_WORK:
        raise ValueError('Matching work exceeds bound or no valid grid')
    points=[];f=s['focal_px'];baseline=s['baseline_m'];cx=(w-1)/2;cy=(h-1)/2
    for y in ys:
        for x in xs:
            t=patch(a,w,x,y)
            if max(t)-min(t)<12:continue
            m=match(t,b,w,x,y,s,-1)
            if m is None:continue
            error,d=m;rx=x-d
            reverse=match(patch(b,w,rx,y),a,w,rx,y,s,1)
            if reverse is None or reverse[1]!=d:continue
            z=f*baseline/d
            points.append({'left_xy':[x,y],'right_xy':[rx,y],'xyz_m':[(x-cx)*z/f,(cy-y)*z/f,z],
                           'disparity_px':d,'mean_absolute_error':error/25})
    if not points:raise ValueError('No mutually consistent textured matches')
    return {'schema':SCHEMA,'dimensions':[w,h],'coordinate_system':'left camera, x right, y up, z forward, meters',
            'calibration':{'focal_px':f,'baseline_m':baseline,'principal_point_px':[cx,cy]},
            'points':points,'grid_samples':total,'rejected_samples':total-len(points),
            'automatic_correspondence':True,'mutual_disparity_check':True,'calibration_independently_verified':False,
            'rectification_verified':False,'mesh_generated':False,'metric_accuracy_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Missing reviewed stereo inputs')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    paths=[guard.path_for(Path(root).resolve(strict=True),s[k],plan['exclude'],{'.png'},exists=True) for k in ('left','right')]
    if any(x.stat().st_size>guard.MAX_INPUT for x in paths) or [snapshot_file(x) for x in paths]!=plan['guards'][1:]:
        raise ValueError('Reviewed stereo images changed')
    return s,dst,paths

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    paths=[guard.path_for(Path(root).resolve(strict=True),s[k],plan['exclude'],{'.png'},exists=True) for k in ('left','right')]
    if any(x.stat().st_size>guard.MAX_INPUT for x in paths):raise ValueError('Image exceeds byte bound')
    plan['guards'].extend(snapshot_file(x) for x in paths)
    validate(root,plan)
    dimensions=[gray(guard.exact(x,g,guard.MAX_INPUT))[:2] for x,g in zip(paths,plan['guards'][1:])]
    if dimensions[0]!=dimensions[1]:raise ValueError('Stereo dimensions differ')
    return plan,dict(s,dimensions=list(dimensions[0]),scope='Owner-calibrated rectified stereo pair, sparse automatic mutual patch matching and 3D points. No camera calibration, mesh, dense reconstruction or independent accuracy claim.')

def execute(root,plan):
    s,dst,paths=validate(root,plan)
    raw=[guard.exact(x,g,guard.MAX_INPUT) for x,g in zip(paths,plan['guards'][1:])]
    report=reconstruct(*raw,s)
    report['source_sha256']=[hashlib.sha256(x).hexdigest() for x in raw]
    payload=(json.dumps(report,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode('ascii')
    if json.loads(payload)!=report:raise ValueError('Point cloud JSON verification failed')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'stereo_points_saved','output':plan['output'],'sha256':digest,
            'point_count':len(report['points']),'rejected_samples':report['rejected_samples'],'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed stereo reconstruction unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
