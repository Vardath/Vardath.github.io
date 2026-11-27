"""Reviewed activity-based highlight montage from bounded local video."""
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
from deepthort_local.video_trimming import probe,decode,encode_verified,MAX_RENDER_RGB
from deepthort_local.texture_pixels import image_module
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-video-highlights-v1'
EXTRA=('video','.mp4')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','start_frame','end_frame','segment_frames','max_segments','min_change'} or not isinstance(s['video'],str):
        raise ValueError('Expected source, frame interval, segment length/count and minimum visual change')
    a,b,n,k,e=(s[x] for x in ('start_frame','end_frame','segment_frames','max_segments','min_change'))
    if any(type(v) is not int for v in (a,b,n,k,e)) or not 0<=a<b<=300 or not 2<=b-a<=120 or not 2<=n<=30 or n>b-a or not 1<=k<=4 or not 1<=e<=100:
        raise ValueError('Invalid bounded highlight selection')
    return s

def highlights(raw,size,s):
    checked(s);w,h=size;stride=w*h*3;count=s['end_frame']-s['start_frame'];n=s['segment_frames']
    if not 1<=w<=640 or not 1<=h<=480 or len(raw)!=count*stride or len(raw)>MAX_RENDER_RGB:
        raise ValueError('Invalid decoded highlight frame buffer')
    Image=image_module();previous=None;changes=[0.0]
    for i in range(count):
        with Image.frombytes('RGB',size,raw[i*stride:(i+1)*stride]) as im:
            with im.resize((32,24),Image.Resampling.BOX) as sample:
                pixels=sample.tobytes()
        if previous is not None:changes.append(sum(abs(a-b) for a,b in zip(pixels,previous))/len(pixels))
        previous=pixels
    # Score internal consecutive-frame changes, excluding a cut into the window.
    candidates=[(sum(changes[a+1:a+n])/(n-1),a,a+n) for a in range(count-n+1)]
    chosen=[]
    for score,a,b in sorted(candidates,key=lambda x:(-x[0],x[1])):
        if score<s['min_change']:break
        if any(a<d and c<b for _,c,d in chosen):continue
        chosen.append((score,a,b))
        if len(chosen)==s['max_segments']:break
    return [{'start_frame':a+s['start_frame'],'end_frame':b+s['start_frame'],'mean_rgb_change':round(score,6)}
            for score,a,b in sorted(chosen,key=lambda x:x[1])]

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing reviewed video and codec guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    if tuple(plan['guards'][2:])!=installed(root):raise ValueError('Reviewed codec changed')
    return s,dst,src

def operation(root,plan,render=False):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    tools=plan['guards'][2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-highlights-',dir=dst.parent) as tmp:
        folder=Path(tmp);path=folder/'source.mp4';path.write_bytes(raw)
        meta=probe(fp,path);w,h=meta['width'],meta['height'];stride=w*h*3
        if s['end_frame']>meta['frames']:raise ValueError('Requested interval exceeds video')
        result={'source_sha256':hashlib.sha256(raw).hexdigest(),'source_format':meta,
                'method':'mean RGB activity, nonoverlapping windows in chronological order',
                'semantic_importance_verified':False,'audio_supported':False}
        if not render:return None,result
        frames=decode(ff,path,s['start_frame'],s['end_frame'],w,h)
        rows=highlights(frames,(w,h),s)
        if not rows:raise ValueError('No candidate exceeds the reviewed activity threshold')
        selected=bytearray()
        for r in rows:
            a,b=(r[k]-s['start_frame'] for k in ('start_frame','end_frame'))
            selected.extend(frames[a*stride:b*stride])
            r['start_seconds']=r['start_frame']/meta['fps'];r['end_seconds']=r['end_frame']/meta['fps']
        count=len(selected)//stride
        payload=encode_verified(selected,(w,h),meta['fps'],count,tools,folder)
        result.update(segments=rows,frames=count,fps=meta['fps'],duration_seconds=count/meta['fps'],
            decoded_rgb_sequence_verified=True,selected_rgb_sha256=hashlib.sha256(selected).hexdigest(),
            visual_playback_verified=False)
        return payload,result

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    plan['guards'].extend(installed(root));_,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Automatic visual activity selection only. No semantic, audio or narrative judgement.')

def execute(root,plan):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-video-highlights-result-v1','status':'highlight_pixels_verified','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'No eligible highlight or invalid reviewed local video'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
