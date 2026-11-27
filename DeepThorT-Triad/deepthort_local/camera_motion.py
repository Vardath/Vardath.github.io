"""Reviewed multi-keyframe virtual camera reframing of existing silent video."""
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

SCHEMA='janus-camera-motion-v1'
EXTRA=('video','.mp4')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','start_frame','end_frame','width','height','keyframes'} or not isinstance(s['video'],str):
        raise ValueError('Specify exact video, frame interval, canvas and camera keyframes')
    a,b,w,h=(s[k] for k in ('start_frame','end_frame','width','height'))
    if any(type(v) is not int for v in (a,b,w,h)) or not 0<=a<b<=300 or not 2<=b-a<=60 or not 16<=w<=640 or not 16<=h<=480 or (b-a)*w*h*3>MAX_RENDER_RGB:
        raise ValueError('Invalid camera output bounds')
    keys=s['keyframes']
    if not isinstance(keys,list) or not 2<=len(keys)<=8:raise ValueError('Choose two to eight camera keyframes')
    last=-1
    for k in keys:
        if not isinstance(k,dict) or set(k)!={'frame','crop'} or type(k['frame']) is not int or not last<k['frame']<b-a:
            raise ValueError('Keyframes must be in increasing relative frame order')
        last=k['frame'];r=k['crop']
        if not isinstance(r,list) or len(r)!=4 or any(type(v) is not int for v in r):raise ValueError('Expected integer crop rectangle')
        x,y,cw,ch=r
        if min(x,y)<0 or min(cw,ch)<2 or x+cw>640 or y+ch>480 or cw*h!=ch*w:
            raise ValueError('Invalid camera crop or aspect ratio')
    if keys[0]['frame']!=0 or last!=b-a-1 or all(k['crop']==keys[0]['crop'] for k in keys):
        raise ValueError('Require first/last keyframes and a changing crop')
    return s

def geometry(s,size):
    checked(s);w,h=size
    for k in s['keyframes']:
        x,y,cw,ch=k['crop']
        if x+cw>w or y+ch>h:raise ValueError('Camera crop exceeds source frame')
    return size

def crop_at(s,i):
    if type(i) is not int or not 0<=i<s['end_frame']-s['start_frame']:raise ValueError('Invalid camera frame')
    keys=s['keyframes']
    for a,b in zip(keys,keys[1:]):
        if a['frame']<=i<=b['frame']:
            t=(i-a['frame'])/(b['frame']-a['frame']);t=t*t*(3-2*t)
            x,y,w,h=(v+(z-v)*t for v,z in zip(a['crop'],b['crop']))
            return x,y,x+w,y+h
    raise ValueError('Missing camera interval')

def reframe(raw,size,s):
    geometry(s,size);w,h=size;n=s['end_frame']-s['start_frame'];stride=w*h*3
    if not 1<=w<=640 or not 1<=h<=480 or len(raw)!=n*stride or len(raw)>MAX_RENDER_RGB:
        raise ValueError('Invalid source RGB frames')
    Image=image_module();out=bytearray()
    for i in range(n):
        with Image.frombytes('RGB',size,bytes(raw[i*stride:(i+1)*stride])) as im:
            with im.resize((s['width'],s['height']),Image.Resampling.BICUBIC,box=crop_at(s,i)) as frame:
                out.extend(frame.tobytes())
    if len(out)!=n*s['width']*s['height']*3:raise ValueError('Invalid camera output buffer')
    return out

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing exact camera input guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    if tuple(plan['guards'][2:])!=installed(root):raise ValueError('Reviewed codec changed')
    return s,dst,src

def operation(root,plan,render=False):
    s,dst,src=validate(root,plan);raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    tools=plan['guards'][2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-camera-',dir=dst.parent) as tmp:
        folder=Path(tmp);path=folder/'source.mp4';path.write_bytes(raw)
        meta=probe(fp,path);size=(meta['width'],meta['height']);geometry(s,size)
        if s['end_frame']>meta['frames']:raise ValueError('Camera interval exceeds source')
        n=s['end_frame']-s['start_frame'];target=(s['width'],s['height'])
        receipt={'source_format':meta,'source_sha256':hashlib.sha256(raw).hexdigest(),'frames':n,'fps':meta['fps'],
                 'width':target[0],'height':target[1],'method':'piecewise smoothstep keyframed virtual camera crop',
                 'physical_3d_camera':False,'novel_view_synthesis':False,'audio_supported':False,'visual_quality_verified':False}
        if not render:return None,receipt
        selected=reframe(decode(ff,path,s['start_frame'],s['end_frame'],*size),size,s)
        payload=encode_verified(selected,target,meta['fps'],n,tools,folder)
        receipt.update(decoded_rgb_sequence_verified=True,rgb_sequence_sha256=hashlib.sha256(selected).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    plan['guards'].extend(installed(root));_,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Reframe existing silent video along explicit camera crop keyframes; no inferred 3D scene or new viewpoints.')

def execute(root,plan):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'camera_motion_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed camera motion unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
