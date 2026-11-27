"""Bounded local PCM WAV tempo estimation from observed rhythmic transients."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import io
import json
from pathlib import Path
import statistics
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-tempo-detection-v1'
EXTRA=('audio','.wav')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','min_bpm','max_bpm'} or not isinstance(spec['audio'],str):
        raise ValueError('Expected PCM WAV and explicit BPM range')
    lo,hi=spec['min_bpm'],spec['max_bpm']
    if type(lo) is not int or type(hi) is not int or not 40<=lo<hi<=240:
        raise ValueError('BPM bounds must be ordered integers within 40–240')
    return spec

def pcm(raw):
    try:
        with wave.open(io.BytesIO(raw),'rb') as f:
            rate=f.getframerate();channels=f.getnchannels();frames=f.getnframes()
            if f.getsampwidth()!=2 or channels not in (1,2) or f.getcomptype()!='NONE' or not 8000<=rate<=48000:
                raise ValueError('Requires 16-bit PCM mono/stereo WAV, 8–48 kHz')
            if not 3*rate<=frames<=120*rate or frames*channels*2>guard.MAX_INPUT:
                raise ValueError('Audio duration must be 3–120 seconds within input byte bound')
            data=f.readframes(frames)
            if len(data)!=frames*channels*2:raise ValueError('Truncated audio frames')
    except (wave.Error,EOFError) as exc:raise ValueError('Unsupported or invalid WAV') from exc
    samples=array('h');samples.frombytes(data)
    if sys.byteorder!='little':samples.byteswap()
    return samples,rate,channels,frames

def estimate(raw,spec):
    samples,rate,channels,frames=pcm(raw)
    hop=max(1,round(rate/100));stride=hop*channels
    envelope=[]
    for start in range(0,len(samples)-stride+1,stride):
        block=samples[start:start+stride]
        envelope.append(sum(abs(v) for v in block)/len(block))
    onset=[max(0.0,b-a) for a,b in zip([0.0]+envelope,envelope)]
    maximum=max(onset,default=0);threshold=max(100.0,maximum*.15,statistics.median(onset)*4)
    peaks=[];gap=max(1,round(.09*rate/hop))
    for i,v in enumerate(onset):
        if v<threshold:continue
        if i and onset[i-1]>v:continue
        if i+1<len(onset) and onset[i+1]>=v:continue
        if peaks and i-peaks[-1]<gap:
            if v>onset[peaks[-1]]:peaks[-1]=i
        else:peaks.append(i)
    result={'schema':'janus-tempo-report-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'sample_rate':rate,'channels':channels,'duration_seconds':round(frames/rate,6),
            'onset_count':len(peaks),'hop_seconds':hop/rate,'tempo_bpm':None,'interval_support':0,
            'interval_count':max(0,len(peaks)-1),'support_fraction':None,'alternatives_bpm':[],
            'method':'positive mean-absolute-amplitude changes; adjacent onset interval consensus',
            'scope':'Steady rhythmic onset estimate only; half/double ambiguity and complex rhythms require listening.'}
    if len(peaks)<4:
        result['status']='insufficient_transients';return result
    intervals=[b-a for a,b in zip(peaks,peaks[1:])]
    min_lag=max(1,int(60*rate/(hop*spec['max_bpm'])))
    max_lag=int(60*rate/(hop*spec['min_bpm']))+1
    candidates=sorted({v for v in intervals if min_lag<=v<=max_lag})
    if not candidates:
        result['status']='no_supported_period';return result
    def supporting(lag):
        tolerance=max(1,lag*.04)
        return [v for v in intervals if abs(v-lag)<=tolerance]
    best=max(candidates,key=lambda lag:(len(supporting(lag)),-sum(abs(v-lag) for v in supporting(lag)),-lag))
    accepted=supporting(best);support=len(accepted)/len(intervals)
    result['interval_support']=len(accepted);result['support_fraction']=round(support,4)
    if len(accepted)<3 or support<.6:
        result['status']='inconsistent_transients';return result
    bpm=60*rate/(hop*statistics.median(accepted))
    if not spec['min_bpm']<=bpm<=spec['max_bpm']:
        result['status']='outside_requested_range';return result
    result.update(status='steady_tempo_estimate',tempo_bpm=round(bpm,2),
        alternatives_bpm=[round(v,2) for v in (bpm/2,bpm*2) if spec['min_bpm']<=v<=spec['max_bpm']])
    return result

def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);report=estimate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    payload=(json.dumps(report,indent=2,sort_keys=True)+'\n').encode()
    if json.loads(payload)!=report:raise ValueError('Tempo report roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-tempo-result-v1','status':report['status'],'output':plan['output'],'sha256':sha,
            'tempo_bpm':report['tempo_bpm'],'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Tempo analysis unavailable; inspect PCM WAV format, duration and bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
