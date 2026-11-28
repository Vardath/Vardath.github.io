"""Bounded local translation tracking of a user-selected image patch.

No object identity, surveillance, occlusion recovery or semantic recognition.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-video-motion-track-v1'
EXTRA=('video','.mp4')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','start_frame','end_frame','box','radius','max_error'} or not isinstance(s['video'],str):
        raise ValueError('Expected video, interval, patch, search radius and error limit')
    a,b,r,e=(s[k] for k in ('start_frame','end_frame','radius','max_error'))
    if any(type(v) is not int for v in (a,b,r,e)) or not 0<=a<b<=300 or not 2<=b-a<=60 or not 1<=r<=12 or not 0<=e<=50:
        raise ValueError('Invalid tracking bounds')
    box=s['box']
    if not isinstance(box,list) or len(box)!=4 or any(type(v) is not int for v in box) or min(box[:2])<0 or not all(4<=v<=32 for v in box[2:]) or box[0]+box[2]>640 or box[1]+box[3]>480:
        raise ValueError('Choose a 4–32 pixel patch in the source frame')
    if (b-a)*(2*r+1)**2*box[2]*box[3]*3>30_000_000:
        raise ValueError('Tracking exceeds comparison budget')
    return s

def patch(raw,size,box):
    w,h=size;x,y,bw,bh=box
    return b''.join(raw[((y+j)*w+x)*3:((y+j)*w+x+bw)*3] for j in range(bh))

def track(raw,size,s):
    checked(s);w,h=size;x,y,bw,bh=s['box'];stride=w*h*3
    if not 1<=w<=640 or not 1<=h<=480 or x+bw>w or y+bh>h or len(raw)!=(s['end_frame']-s['start_frame'])*stride:
        raise ValueError('Patch or frames do not match source')
    template=patch(raw[:stride],size,(x,y,bw,bh))
    if all(template[i:i+3]==template[:3] for i in range(0,len(template),3)):
        raise ValueError('Select a nonuniform initial patch')
    rows=[{'frame':s['start_frame'],'box':[x,y,bw,bh],'mean_absolute_error':0.0,'state':'initial'}]
    for k in range(1,s['end_frame']-s['start_frame']):
        frame=raw[k*stride:(k+1)*stride];candidates=[]
        for yy in range(max(0,y-s['radius']),min(h-bh,y+s['radius'])+1):
            for xx in range(max(0,x-s['radius']),min(w-bw,x+s['radius'])+1):
                p=patch(frame,size,(xx,yy,bw,bh))
                error=sum(abs(a-b) for a,b in zip(template,p))
                candidates.append((error,xx,yy))
        candidates.sort()
        error,nx,ny=candidates[0];mean=error/len(template)
        ambiguous=len(candidates)>1 and candidates[1][0]==error
        if mean>s['max_error'] or ambiguous:
            rows.append({'frame':s['start_frame']+k,'box':None,'mean_absolute_error':mean,'state':'ambiguous' if ambiguous else 'lost'})
            break
        x,y=nx,ny
        rows.append({'frame':s['start_frame']+k,'box':[x,y,bw,bh],'mean_absolute_error':mean,'state':'matched'})
    return rows

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing tracking source and codec guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    if tuple(plan['guards'][2:])!=installed(root):raise ValueError('Reviewed codec changed')
    return s,dst,src

def operation(root,plan,render=False):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    tools=plan['guards'][2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-track-',dir=dst.parent) as tmp:
        path=Path(tmp)/'source.mp4';path.write_bytes(raw)
        meta=probe(fp,path);w,h=meta['width'],meta['height'];x,y,bw,bh=s['box']
        if s['end_frame']>meta['frames'] or x+bw>w or y+bh>h:raise ValueError('Tracking bounds exceed source')
        result={'source_sha256':hashlib.sha256(raw).hexdigest(),'source_format':meta,'method':'fixed RGB template, bounded translation search',
                'semantic_identity_verified':False,'occlusion_recovery_supported':False}
        if render:
            frames=decode(ff,path,s['start_frame'],s['end_frame'],w,h)
            rows=track(frames,(w,h),s)
            for row in rows:row['seconds']=row['frame']/meta['fps']
            result.update(samples=rows,decoded_rgb_sha256=hashlib.sha256(frames).hexdigest(),
                tracked_entire_interval=len(rows)==s['end_frame']-s['start_frame'] and rows[-1]['box'] is not None)
        verify_guards(tools)
        return result

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    plan['guards'].extend(installed(root))
    return plan,dict(s,observations=operation(root,plan),scope='User-selected patch translation only. Stop at ambiguity or excessive error.')

def execute(root,plan):
    _,dst,_=validate(root,plan);r=operation(root,plan,True)
    payload=(json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    if json.loads(payload)!=r:raise ValueError('Tracking JSON roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-video-motion-track-result-v1','status':'motion_observations_saved','output':plan['output'],
        'sha256':sha,'samples':len(r['samples']),'tracked_entire_interval':r['tracked_entire_interval'],'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed local patch tracking operation'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
