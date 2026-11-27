"""Optional owner-installed Piper neural voice renderer; no runtime or voice downloads."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import tempfile
import time
import wave
from array import array
import sys
from . import typed_project_tool as guard
from .source_security import exclusions,linked,identity
from .structured_source import strict_json

MAX_MODEL=128*1024**2
MAX_CONFIG=1024*1024
MAX_EXE=32*1024**2
MAX_WAV=16*1024**2
MEMORY_LIMIT=512*1024**2
def exact_file(path,limit):
    path=Path(path)
    if not path.is_absolute() or path.resolve(strict=True)!=path or not path.is_file() or any(linked(p) for p in (path,*path.parents) if p.exists()):
        raise ValueError('Use an exact regular installed file, not a linked path')
    before=path.stat()
    if not 1<=before.st_size<=limit:raise ValueError('Installed file exceeds supported bound')
    digest=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while True:
            part=stream.read(min(1024*1024,limit-size+1))
            if not part:break
            size+=len(part)
            if size>limit:raise ValueError('Installed file exceeds supported bound')
            digest.update(part)
    if size!=before.st_size or identity(path.stat())!=identity(before) or linked(path):raise ValueError('Installed file changed during review')
    return {'path':str(path),'size':size,'sha256':digest.hexdigest()}

def installed(root,exe,model):
    root=Path(root).resolve(strict=True);exe=Path(exe);model=Path(model)
    if exe.name.casefold()!='piper.exe' or model.suffix.casefold()!='.onnx':raise ValueError('Select an installed Piper executable and local ONNX voice')
    if any(p.resolve(strict=True).is_relative_to(root) for p in (exe,model)):raise ValueError('Do not execute project-supplied engines or voices')
    config=model.with_name(model.name+'.json')
    files=[exact_file(exe,MAX_EXE),exact_file(model,MAX_MODEL),exact_file(config,MAX_CONFIG)]
    raw=config.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=files[2]['sha256']:raise ValueError('Voice config changed')
    value=strict_json(raw.decode('utf-8-sig'))
    if not isinstance(value,dict) or not isinstance(value.get('audio'),dict) or type(value['audio'].get('sample_rate')) is not int or value['audio']['sample_rate'] not in (16000,22050,24000,44100,48000):
        raise ValueError('Unsupported Piper voice sample rate')
    if type(value.get('num_speakers')) is not int or value['num_speakers']!=1:raise ValueError('This initial integration supports single-speaker voice files only')
    if value.get('phoneme_type') not in ('espeak','text'):raise ValueError('Unsupported voice phoneme configuration')
    return files,value['audio']['sample_rate']

def settings(text,length,noise,variation):
    if not isinstance(text,str) or not text.strip() or len(text)>1000 or any((ord(v)<32 and v not in '\n\t') or 0xd800<=ord(v)<=0xdfff for v in text) or '[[' in text:
        raise ValueError('Use bounded plain text, not raw phonemes or markup commands')
    for v,lo,hi in ((length,.7,1.5),(noise,0,1),(variation,0,1)):
        if type(v) not in (float,int) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Synthesis controls outside bounds')
    return {'text':text,'length_scale':length,'noise_scale':noise,'noise_w_scale':variation}

def review(root,exe,model,output,text,length,noise,variation,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    guard.path_for(root,output,exclude,{'.wav'},exists=False)
    controls=settings(text,length,noise,variation);files,rate=installed(root,exe,model)
    return {'schema':'janus-piper-neural-speech-v1','root':str(root),'output':output,'exclude':exclude,'files':files,'sample_rate':rate,
            'controls':controls,'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','output','exclude','files','sample_rate','controls','expires_at'} or plan['schema']!='janus-piper-neural-speech-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid or expired neural speech review')
    controls=plan['controls']
    if not isinstance(controls,dict) or set(controls)!={'text','length_scale','noise_scale','noise_w_scale'}:raise ValueError('Invalid synthesis settings')
    settings(controls['text'],controls['length_scale'],controls['noise_scale'],controls['noise_w_scale'])
    if not isinstance(plan['files'],list) or len(plan['files'])!=3:raise ValueError('Missing installed identities')
    files,rate=installed(root,plan['files'][0]['path'],plan['files'][1]['path'])
    if files!=plan['files'] or rate!=plan['sample_rate']:raise ValueError('Installed engine or voice changed since review')
    return guard.path_for(root,plan['output'],plan['exclude'],{'.wav'},exists=False)

def inspect(raw,rate):
    if not isinstance(raw,bytes) or not 44<=len(raw)<=MAX_WAV:raise ValueError('Neural WAV outside supported byte bound')
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            frames=f.getnframes()
            if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getcomptype())!=(1,2,rate,'NONE') or not rate*.25<=frames<=rate*120:raise ValueError('Unexpected output WAV format or duration')
            pcm=f.readframes(frames)
            if len(pcm)!=frames*2:raise ValueError('Truncated output')
    except (wave.Error,EOFError) as exc:raise ValueError('Invalid output WAV') from exc
    samples=array('h');samples.frombytes(pcm)
    if sys.byteorder!='little':samples.byteswap()
    peak=max(abs(v) for v in samples)
    if peak<250 or sum(abs(v)>=100 for v in samples)<len(samples)*.005:raise ValueError('Output silent or nearly silent')
    return {'sample_rate':rate,'duration_seconds':round(frames/rate,6),'peak':peak,'sha256':hashlib.sha256(raw).hexdigest()}

def stopped(cancelled):
    if cancelled and cancelled():raise ValueError('Neural speech cancelled')

class Piper:
    def render(self,plan,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary renderer required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-piper-') as temp:
            folder=Path(temp);text=folder/'text.txt';out=folder/'speech.wav';log=folder/'piper.log'
            text.write_text(plan['controls']['text'],encoding='utf-8')
            exe,model,config=(f['path'] for f in plan['files']);c=plan['controls']
            command=[exe,'--model',model,'--config',config,'--input-file',str(text),'--output-file',str(out),
                     '--length-scale',str(c['length_scale']),'--noise-scale',str(c['noise_scale']),'--noise-w-scale',str(c['noise_w_scale'])]
            # Explicitly owner-selected installed engine; Job Objects constrain resources,
            # not network access or file permissions of a malicious executable.
            with child_server(command,Path(exe).parent,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                end=time.monotonic()+150
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=end:raise TimeoutError('Piper timed out')
                    if any(p.exists() and p.stat().st_size>limit for p,limit in ((out,MAX_WAV),(log,1024*1024))):raise ValueError('Piper output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed Piper failed under resource cap')
            stopped(cancelled)
            if not out.is_file() or out.is_symlink():raise ValueError('No output produced')
            return guard.read_bound(out,MAX_WAV)

def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit neural speech render approval required')
    stopped(cancelled);dst=validate(root,plan)
    raw=(backend or Piper()).render(plan,cancelled)
    stopped(cancelled);info=inspect(raw,plan['sample_rate'])
    def revalidate():
        stopped(cancelled);validate(root,plan)
    digest=guard.publish(raw,dst,revalidate)
    return {'status':'speech_wav_published','output':plan['output'],'sha256':digest,**info,
            'backend':'owner-installed Piper CLI','expressive_quality_verified':False,'intelligibility_verified':False,'voice_cloning':False}
