"""Bounded procedural game sound effects with deterministic reviewed synthesis."""
from __future__ import annotations
import argparse
from array import array
import hashlib
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

SCHEMA='janus-sound-effect-generation-v1'
RATE=24000
MODES=('ui_beep','sweep','impact','whoosh')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'effect','duration_ms','start_hz','end_hz','noise_percent','seed','peak_dbfs'} or s['effect'] not in MODES:
        raise ValueError('Expected one supported procedural effect and explicit settings')
    for k,lo,hi in (('duration_ms',100,3000),('start_hz',40,5000),('end_hz',40,5000),('noise_percent',0,100),('seed',0,2147483647),('peak_dbfs',-24,-1)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid '+k)
    if s['effect']=='ui_beep' and (s['start_hz']!=s['end_hz'] or s['noise_percent']!=0):
        raise ValueError('UI beep requires constant frequency and no noise')
    if s['effect']=='sweep' and s['start_hz']==s['end_hz']:raise ValueError('Sweep requires frequency change')
    if s['effect']=='whoosh' and s['noise_percent']==0:raise ValueError('Whoosh requires noise')
    return s

def generate(s):
    s=checked(s);n=RATE*s['duration_ms']//1000;mode=s['effect']
    rand=random.Random(s['seed']);phase=0.;filtered=0.;raw=array('d')
    mix=s['noise_percent']/100
    for i in range(n):
        t=i/(n-1)
        hz=s['start_hz']+(s['end_hz']-s['start_hz'])*t
        phase+=2*math.pi*hz/RATE
        a=1-math.exp(-2*math.pi*hz/RATE)
        filtered+=a*(rand.uniform(-1,1)-filtered)
        if mode=='impact':env=min(1,t/.02)*math.exp(-7*t)*min(1,(1-t)/.04)
        elif mode=='whoosh':env=math.sin(math.pi*t)**2
        else:env=min(1,t/.08,(1-t)/.15)
        value=env*((1-mix)*math.sin(phase)+mix*filtered)
        raw.append(value)
    raw[0]=raw[-1]=0.
    peak=max(abs(x) for x in raw)
    if not math.isfinite(peak) or peak<=0:raise ValueError('No generated signal')
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20))
    out=array('h',(round(x/peak*ceiling) for x in raw))
    payload=encode(out,RATE,1);wav(payload,max_chunks=16)
    with wave.open(io.BytesIO(payload),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(1,2,RATE,n):
            raise ValueError('Output WAV format changed')
        decoded=array('h');decoded.frombytes(f.readframes(n))
        if sys.byteorder!='little':decoded.byteswap()
    if decoded!=out or max(abs(x) for x in decoded)>ceiling:raise ValueError('Output PCM verification failed')
    return payload,{'effect':mode,'sample_rate':RATE,'channels':1,'frames':n,'peak_pcm':max(abs(x) for x in out),
                    'seed':s['seed'],'procedural_synthesis':True,'pcm_verified':True,
                    'neural_generation':False,'listening_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    return plan,dict(s,scope='Generate synthetic short beep, sweep, impact or whoosh. No recordings, downloads or text-to-audio model. Listen before use.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,receipt=generate(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'procedural_effect_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed procedural effect unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
