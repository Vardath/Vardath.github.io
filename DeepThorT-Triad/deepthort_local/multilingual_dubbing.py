"""Reviewed local multilingual speech synthesis into a silent video interval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode,MAX_RENDER_RGB
from deepthort_local.lip_sync import mux
from deepthort_local.local_speech import WindowsSpeech,inspect_audio,voice_record
from deepthort_local.multilingual_speech import checked as check_speech,select
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-multilingual-dubbing-v1'
EXTRA=('video','.mp4')
RATE=48000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','start_frame','end_frame','cues'} or not isinstance(s['video'],str):
        raise ValueError('Expected exact video, frame interval and reviewed translated cues')
    a,b=s['start_frame'],s['end_frame']
    if type(a) is not int or type(b) is not int or not 0<=a<b<=300 or not 2<=b-a<=120:
        raise ValueError('Invalid frame interval')
    cues=s['cues']
    if not isinstance(cues,list) or not 1<=len(cues)<=4:raise ValueError('Use one to four speech cues')
    last=0
    for c in cues:
        if not isinstance(c,dict) or set(c)!={'start_frame','end_frame','voice','text'}:raise ValueError('Invalid cue')
        x,y=c['start_frame'],c['end_frame']
        if type(x) is not int or type(y) is not int or not last<=x<y<=b-a:
            raise ValueError('Cues must be ordered, nonoverlapping and relative to the selected clip')
        voice=voice_record(c['voice'])
        check_speech({'segments':[{'culture':voice['culture'],'voice_id':voice['id'],'text':c['text']}],'pause_ms':0})
        last=y
    return s

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing exact source and codec guards')
    s,dst,video=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,
        checked=checked,output_suffix='.mp4',extra=EXTRA)
    if tuple(plan['guards'][-2:])!=installed(root):raise ValueError('Reviewed codec changed')
    return s,dst,video

def resample(raw,capacity):
    if not raw or len(raw)%2:raise ValueError('Invalid speech samples')
    count=((len(raw)//2)*RATE+22049)//22050
    if count>capacity:raise ValueError('Generated speech exceeds reviewed cue; adjust text or timing')
    values=struct.unpack('<%dh'%(len(raw)//2),raw)
    result=bytearray()
    for i in range(count):
        j,f=divmod(i*22050,RATE)
        j=min(j,len(values)-1)
        result.extend(struct.pack('<h',(values[j]*(RATE-f)+values[min(j+1,len(values)-1)]*f)//RATE))
    return bytes(result)

def operation(root,plan,render=False,backend=None):
    s,dst,video=validate(root,plan)
    raw=guard.exact(video,plan['guards'][1],guard.MAX_INPUT)
    tools=plan['guards'][-2:];verify_guards(tools);ff,fp=(g['path'] for g in tools)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-multilingual-dub-',dir=dst.parent) as tmp:
        folder=Path(tmp);source=folder/'source.mp4';source.write_bytes(raw)
        m=probe(fp,source);w,h=m['width'],m['height'];fps=m['fps'];n=s['end_frame']-s['start_frame']
        if s['end_frame']>m['frames'] or n*w*h*3>MAX_RENDER_RGB:raise ValueError('Frame interval exceeds bound')
        receipt={'source_format':m,'source_sha256':hashlib.sha256(raw).hexdigest(),'frames':n,'fps':fps,
                 'automatic_translation':False,'automatic_alignment':False,'original_audio_replacement_supported':False,
                 'pronunciation_verified':False,'playback_quality_verified':False}
        if not render:return None,receipt
        backend=backend or WindowsSpeech()
        voices=backend.voices(None)
        for c in s['cues']:
            v=c['voice']
            spec={'segments':[{'culture':v['culture'],'voice_id':v['id'],'text':c['text']}],'pause_ms':0}
            if select(voices,spec)!=[v]:raise ValueError('Exact reviewed installed voice missing or changed')
        pcm=bytearray(n*RATE//fps*2);receipts=[]
        for i,c in enumerate(s['cues']):
            validate(root,plan)
            path=folder/f'cue-{i}.wav'
            evidence=backend.synthesize(c['text'],c['voice'],path,None)
            if inspect_audio(path)!=evidence:raise ValueError('Speech evidence changed')
            with wave.open(str(path),'rb') as f:
                samples=f.readframes(f.getnframes())
                if len(samples)!=evidence['frames']*2:raise ValueError('Truncated speech')
            a,b=(c[k]*RATE//fps for k in ('start_frame','end_frame'))
            converted=resample(samples,b-a)
            pcm[a*2:a*2+len(converted)]=converted
            receipts.append({'cue':i+1,'culture':c['voice']['culture'],'voice_id':c['voice']['id'],
                             'start_frame':c['start_frame'],'end_frame':c['end_frame'],
                             'speech_samples':len(converted)//2,'speech_sha256':hashlib.sha256(converted).hexdigest()})
        selected=decode(ff,source,s['start_frame'],s['end_frame'],w,h)
        payload=mux(selected,(w,h),bytes(pcm),{'fps':fps,'frames':n},tools,folder)
        receipt.update(cues=receipts,decoded_rgb_verified=True,decoded_pcm_verified=True,
                       speech_pcm_sha256=hashlib.sha256(pcm).hexdigest())
        return payload,receipt

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    plan['guards'].extend(installed(root));_,r=operation(root,plan)
    return plan,dict(s,observations=r,scope='Synthesize supplied translated text in exact installed voices; pad with silence, never truncate. No automatic translation or alignment.')

def execute(root,plan,*,backend=None):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True,backend)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'reviewed_multilingual_dub_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed multilingual dubbing unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
