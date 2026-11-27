"""Reviewed local PCM voice effects; not voice cloning or neural conversion."""
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

SCHEMA='janus-voice-transformation-v1'
EXTRA=('audio','.wav')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'audio','speed_percent','ring_hz','ring_depth_percent','lowpass_hz'} or not isinstance(s['audio'],str):
        raise ValueError('Expected mono WAV and reviewed voice effect settings')
    for key,lo,hi in (('speed_percent',75,150),('ring_hz',0,120),('ring_depth_percent',0,100),('lowpass_hz',0,3000)):
        if type(s[key]) is not int or not lo<=s[key]<=hi:raise ValueError('Invalid '+key)
    if (s['ring_hz']==0)!=(s['ring_depth_percent']==0) or 0<s['ring_hz']<20:
        raise ValueError('Ring modulation requires 20–120 Hz and nonzero depth, or both off')
    if 0<s['lowpass_hz']<600:raise ValueError('Low-pass cutoff must be off or 600–3000 Hz')
    if s['speed_percent']==100 and not s['ring_hz'] and not s['lowpass_hz']:raise ValueError('Select at least one voice effect')
    return s

def input_pcm(raw,s):
    samples,rate,channels,frames=pcm(raw)
    if channels!=1 or not 5*rate<=frames<=20*rate:raise ValueError('Use 5–20 seconds of mono PCM16 WAV')
    if max(abs(x) for x in samples)<100:raise ValueError('Silent or nearly silent input')
    n=(frames*100+s['speed_percent']-1)//s['speed_percent']
    if not 3*rate<=n<=30*rate:raise ValueError('Output duration outside bounds')
    return samples,rate,frames,n

def transform(raw,s):
    s=checked(s);samples,rate,frames,n=input_pcm(raw,s)
    speed=s['speed_percent'];ring=s['ring_hz'];depth=s['ring_depth_percent']/100
    # For faster playback, attenuate content near the new Nyquist before interpolation.
    # This one-pole filter is conservative, not a high-quality bandlimited resampler.
    prefilter=rate*.40*100/speed if speed>100 else None
    if prefilter:
        k=1-math.exp(-2*math.pi*prefilter/rate);previous=float(samples[0]);filtered=array('d')
        for x in samples:
            previous+=k*(x-previous);filtered.append(previous)
    else:filtered=samples
    cutoff=s['lowpass_hz'];alpha=1-math.exp(-2*math.pi*cutoff/rate) if cutoff else 1.
    state=0.;out=array('h')
    for i in range(n):
        j,f=divmod(i*speed,100);j=min(j,frames-1)
        x=(filtered[j]*(100-f)+filtered[min(j+1,frames-1)]*f)/100
        if ring:x*=1-depth+depth*math.cos(2*math.pi*ring*i/rate)
        state+=alpha*(x-state)
        out.append(max(-32768,min(32767,round(state))))
    if not any(out) or (n==frames and out==samples):raise ValueError('No measurable voice effect')
    payload=encode(out,rate,1);wav(payload,max_chunks=16)
    decoded,sr,ch,count=pcm(payload)
    if (sr,ch,count)!=(rate,1,n) or decoded!=out:raise ValueError('PCM roundtrip failed')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),'sample_rate':rate,'channels':1,
        'source_frames':frames,'output_frames':n,'speed_percent':speed,
        'pitch_ratio':speed/100,'duration_preserved':n==frames,
        'ring_hz':ring,'ring_depth_percent':s['ring_depth_percent'],'lowpass_hz':cutoff,
        'output_peak_pcm':max(abs(x) for x in out),'pcm_verified':True,
        'independent_pitch_shift':False,'voice_identity_conversion':False,'listening_verified':False}

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan);_,rate,frames,n=input_pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,source_format={'sample_rate':rate,'frames':frames},output_frames=n,
        scope='Varispeed changes pitch AND duration; optional ring modulation and low-pass tone. No identity imitation, formant-preserving pitch shift or neural conversion.')

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)

def execute(root,plan):
    s,dst,path=validate(root,plan);payload,receipt=transform(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'reviewed_voice_effect_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed voice effect unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
