"""Optional pinned offline UVR/MDX-Net two-stem separation under the existing cap."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import time
import zipfile
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions,linked
from .tempo_detection import pcm
from .artifact_media_checks import wav
from .neural_speech import exact_file
from .speaker_diarisation import stopped,MEMORY_LIMIT,MAX_LOG,MAX_FILE

EXE='sherpa-onnx-offline-source-separation.exe'
MODEL='UVR_MDXNET_1_9703.onnx'
MODEL_SHA='1edd6f6891afd845cdc5b325d008075007ccffa6965861ae88411396d60fcc03'
MODEL_SIZE=29704740
RATE=44100
MAX_SECONDS=15
NAMES=('vocals.wav','accompaniment.wav')
MAX_WAV=RATE*MAX_SECONDS*4+65536
def input_pcm(raw):
    s,r,c,n=pcm(raw)
    if (r,c)!=(RATE,2) or n>RATE*MAX_SECONDS:raise ValueError('Requires 3–15 seconds of stereo 44.1 kHz PCM16 WAV')
    return s,n
def installed(root,exe,model):
    root=Path(root).resolve(strict=True);exe=Path(exe);model=Path(model)
    if exe.name.casefold()!=EXE or model.name!=MODEL or any(p.resolve(strict=True).is_relative_to(root) for p in (exe,model)):
        raise ValueError('Select trusted installed sherpa-onnx CLI and exact supported UVR model outside project')
    files=[exact_file(exe,MAX_FILE),exact_file(model,MAX_FILE)]
    if (files[1]['sha256'],files[1]['size'])!=(MODEL_SHA,MODEL_SIZE):raise ValueError('Model differs from pinned upstream release asset')
    return files
def review(root,source,output,exe,model,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.wav'},exists=True)
    guard.path_for(root,output,exclude,{'.zip'},exists=False)
    pin=snapshot_file(src);_,frames=input_pcm(guard.exact(src,pin,MAX_WAV))
    return {'schema':'janus-musical-stems-v1','root':str(root),'source':source,'output':output,'exclude':exclude,
            'guard':pin,'files':installed(root,exe,model),'frames':frames,'expires_at':int(time.time())+1800}
def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','files','frames','expires_at'} or plan['schema']!='janus-musical-stems-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid stem separation review')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.wav'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.zip'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed mix changed')
    raw=guard.exact(src,plan['guard'],MAX_WAV);_,frames=input_pcm(raw)
    if type(plan['frames']) is not int or plan['frames']!=frames:raise ValueError('Reviewed duration changed')
    if not isinstance(plan['files'],list) or len(plan['files'])!=2 or installed(root,*(f['path'] for f in plan['files']))!=plan['files']:
        raise ValueError('Installed engine or pinned model changed')
    return raw,dst
def command(plan,folder):
    exe,model=(f['path'] for f in plan['files'])
    return [exe,'--uvr-model='+model,'--num-threads=1','--provider=cpu',
            '--input-wav='+str(folder/'mix.wav'),'--output-vocals-wav='+str(folder/NAMES[0]),
            '--output-accompaniment-wav='+str(folder/NAMES[1])]
class Sherpa:
    def run(self,plan,raw,cancelled):
        stopped(cancelled)
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary engine required')
        from .triad_job import verify_root_cap,child_server
        _,available,total=verify_root_cap()
        if available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient foreground memory reserve')
        with tempfile.TemporaryDirectory(prefix='janus-stems-') as td:
            folder=Path(td);(folder/'mix.wav').write_bytes(raw);log=folder/'engine.log'
            with child_server(command(plan,folder),Path(plan['files'][0]['path']).parent,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+240
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Stem separation timed out')
                    for path,limit in [(log,MAX_LOG)]+[(folder/n,MAX_WAV) for n in NAMES]:
                        if path.exists() and path.stat().st_size>limit:raise ValueError('Engine output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed separation engine failed under cap')
            stopped(cancelled)
            outputs={}
            for name in NAMES:
                path=folder/name
                if not path.is_file() or linked(path):raise ValueError('Missing regular stem file')
                outputs[name]=guard.read_bound(path,MAX_WAV)
            return outputs
def verify(raw,outputs):
    original,frames=input_pcm(raw)
    if not isinstance(outputs,dict) or set(outputs)!=set(NAMES):raise ValueError('Exactly two model stems required')
    samples=[];records=[]
    for name in NAMES:
        data=outputs[name]
        if not isinstance(data,bytes) or len(data)>MAX_WAV:raise ValueError('Stem exceeds byte bound')
        wav(data,max_chunks=16);decoded,r,c,n=pcm(data)
        if (r,c,n)!=(RATE,2,frames):raise ValueError('Stem rate, channels or frame count differs from mix')
        samples.append(decoded)
        records.append({'file':name,'sha256':hashlib.sha256(data).hexdigest(),'peak_pcm':max(abs(v) for v in decoded)})
    error=sum((a+b-v)**2 for a,b,v in zip(*samples,original))
    energy=sum(v*v for v in original)
    return {'schema':'janus-musical-stems-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'model_sha256':MODEL_SHA,'sample_rate':RATE,'channels':2,'frames':frames,'stems':records,
            'relative_reconstruction_rmse':round((error/energy)**.5,6) if energy else None,
            'semantic_quality_verified':False,'listening_verified':False,
            'scope':'Model-estimated vocals and accompaniment only; other individual instruments and overlapping voices are not separated.'}
def render(root,plan,cancelled=None,*,approved=False,backend=None):
    if approved is not True:raise PermissionError('Explicit mix and engine approval required')
    stopped(cancelled);raw,dst=validate(root,plan)
    outputs=(backend or Sherpa()).run(plan,raw,cancelled)
    stopped(cancelled);report=verify(raw,outputs);report['engine_sha256']=plan['files'][0]['sha256']
    files={**outputs,'manifest.json':json.dumps(report,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Stem bundle exceeds bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if set(z.namelist())!=set(files) or any(z.read(n)!=v for n,v in files.items()):raise ValueError('Stem bundle verification failed')
    def revalidate():
        stopped(cancelled);validate(root,plan)
    sha=guard.publish(payload,dst,revalidate)
    return {'status':'two_stem_bundle_saved','output':plan['output'],'sha256':sha,**report}
