"""Reviewed same-duration song section replacement and gain editing."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.noise_reduction import encode
from deepthort_local.section_song import read_pcm
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-song-section-edit-v1'
EXTRA=('audio','.wav')
BASE={'audio','start_frame','end_frame','fade_frames','mode','gain_db'}

def checked(s):
    if not isinstance(s,dict) or s.get('mode') not in ('gain','replace'):
        raise ValueError('Choose gain or replace')
    if set(s)!=(BASE|{'replacement'} if s['mode']=='replace' else BASE):
        raise ValueError('Invalid section edit fields')
    for k in ('audio','replacement'):
        if k in s and (not isinstance(s[k],str) or not s[k]):raise ValueError('Expected exact project WAV path')
    if s['mode']=='replace' and s['audio'].casefold()==s['replacement'].casefold():
        raise ValueError('Replacement must be distinct from source')
    a,b,f=(s[k] for k in ('start_frame','end_frame','fade_frames'))
    if any(type(v) is not int for v in (a,b,f)) or not 0<=a<b<=5760000 or not 2<=f<=24000 or 2*f>=b-a:
        raise ValueError('Invalid sample-frame interval or inside-boundary fade')
    gain=s['gain_db']
    if type(gain) not in (int,float) or not math.isfinite(gain) or not -60<=gain<=12:
        raise ValueError('Gain outside -60 to +12 dB')
    if s['mode']=='gain' and gain==0:raise ValueError('Choose nonzero gain')
    return s

def decode(raw):
    if not isinstance(raw,bytes) or not 0<len(raw)<=guard.MAX_INPUT:raise ValueError('WAV exceeds input bound')
    try:
        with wave.open(io.BytesIO(raw),'rb') as w:
            rate,channels,n=w.getframerate(),w.getnchannels(),w.getnframes()
            if rate not in (22050,24000,44100,48000) or channels not in (1,2) or w.getsampwidth()!=2 or w.getcomptype()!='NONE' or not 1<=n<=rate*120 or 2*n*channels>guard.MAX_INPUT:
                raise ValueError('Expected bounded PCM16 mono/stereo WAV at supported rate')
    except (wave.Error,EOFError) as exc:raise ValueError('Invalid WAV') from exc
    return read_pcm(raw,rate,channels,n),rate,channels,n

def inputs(raw,s,replacement=None):
    checked(s);samples,rate,channels,n=decode(raw)
    a,b,f=(s[k] for k in ('start_frame','end_frame','fade_frames'))
    if b>n or f>rate//2:raise ValueError('Edit exceeds source or half-second fade limit')
    if s['mode']=='replace':
        other,r,c,frames=decode(replacement)
        if (r,c,frames)!=(rate,channels,b-a):raise ValueError('Replacement must exactly match rate, channels and selected frame count')
    else:
        if replacement is not None:raise ValueError('Unexpected replacement')
        other=samples[a*channels:b*channels]
    return samples,other,rate,channels,n

def render(raw,s,replacement=None):
    samples,other,rate,channels,n=inputs(raw,s,replacement)
    a,b,f=(s[k] for k in ('start_frame','end_frame','fade_frames'))
    gain=10**(s['gain_db']/20)
    out=array('h',samples);changed=0
    for i in range(b-a):
        weight=min(1.,i/f,(b-a-1-i)/f)
        for ch in range(channels):
            j=(a+i)*channels+ch
            value=round(samples[j]*(1-weight)+other[i*channels+ch]*gain*weight)
            if not -32768<=value<=32767:raise ValueError('Edit would clip; reduce gain')
            changed+=value!=samples[j];out[j]=value
    if not changed:raise ValueError('No observable sample edit')
    if out[:a*channels]!=samples[:a*channels] or out[b*channels:]!=samples[b*channels:]:
        raise ValueError('Samples outside selected interval changed')
    payload=encode(out,rate,channels)
    if read_pcm(payload,rate,channels,n)!=out:raise ValueError('Edited WAV roundtrip failed')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),
        'replacement_sha256':hashlib.sha256(replacement).hexdigest() if replacement is not None else None,
        'sample_rate':rate,'channels':channels,'frames':n,'start_frame':a,'end_frame':b,
        'fade_frames':f,'mode':s['mode'],'gain_db':s['gain_db'],'changed_samples':changed,
        'outside_interval_pcm_preserved':True,'duration_preserved':True,'pcm_verified':True,
        'neural_inpainting':False,'listening_verified':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards']) not in (2,3):
        raise ValueError('Invalid section edit approval')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    other=None
    if s['mode']=='replace':
        if len(plan['guards'])!=3:raise ValueError('Missing replacement approval')
        other=guard.path_for(Path(root).resolve(strict=True),s['replacement'],plan['exclude'],{'.wav'},exists=True)
        if other.samefile(src) or other.stat().st_size>guard.MAX_INPUT or snapshot_file(other)!=plan['guards'][2]:
            raise ValueError('Replacement changed or aliases source')
    elif len(plan['guards'])!=2:raise ValueError('Unexpected replacement approval')
    return s,dst,src,other

def exact_inputs(src,other,plan):
    return guard.exact(src,plan['guards'][1],guard.MAX_INPUT),guard.exact(other,plan['guards'][2],guard.MAX_INPUT) if other else None

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    if s['mode']=='replace':
        other=guard.path_for(Path(plan['root']),s['replacement'],plan['exclude'],{'.wav'},exists=True)
        if other.stat().st_size>guard.MAX_INPUT:raise ValueError('Replacement too large')
        plan['guards'].append(snapshot_file(other))
    _,_,src,other=validate(root,plan);raw,replacement=exact_inputs(src,other,plan)
    _,_,rate,channels,n=inputs(raw,s,replacement)
    return plan,dict(s,sample_rate=rate,channels=channels,frames=n,
        scope='Replace or gain-edit only the selected sample-frame interval, with fades entirely inside it. Preserve source duration and every outside PCM sample. Refuse clipping. No neural regeneration.')

def execute(root,plan):
    s,dst,src,other=validate(root,plan);require_storage(dst.parent)
    raw,replacement=exact_inputs(src,other,plan);payload,receipt=render(raw,s,replacement)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'song_section_edit_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
