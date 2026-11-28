"""Reviewed PCM-envelope-driven animation of an image layer with lossless sound."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import MAX_RENDER_RGB
from deepthort_local.texture_pixels import image_module,decode as decode_png
from deepthort_local.image_composition import decode_layer
from deepthort_local.lip_sync import speech,mux,RATE
from deepthort_local.disk_gate import require_storage
SCHEMA='janus-audio-animation-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'background','layer','audio','fps','frames','anchor','travel_px','reference_rms'} or any(not isinstance(s[k],str) for k in ('background','layer','audio')):
        raise ValueError('Specify canvas, layer, exact audio, interval and motion parameters')
    if len({s[k].casefold() for k in ('background','layer','audio')})!=3:raise ValueError('Distinct inputs required')
    fps,n,t,r=(s[k] for k in ('fps','frames','travel_px','reference_rms'))
    if any(type(v) is not int for v in (fps,n,t,r)) or fps not in (24,25,30) or not 2<=n<=120 or not 1<=t<=240 or not 1<=r<=32768:
        raise ValueError('Invalid animation settings')
    a=s['anchor']
    if not isinstance(a,list) or len(a)!=2 or any(type(v) is not int for v in a) or not 0<=a[0]<640 or not 0<=a[1]<480:
        raise ValueError('Invalid layer anchor')
    return s

def envelope(pcm,s):
    checked(s);step=RATE//s['fps']
    if len(pcm)!=s['frames']*step*2:raise ValueError('Audio duration differs')
    result=[]
    for i in range(s['frames']):
        samples=struct.iter_unpack('<h',pcm[i*step*2:(i+1)*step*2])
        rms=math.sqrt(sum(v*v for (v,) in samples)/step)
        result.append(round(s['travel_px']*min(1,rms/s['reference_rms'])))
    return result

def prepare(raws,s,render=False):
    checked(s)
    if len(raws)!=3:raise ValueError('Expected three sources')
    w,h,_,background=decode_png(raws[0],('RGB',));pcm=speech(raws[2],s);offsets=envelope(pcm,s)
    x,y=s['anchor'];Image=image_module()
    if not 1<=w<=640 or not 1<=h<=480 or s['frames']*w*h*3>MAX_RENDER_RGB or min(offsets)==max(offsets):
        raise ValueError('Canvas exceeds bound or no changing envelope')
    with decode_layer(raws[1]) as layer:
        lw,lh=layer.size
        with layer.getchannel('A') as alpha:
            if alpha.getextrema()[1]==0:raise ValueError('Layer is invisible')
        if x+lw>w or y+lh>h or y-s['travel_px']<0:raise ValueError('Full motion range must fit canvas')
        if not render:return (w,h),pcm,offsets,None
        selected=bytearray()
        with Image.frombytes('RGB',(w,h),background) as bg:
            for offset in offsets:
                with bg.convert('RGBA') as canvas:
                    canvas.alpha_composite(layer,dest=(x,y-offset))
                    with canvas.convert('RGB') as frame:selected.extend(frame.tobytes())
        stride=w*h*3
        if all(selected[i:i+stride]==selected[:stride] for i in range(stride,len(selected),stride)):
            raise ValueError('No observable motion')
        return (w,h),pcm,offsets,selected

def paths_for(root,s,exclude):
    pp=[guard.path_for(root,s[k],exclude,{'.wav'} if k=='audio' else {'.png'},exists=True) for k in ('background','layer','audio')]
    if any(a.samefile(b) for i,a in enumerate(pp) for b in pp[:i]) or sum(p.stat().st_size for p in pp)>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized inputs')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=6:raise ValueError('Missing exact input guards')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths_for(Path(root).resolve(strict=True),s,plan['exclude'])
    if tuple(plan['guards'][-2:])!=installed(root) or any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:4])):
        raise ValueError('Reviewed inputs changed')
    return s,dst,pp

def inputs(pp,plan):return [guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:4])]

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths_for(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in pp)
    plan['guards'].extend(installed(root));s,_,pp=validate(root,plan)
    size,pcm,offsets,_=prepare(inputs(pp,plan),s)
    return plan,dict(s,canvas=list(size),motion_offsets=offsets,scope='Vertical layer motion from framewise PCM RMS, exact-duration audio; no learned gesture or beat recognition.')

def execute(root,plan):
    s,dst,pp=validate(root,plan);size,pcm,offsets,selected=prepare(inputs(pp,plan),s,True)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-audio-motion-',dir=dst.parent) as tmp:
        payload=mux(selected,size,pcm,s,plan['guards'][-2:],tmp)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'audio_envelope_animation_verified','output':plan['output'],'sha256':digest,
            'frames':s['frames'],'fps':s['fps'],'motion_offsets':offsets,'speech_pcm_sha256':hashlib.sha256(pcm).hexdigest(),
            'decoded_rgb_verified':True,'decoded_pcm_verified':True,'neural_motion':False,'visual_quality_verified':False,'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed audio animation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
