"""Local rhythm-conditioned music synthesis from exact recorded transient evidence."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.section_song import read_pcm
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-rhythm-conditioned-music-v1'
EXTRA=('audio','.wav')
RATE=24000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'audio','root_midi','seed','peak_dbfs','pattern'} or not isinstance(s['audio'],str):
        raise ValueError('Expected audio, bass root, seed, peak and arrangement pattern')
    if type(s['root_midi']) is not int or not 36<=s['root_midi']<=55 or type(s['seed']) is not int or not 0<=s['seed']<=2**32-1:
        raise ValueError('Invalid bass root or seed')
    if type(s['peak_dbfs']) not in (int,float) or not math.isfinite(s['peak_dbfs']) or not -18<=s['peak_dbfs']<=-1:
        raise ValueError('Invalid peak ceiling')
    if s['pattern'] not in ('electronic','soft'):raise ValueError('Choose electronic or soft pattern')
    return s

def analyse(raw):
    samples,rate,channels,frames=pcm(raw)
    if frames>20*rate:raise ValueError('Use 3–20 seconds of PCM WAV')
    hop=round(rate/100);envelope=[]
    for a in range(0,frames-hop+1,hop):
        block=samples[a*channels:(a+hop)*channels]
        envelope.append(sum(abs(v) for v in block)/len(block))
    onset=[max(0.,b-a) for a,b in zip([0.]+envelope,envelope)]
    maximum=max(onset,default=0.)
    threshold=max(160.,maximum*.18,statistics.median(onset)*5)
    candidates=[]
    for i,v in enumerate(onset):
        if v<threshold or (i and onset[i-1]>v) or (i+1<len(onset) and onset[i+1]>=v):continue
        if candidates and i-candidates[-1]<10:
            if v>onset[candidates[-1]]:candidates[-1]=i
        else:candidates.append(i)
    if not 3<=len(candidates)<=100:raise ValueError('Need 3–100 distinct rhythmic transients; no rhythm invented')
    events=[{'frame':round(i*hop*RATE/rate),'accent':round(onset[i]/maximum,6)} for i in candidates]
    gaps=[b['frame']-a['frame'] for a,b in zip(events,events[1:])]
    return events,round(frames*RATE/rate),{'source_rate':rate,'source_channels':channels,'source_frames':frames,
        'median_onset_interval_seconds':statistics.median(gaps)/RATE,'threshold':threshold}

def generate(raw,s):
    checked(s);events,n,info=analyse(raw)
    left=array('d',[0.])*n;right=array('d',[0.])*n
    rng=random.Random(s['seed']);soft=s['pattern']=='soft'
    for index,event in enumerate(events):
        at=event['frame'];accent=event['accent']
        # Each event triggers newly synthesized bass and percussion, never sampled input.
        pitch=s['root_midi']+(7 if index%4==3 else 0)
        freq=440*2**((pitch-69)/12)
        gap=events[index+1]['frame']-at if index+1<len(events) else n-at
        length=min(n-at,round(.28*RATE),gap)
        for j in range(length):
            t=j/RATE;env=min(1.,j/120,(length-1-j)/180)
            bass=math.sin(2*math.pi*freq*t)+.2*math.sin(4*math.pi*freq*t)
            v=.38*accent*env*math.exp(-3*t)*bass
            left[at+j]+=v;right[at+j]+=v
        length=min(n-at,round((.14 if soft else .20)*RATE))
        phase=0.
        for j in range(length):
            t=j/RATE;env=min(1.,j/24,(length-1-j)/120)
            phase+=2*math.pi*(48+75*math.exp(-35*t))/RATE
            kick=math.sin(phase)*math.exp(-22*t)
            noise=(rng.random()*2-1)*math.exp(-65*t)
            v=accent*env*((.22 if soft else .48)*kick+(.035 if soft else .12)*noise)
            left[at+j]+=v*(.85 if index%2 else 1.)
            right[at+j]+=v*(1. if index%2 else .85)
    peak=max(max(map(abs,left)),max(map(abs,right)))
    if not math.isfinite(peak) or peak<=0:raise ValueError('No synthesized music signal')
    scale=min(1.,10**(s['peak_dbfs']/20)/peak)*32767
    samples=array('h',(round(x*scale) for pair in zip(left,right) for x in pair))
    if not any(samples):raise ValueError('Synthesized output below PCM resolution')
    payload=encode(samples,RATE,2)
    if read_pcm(payload,RATE,2,n)!=samples or max(map(abs,samples))>math.floor(32767*10**(s['peak_dbfs']/20))+1:
        raise ValueError('PCM or peak verification failed')
    return payload,dict(info,source_sha256=hashlib.sha256(raw).hexdigest(),events=events,frames=n,
        sample_rate=RATE,channels=2,seed=s['seed'],root_midi=s['root_midi'],pattern=s['pattern'],
        peak_pcm=max(map(abs,samples)),pcm_verified=True,source_audio_copied=False,
        melody_transcribed=False,neural_music_generation=False,listening_verified=False)

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,src=validate(root,plan);events,n,info=analyse(guard.exact(src,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(s,observations=info,events=events,duration_seconds=n/RATE,
        scope='Create synthetic bass and percussion using exact observed transient times and relative accents. No source copying, melody recognition, neural style or musical quality claim.')

def execute(root,plan):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    payload,receipt=generate(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'rhythm_conditioned_music_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
