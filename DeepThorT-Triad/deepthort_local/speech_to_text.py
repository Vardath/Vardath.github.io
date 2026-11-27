"""Bounded, explicitly requested local Windows dictation from reviewed PCM WAV."""
from __future__ import annotations
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
import wave
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions
from .structured_source import strict_json

RATE=16000
MAX_SECONDS=30
MEMORY_LIMIT=512*1024**2
MAX_WAV=2*1024**2
LANG=re.compile(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){1,3}\Z')
def stopped(cancelled):
    if cancelled and cancelled():raise ValueError('Speech recognition cancelled')
def audio(raw):
    if not isinstance(raw,bytes) or not 44<=len(raw)<=MAX_WAV:raise ValueError('Invalid bounded WAV')
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            frames=f.getnframes()
            if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getcomptype())!=(1,2,RATE,'NONE') or not RATE<=frames<=RATE*MAX_SECONDS:
                raise ValueError('Requires 1–30 seconds mono 16 kHz PCM16 WAV')
            pcm=f.readframes(frames)
            if len(pcm)!=frames*2:raise ValueError('Truncated recording')
    except (wave.Error,EOFError) as exc:raise ValueError('Invalid PCM WAV') from exc
    # Canonicalize the staged file, not the original, avoiding arbitrary RIFF metadata.
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm)
    return out.getvalue(),frames/RATE
def language(value):
    if not isinstance(value,str) or not LANG.fullmatch(value):raise ValueError('Use exact installed recognizer culture such as en-AU or en-US')
    return value
def review(root,relative,culture,excluded=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(excluded);language(culture)
    src=guard.path_for(root,relative,exclude,{'.wav'},exists=True)
    identity=snapshot_file(src);raw=guard.exact(src,identity,MAX_WAV);_,seconds=audio(raw)
    return {'schema':'janus-local-dictation-v1','root':str(root),'source':relative,'culture':culture,'exclude':exclude,'guard':identity,'expires_at':int(time.time())+1800},seconds
def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','culture','exclude','guard','expires_at'} or plan['schema']!='janus-local-dictation-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid reviewed source or approval expiry')
    language(plan['culture']);src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed audio changed')
    raw=guard.exact(src,plan['guard'],MAX_WAV)
    staged,seconds=audio(raw)
    return raw,staged,seconds

class WindowsRecognizer:
    def recognize(self,staged,culture,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Local Windows recognizer required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        exe=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        adapter=Path(__file__).resolve().parents[1]/'triad_recognize.ps1'
        if not exe.is_file() or not adapter.is_file():raise RuntimeError('Windows recognition adapter unavailable')
        with tempfile.TemporaryDirectory(prefix='janus-dictation-') as temp:
            folder=Path(temp)
            (folder/'input.wav').write_bytes(staged)
            (folder/'request.json').write_text(json.dumps({'culture':culture}),encoding='utf-8')
            command=[str(exe),'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','RemoteSigned','-File',str(adapter),'-Folder',str(folder)]
            with child_server(command,folder,folder/'recognizer.log',memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+90
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Local dictation timed out')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Windows dictation recognizer unavailable or failed')
                stopped(cancelled)
                result=folder/'result.json'
                if not result.is_file() or result.stat().st_size>131072:raise ValueError('Recognition receipt missing or oversized')
                return strict_json(result.read_text('utf-8'))

def normalize(result,culture,seconds):
    if not isinstance(result,dict) or set(result)!={'culture','recognizer_id','segments'} or not isinstance(result['culture'],str) or result['culture'].casefold()!=culture.casefold() or not isinstance(result['recognizer_id'],str) or not 1<=len(result['recognizer_id'])<=500 or not isinstance(result['segments'],list) or len(result['segments'])>128:
        raise ValueError('Unexpected recognizer identity or result')
    segments=[];total=0;end=0
    for row in result['segments']:
        if not isinstance(row,dict) or set(row)!={'text','confidence','start_seconds','duration_seconds'}:raise ValueError('Invalid recognition segment')
        text=row['text'];confidence=row['confidence'];start=row['start_seconds'];length=row['duration_seconds']
        if not isinstance(text,str) or not text.strip() or len(text)>4000 or any((ord(v)<32 and v not in '\n\t') or 0xd800<=ord(v)<=0xdfff for v in text):
            raise ValueError('Invalid recognition text')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (confidence,start,length)) or not 0<=confidence<=1 or start<0 or length<=0 or start+length>seconds+.1 or start<end-.05:
            raise ValueError('Invalid recognition timing or confidence')
        end=start+length;total+=len(text)
        if total>16000:raise ValueError('Transcript exceeds bound')
        segments.append({'text':text,'confidence':round(confidence,5),'start_seconds':round(start,5),'duration_seconds':round(length,5)})
    return {'culture':result['culture'],'recognizer_id':result['recognizer_id'],'segments':segments,'text':' '.join(s['text'] for s in segments),'status':'recognized' if segments else 'no_speech_recognized'}

def recognize(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit speech recognition approval required')
    stopped(cancelled);raw,staged,seconds=validate(root,plan)
    result=(backend or WindowsRecognizer()).recognize(staged,plan['culture'],cancelled)
    stopped(cancelled);validate(root,plan)
    return {'schema':'janus-local-dictation-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),'audio_seconds':seconds,
            **normalize(result,plan['culture'],seconds),'accuracy_verified':False,'automatically_submitted':False}
