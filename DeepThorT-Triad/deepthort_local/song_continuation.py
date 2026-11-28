"""Reviewed song extension from measured trailing tempo and key evidence."""
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
from deepthort_local import reference_music as reference
from deepthort_local import instrumental_synthesis as synth
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.section_song import read_pcm
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-song-continuation-v1'
EXTRA=('reference','.wav')
RATE=synth.RATE

def checked(s):
    if not isinstance(s,dict) or set(s)!={'reference','min_bpm','max_bpm','channel','bars','seed','lead_timbre','backing_timbre','peak_dbfs','tail_seconds','fade_ms'}:
        raise ValueError('Expected reference-music controls, analysis tail and boundary fade')
    reference.checked({k:v for k,v in s.items() if k not in ('tail_seconds','fade_ms')})
    if type(s['tail_seconds']) is not int or not 3<=s['tail_seconds']<=20:
        raise ValueError('Use 3–20 seconds of trailing analysis')
    if type(s['fade_ms']) is not int or not 20<=s['fade_ms']<=500:
        raise ValueError('Use 20–500 ms continuation fade')
    return s

def source(raw,s):
    samples,rate,channels,n=pcm(raw)
    if rate!=RATE or channels!=2 or n>RATE*60 or n<s['tail_seconds']*RATE:
        raise ValueError('Use stereo PCM16 22.05 kHz WAV, sufficient analysis tail and at most 60 seconds')
    tail=encode(samples[-2*s['tail_seconds']*RATE:],rate,channels)
    settings={k:v for k,v in s.items() if k not in ('tail_seconds','fade_ms')}
    return samples,n,tail,settings

def inspect_source(raw,s):
    samples,n,tail,settings=source(raw,s)
    profile=reference.analyse(tail,settings)
    return samples,n,profile,settings

def append(original,continuation,n,s):
    if len(original)!=n*2 or len(continuation)%2 or not continuation:
        raise ValueError('Unexpected stereo extent')
    frames=len(continuation)//2
    fade=min(frames-1,round(s['fade_ms']*RATE/1000))
    if fade<2:raise ValueError('Continuation too short')
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20))
    # Preserve the original exactly. Bridge its last sample into the new score,
    # then fade to the synthesized signal; never alter existing samples.
    joined=array('h',original)
    for i in range(frames):
        weight=min(1.,i/fade)
        for ch in (0,1):
            v=round(original[-2+ch]*(1-weight)+continuation[2*i+ch]*weight)
            joined.append(max(-32768,min(32767,v)))
    if joined[:2*n]!=original or max(map(abs,joined[2*(n+fade):]),default=0)>ceiling+1:
        raise ValueError('Source preservation or continuation peak failed')
    payload=encode(joined,RATE,2)
    if read_pcm(payload,RATE,2,n+frames)!=joined:raise ValueError('Song continuation PCM verification failed')
    return payload,{'source_frames':n,'appended_frames':frames,'frames':n+frames,
        'sample_rate':RATE,'channels':2,'boundary_fade_frames':fade,'original_pcm_preserved':True,
        'new_section_peak_pcm':max(map(abs,joined[2*n:])), 'pcm_verified':True,
        'whole_song_peak_limited':False,'neural_continuation':False,'listening_verified':False}

def generate(raw,s):
    checked(s);original,n,profile,settings=inspect_source(raw,s)
    midi,voices,progression=reference.compose(profile,settings)
    audio,report=synth.render(midi,voices)
    continuation=read_pcm(audio,RATE,2,report['frames'])
    payload,receipt=append(original,continuation,n,s)
    return payload,dict(receipt,source_sha256=hashlib.sha256(raw).hexdigest(),reference_profile=profile,
        progression=progression,seed=s['seed'],tail_seconds=s['tail_seconds'])

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)

def review(root,source_path,output,exclude=()):
    plan,s=guard.review(root,source_path,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,src=validate(root,plan);_,n,profile,_=inspect_source(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,source_seconds=n/RATE,reference_profile=profile,
        scope='Append a newly synthesized tempo/key-conditioned section while preserving all original PCM samples. Boundary bridge may retain source end amplitude. No neural continuation, lyrics or style similarity claim.')

def execute(root,plan):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    payload,receipt=generate(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'song_continuation_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
