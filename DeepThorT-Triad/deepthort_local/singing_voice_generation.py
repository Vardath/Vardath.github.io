"""Reviewed synthetic sung-vowel score with harmonic formants and vibrato."""
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
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-singing-voice-generation-v1'
RATE=24000
# Illustrative fixed vowel resonance centers and bandwidths, not measured speaker models.
FORMANTS={'ah':((800,180),(1200,220),(2600,350)),
          'ee':((300,120),(2200,220),(3000,350)),
          'oo':((350,140),(850,180),(2400,350)),
          'eh':((550,160),(1900,220),(2600,350)),
          'oh':((450,150),(900,180),(2500,350))}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'notes','vibrato_hz','vibrato_cents','peak_dbfs'}:
        raise ValueError('Expected sequential vowel note score and exact controls')
    for key,lo,hi in (('vibrato_hz',4,8),('vibrato_cents',0,60),('peak_dbfs',-24,-3)):
        if type(s[key]) is not int or not lo<=s[key]<=hi:raise ValueError('Invalid '+key)
    notes=s['notes']
    if not isinstance(notes,list) or not 1<=len(notes)<=24:raise ValueError('Use 1–24 notes')
    total=0;voiced=0
    for note in notes:
        if not isinstance(note,dict) or set(note)!={'midi','vowel','duration_ms'} or type(note['duration_ms']) is not int or not 150<=note['duration_ms']<=2000:
            raise ValueError('Invalid note duration or fields')
        if note['midi'] is None:
            if note['vowel'] is not None:raise ValueError('Rest requires null vowel')
        else:
            if type(note['midi']) is not int or not 45<=note['midi']<=84 or note['vowel'] not in FORMANTS:
                raise ValueError('Use MIDI 45–84 and supported vowel')
            voiced+=1
        total+=note['duration_ms']
    if not voiced or total>12000:raise ValueError('Use at least one voiced note and at most twelve seconds')
    return s

def weights(frequency,vowel,cents):
    max_freq=frequency*2**(cents/1200)
    count=min(32,int((RATE/2-1)//max_freq))
    result=[]
    for k in range(1,count+1):
        hz=frequency*k
        # Include a small fundamental floor; shape upper harmonics by vowel resonances.
        resonances=sum(g*math.exp(-.5*((hz-center)/bw)**2) for (center,bw),g in zip(FORMANTS[vowel],(1.,.75,.35)))
        result.append((k,(.12+resonances)/math.sqrt(k)))
    total=sum(a for _,a in result)
    return [(k,a/total) for k,a in result]

def generate(s):
    s=checked(s);raw=array('d');receipts=[]
    for row in s['notes']:
        n=row['duration_ms']*RATE//1000;start=len(raw)
        if row['midi'] is None:
            raw.extend(array('d',[0.])*n)
        else:
            f=440*2**((row['midi']-69)/12)
            coeff=weights(f,row['vowel'],s['vibrato_cents']);phase=0.
            rise=min(n//3,round(.035*RATE));fall=min(n//3,round(.065*RATE))
            for i in range(n):
                t=i/RATE
                vibrato=s['vibrato_cents']*min(1,t/.12)*math.sin(2*math.pi*s['vibrato_hz']*t)
                phase=(phase+2*math.pi*f*2**(vibrato/1200)/RATE)%(2*math.pi)
                envelope=min(1,i/rise,(n-1-i)/fall)
                raw.append(envelope*sum(a*math.sin(k*phase) for k,a in coeff))
        receipts.append(dict(row,start_frame=start,frames=n))
    peak=max(abs(x) for x in raw)
    if not math.isfinite(peak) or peak<=0:raise ValueError('No voiced signal')
    ceiling=math.floor(32767*10**(s['peak_dbfs']/20))
    out=array('h',(round(x/peak*ceiling) for x in raw))
    payload=encode(out,RATE,1);wav(payload,max_chunks=16)
    with wave.open(io.BytesIO(payload),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(1,2,RATE,len(out)):
            raise ValueError('Unexpected WAV format')
        decoded=array('h');decoded.frombytes(f.readframes(f.getnframes()))
        if sys.byteorder!='little':decoded.byteswap()
    if decoded!=out or max(abs(x) for x in out)>ceiling:raise ValueError('PCM roundtrip failed')
    return payload,{'sample_rate':RATE,'channels':1,'frames':len(out),'notes':receipts,'peak_pcm':max(abs(x) for x in out),
        'formant_synthesis':True,'pcm_verified':True,'lyric_synthesis':False,'neural_voice':False,'listening_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    return plan,dict(s,scope='Synthetic pitched vowels and rests with vibrato, not intelligible lyrics or realistic neural singing.')

def execute(root,plan):
    s,dst,_=validate(root,plan);payload,receipt=generate(s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'sung_vowel_score_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed sung vowel generation unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
