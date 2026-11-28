"""Reviewed multi-marker 2D capture for animation references; no pose estimation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode,MAX_RENDER_RGB
from deepthort_local.video_motion_tracking import checked as check_patch,track
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-motion-capture-v1'
EXTRA=('video','.mp4')
MAX_WORK=30_000_000

def patch_spec(s,marker):
    return {k:s[k] for k in ('video','start_frame','end_frame','radius','max_error')}|{'box':marker['box']}

def intersects(a,b):
    return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','start_frame','end_frame','radius','max_error','markers'}:
        raise ValueError('Expected reviewed video interval and named marker patches')
    markers=s['markers']
    if not isinstance(markers,list) or not 2<=len(markers)<=8:raise ValueError('Use two to eight distinct markers')
    names=set();boxes=[];work=0
    for m in markers:
        if not isinstance(m,dict) or set(m)!={'name','box'} or not isinstance(m['name'],str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',m['name']):
            raise ValueError('Use a short ASCII marker label')
        if m['name'].casefold() in names:raise ValueError('Duplicate marker label')
        names.add(m['name'].casefold());check_patch(patch_spec(s,m));box=m['box']
        if any(intersects(box,other) for other in boxes):raise ValueError('Initial marker patches overlap')
        boxes.append(box)
        work+=(s['end_frame']-s['start_frame'])*(2*s['radius']+1)**2*box[2]*box[3]*3
    if work>MAX_WORK:raise ValueError('Combined marker comparison budget exceeded')
    return s

def capture(raw,size,s,fps):
    s=checked(s);n=s['end_frame']-s['start_frame']
    if type(fps) is not int or fps not in (24,25,30):raise ValueError('Unsupported frame rate')
    tracks=[track(raw,size,patch_spec(s,m)) for m in s['markers']]
    rows=[];stop=None
    for i in range(n):
        if any(i>=len(t) for t in tracks):
            stop={'frame':s['start_frame']+i,'reason':'marker unavailable'};break
        observations=[t[i] for t in tracks]
        lost=[m['name'] for m,row in zip(s['markers'],observations) if row['box'] is None]
        if lost:
            stop={'frame':s['start_frame']+i,'reason':'marker lost or ambiguous','markers':lost};break
        boxes=[row['box'] for row in observations]
        if any(intersects(box,other) for j,box in enumerate(boxes) for other in boxes[:j]):
            stop={'frame':s['start_frame']+i,'reason':'marker patches overlap'};break
        points=[]
        for marker,row in zip(s['markers'],observations):
            x,y,w,h=row['box']
            points.append({'name':marker['name'],'center_xy':[x+(w-1)/2,y+(h-1)/2],
                           'box':row['box'],'mean_absolute_error':row['mean_absolute_error']})
        rows.append({'frame':s['start_frame']+i,'time_seconds':i/fps,'markers':points})
    return {'samples':rows,'stop':stop,'complete_interval':len(rows)==n,
            'coordinate_system':'image pixels, x right, y down; time relative to reviewed interval',
            'depth_recovered':False,'skeleton_inferred':False,'identity_verified':False,
            'occlusion_recovery_supported':False,'native_animation_playback_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing source and installed codec guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    if tuple(plan['guards'][2:])!=installed(root):raise ValueError('Reviewed codecs changed')
    return s,dst,src

def operation(root,plan,render=False):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    tools=plan['guards'][2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-marker-capture-',dir=dst.parent) as tmp:
        path=Path(tmp)/'source.mp4';path.write_bytes(raw)
        meta=probe(fp,path);w,h=meta['width'],meta['height'];n=s['end_frame']-s['start_frame']
        if s['end_frame']>meta['frames'] or n*w*h*3>MAX_RENDER_RGB:
            raise ValueError('Frame interval exceeds source or buffer bound')
        for m in s['markers']:
            x,y,bw,bh=m['box']
            if x+bw>w or y+bh>h:raise ValueError('Marker outside source frame')
        report={'schema':SCHEMA,'source_sha256':hashlib.sha256(raw).hexdigest(),'source_format':meta,
                'method':'multiple fixed RGB templates with bounded local translation search'}
        if render:
            rgb=decode(ff,path,s['start_frame'],s['end_frame'],w,h)
            report.update(capture(rgb,(w,h),s,meta['fps']),decoded_rgb_sha256=hashlib.sha256(rgb).hexdigest())
        verify_guards(tools)
        return report

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    plan['guards'].extend(installed(root))
    return plan,dict(s,observations=operation(root,plan),scope='Track 2–8 reviewed markers in 2D. Export synchronized partial or complete trajectories; stop at lost, ambiguous or overlapping markers. No inferred skeleton, identity or 3D reconstruction.')

def execute(root,plan):
    _,dst,_=validate(root,plan);r=operation(root,plan,True)
    payload=(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode('ascii')
    if json.loads(payload)!=r:raise ValueError('Trajectory JSON roundtrip failed')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'marker_trajectories_saved' if r['complete_interval'] else 'partial_marker_trajectories_saved',
            'output':plan['output'],'sha256':digest,'samples':len(r['samples']),'complete_interval':r['complete_interval'],'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed marker capture unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
