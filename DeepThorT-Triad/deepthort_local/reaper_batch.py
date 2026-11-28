"""Reviewed fixed REAPER batch resampling of a single PCM WAV; no project/scripts/FX."""
from __future__ import annotations
import io
import os
from pathlib import Path
import tempfile
import time
import wave
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions, linked
from .neural_speech import exact_file
from .speaker_diarisation import stopped, MAX_LOG, MEMORY_LIMIT
from .disk_gate import require_storage

EXE='reaper.exe'
SCHEMA='janus-reaper-batch-v1'
RATES=(22050,44100,48000)
MAX_EXE=128*1024**2

def rate(value):
    if type(value) is not int or value not in RATES:raise ValueError('Use 22050, 44100 or 48000 Hz')
    return value

def audio(raw):
    if not isinstance(raw,bytes) or not 44<=len(raw)<=guard.MAX_INPUT:raise ValueError('WAV outside byte bound')
    try:
        with wave.open(io.BytesIO(raw),'rb') as w:
            n=w.getnframes();c=w.getnchannels();r=w.getframerate();width=w.getsampwidth()
            if not 1<=n<=60*r or c not in (1,2) or width!=2 or r not in RATES or w.getcomptype()!='NONE':
                raise ValueError('Use mono/stereo PCM16 WAV up to 60 seconds at supported sample rates')
            pcm=w.readframes(n)
            if len(pcm)!=n*c*2:raise ValueError('Truncated PCM data')
    except (wave.Error,EOFError) as e:raise ValueError('Invalid PCM WAV') from e
    return {'frames':n,'channels':c,'rate':r,'nonzero':any(pcm)}

def installed(root,exe):
    p=Path(exe)
    if p.name.casefold()!=EXE or p.resolve(strict=True).is_relative_to(root):
        raise ValueError('Choose trusted separately installed REAPER executable')
    return exact_file(p,MAX_EXE)

def review(root,source,output,exe,target,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.wav'},exists=True)
    guard.path_for(root,output,exclude,{'.wav'},exists=False)
    pin=snapshot_file(src);info=audio(guard.exact(src,pin,guard.MAX_INPUT))
    if rate(target)==info['rate']:raise ValueError('Choose a different target sample rate')
    return {'schema':SCHEMA,'root':str(root),'source':source,'output':output,'exclude':exclude,
            'guard':pin,'engine':installed(root,exe),'input':info,'target':target,'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','engine','input','target','expires_at'} or plan['schema']!=SCHEMA or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid reviewed REAPER plan')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.wav'},exists=False)
    if snapshot_file(src)!=plan['guard'] or installed(root,plan['engine']['path'])!=plan['engine']:
        raise ValueError('Reviewed WAV or REAPER executable changed')
    raw=guard.exact(src,plan['guard'],guard.MAX_INPUT)
    if audio(raw)!=plan['input'] or rate(plan['target'])==plan['input']['rate']:raise ValueError('Reviewed audio changed')
    return raw,dst

def config(plan,stage):
    source=str(stage/'input.wav');output=str(stage/'output.wav')
    if any(c in source+output for c in ('\t','\r','\n')):raise ValueError('Invalid staging path')
    # Fixed list grammar from REAPER's command-line help. WAV format is independently
    # checked after conversion; no FX chain, template, user script or arbitrary flags.
    return (source+'\t'+output+'\n<CONFIG\nSRATE '+str(rate(plan['target']))+
            '\nNCH '+str(plan['input']['channels'])+'\nCPULIMIT 1\n<OUTFMT\nZXZhdxAAAA==\n>\n>\n')

def command(plan,stage):
    return [plan['engine']['path'],'-newinst','-nosplash','-noactivate','-cfgfile',
            str(stage/'reaper.ini'),'-batchconvert',str(stage/'batch.txt')]

def verify(plan,payload):
    info=audio(payload);old=plan['input']
    # Allow two output frames of rounding, not truncated or unrelated duration.
    if info['rate']!=plan['target'] or info['channels']!=old['channels'] or abs(info['frames']*old['rate']-old['frames']*plan['target'])>2*old['rate'] or (old['nonzero'] and not info['nonzero']):
        raise ValueError('Unexpected REAPER output format, duration or silent conversion')
    return info

class Reaper:
    def run(self,plan,raw,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows REAPER required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-reaper-') as td:
            stage=Path(td);log=stage/'engine.log';out=stage/'output.wav'
            require_storage(stage)
            (stage/'input.wav').write_bytes(raw)
            (stage/'reaper.ini').write_bytes(b'')
            (stage/'batch.txt').write_text(config(plan,stage),encoding='utf-8')
            with child_server(command(plan,stage),stage,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+120
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('REAPER batch timed out')
                    for p,limit in ((log,MAX_LOG),(out,guard.MAX_OUTPUT)):
                        if p.exists() and p.stat().st_size>limit:raise ValueError('REAPER output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('REAPER batch failed under cap')
            stopped(cancelled)
            if not out.is_file() or linked(out):raise ValueError('Missing regular staged WAV')
            return guard.read_bound(out,guard.MAX_OUTPUT)

def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit DAW batch approval required')
    stopped(cancelled);raw,dst=validate(root,plan)
    payload=(backend or Reaper()).run(plan,raw,cancelled)
    stopped(cancelled);info=verify(plan,payload)
    def revalidate():
        stopped(cancelled);validate(root,plan)
    sha=guard.publish(payload,dst,revalidate)
    return {'schema':'janus-reaper-result-v1','output':plan['output'],'sha256':sha,'audio':info,
            'source_unchanged':True,'native_engine_used':backend is None,'quality_verified':False,'scope':'Single PCM16 WAV sample-rate conversion only'}
