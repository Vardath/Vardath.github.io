"""Offline bounded multi-window audio transcription using the existing Windows recognizer."""
import hashlib
import io
import json
from pathlib import Path
import time
import wave
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions
from .speech_to_text import RATE,MAX_SECONDS,WindowsRecognizer,language,normalize,stopped

MAX_DURATION=120
MAX_BYTES=MAX_DURATION*RATE*2+65536

def pcm(raw):
    if not isinstance(raw,bytes) or not 44<=len(raw)<=MAX_BYTES:raise ValueError('Audio outside byte bound')
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            frames=f.getnframes()
            if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getcomptype())!=(1,2,RATE,'NONE') or not RATE<=frames<=RATE*MAX_DURATION:
                raise ValueError('Requires 1–120 seconds of mono 16 kHz PCM16 WAV')
            samples=f.readframes(frames)
            if len(samples)!=frames*2:raise ValueError('Truncated audio')
    except (wave.Error,EOFError) as exc:raise ValueError('Invalid WAV') from exc
    return samples,frames

def windows(raw):
    samples,frames=pcm(raw)
    # Balanced non-overlapping windows prevent a final sub-second fragment.
    count=(frames+RATE*MAX_SECONDS-1)//(RATE*MAX_SECONDS)
    for i in range(count):
        start=i*frames//count;end=(i+1)*frames//count
        out=io.BytesIO()
        with wave.open(out,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE)
            f.writeframes(samples[2*start:2*end])
        yield start/RATE,(end-start)/RATE,out.getvalue()

def review(root,source,output,culture,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude);language(culture)
    src=guard.path_for(root,source,exclude,{'.wav'},exists=True)
    guard.path_for(root,output,exclude,{'.json'},exists=False)
    identity=snapshot_file(src);_,frames=pcm(guard.exact(src,identity,MAX_BYTES))
    return {'schema':'janus-audio-transcription-v1','root':str(root),'source':source,'output':output,'culture':culture,
            'exclude':exclude,'guard':identity,'expires_at':int(time.time())+1800},frames/RATE

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','culture','exclude','guard','expires_at'} or plan['schema']!='janus-audio-transcription-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid transcription review')
    language(plan['culture']);src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.json'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed input changed')
    raw=guard.exact(src,plan['guard'],MAX_BYTES)
    return raw,dst

def transcribe(root,plan,cancelled=None,*,approved=False,backend=None,stage=None):
    if approved is not True:raise PermissionError('Explicit transcription approval required')
    stopped(cancelled);raw,_=validate(root,plan);_,frames=pcm(raw)
    backend=backend or WindowsRecognizer();segments=[];receipts=[];identity=None;total=0
    for i,(offset,seconds,staged) in enumerate(windows(raw),1):
        stopped(cancelled);validate(root,plan)
        if stage:stage(i)
        result=normalize(backend.recognize(staged,plan['culture'],cancelled),plan['culture'],seconds)
        recognizer=(result['culture'],result['recognizer_id'])
        if identity is not None and recognizer!=identity:raise ValueError('Recognizer changed between windows')
        identity=recognizer
        receipts.append({'window':i,'start_seconds':offset,'duration_seconds':seconds,'status':result['status'],'segments':len(result['segments'])})
        for row in result['segments']:
            total+=len(row['text'])
            if total>64000:raise ValueError('Transcript exceeds bound')
            start=max(0,min(seconds,row['start_seconds']));end=min(seconds,start+row['duration_seconds'])
            if end<=start:raise ValueError('Recognition segment outside window')
            segments.append({'window':i,'start_seconds':round(offset+start,5),'duration_seconds':round(end-start,5),'text':row['text'],'confidence':row['confidence']})
    stopped(cancelled);validate(root,plan)
    return {'schema':'janus-audio-transcription-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'audio_seconds':frames/RATE,'culture':identity[0],'recognizer_id':identity[1],
            'windows':receipts,'segments':segments,'text':' '.join(r['text'] for r in segments),
            'status':'recognized' if segments else 'no_speech_recognized','accuracy_verified':False,
            'speaker_identification':False,'speaker_separation':False,'boundary_limitation':'Speech spanning window boundaries may be missed or split.'}

def save(root,plan,result,cancelled=None,*,approved=False):
    if approved is not True:raise PermissionError('Explicit transcript save approval required')
    stopped(cancelled);raw,dst=validate(root,plan)
    if not isinstance(result,dict) or result.get('schema')!='janus-audio-transcription-result-v1' or result.get('source_sha256')!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Transcript source identity differs')
    payload=json.dumps(result,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')
    def revalidate():
        stopped(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'status':'transcript_saved','output':plan['output'],'sha256':digest,'accuracy_verified':False}
