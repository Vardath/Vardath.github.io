"""Reviewed bounded linked dynamics and RMS-based audio mastering."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav
from deepthort_local.automated_audio_mixing import number,db

SCHEMA='janus-automated-mastering-v1'
EXTRA=('audio','.wav')
MAX_SECONDS=30
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','threshold_dbfs','ratio','attack_ms','release_ms','target_rms_dbfs','max_boost_db','peak_dbfs'} or not isinstance(spec['audio'],str):
        raise ValueError('Expected PCM WAV and explicit dynamics/mastering settings')
    for key,lo,hi in (('threshold_dbfs',-36,-6),('ratio',1,8),('attack_ms',1,100),('release_ms',20,500),
                      ('target_rms_dbfs',-30,-10),('max_boost_db',0,12),('peak_dbfs',-12,-1)):
        if not number(spec[key],lo,hi):raise ValueError('Invalid mastering setting: '+key)
    return spec
def input_pcm(raw):
    samples,rate,channels,frames=pcm(raw)
    if frames>MAX_SECONDS*rate:raise ValueError('Mastering duration exceeds bound')
    rms=math.sqrt(sum(v*v for v in samples)/len(samples))
    if rms<=32768*10**(-60/20):raise ValueError('Silence or nearly silent input')
    return samples,rate,channels,frames,rms
def master(raw,spec):
    spec=checked(spec);samples,rate,channels,frames,before=input_pcm(raw)
    attack=math.exp(-1/(rate*spec['attack_ms']/1000))
    release=math.exp(-1/(rate*spec['release_ms']/1000))
    threshold=32768*10**(spec['threshold_dbfs']/20)
    env=0.;compressed=array('d');min_gain=1.
    for i in range(0,len(samples),channels):
        level=max(abs(samples[i+c]) for c in range(channels))
        coefficient=attack if level>env else release
        env=coefficient*env+(1-coefficient)*level
        gain=(env/threshold)**(1/spec['ratio']-1) if env>threshold else 1.
        min_gain=min(min_gain,gain)
        compressed.extend(samples[i+c]*gain for c in range(channels))
    rms=math.sqrt(sum(v*v for v in compressed)/len(compressed))
    makeup_db=max(-36,min(spec['max_boost_db'],spec['target_rms_dbfs']-db(rms)))
    makeup=10**(makeup_db/20)
    peak=max(abs(v) for v in compressed)
    ceiling=math.floor(32767*10**(spec['peak_dbfs']/20))
    # Shared attenuation avoids clipping, without sample-specific distortion.
    headroom=min(1.,ceiling/(peak*makeup))
    out=array('h',(round(v*makeup*headroom) for v in compressed))
    if not any(out):raise ValueError('Mastered signal below PCM resolution')
    payload=encode(out,rate,channels);wav(payload,max_chunks=16)
    decoded,r,c,n=pcm(payload)
    if (r,c,n)!=(rate,channels,frames) or decoded!=out:raise ValueError('PCM roundtrip failed')
    after=math.sqrt(sum(v*v for v in out)/len(out))
    return payload,{'sample_rate':rate,'channels':channels,'frames':frames,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'input_rms_dbfs':round(db(before),6),
        'output_rms_dbfs':round(db(after),6),'input_peak_pcm':max(abs(v) for v in samples),
        'output_peak_pcm':max(abs(v) for v in out),'max_compression_reduction_db':round(-20*math.log10(min_gain),6),
        'makeup_gain_db':round(makeup_db,6),'shared_headroom_gain':headroom,
        'target_rms_dbfs':spec['target_rms_dbfs'],'peak_ceiling_dbfs':spec['peak_dbfs'],
        'method':'linked peak-envelope compression, bounded RMS makeup and shared sample-peak attenuation',
        'lufs_verified':False,'true_peak_verified':False,'listening_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan)
    _,r,c,n,rms=input_pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_format={'sample_rate':r,'channels':c,'frames':n,'rms_dbfs':db(rms)},
        scope='Linked dynamics and RMS/sample-peak control only; no LUFS, true peak, EQ or listening claim.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,report=master(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-automated-mastering-result-v1','status':'mastered_pcm_verified','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**report}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed audio, dynamics settings or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
