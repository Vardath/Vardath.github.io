"""Bounded, reviewed PCM repair for isolated impulses, DC offset and mains hum."""
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

SCHEMA='janus-audio-restoration-v1'
EXTRA=('audio','.wav')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','remove_dc','hum_hz','click_threshold'} or not isinstance(spec['audio'],str) or type(spec['remove_dc']) is not bool:
        raise ValueError('Expected PCM WAV and explicit restoration controls')
    if type(spec['hum_hz']) is not int or spec['hum_hz'] not in (0,50,60):raise ValueError('Hum notch must be off, 50 or 60 Hz')
    t=spec['click_threshold']
    if type(t) is not int or not (t==0 or 2000<=t<=32767):raise ValueError('Click threshold must be 0 or 2000–32767 PCM units')
    if not (spec['remove_dc'] or spec['hum_hz'] or t):raise ValueError('Choose at least one repair operation')
    return spec

def notch(rate,hz):
    omega=2*math.pi*hz/rate;alpha=math.sin(omega)/60
    a0=1+alpha;middle=-2*math.cos(omega)/a0
    return (1/a0,middle,1/a0,middle,(1-alpha)/a0)

def restore(raw,spec):
    spec=checked(spec);samples,rate,channels,frames=pcm(raw)
    out=array('d',samples);clicks=[0]*channels;threshold=spec['click_threshold']
    if threshold:
        # Use the immutable original neighbours, not previously repaired samples.
        for i in range(1,frames-1):
            for c in range(channels):
                j=i*channels+c;a,b,v=samples[j-channels],samples[j+channels],samples[j]
                if abs(a-b)<=threshold/4 and (v-max(a,b)>=threshold or min(a,b)-v>=threshold):
                    out[j]=(a+b)/2;clicks[c]+=1
    before=[sum(samples[c::channels])/frames for c in range(channels)]
    removed=[0.0]*channels
    if spec['remove_dc']:
        removed=[sum(out[c::channels])/frames for c in range(channels)]
        for j in range(len(out)):out[j]-=removed[j%channels]
    if spec['hum_hz']:
        b0,b1,b2,a1,a2=notch(rate,spec['hum_hz'])
        for c in range(channels):
            x1=x2=y1=y2=0.0
            for j in range(c,len(out),channels):
                x=out[j];y=b0*x+b1*x1+b2*x2-a1*y1-a2*y2
                out[j]=y;x2,x1,y2,y1=x1,x,y1,y
    peak=max(abs(v) for v in out)
    if not math.isfinite(peak):raise ValueError('Unstable restoration output')
    # Apply one shared gain only when necessary to avoid new clipping.
    gain=min(1.0,32767/peak) if peak else 1.0
    repaired=array('h',(round(v*gain) for v in out))
    payload=encode(repaired,rate,channels);wav(payload,max_chunks=16)
    decoded,r,c,f=pcm(payload)
    if (r,c,f)!=(rate,channels,frames) or decoded!=repaired:raise ValueError('Restored PCM roundtrip failed')
    after=[sum(decoded[c::channels])/frames for c in range(channels)]
    return payload,{'sample_rate':rate,'channels':channels,'frames':frames,'isolated_sample_repairs':clicks,
        'dc_before_pcm':before,'dc_removed_pcm':removed,'dc_after_pcm':after,'hum_notch_hz':spec['hum_hz'],
        'hum_notch_q':30 if spec['hum_hz'] else None,'linked_headroom_gain':gain,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'listening_verified':False,
        'metadata_preserved':False,'scope':'Single-sample impulse interpolation, mean offset removal and optional narrow mains-frequency notch only. May affect wanted sound; does not reconstruct clipped or missing audio.'}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan);_,rate,channels,frames=pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_format={'sample_rate':rate,'channels':channels,'frames':frames},
        scope='Heuristic single-sample repairs, optional DC removal and narrow hum notch. May change desired signal. One shared attenuation if needed to prevent clipping. No overwrite.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=restore(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-audio-restoration-result-v1','status':'restored_pcm_verified','output':plan['output'],'sha256':sha,
            **receipt,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Restoration unavailable; inspect reviewed PCM and repair settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
