"""Reviewed optional CPU demucs.cpp six-source instrument extraction."""
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import time
import zipfile
from array import array
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions,linked
from .tempo_detection import pcm
from .noise_reduction import encode
from .artifact_media_checks import wav
from .neural_speech import exact_file
from .speaker_diarisation import stopped,MEMORY_LIMIT,MAX_LOG,MAX_FILE

EXE='demucs.cpp.main.exe'
MODEL='ggml-model-htdemucs-6s-f16.bin'
NAMES=('drums','bass','other','vocals','guitar','piano')
INSTRUMENTS=('drums','bass','guitar','piano')
RATE=44100
MAX_SECONDS=8
MAX_WAV=RATE*MAX_SECONDS*8+65536
def input_pcm(raw):
    s,r,c,n=pcm(raw)
    if (r,c)!=(RATE,2) or n>RATE*MAX_SECONDS:raise ValueError('Requires 3–8 seconds of stereo 44.1 kHz PCM16 WAV')
    return s,n
def instrument(value):
    if value not in INSTRUMENTS:raise ValueError('Choose drums, bass, guitar or piano')
    return value
def installed(root,exe,model):
    root=Path(root).resolve(strict=True);exe=Path(exe);model=Path(model)
    if exe.name.casefold()!=EXE or model.name!=MODEL or any(p.resolve(strict=True).is_relative_to(root) for p in (exe,model)):
        raise ValueError('Select trusted installed demucs.cpp executable and six-source weights outside project')
    return [exact_file(exe,MAX_FILE),exact_file(model,MAX_FILE)]
def review(root,source,output,exe,model,target,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.wav'},exists=True)
    guard.path_for(root,output,exclude,{'.zip'},exists=False)
    pin=snapshot_file(src);_,frames=input_pcm(guard.exact(src,pin,MAX_WAV))
    return {'schema':'janus-instrument-isolation-v1','root':str(root),'source':source,'output':output,'exclude':exclude,
            'guard':pin,'files':installed(root,exe,model),'target':instrument(target),'frames':frames,'expires_at':int(time.time())+1800}
def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','files','target','frames','expires_at'} or plan['schema']!='janus-instrument-isolation-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid instrument review')
    instrument(plan['target'])
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.zip'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed mix changed')
    raw=guard.exact(src,plan['guard'],MAX_WAV);_,frames=input_pcm(raw)
    if type(plan['frames']) is not int or plan['frames']!=frames:raise ValueError('Reviewed duration changed')
    if not isinstance(plan['files'],list) or len(plan['files'])!=2 or installed(root,*(f['path'] for f in plan['files']))!=plan['files']:
        raise ValueError('Installed executable or weights changed')
    return raw,dst
def filename(name):
    return 'target_'+str(NAMES.index(name))+'_'+name+'.wav'
def command(plan,folder):
    exe,model=(f['path'] for f in plan['files'])
    return [exe,model,str(folder/'mix.wav'),str(folder/'out')]
def decode_float(raw,frames):
    if not isinstance(raw,bytes) or len(raw)>MAX_WAV:raise ValueError('Float WAV outside byte bound')
    wav(raw,max_chunks=16)
    pos=12;fmt=None;data=None
    while pos<len(raw):
        kind,n=struct.unpack_from('<4sI',raw,pos);start=pos+8
        if kind==b'fmt ':fmt=struct.unpack_from('<HHIIHH',raw,start)
        elif kind==b'data':data=raw[start:start+n]
        pos=start+n+(n&1)
    if fmt!=(3,2,RATE,RATE*8,8,32) or data is None or len(data)!=frames*8:
        raise ValueError('Expected aligned stereo IEEE float32 WAV at 44.1 kHz')
    out=array('f');out.frombytes(data)
    import sys
    if sys.byteorder!='little':out.byteswap()
    if any(not math.isfinite(v) or abs(v)>16 for v in out):raise ValueError('Nonfinite or excessive model samples')
    return out
class Demucs:
    def run(self,plan,raw,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary engine required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-instrument-') as td:
            folder=Path(td);(folder/'mix.wav').write_bytes(raw);out=folder/'out';out.mkdir();log=folder/'engine.log'
            names=[filename(n) for n in NAMES]
            with child_server(command(plan,folder),Path(plan['files'][0]['path']).parent,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+300
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Instrument isolation timed out')
                    for path,limit in [(log,MAX_LOG)]+[(out/n,MAX_WAV) for n in names]:
                        if path.exists() and path.stat().st_size>limit:raise ValueError('Engine output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed instrument engine failed under cap')
            stopped(cancelled)
            if {p.name for p in out.iterdir()}!=set(names):raise ValueError('Expected exact six-source output')
            result={}
            for name in NAMES:
                path=out/filename(name)
                if not path.is_file() or linked(path):raise ValueError('Missing regular stem file')
                result[name]=guard.read_bound(path,MAX_WAV)
            return result
def prepare(raw,outputs,target):
    original,frames=input_pcm(raw);instrument(target)
    if not isinstance(outputs,dict) or set(outputs)!=set(NAMES):raise ValueError('Expected six model stems')
    decoded={name:decode_float(outputs[name],frames) for name in NAMES}
    selected=decoded[target]
    # Other model stems form the complement; preserve relative balance with shared headroom.
    residual=array('d',(sum(decoded[name][i] for name in NAMES if name!=target) for i in range(len(original))))
    peak=max(max(abs(v) for v in selected),max(abs(v) for v in residual))
    gain=min(1.0,32767/(32768*peak)) if peak else 1.0
    a=array('h',(round(v*32768*gain) for v in selected));b=array('h',(round(v*32768*gain) for v in residual))
    files={'instrument.wav':encode(a,RATE,2),'other_stems.wav':encode(b,RATE,2)}
    for name,s in zip(files,(a,b)):
        decoded_pcm,r,c,n=pcm(files[name]);wav(files[name],max_chunks=16)
        if (r,c,n)!=(RATE,2,frames) or decoded_pcm!=s:raise ValueError('Output PCM verification failed')
    energy=sum(v*v for v in original)
    error=sum((x+y-v)**2 for x,y,v in zip(a,b,original))
    report={'schema':'janus-instrument-isolation-result-v1','target':target,'source_sha256':hashlib.sha256(raw).hexdigest(),
            'sample_rate':RATE,'channels':2,'frames':frames,'shared_gain':gain,
            'relative_reconstruction_rmse':round((error/energy)**.5,6) if energy else None,
            'model_outputs':[{'name':n,'sha256':hashlib.sha256(outputs[n]).hexdigest()} for n in NAMES],
            'files':[{'file':n,'sha256':hashlib.sha256(v).hexdigest()} for n,v in files.items()],
            'semantic_quality_verified':False,'listening_verified':False,
            'scope':'Estimated target and sum of other model stems. Not exact instrument recovery; no claim of isolation quality.'}
    return files,report
def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit instrument isolation approval required')
    stopped(cancelled);raw,dst=validate(root,plan)
    outputs=(backend or Demucs()).run(plan,raw,cancelled)
    stopped(cancelled);files,report=prepare(raw,outputs,plan['target'])
    report['engine_sha256']=plan['files'][0]['sha256'];report['model_sha256']=plan['files'][1]['sha256']
    files['manifest.json']=json.dumps(report,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if set(z.namelist())!=set(files) or any(z.read(n)!=v for n,v in files.items()):raise ValueError('Bundle verification failed')
    def revalidate():
        stopped(cancelled);validate(root,plan)
    sha=guard.publish(payload,dst,revalidate)
    return {'status':'instrument_bundle_saved','output':plan['output'],'sha256':sha,**report}
