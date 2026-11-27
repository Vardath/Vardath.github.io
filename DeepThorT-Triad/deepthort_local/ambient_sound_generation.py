"""Reviewed procedural stereo ambience with periodic circular filtering."""
from __future__ import annotations
import argparse
from array import array
import io
import json
import math
from pathlib import Path
import random
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-ambient-sound-generation-v1'
RATE=24000
PROFILES=('wind','rain','machine_hum')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'profile','duration_seconds','intensity_percent','stereo_width_percent','seed','peak_dbfs'} or s['profile'] not in PROFILES:
        raise ValueError('Expected a supported ambient profile and exact controls')
    for key,lo,hi in (('duration_seconds',4,20),('intensity_percent',10,100),('stereo_width_percent',0,100),('seed',0,2147483647),('peak_dbfs',-30,-3)):
        if type(s[key]) is not int or not lo<=s[key]<=hi:raise ValueError('Invalid '+key)
    return s

def circular_mean(values,width):
    # Every output includes the same number of periodic source samples.
    n=len(values)
    if not 1<=width<=n:raise ValueError('Invalid circular window')
    acc=sum(values[-width+1:]) if width>1 else 0.
    out=array('d')
    for i,value in enumerate(values):
        acc+=value
        out.append(acc/width)
        acc-=values[(i-width+1)%n]
    return out

def texture(rng,n,profile):
    noise=array('d',(rng.uniform(-1,1) for _ in range(n)))
    if profile=='wind':
        return circular_mean(circular_mean(noise,32),96)
    if profile=='rain':
        smooth=circular_mean(noise,12)
        return array('d',(.65*(x-y)+.35*y for x,y in zip(noise,smooth)))
    return circular_mean(noise,24)

def generate(s):
    s=checked(s);n=RATE*s['duration_seconds'];profile=s['profile']
    rng=random.Random(s['seed'])
    common=texture(rng,n,profile);side=texture(rng,n,profile)
    width=s['stereo_width_percent']/100;strength=s['intensity_percent']/100
    phase=rng.uniform(0,2*math.pi);mod_phase=rng.uniform(0,2*math.pi)
    result=array('d')
    for i,(x,y) in enumerate(zip(common,side)):
        t=2*math.pi*i/n
        if profile=='wind':
            envelope=.65+.25*strength*math.sin(3*t+phase)+.10*math.cos(7*t+mod_phase)
            center=x*envelope;difference=y*envelope
        elif profile=='rain':
            envelope=.85+.15*strength*math.cos(5*t+phase)
            center=envelope*x;difference=envelope*y
        else:
            # Integral cycles across the clip preserve the periodic phase.
            base=60*s['duration_seconds']
            tone=.55*math.sin(base*t+phase)+.20*math.sin(2*base*t)+.10*math.sin(3*base*t+mod_phase)
            center=tone+.35*strength*x;difference=.35*strength*y
        result.extend((center+width*difference,center-width*difference))
    peak=max(abs(x) for x in result)
    if not math.isfinite(peak) or peak<=0:raise ValueError('No generated ambience')
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20))
    out=array('h',(round(x/peak*ceiling) for x in result))
    payload=encode(out,RATE,2);wav(payload,max_chunks=16)
    with wave.open(io.BytesIO(payload),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(2,2,RATE,n):
            raise ValueError('Unexpected WAV format')
        decoded=array('h');decoded.frombytes(f.readframes(n))
        if sys.byteorder!='little':decoded.byteswap()
    if decoded!=out or max(abs(x) for x in out)>ceiling:raise ValueError('PCM roundtrip failed')
    seam=[abs(out[c]-out[-2+c]) for c in range(2)]
    return payload,{'profile':profile,'sample_rate':RATE,'channels':2,'frames':n,'seed':s['seed'],
        'peak_pcm':max(abs(x) for x in out),'loop_boundary_delta_pcm':seam,
        'periodic_construction':True,'seam_audibility_verified':False,'pcm_verified':True,
        'neural_generation':False,'listening_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    return plan,dict(s,scope='Synthetic periodic stereo wind, rain or machine-hum texture, with measured seam delta. No real recordings or listening/inaudibility claim.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,receipt=generate(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'procedural_ambience_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed ambience unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
