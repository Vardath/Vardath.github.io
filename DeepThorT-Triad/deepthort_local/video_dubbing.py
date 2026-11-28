"""Reviewed exact-duration replacement narration for a silent video interval."""
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
from deepthort_local.video_trimming import probe,decode,MAX_RENDER_RGB
from deepthort_local.lip_sync import speech,mux
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-video-dubbing-v1'
EXTRA=('video','.mp4')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','audio','start_frame','end_frame'} or any(not isinstance(s[k],str) for k in ('video','audio')):
        raise ValueError('Choose exact silent video, replacement audio and frame interval')
    a,b=s['start_frame'],s['end_frame']
    if type(a) is not int or type(b) is not int or not 0<=a<b<=300 or not 2<=b-a<=120:
        raise ValueError('Invalid reviewed frame interval')
    return s

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=5:
        raise ValueError('Missing exact dubbing source guards')
    s,dst,video=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    audio=guard.path_for(Path(root).resolve(strict=True),s['audio'],plan['exclude'],{'.wav'},exists=True)
    if audio.stat().st_size>guard.MAX_INPUT or snapshot_file(audio)!=plan['guards'][2] or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed audio or codec changed')
    return s,dst,video,audio

def operation(root,plan,render=False):
    s,dst,video,audio=validate(root,plan)
    raw=guard.exact(video,plan['guards'][1],guard.MAX_INPUT)
    sound=guard.exact(audio,plan['guards'][2],guard.MAX_INPUT)
    tools=plan['guards'][-2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-dubbing-',dir=dst.parent) as tmp:
        folder=Path(tmp);source=folder/'source.mp4';source.write_bytes(raw)
        m=probe(fp,source);w,h=m['width'],m['height'];n=s['end_frame']-s['start_frame']
        if s['end_frame']>m['frames'] or n*w*h*3>MAX_RENDER_RGB:raise ValueError('Frame interval exceeds source or buffer bound')
        timing={'fps':m['fps'],'frames':n}
        pcm=speech(sound,timing)
        receipt={'source_format':m,'source_sha256':hashlib.sha256(raw).hexdigest(),'audio_source_sha256':hashlib.sha256(sound).hexdigest(),
                 'frames':n,'fps':m['fps'],'speech_samples':len(pcm)//2,'speech_pcm_sha256':hashlib.sha256(pcm).hexdigest(),
                 'automatic_translation':False,'automatic_alignment':False,'original_audio_replacement_supported':False,
                 'voice_identity_verified':False,'playback_quality_verified':False}
        if not render:return None,receipt
        selected=decode(ff,source,s['start_frame'],s['end_frame'],w,h)
        payload=mux(selected,(w,h),pcm,timing,tools,folder)
        receipt.update(decoded_rgb_verified=True,decoded_pcm_verified=True,source_rgb_sha256=hashlib.sha256(selected).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    audio=guard.path_for(Path(plan['root']),s['audio'],plan['exclude'],{'.wav'},exists=True)
    if audio.stat().st_size>guard.MAX_INPUT:raise ValueError('Oversized audio source')
    plan['guards'].append(snapshot_file(audio));plan['guards'].extend(installed(root));_,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Add supplied exact-duration narration to a reviewed silent clip interval; no automatic translation, alignment or replacement of existing soundtrack.')

def execute(root,plan):
    _,dst,_,_=validate(root,plan);payload,r=operation(root,plan,True)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'reviewed_dub_mux_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed video dubbing unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
