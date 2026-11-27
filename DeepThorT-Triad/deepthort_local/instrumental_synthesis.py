"""Bounded reviewed additive synthesis from canonical JANUS MIDI profiles."""
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
from deepthort_local.musical_arrangement import inspect as inspect_arrangement
from deepthort_local.audio_to_midi import inspect as inspect_timed,frequency
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-instrumental-synthesis-v1'
EXTRA=('midi',{'.mid','.midi'})
RATE=22050
MAX_SECONDS=30
MAX_WORK=2000000
# Harmonic amplitudes, attack and release fractions, and within-note decay.
TIMBRES={
    'sine':((1,),.025,.08,0),
    'organ':((1,.5,.25,.12),.02,.06,0),
    'pluck':((1,.5,.28,.15,.08),.025,.12,3),
    'strings':((1,.65,.45,.3,.2),.22,.18,.1),
    'bass':((1,.35,.12),.04,.10,1),
}
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'midi','voices','peak_dbfs'} or not isinstance(spec['midi'],str):
        raise ValueError('Expected MIDI, explicit per-part synthesizer voices and peak ceiling')
    voices=spec['voices']
    if not isinstance(voices,list) or not 1<=len(voices)<=8:raise ValueError('Expected 1–8 voices')
    for v in voices:
        if not isinstance(v,dict) or set(v)!={'timbre','gain_db','pan'} or v['timbre'] not in TIMBRES:raise ValueError('Unknown synthesis voice')
        for key,lo,hi in (('gain_db',-36,0),('pan',-1,1)):
            n=v[key]
            if type(n) not in (float,int) or not math.isfinite(n) or not lo<=n<=hi:raise ValueError('Invalid voice gain or pan')
    peak=spec['peak_dbfs']
    if type(peak) not in (float,int) or not math.isfinite(peak) or not -18<=peak<=-1:raise ValueError('Invalid peak ceiling')
    return spec
def score(raw):
    if not isinstance(raw,bytes) or not 40<=len(raw)<=32768:raise ValueError('Unsupported MIDI byte extent')
    if raw[8:10]==b'\x00\x01':return inspect_arrangement(raw)
    timed=inspect_timed(raw)
    return {'bpm':timed['bpm'],'parts':[{'name':'Melody','program':0,'notes':[[start,length,pitch,80] for start,length,pitch in timed['notes']]}]}
def schedule(raw,spec):
    spec=checked(spec);data=score(raw)
    if len(data['parts'])!=len(spec['voices']):raise ValueError('Specify exactly one voice per MIDI part')
    scale=RATE*round(60000000/data['bpm'])/(480*1000000)
    scheduled=[];end=work=0
    for part,voice in zip(data['parts'],spec['voices']):
        for start,length,pitch,velocity in part['notes']:
            a,b=round(start*scale),round((start+length)*scale)
            if b<=a or b>RATE*MAX_SECONDS:raise ValueError('Note or duration outside render bound')
            if frequency(pitch)>=RATE/2:raise ValueError('Pitch above renderer Nyquist frequency')
            end=max(end,b);work+=b-a
            if work>MAX_WORK:raise ValueError('Total synthesis work exceeds bound')
            scheduled.append((a,b,pitch,velocity,voice))
    if not scheduled:raise ValueError('No renderable notes')
    return scheduled,end,data
def render(raw,spec):
    jobs,frames,data=schedule(raw,spec)
    left=array('d',[0])*frames;right=array('d',[0])*frames
    for start,end,pitch,velocity,voice in jobs:
        n=end-start;freq=frequency(pitch)
        coeff,attack,release,decay=TIMBRES[voice['timbre']]
        harmonics=[(i+1,a) for i,a in enumerate(coeff) if freq*(i+1)<RATE/2]
        norm=sum(a for _,a in harmonics)
        angle=(voice['pan']+1)*math.pi/4
        amp=velocity/127*10**(voice['gain_db']/20)/norm
        gl,gr=amp*math.cos(angle),amp*math.sin(angle)
        phase=2*math.pi*freq/RATE
        rise=max(1,round(n*attack));fall=max(1,round(n*release))
        for i in range(n):
            env=min(1,i/rise,(n-1-i)/fall)*math.exp(-decay*i/max(1,n-1))
            sample=env*sum(a*math.sin(phase*k*i) for k,a in harmonics)
            left[start+i]+=sample*gl;right[start+i]+=sample*gr
    peak=max(max(abs(v) for v in left),max(abs(v) for v in right))
    if not math.isfinite(peak) or peak<=0:raise ValueError('Empty or nonfinite synthesis')
    # A single attenuation preserves relative mix; never boost quiet scores.
    scale=min(1,10**(spec['peak_dbfs']/20)/peak)*32767
    samples=array('h',(round(x*scale) for pair in zip(left,right) for x in pair))
    if not any(samples):raise ValueError('Rendered signal below PCM resolution')
    payload=encode(samples,RATE,2);wav(payload,max_chunks=16)
    with wave.open(io.BytesIO(payload),'rb') as f:
        if (f.getframerate(),f.getnchannels(),f.getsampwidth(),f.getnframes())!=(RATE,2,2,frames):raise ValueError('WAV header mismatch')
        decoded=array('h');decoded.frombytes(f.readframes(frames))
        if sys.byteorder!='little':decoded.byteswap()
        if decoded!=samples:raise ValueError('WAV PCM roundtrip failed')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),'sample_rate':RATE,'channels':2,'frames':frames,
        'duration_seconds':frames/RATE,'parts':len(data['parts']),'notes':len(jobs),
        'peak_pcm':max(abs(v) for v in samples),'shared_gain':scale/32767,
        'method':'deterministic band-limited additive synthesis with envelope and equal-power pan',
        'listening_verified':False,'real_instrument_quality_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan);jobs,frames,data=schedule(guard.exact(path,plan['guards'][1],32768),spec)
    return plan,dict(spec,parts=[p['name'] for p in data['parts']],notes=len(jobs),duration_seconds=frames/RATE,
                     scope='Synthetic timbres only, not sampled instruments or automatic composition.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,report=render(guard.exact(path,plan['guards'][1],32768),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-instrumental-synthesis-result-v1','status':'synthesized_pcm_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**report}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed MIDI, synthesis voice, duration or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
