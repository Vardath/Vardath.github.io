"""Reviewed still-image camera motion, rendered and decoded with existing verified video pipeline."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.texture_pixels import decode,image_module
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import encode_verified,MAX_RENDER_RGB
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-image-motion-v1'
EXTRA=('image','.png')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','width','height','fps','frames','start','end'} or not isinstance(s['image'],str):
        raise ValueError('Specify PNG, output canvas, frame rate, count and two crop rectangles')
    w,h,fps,n=(s[k] for k in ('width','height','fps','frames'))
    if any(type(v) is not int for v in (w,h,fps,n)) or not 16<=w<=640 or not 16<=h<=480 or fps not in (24,25,30) or not 2<=n<=120 or n*w*h*3>MAX_RENDER_RGB:
        raise ValueError('Video dimensions or duration outside bound')
    for k in ('start','end'):
        r=s[k]
        if not isinstance(r,list) or len(r)!=4 or any(type(v) is not int for v in r):
            raise ValueError('Crop is [x,y,width,height] in source pixels')
        x,y,cw,ch=r
        if min(x,y)<0 or min(cw,ch)<2 or x+cw>2048 or y+ch>2048 or cw*h!=ch*w:
            raise ValueError('Crop outside bounds or incompatible aspect ratio')
    if s['start']==s['end']:raise ValueError('Choose distinct start and end crop')
    return s

def geometry(s,size):
    checked(s)
    sw,sh=size
    for x,y,w,h in (s['start'],s['end']):
        if x+w>sw or y+h>sh:raise ValueError('Crop exceeds exact image dimensions')
    return size

def crop_at(s,i):
    n=s['frames']
    if type(i) is not int or not 0<=i<n:raise ValueError('Invalid frame index')
    a,b=s['start'],s['end']
    # Smoothstep interpolation preserves exact endpoints and aspect ratio.
    t=i/(n-1);t=t*t*(3-2*t)
    x,y,w,h=(a[k]+(b[k]-a[k])*t for k in range(4))
    return (x,y,x+w,y+h)

def frames(raw,s):
    sw,sh,mode,pixels=decode(raw,('RGB',))
    geometry(s,(sw,sh));Image=image_module()
    selected=bytearray()
    with Image.frombytes(mode,(sw,sh),pixels) as im:
        for i in range(s['frames']):
            with im.resize((s['width'],s['height']),Image.Resampling.BICUBIC,box=crop_at(s,i)) as frame:
                selected.extend(frame.tobytes())
    stride=s['width']*s['height']*3
    if len(selected)!=stride*s['frames'] or len(selected)>MAX_RENDER_RGB:raise ValueError('Invalid motion buffer')
    if selected[:stride]==selected[-stride:] and all(selected[:stride]==selected[i:i+stride] for i in range(stride,len(selected),stride)):
        raise ValueError('Source/crops produce no observable pixel motion')
    return selected,{'source_dimensions':[sw,sh],'width':s['width'],'height':s['height'],'frames':s['frames'],'fps':s['fps'],
                     'source_sha256':hashlib.sha256(raw).hexdigest(),'rgb_sequence_sha256':hashlib.sha256(selected).hexdigest(),
                     'motion_method':'smoothstep pan/zoom crop resampling','neural_motion_generated':False,'audio_supported':False,
                     'visual_quality_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Invalid image motion approval')
    s,dst,path=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    if tuple(plan['guards'][-2:])!=installed(root):raise ValueError('Reviewed video tools changed')
    return s,dst,path

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    plan['guards'].extend(installed(root))
    _,_,path=validate(root,plan)
    sw,sh,_,_=decode(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),('RGB',))
    geometry(s,(sw,sh))
    return plan,dict(s,source_dimensions=[sw,sh],scope='Smooth pan and zoom from one opaque RGB PNG. No generated subject movement or neural video.')

def execute(root,plan):
    s,dst,path=validate(root,plan)
    selected,receipt=frames(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-image-motion-',dir=dst.parent) as folder:
        payload=encode_verified(selected,(s['width'],s['height']),s['fps'],s['frames'],plan['guards'][-2:],folder)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'image_motion_pixels_verified','output':plan['output'],'sha256':digest,
            'decoded_rgb_sequence_verified':True,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed image motion unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
