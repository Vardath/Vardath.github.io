"""Reviewed local speaker diarisation: per-recording labels, no identity or voiceprint storage."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions
from .audio_transcription import pcm,MAX_BYTES,RATE
from .neural_speech import exact_file

MAX_FILE=128*1024**2
MAX_LOG=1024*1024
MEMORY_LIMIT=512*1024**2
EXE='sherpa-onnx-offline-speaker-diarization.exe'
ROW=re.compile(r'(\d{1,3}\.\d{3}) -- (\d{1,3}\.\d{3}) speaker_(\d{1,3})')

def stopped(cancelled):
    if cancelled and cancelled():raise ValueError('Diarisation cancelled')

def installed(root,exe,segmentation,embedding):
    root=Path(root).resolve(strict=True)
    paths=[Path(x) for x in (exe,segmentation,embedding)]
    if paths[0].name.casefold()!=EXE or any(p.suffix.casefold()!='.onnx' for p in paths[1:]):
        raise ValueError('Select installed sherpa-onnx CLI and local segmentation/embedding models')
    if any(p.resolve(strict=True).is_relative_to(root) for p in paths) or len(set(paths))!=3:
        raise ValueError('Select distinct trusted installed files outside the project')
    files=[exact_file(p,MAX_FILE) for p in paths]
    if files[1]['sha256']==files[2]['sha256']:raise ValueError('Segmentation and embedding models must differ')
    return files

def count(value):
    if type(value) is not int or not (value==-1 or 2<=value<=8):
        raise ValueError('Specify -1 to estimate speakers or an expected count of 2–8')
    return value

def review(root,source,output,exe,segmentation,embedding,expected=-1,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.wav'},exists=True)
    guard.path_for(root,output,exclude,{'.json'},exists=False)
    pin=snapshot_file(src);_,frames=pcm(guard.exact(src,pin,MAX_BYTES))
    return {'schema':'janus-anonymous-diarisation-v1','root':str(root),'source':source,'output':output,
            'exclude':exclude,'guard':pin,'files':installed(root,exe,segmentation,embedding),
            'expected':count(expected),'audio_seconds':frames/RATE,'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','files','expected','audio_seconds','expires_at'} or plan['schema']!='janus-anonymous-diarisation-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid diarisation review')
    count(plan['expected'])
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.json'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed recording changed')
    raw=guard.exact(src,plan['guard'],MAX_BYTES);_,frames=pcm(raw)
    if plan['audio_seconds']!=frames/RATE:raise ValueError('Recording duration changed')
    if not isinstance(plan['files'],list) or len(plan['files'])!=3 or installed(root,*(f['path'] for f in plan['files']))!=plan['files']:
        raise ValueError('Installed engine or models changed')
    return raw,dst

def command(plan,staged):
    exe,seg,emb=(f['path'] for f in plan['files'])
    clustering='--clustering.cluster-threshold=0.90' if plan['expected']==-1 else '--clustering.num-clusters='+str(plan['expected'])
    return [exe,'--segmentation.pyannote-model='+seg,'--embedding.model='+emb,
            '--segmentation.num-threads=1','--embedding.num-threads=1',
            '--segmentation.provider=cpu','--embedding.provider=cpu',clustering,str(staged)]

def parse(log,seconds):
    if not isinstance(log,bytes) or not 1<=len(log)<=MAX_LOG:raise ValueError('Diarisation log outside bound')
    text=log.decode('utf-8',errors='strict');rows=[];labels={};started=False;previous=-1;ends={}
    for line in text.splitlines():
        line=line.strip()
        if line=='Started':
            if started:raise ValueError('Repeated engine start')
            started=True;continue
        match=ROW.fullmatch(line)
        if match:
            if not started:raise ValueError('Segment before engine start')
            start,end=float(match[1]),float(match[2]);key=int(match[3])
            # CLI rounds to milliseconds, so tolerate only one millisecond at the recording end.
            if not 0<=start<end<=seconds+.001 or start<previous or start<ends.get(key,0):
                raise ValueError('Invalid, unordered or same-speaker overlapping segment')
            end=min(end,seconds)
            if end<=start:raise ValueError('Segment outside recording')
            if key not in labels:
                if len(labels)>=8:raise ValueError('Speaker count exceeds supported bound')
                labels[key]='Speaker '+str(len(labels)+1)
            rows.append({'speaker':labels[key],'start_seconds':start,'end_seconds':end})
            if len(rows)>1000:raise ValueError('Segment count exceeds supported bound')
            previous=start;ends[key]=end
        elif started and ('speaker_' in line or re.match(r'^\d+\.\d+\s+--',line)):
            raise ValueError('Unrecognized segment format')
    if not started or not rows:raise ValueError('No supported diarisation segments confirmed')
    return rows

class Sherpa:
    def run(self,plan,raw,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary engine required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-diarisation-') as temp:
            folder=Path(temp);audio=folder/'recording.wav';log=folder/'engine.log'
            audio.write_bytes(raw)
            # Local tool chosen by owner; inherited Job Object limits resources, not security permissions.
            with child_server(command(plan,audio),Path(plan['files'][0]['path']).parent,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+180
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Diarisation timed out')
                    if log.exists() and log.stat().st_size>MAX_LOG:raise ValueError('Engine log exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed diarisation engine failed')
            stopped(cancelled)
            return guard.read_bound(log,MAX_LOG)

def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit recording and engine approval required')
    stopped(cancelled);raw,dst=validate(root,plan)
    rows=parse((backend or Sherpa()).run(plan,raw,cancelled),plan['audio_seconds'])
    stopped(cancelled)
    actual=len({r['speaker'] for r in rows})
    result={'schema':'janus-anonymous-diarisation-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'engine_sha256':plan['files'][0]['sha256'],'model_sha256':[f['sha256'] for f in plan['files'][1:]],
            'audio_seconds':plan['audio_seconds'],'expected_speakers':plan['expected'],'observed_labels':actual,
            'segments':rows,'speaker_identification':False,'cross_recording_matching':False,
            'voiceprints_retained':False,'accuracy_verified':False,'audio_separated':False,
            'note':'Labels are anonymous and unique only within this recording; overlapping speech may be imperfect.'}
    payload=json.dumps(result,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')
    def revalidate():
        stopped(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'status':'diarisation_report_saved','output':plan['output'],'sha256':digest,**result}
