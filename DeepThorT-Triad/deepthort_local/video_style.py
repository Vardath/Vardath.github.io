"""Reviewed temporally consistent reference-palette transfer for a bounded video interval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode,encode_verified,MAX_RENDER_RGB
from deepthort_local.texture_pixels import decode as decode_png
from deepthort_local.image_style_transfer import mapping
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-video-style-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','reference','start_frame','end_frame','strength_percent'} or any(not isinstance(s[k],str) for k in ('video','reference')):
        raise ValueError('Specify exact video, reference PNG, interval and strength')
    a,b,v=(s[k] for k in ('start_frame','end_frame','strength_percent'))
    if any(type(x) is not int for x in (a,b,v)) or not 0<=a<b<=300 or b-a>60 or not 1<=v<=100:
        raise ValueError('Invalid frame interval or strength')
    return s

def transfer(raw,reference,size,s):
    checked(s);w,h=size;n=s['end_frame']-s['start_frame']
    if not 1<=w<=640 or not 1<=h<=480 or len(raw)!=n*w*h*3 or len(raw)>MAX_RENDER_RGB or not 3<=len(reference)<=1024*1024*3 or len(reference)%3:
        raise ValueError('Invalid reviewed RGB buffers')
    # One LUT per channel for the complete interval, not per-frame adjustments.
    strength=s['strength_percent'];luts=[]
    for c in range(3):
        mapped=mapping(raw[c::3],reference[c::3])
        lut=bytes((v*(100-strength)+mapped[v]*strength+50)//100 for v in range(256))
        if any(a>b for a,b in zip(lut,lut[1:])):raise ValueError('Nonmonotonic palette mapping')
        luts.append(lut)
    out=bytearray(len(raw))
    for c,lut in enumerate(luts):out[c::3]=raw[c::3].translate(lut)
    if out==raw:raise ValueError('No observable palette change')
    return out,{'strength_percent':strength,'shared_temporal_lut':True,'lut_sha256':hashlib.sha256(b''.join(luts)).hexdigest(),
                'spatial_layout_preserved':True,'neural_style_transfer':False,'visual_quality_verified':False,'audio_supported':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=5:
        raise ValueError('Invalid video background approval')
    s,dst,video=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    bg=guard.path_for(Path(root).resolve(strict=True),s['reference'],plan['exclude'],{'.png'},exists=True)
    if bg.stat().st_size>guard.MAX_INPUT or snapshot_file(bg)!=plan['guards'][2] or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed reference or codec changed')
    return s,dst,video,bg

def operation(root,plan,render=False):
    s,dst,video,bg=validate(root,plan)
    raw=guard.exact(video,plan['guards'][1],guard.MAX_INPUT)
    image=guard.exact(bg,plan['guards'][2],guard.MAX_INPUT)
    bw,bh,_,pixels=decode_png(image,('RGB',))
    if bw*bh>1024*1024:raise ValueError('Reference exceeds one megapixel')
    tools=plan['guards'][-2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-video-style-',dir=dst.parent) as tmp:
        folder=Path(tmp);source=folder/'source.mp4';source.write_bytes(raw)
        m=probe(fp,source);w,h=m['width'],m['height'];n=s['end_frame']-s['start_frame']
        if s['end_frame']>m['frames']:raise ValueError('Frame interval mismatch')
        receipt={'source_format':m,'source_sha256':hashlib.sha256(raw).hexdigest(),'reference_sha256':hashlib.sha256(image).hexdigest(),
                 'frames':n,'fps':m['fps'],'method':'whole-interval empirical RGB quantile palette transfer'}
        if not render:return None,receipt
        selected,r=transfer(decode(ff,source,s['start_frame'],s['end_frame'],w,h),pixels,(w,h),s)
        payload=encode_verified(selected,(w,h),m['fps'],n,tools,folder)
        receipt.update(r,decoded_rgb_sequence_verified=True,rgb_sequence_sha256=hashlib.sha256(selected).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    bg=guard.path_for(Path(plan['root']),s['reference'],plan['exclude'],{'.png'},exists=True)
    if bg.stat().st_size>guard.MAX_INPUT:raise ValueError('Oversized reference')
    plan['guards'].append(snapshot_file(bg));plan['guards'].extend(installed(root))
    _,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Apply one shared RGB palette mapping to a reviewed silent clip using an exact reference PNG; no neural style synthesis.')

def execute(root,plan):
    _,dst,_,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'video_palette_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed video palette transfer unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
