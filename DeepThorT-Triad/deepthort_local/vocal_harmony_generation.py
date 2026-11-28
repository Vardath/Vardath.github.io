"""Reviewed interval harmonization of the synthetic sung-vowel score."""
from __future__ import annotations
import argparse
from array import array
import io
import json
import math
from pathlib import Path
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import singing_voice_generation as singer
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-vocal-harmony-generation-v1'
RATE=singer.RATE

def checked(s):
    if not isinstance(s,dict) or set(s)!={'score','parts','peak_dbfs'}:
        raise ValueError('Expected a reviewed vowel score and explicit harmony intervals')
    score=singer.checked(s['score'])
    if sum(n['duration_ms'] for n in score['notes'])>8000:
        raise ValueError('Harmony score must not exceed eight seconds')
    if type(s['peak_dbfs']) is not int or not -24<=s['peak_dbfs']<=-3:
        raise ValueError('Invalid peak ceiling')
    parts=s['parts']
    if not isinstance(parts,list) or not 2<=len(parts)<=3:
        raise ValueError('Use two or three parts including lead')
    seen=set()
    for part in parts:
        if not isinstance(part,dict) or set(part)!={'semitones','gain_db','pan_percent'}:
            raise ValueError('Expected exact part interval, gain and pan')
        for k,lo,hi in (('semitones',-12,12),('gain_db',-24,0),('pan_percent',-100,100)):
            if type(part[k]) is not int or not lo<=part[k]<=hi:raise ValueError('Invalid '+k)
        shift=part['semitones']
        if shift in seen:raise ValueError('Harmony intervals must be distinct')
        seen.add(shift)
        for note in score['notes']:
            if note['midi'] is not None and not 45<=note['midi']+shift<=84:
                raise ValueError('Transposed note exceeds supported vocal range')
    if 0 not in seen:raise ValueError('Include the untransposed lead')
    return s

def decode(raw,channels):
    with wave.open(io.BytesIO(raw),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getcomptype())!=(channels,2,RATE,'NONE'):
            raise ValueError('Unexpected PCM format')
        frames=f.getnframes();data=f.readframes(frames)
    if len(data)!=frames*channels*2:raise ValueError('Truncated PCM')
    a=array('h');a.frombytes(data)
    if sys.byteorder!='little':a.byteswap()
    return a,frames

def generate(s):
    s=checked(s);score=s['score']
    n=sum(note['duration_ms'] for note in score['notes'])*RATE//1000
    mix=array('d',[0])*(n*2);receipts=[]
    for part in s['parts']:
        shift=part['semitones']
        notes=[dict(note,midi=None if note['midi'] is None else note['midi']+shift) for note in score['notes']]
        raw,receipt=singer.generate(dict(score,notes=notes))
        samples,frames=decode(raw,1)
        if frames!=n or not receipt['pcm_verified']:raise ValueError('Harmony part timing mismatch')
        angle=(part['pan_percent']/100+1)*math.pi/4
        gain=10**(part['gain_db']/20)
        left,right=gain*math.cos(angle),gain*math.sin(angle)
        for i,x in enumerate(samples):
            mix[2*i]+=left*x;mix[2*i+1]+=right*x
        receipts.append(dict(part,notes=notes,frames=frames))
    peak=max(abs(x) for x in mix)
    if not math.isfinite(peak) or peak<=0:raise ValueError('No mixed signal')
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20))
    scale=min(1.,ceiling/peak)
    out=array('h',(round(x*scale) for x in mix))
    payload=encode(out,RATE,2);wav(payload,max_chunks=16)
    decoded,frames=decode(payload,2)
    if frames!=n or decoded!=out or max(abs(x) for x in out)>ceiling:
        raise ValueError('Harmony PCM verification failed')
    return payload,{'sample_rate':RATE,'channels':2,'frames':n,'parts':receipts,
        'peak_pcm':max(abs(x) for x in out),'linked_attenuation':scale,'pcm_verified':True,
        'automatic_interval_application':True,'key_aware_harmonization':False,
        'recorded_vocal_harmonization':False,'lyric_synthesis':False,'listening_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    return plan,dict(s,scope='Generate lead and one or two fixed chromatic-interval sung-vowel parts; no key-aware harmony, recording conversion or intelligible lyrics.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,receipt=generate(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'vocal_harmony_score_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed vocal harmony unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
