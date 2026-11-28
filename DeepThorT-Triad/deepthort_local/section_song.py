"""Reviewed section-based full song rendering with synthetic sung vowels and instruments."""
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
from deepthort_local import musical_arrangement as arranger
from deepthort_local import instrumental_synthesis as instruments
from deepthort_local import singing_voice_generation as singer
from deepthort_local.noise_reduction import encode
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-section-song-v1'
RATE=singer.RATE
MAX_SECONDS=120

def section_plan(section):
    if not isinstance(section,dict) or set(section)!={'name','arrangement','voices','vocal','vocal_gain_db'}:
        raise ValueError('Expected named section with arrangement, voices and vocal score or null')
    name=section['name']
    if not isinstance(name,str) or not 1<=len(name.strip())<=60 or any(ord(c)<32 for c in name):
        raise ValueError('Invalid section name')
    arrangement=arranger.checked(section['arrangement'])
    midi=arranger.midi(arrangement)
    settings={'midi':'section.mid','voices':section['voices'],'peak_dbfs':-6}
    jobs,n,_=instruments.schedule(midi,settings)
    frames=round(n*RATE/instruments.RATE)
    if not RATE//4<=frames<=12*RATE:raise ValueError('Section must span 0.25–12 seconds')
    gain=section['vocal_gain_db']
    if type(gain) not in (int,float) or not math.isfinite(gain) or not -24<=gain<=0:
        raise ValueError('Invalid vocal gain')
    if section['vocal'] is not None:
        score=singer.checked(section['vocal'])
        vn=sum(x['duration_ms'] for x in score['notes'])*RATE//1000
        if abs(vn-frames)>2:raise ValueError('Vocal and accompaniment section timings must match within two samples')
    return midi,settings,n,frames

def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','sections','order','peak_dbfs'}:
        raise ValueError('Expected title, section definitions, playback order and peak ceiling')
    if not isinstance(s['title'],str) or not 1<=len(s['title'].strip())<=120 or any(ord(c)<32 for c in s['title']):
        raise ValueError('Invalid title')
    peak=s['peak_dbfs']
    if type(peak) not in (int,float) or not math.isfinite(peak) or not -18<=peak<=-1:
        raise ValueError('Invalid output ceiling')
    sections=s['sections'];order=s['order']
    if not isinstance(sections,list) or not 2<=len(sections)<=6 or not isinstance(order,list) or not 2<=len(order)<=24:
        raise ValueError('Use 2–6 distinct sections in a 2–24 item song order')
    sizes={};voiced=False;budget=0
    for section in sections:
        _,_,_,n=section_plan(section);name=section['name']
        if name.casefold() in {x.casefold() for x in sizes}:raise ValueError('Duplicate section name')
        sizes[name]=n;voiced|=section['vocal'] is not None;budget+=n
    if not voiced or any(not isinstance(x,str) or x not in sizes for x in order) or set(order)!=set(sizes):
        raise ValueError('Every section must occur and at least one must contain sung vowels')
    if sum(sizes[x] for x in order)>MAX_SECONDS*RATE or budget>36*RATE:
        raise ValueError('Song or unique section work exceeds bounded profile')
    return s

def read_pcm(raw,rate,channels,n):
    if not isinstance(raw,bytes) or len(raw)>guard.MAX_OUTPUT:raise ValueError('PCM exceeds bound')
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            if (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getcomptype(),f.getnframes())!=(rate,channels,2,'NONE',n):
                raise ValueError('Unexpected section PCM format or duration')
            data=f.readframes(n)
    except (wave.Error,EOFError) as exc:raise ValueError('Invalid section WAV') from exc
    if len(data)!=n*channels*2:raise ValueError('Truncated PCM')
    out=array('h');out.frombytes(data)
    if sys.byteorder!='little':out.byteswap()
    return out

def stereo_resample(samples,n,out_n):
    if len(samples)!=2*n or n<2 or out_n<2:raise ValueError('Invalid resampling input')
    out=array('h')
    # Rational sample-position interpolation; clamp the final source sample.
    for i in range(out_n):
        q,r=divmod(i*instruments.RATE,RATE);q=min(q,n-1);j=min(q+1,n-1)
        for channel in (0,1):
            out.append(round((samples[2*q+channel]*(RATE-r)+samples[2*j+channel]*r)/RATE))
    return out

def render_section(section):
    midi,settings,n,frames=section_plan(section)
    music,_=instruments.render(midi,settings)
    backing=stereo_resample(read_pcm(music,instruments.RATE,2,n),n,frames)
    voice=section['vocal'];lead=array('h');vocal_hash=None
    if voice is not None:
        data,receipt=singer.generate(voice)
        vn=sum(x['duration_ms'] for x in voice['notes'])*RATE//1000
        lead=read_pcm(data,RATE,1,vn)
        if not any(lead) or receipt.get('pcm_verified') is not True:raise ValueError('Missing verified voiced samples')
        vocal_hash=hashlib.sha256(data).hexdigest()
    gain=10**(section['vocal_gain_db']/20)*math.sqrt(.5)
    out=array('d')
    for i in range(frames):
        v=(lead[i] if i<len(lead) else 0)*gain
        out.extend((backing[2*i]+v,backing[2*i+1]+v))
    if not any(out):raise ValueError('Silent section')
    return out,{'name':section['name'],'frames':frames,'instrument_sha256':hashlib.sha256(music).hexdigest(),
        'vocal_sha256':vocal_hash,'vocal_present':voice is not None,'midi_sha256':hashlib.sha256(midi).hexdigest()}

def generate(s):
    checked(s);cache={};records=[]
    for section in s['sections']:
        audio,record=render_section(section);cache[section['name']]=audio;records.append(record)
    peak=max(max(abs(x) for x in audio) for audio in cache.values())
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20));scale=min(1.,ceiling/peak)
    samples=array('h');timeline=[];cursor=0
    for name in s['order']:
        audio=cache[name];n=len(audio)//2
        samples.extend(round(x*scale) for x in audio)
        timeline.append({'section':name,'start_frame':cursor,'frames':n});cursor+=n
    payload=encode(samples,RATE,2)
    if read_pcm(payload,RATE,2,cursor)!=samples or max(abs(v) for v in samples)>ceiling:
        raise ValueError('Song PCM or peak ceiling verification failed')
    return payload,{'title':s['title'],'sample_rate':RATE,'channels':2,'frames':cursor,'duration_seconds':cursor/RATE,
        'sections':records,'timeline':timeline,'shared_gain':scale,'peak_pcm':max(abs(x) for x in samples),
        'synthetic_sung_vowels':True,'lyric_synthesis':False,'neural_song_generation':False,
        'listening_verified':False,'pcm_verified':True}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    sizes={x['name']:section_plan(x)[3] for x in s['sections']}
    return plan,dict(s,duration_seconds=sum(sizes[x] for x in s['order'])/RATE,
        scope='Render and repeat exact arranged song sections with local synthetic instrumental timbres and sung vowels. No intelligible lyric synthesis or neural music quality claim.')

def execute(root,plan):
    s,dst,_=validate(root,plan);require_storage(dst.parent);payload,receipt=generate(s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'section_song_pcm_verified','output':plan['output'],'sha256':sha,
        'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
