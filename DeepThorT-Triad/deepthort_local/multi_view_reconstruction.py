"""Reviewed sparse reconstruction from three to five calibrated rectified views.

Parallel cameras share focal length, principal point and orientation. Baselines
are supplied by the owner. This is not automatic pose estimation or meshing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import photogrammetry as stereo
from deepthort_local.action_guards import snapshot_file

SCHEMA='deepthortriad-multi-view-reconstruction-v1'
MATCH=('focal_px','min_disparity','max_disparity','step','max_error','min_margin')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'reference','views',*MATCH,'max_depth_error_m','max_reprojection_px'}:
        raise ValueError('Expected reference, calibrated views and matching tolerances')
    views=s['views']
    if not isinstance(s['reference'],str) or not s['reference'] or not isinstance(views,list) or not 2<=len(views)<=4:
        raise ValueError('Choose reference and two to four additional views')
    names={s['reference'].casefold()};baselines=set()
    for v in views:
        if not isinstance(v,dict) or set(v)!={'image','baseline_m'} or not isinstance(v['image'],str) or not v['image'] or v['image'].casefold() in names:
            raise ValueError('Expected distinct calibrated image paths')
        stereo.checked(pair_spec(s,v))
        if v['baseline_m'] in baselines:raise ValueError('Use distinct positive camera baselines')
        names.add(v['image'].casefold());baselines.add(v['baseline_m'])
    for k,lo,hi in (('max_depth_error_m',.0001,2),('max_reprojection_px',.1,2)):
        x=s[k]
        if type(x) not in (int,float) or not math.isfinite(x) or not lo<=x<=hi:
            raise ValueError('Invalid '+k)
    return s

def pair_spec(s,v):
    return dict({k:s[k] for k in MATCH},left=s['reference'],right=v['image'],baseline_m=v['baseline_m'])

def dimensions(raw,s):
    if len(raw)!=len(s['views'])+1:raise ValueError('Image count mismatch')
    shapes=[stereo.gray(x)[:2] for x in raw]
    if any(x!=shapes[0] for x in shapes):raise ValueError('View dimensions differ')
    w,h=shapes[0]
    count=len(range(2+s['max_disparity'],w-2,s['step']))*len(range(2,h-2,s['step']))
    if not count or count*len(s['views'])*2*(s['max_disparity']-s['min_disparity']+1)*25>stereo.MAX_WORK:
        raise ValueError('Combined matching work exceeds bound')
    return w,h

def reconstruct(raw,s):
    checked(s);w,h=dimensions(raw,s);f=s['focal_px'];cx=(w-1)/2;cy=(h-1)/2
    reports=[stereo.reconstruct(raw[0],image,pair_spec(s,v)) for image,v in zip(raw[1:],s['views'])]
    maps=[{tuple(q['left_xy']):q for q in r['points']} for r in reports]
    common=set(maps[0]).intersection(*(set(m) for m in maps[1:]))
    points=[];rejected=0
    for x,y in sorted(common,key=lambda p:(p[1],p[0])):
        obs=[m[(x,y)] for m in maps];depths=[q['xyz_m'][2] for q in obs]
        z=statistics.median(depths)
        if max(depths)-min(depths)>s['max_depth_error_m']:
            rejected+=1;continue
        X=(x-cx)*z/f;Y=(cy-y)*z/f
        errs=[abs(f*(X-v['baseline_m'])/z+cx-q['right_xy'][0]) for v,q in zip(s['views'],obs)]
        if max(errs)>s['max_reprojection_px']:
            rejected+=1;continue
        points.append({'reference_xy':[x,y],'xyz_m':[X,Y,z],
                       'views':[{'image_index':i+1,'xy':q['right_xy'],'depth_m':depths[i],
                                 'reprojection_error_px':errs[i]} for i,q in enumerate(obs)]})
    if not points:raise ValueError('No consistent points observed in every view')
    return {'schema':SCHEMA,'dimensions':[w,h],'coordinate_system':'reference camera: x right, y up, z forward, meters',
            'calibration':{'focal_px':f,'principal_point_px':[cx,cy],'baselines_m':[v['baseline_m'] for v in s['views']]},
            'points':points,'views_required':len(raw),'common_candidates':len(common),'rejected_consensus':rejected,
            'pair_point_counts':[len(m) for m in maps],'max_depth_error_m':s['max_depth_error_m'],
            'max_reprojection_px':s['max_reprojection_px'],'calibration_independently_verified':False,
            'camera_pose_estimated':False,'mesh_generated':False,'metric_accuracy_verified':False}

def input_paths(root,s,exclude):
    paths=[guard.path_for(Path(root).resolve(strict=True),name,exclude,{'.png'},exists=True)
           for name in [s['reference'],*(v['image'] for v in s['views'])]]
    if any(x.stat().st_size>guard.MAX_INPUT for x in paths) or any(x.samefile(y) for i,x in enumerate(paths) for y in paths[:i]):
        raise ValueError('Oversize or aliased view')
    return paths

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 4<=len(plan['guards'])<=6:
        raise ValueError('Invalid multi-view approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    paths=input_paths(root,s,plan['exclude'])
    if [snapshot_file(x) for x in paths]!=plan['guards'][1:]:raise ValueError('Reviewed views changed')
    return s,dst,paths

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    paths=input_paths(root,s,plan['exclude']);plan['guards'].extend(snapshot_file(x) for x in paths)
    validate(root,plan)
    raw=[guard.exact(x,g,guard.MAX_INPUT) for x,g in zip(paths,plan['guards'][1:])]
    size=dimensions(raw,s)
    return plan,dict(s,dimensions=list(size),scope='Sparse measured-disparity fusion for owner-calibrated parallel rectified cameras; every accepted point must agree across all views. No automatic calibration, dense mesh or independent accuracy certification.')

def execute(root,plan):
    s,dst,paths=validate(root,plan)
    raw=[guard.exact(x,g,guard.MAX_INPUT) for x,g in zip(paths,plan['guards'][1:])]
    report=reconstruct(raw,s);report['source_sha256']=[hashlib.sha256(x).hexdigest() for x in raw]
    payload=(json.dumps(report,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode('ascii')
    if json.loads(payload)!=report:raise ValueError('Point cloud roundtrip failed')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'multi_view_points_saved','output':plan['output'],'sha256':digest,
            'point_count':len(report['points']),'views_required':report['views_required'],'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
