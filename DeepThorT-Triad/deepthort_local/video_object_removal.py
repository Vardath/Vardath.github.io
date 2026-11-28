"""Reviewed fixed-mask video object removal using an exact clean background plate."""
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
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-video-object-removal-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','plate','mask','start_frame','end_frame'} or any(not isinstance(s[k],str) for k in ('video','plate','mask')) or s['plate'].casefold()==s['mask'].casefold():
        raise ValueError('Specify video, distinct clean plate and grayscale mask, and interval')
    a,b=s['start_frame'],s['end_frame']
    if type(a) is not int or type(b) is not int or not 0<=a<b<=300 or b-a>60:
        raise ValueError('Invalid reviewed frame interval')
    return s

def remove(raw,plate,mask,size,s):
    checked(s);w,h=size;n=s['end_frame']-s['start_frame'];stride=w*h*3
    if not 1<=w<=640 or not 1<=h<=480 or len(raw)!=n*stride or len(plate)!=stride or len(mask)!=w*h or len(raw)>MAX_RENDER_RGB:
        raise ValueError('Reviewed mask, plate and frames must match')
    if not any(mask) or all(v==255 for v in mask):raise ValueError('Choose a nonempty mask that retains some original pixels')
    # Pillow's exact integer RGB composite is bounded and avoids a Python loop per pixel.
    from deepthort_local.texture_pixels import image_module
    Image=image_module();out=bytearray()
    with Image.frombytes('RGB',size,plate) as clean, Image.frombytes('L',size,mask) as matte:
        for offset in range(0,len(raw),stride):
            with Image.frombytes('RGB',size,bytes(raw[offset:offset+stride])) as frame:
                with Image.composite(clean,frame,matte) as result:
                    out.extend(result.tobytes())
    if out==raw:raise ValueError('Mask and plate produce no observable change')
    return out,{'mask_coverage_pixels':sum(v>0 for v in mask),'fully_replaced_pixels_per_frame':mask.count(255),
                'method':'fixed reviewed grayscale mask and clean plate','semantic_detection':False,
                'inpainting':False,'moving_mask_supported':False,'visual_quality_verified':False,'audio_supported':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=6:
        raise ValueError('Invalid reviewed object removal approval')
    s,dst,video=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    paths=[guard.path_for(Path(root).resolve(strict=True),s[k],plan['exclude'],{'.png'},exists=True) for k in ('plate','mask')]
    if paths[0].samefile(paths[1]) or any(p.stat().st_size>guard.MAX_INPUT or snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][2:4])) or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed plate, mask or codec changed')
    return s,dst,video,paths

def operation(root,plan,render=False):
    s,dst,video,paths=validate(root,plan);raw=guard.exact(video,plan['guards'][1],guard.MAX_INPUT)
    plate,mask=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][2:4])]
    pw,ph,_,pixels=decode_png(plate,('RGB',));mw,mh,_,matte=decode_png(mask,('L',))
    tools=plan['guards'][-2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-video-remove-',dir=dst.parent) as tmp:
        folder=Path(tmp);source=folder/'source.mp4';source.write_bytes(raw)
        m=probe(fp,source);w,h=m['width'],m['height'];n=s['end_frame']-s['start_frame']
        if (pw,ph)!=(w,h) or (mw,mh)!=(w,h) or s['end_frame']>m['frames'] or not any(matte) or all(v==255 for v in matte):
            raise ValueError('Mask, plate or reviewed interval invalid')
        receipt={'source_format':m,'source_sha256':hashlib.sha256(raw).hexdigest(),
                 'plate_sha256':hashlib.sha256(plate).hexdigest(),'mask_sha256':hashlib.sha256(mask).hexdigest(),
                 'frames':n,'fps':m['fps']}
        if not render:return None,receipt
        selected,r=remove(decode(ff,source,s['start_frame'],s['end_frame'],w,h),pixels,matte,(w,h),s)
        payload=encode_verified(selected,(w,h),m['fps'],n,tools,folder)
        receipt.update(r,decoded_rgb_sequence_verified=True,rgb_sequence_sha256=hashlib.sha256(selected).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=('video','.mp4'))
    for key in ('plate','mask'):
        p=guard.path_for(Path(plan['root']),s[key],plan['exclude'],{'.png'},exists=True)
        if p.stat().st_size>guard.MAX_INPUT:raise ValueError('Oversized image')
        plan['guards'].append(snapshot_file(p))
    plan['guards'].extend(installed(root));_,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Fixed reviewed mask over matching clean plate; no inferred segmentation, tracking or inpainting.')

def execute(root,plan):
    _,dst,_,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'masked_video_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed masked video removal unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
