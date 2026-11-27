"""Reviewed framewise chroma-key replacement with an exact still background."""
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
from deepthort_local.background_removal import rgb
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-video-background-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','background','start_frame','end_frame','key','tolerance','feather'} or any(not isinstance(s[k],str) for k in ('video','background')):
        raise ValueError('Specify exact video and PNG background, interval and chroma key')
    rgb(s['key']);a,b,t,f=(s[k] for k in ('start_frame','end_frame','tolerance','feather'))
    if any(type(v) is not int for v in (a,b,t,f)) or not 0<=a<b<=300 or b-a>60 or not 0<=t<=254 or not 0<=f<=255-t:
        raise ValueError('Invalid interval or chroma-key settings')
    return s

def composite(raw,background,size,s):
    checked(s);w,h=size;n=s['end_frame']-s['start_frame'];stride=w*h*3
    if not 1<=w<=640 or not 1<=h<=480 or len(background)!=stride or len(raw)!=n*stride or len(raw)>MAX_RENDER_RGB:
        raise ValueError('Invalid reviewed RGB frame buffer')
    key=s['key'];t=s['tolerance'];f=s['feather'];out=bytearray(len(raw));removed=partial=changed=0
    for offset in range(0,len(raw),stride):
        for j in range(0,stride,3):
            i=offset+j
            d=max(abs(raw[i+k]-key[k]) for k in range(3))
            a=0 if d<=t else 255 if not f or d>=t+f else ((d-t)*255+f//2)//f
            removed+=a==0;partial+=0<a<255
            for k in range(3):
                v=(raw[i+k]*a+background[j+k]*(255-a)+127)//255
                changed+=v!=raw[i+k];out[i+k]=v
    if not changed:raise ValueError('No observable replacement pixels')
    return out,{'fully_replaced_pixels':removed,'partial_pixels':partial,'changed_rgb_channels':changed,
                'semantic_segmentation':False,'visual_quality_verified':False,'audio_supported':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=5:
        raise ValueError('Invalid video background approval')
    s,dst,video=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    bg=guard.path_for(Path(root).resolve(strict=True),s['background'],plan['exclude'],{'.png'},exists=True)
    if bg.stat().st_size>guard.MAX_INPUT or snapshot_file(bg)!=plan['guards'][2] or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed background or codec changed')
    return s,dst,video,bg

def operation(root,plan,render=False):
    s,dst,video,bg=validate(root,plan)
    raw=guard.exact(video,plan['guards'][1],guard.MAX_INPUT)
    image=guard.exact(bg,plan['guards'][2],guard.MAX_INPUT)
    bw,bh,_,pixels=decode_png(image,('RGB',))
    tools=plan['guards'][-2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-video-bg-',dir=dst.parent) as tmp:
        folder=Path(tmp);source=folder/'source.mp4';source.write_bytes(raw)
        m=probe(fp,source);w,h=m['width'],m['height'];n=s['end_frame']-s['start_frame']
        if (bw,bh)!=(w,h) or s['end_frame']>m['frames']:raise ValueError('Background dimensions or frame interval mismatch')
        receipt={'source_format':m,'source_sha256':hashlib.sha256(raw).hexdigest(),'background_sha256':hashlib.sha256(image).hexdigest(),
                 'frames':n,'fps':m['fps'],'method':'framewise RGB chroma key with optional feather'}
        if not render:return None,receipt
        selected,r=composite(decode(ff,source,s['start_frame'],s['end_frame'],w,h),pixels,(w,h),s)
        payload=encode_verified(selected,(w,h),m['fps'],n,tools,folder)
        receipt.update(r,decoded_rgb_sequence_verified=True,rgb_sequence_sha256=hashlib.sha256(selected).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    bg=guard.path_for(Path(plan['root']),s['background'],plan['exclude'],{'.png'},exists=True)
    if bg.stat().st_size>guard.MAX_INPUT:raise ValueError('Oversized background')
    plan['guards'].append(snapshot_file(bg));plan['guards'].extend(installed(root))
    _,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Replace explicit chroma-key pixels in silent video with an exact matching PNG, no semantic segmentation.')

def execute(root,plan):
    _,dst,_,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'video_background_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed video background replacement unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
