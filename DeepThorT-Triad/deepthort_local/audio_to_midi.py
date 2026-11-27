"""Reviewed monophonic pitch tracking to timed Standard MIDI (not polyphonic ASR)."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.tempo_detection import pcm

SCHEMA='janus-audio-to-midi-v1'
EXTRA=('audio','.wav')
RATE=8000
HOP=160
WINDOW=512
COMPARE=320
MAX_NOTES=256
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','bpm','min_pitch','max_pitch','gate_dbfs'} or not isinstance(spec['audio'],str):
        raise ValueError('Expected mono PCM WAV, explicit BPM, pitch range and silence gate')
    lo,hi=spec['min_pitch'],spec['max_pitch']
    if type(lo) is not int or type(hi) is not int or not 36<=lo<hi<=84:
        raise ValueError('Pitch range must be ordered MIDI notes within 36–84')
    if type(spec['bpm']) is not int or not 40<=spec['bpm']<=220:raise ValueError('BPM outside supported range')
    g=spec['gate_dbfs']
    if type(g) not in (float,int) or not math.isfinite(g) or not -65<=g<=-20:raise ValueError('Silence gate outside supported range')
    return spec
def input_pcm(raw):
    s,r,c,n=pcm(raw)
    if c!=1 or r not in (8000,16000) or n>20*r:raise ValueError('Requires 3–20 seconds of mono 8 or 16 kHz PCM16 WAV')
    if r==16000:
        # Simple two-sample averaging prior to 2:1 decimation.
        s=array('h',(round((s[i]+s[i+1])/2) for i in range(0,n-1,2)))
    return s,n/r
def frequency(pitch):
    return 440*2**((pitch-69)/12)
def pitch_frame(frame,spec):
    mean=sum(frame)/len(frame);centered=[v-mean for v in frame]
    if math.sqrt(sum(v*v for v in centered)/len(centered))<32768*10**(spec['gate_dbfs']/20):return None
    # YIN-style cumulative mean normalized squared difference.
    lo=max(2,math.floor(RATE/frequency(spec['max_pitch']+.5)))
    hi=min(WINDOW-COMPARE-1,math.ceil(RATE/frequency(spec['min_pitch']-.5)))
    if hi<=lo:return None
    scores=[1.0];running=0.0
    for lag in range(1,hi+2):
        diff=sum((centered[j]-centered[j+lag])**2 for j in range(COMPARE))
        running+=diff;scores.append(diff*lag/running if running else 1.0)
    lag=lo
    while lag<=hi:
        if scores[lag]<.15:
            while lag<hi and scores[lag+1]<scores[lag]:lag+=1
            break
        lag+=1
    if lag>hi:return None
    a,b,c=scores[lag-1:lag+2];den=a-2*b+c
    refined=lag+max(-.5,min(.5,.5*(a-c)/den)) if den>0 else float(lag)
    note=round(69+12*math.log2(RATE/refined/440))
    if not spec['min_pitch']<=note<=spec['max_pitch']:return None
    return note
def detect(raw,spec):
    spec=checked(spec);s,seconds=input_pcm(raw)
    frames=[]
    for center in range(HOP//2,len(s),HOP):
        begin=center-WINDOW//2;end=begin+WINDOW
        block=[0]*max(0,-begin)+list(s[max(0,begin):min(len(s),end)])+[0]*max(0,end-len(s))
        frames.append(pitch_frame(block,spec))
    # Ignore isolated one/two-frame pitch candidates; preserve gaps rather than invent notes.
    notes=[];i=0;scale=spec['bpm']*480/60
    while i<len(frames):
        j=i+1
        while j<len(frames) and frames[j]==frames[i]:j+=1
        if frames[i] is not None and j-i>=3:
            start=round(i*HOP/RATE*scale);end=round(min(seconds,j*HOP/RATE)*scale)
            if end>start:notes.append([start,end-start,frames[i]])
        i=j
    if not 1<=len(notes)<=MAX_NOTES:raise ValueError('No stable monophonic notes or too many candidates')
    return notes,seconds
def vlq(n):
    if type(n) is not int or not 0<=n<=0x0fffffff:raise ValueError('Invalid MIDI delta')
    result=[n&127];n>>=7
    while n:result.append(128|(n&127));n>>=7
    return bytes(reversed(result))
def midi(bpm,notes):
    if type(bpm) is not int or not 40<=bpm<=220 or not isinstance(notes,list) or not 1<=len(notes)<=MAX_NOTES:raise ValueError('Invalid MIDI score')
    tempo=round(60_000_000/bpm)
    track=bytearray(b'\x00\xff\x51\x03'+tempo.to_bytes(3,'big')+b'\x00\xc0\x00');cursor=0
    for row in notes:
        if not isinstance(row,list) or len(row)!=3 or any(type(v) is not int for v in row):raise ValueError('Invalid timed note')
        start,length,pitch=row
        if not cursor<=start<=36000 or not 1<=length<=36000 or start+length>36000 or not 0<=pitch<=127:raise ValueError('Invalid note bounds or overlap')
        track.extend(vlq(start-cursor)+bytes((0x90,pitch,80))+vlq(length)+bytes((0x80,pitch,0)));cursor=start+length
    track.extend(b'\x00\xff\x2f\x00')
    return b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(track))+track
def inspect(raw):
    if not isinstance(raw,bytes) or not 40<=len(raw)<=8192 or raw[:18]!=b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk' or int.from_bytes(raw[18:22],'big')!=len(raw)-22:
        raise ValueError('Invalid single-track timed MIDI')
    if raw[22:26]!=b'\x00\xff\x51\x03' or raw[29:32]!=b'\x00\xc0\x00':raise ValueError('Missing tempo/program')
    tempo=int.from_bytes(raw[26:29],'big')
    if not tempo:raise ValueError('Invalid tempo')
    bpm=round(60_000_000/tempo);pos=32;cursor=0;notes=[]
    def read_delta():
        nonlocal pos
        n=0
        for _ in range(4):
            if pos>=len(raw):raise ValueError('Truncated delta')
            v=raw[pos];pos+=1;n=(n<<7)|(v&127)
            if not v&128:return n
        raise ValueError('Oversized delta')
    while raw[pos:]!=b'\x00\xff\x2f\x00':
        if len(notes)>=MAX_NOTES:raise ValueError('Too many timed notes')
        start=cursor+read_delta()
        if pos+3>len(raw) or raw[pos]!=0x90 or raw[pos+2]!=80:raise ValueError('Invalid note on')
        pitch=raw[pos+1];pos+=3;length=read_delta()
        if raw[pos:pos+3]!=bytes((0x80,pitch,0)):raise ValueError('Invalid note off')
        pos+=3;notes.append([start,length,pitch]);cursor=start+length
    if midi(bpm,notes)!=raw:raise ValueError('MIDI roundtrip mismatch')
    return {'bpm':bpm,'notes':notes}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mid',extra=EXTRA)
    _,_,path=validate(root,plan);_,seconds=input_pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,duration_seconds=seconds,scope='Approximate monophonic pitch tracking only; no chord or instrument recognition. Unstable candidates are omitted.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.mid',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    notes,seconds=detect(raw,spec);payload=midi(spec['bpm'],notes)
    if inspect(payload)!={'bpm':spec['bpm'],'notes':notes}:raise ValueError('MIDI verification failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-audio-to-midi-result-v1','status':'timed_midi_verified','output':plan['output'],'sha256':sha,
            'source_sha256':hashlib.sha256(raw).hexdigest(),'source_unchanged':True,'audio_seconds':seconds,
            'bpm':spec['bpm'],'notes':len(notes),'timed_notes':notes,'ticks_per_quarter':480,
            'pitch_accuracy_verified':False,'polyphonic':False,'method':'bounded YIN-style monophonic pitch candidates with stable-frame grouping'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Monophonic transcription unavailable; inspect reviewed format, range and gate'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
