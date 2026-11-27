"""Reviewed stereo spatial component extraction; not semantic source separation."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-spatial-source-isolation-v1'
EXTRA=('audio','.wav')
MODES=('center','side','left','right')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','component'} or not isinstance(spec['audio'],str) or spec['component'] not in MODES:
        raise ValueError('Expected stereo WAV and center, side, left or right component')
    return spec
def input_pcm(raw):
    samples,rate,channels,frames=pcm(raw)
    if channels!=2 or frames>20*rate:raise ValueError('Requires 3–20 seconds of stereo PCM16 WAV')
    return samples,rate,frames
def isolate(raw,spec):
    spec=checked(spec);samples,rate,frames=input_pcm(raw)
    selected=array('h');residual=array('h');mode=spec['component']
    for i in range(0,len(samples),2):
        l,r=samples[i],samples[i+1];mid=round((l+r)/2)
        if mode=='center':a,b=mid,mid
        elif mode=='side':a,b=l-mid,r-mid
        elif mode=='left':a,b=l,0
        else:a,b=0,r
        selected.extend((a,b));residual.extend((l-a,r-b))
    files={'selected.wav':encode(selected,rate,2),'residual.wav':encode(residual,rate,2)}
    for name,expected in (('selected.wav',selected),('residual.wav',residual)):
        wav(files[name],max_chunks=16);decoded,sr,ch,n=pcm(files[name])
        if (sr,ch,n)!=(rate,2,frames) or decoded!=expected:raise ValueError('Component PCM verification failed')
    if any(a+b!=v for a,b,v in zip(selected,residual,samples)):raise ValueError('PCM reconstruction mismatch')
    report={'schema':'janus-spatial-isolation-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'component':mode,'sample_rate':rate,'channels':2,'frames':frames,'duration_seconds':frames/rate,
            'components':[{'file':name,'sha256':hashlib.sha256(files[name]).hexdigest(),
                           'nonzero_samples':sum(v!=0 for v in data)}
                          for name,data in (('selected.wav',selected),('residual.wav',residual))],
            'sample_exact_reconstruction':True,'semantic_source_identification':False,
            'semantic_separation_verified':False,'listening_verified':False,'metadata_preserved':False,
            'scope':'Spatial components only. Center contains shared content, not necessarily vocals; side contains differences, not necessarily accompaniment. Mono mixtures and overlapping spatial sources cannot be separated by this method.'}
    files['manifest.json']=json.dumps(report,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Bundle exceeds byte bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if set(z.namelist())!=set(files) or any(z.read(n)!=v for n,v in files.items()):raise ValueError('Bundle verification failed')
    return payload,report
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,path=validate(root,plan);_,rate,frames=input_pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_format={'sample_rate':rate,'channels':2,'frames':frames},
                     scope='Spatial stereo extraction only, not automatic voice or instrument separation. Exact complementary residual, no overwrite.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,report=isolate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'spatial_component_bundle_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**report}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Spatial isolation unavailable; inspect stereo PCM and reviewed component'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
