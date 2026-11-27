"""Linked-channel, bounded PCM noise-floor attenuation (not source separation)."""
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
from deepthort_local.tempo_detection import pcm
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-noise-reduction-v1'
EXTRA=('audio','.wav')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','threshold_dbfs','attenuation_db','attack_ms','release_ms'} or not isinstance(spec['audio'],str):
        raise ValueError('Expected PCM WAV and explicit gate settings')
    for key,lo,hi in (('threshold_dbfs',-90,-10),('attenuation_db',-60,0),('attack_ms',1,100),('release_ms',10,1000)):
        v=spec[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Out-of-range gate setting: '+key)
    return spec

def encode(samples,rate,channels):
    copy=array('h',samples)
    if sys.byteorder!='little':copy.byteswap()
    stream=io.BytesIO()
    with wave.open(stream,'wb') as f:
        f.setnchannels(channels);f.setsampwidth(2);f.setframerate(rate);f.writeframes(copy.tobytes())
    return stream.getvalue()

def reduce(raw,spec):
    samples,rate,channels,frames=pcm(raw)
    threshold=32768*10**(spec['threshold_dbfs']/20)
    floor=10**(spec['attenuation_db']/20)
    opening=math.exp(-1/(rate*spec['attack_ms']/1000))
    closing=math.exp(-1/(rate*spec['release_ms']/1000))
    block=max(1,round(rate*.01));out=array('h');gain=1.0;quiet=0;before=after=0
    for start in range(0,frames,block):
        end=min(frames,start+block)
        # The loudest channel controls a shared gain so the stereo image remains linked.
        rms=max(math.sqrt(sum(samples[i*channels+c]**2 for i in range(start,end))/(end-start)) for c in range(channels))
        low=rms<threshold;target=floor if low else 1.0
        if low:quiet+=end-start
        coefficient=opening if target>gain else closing
        for i in range(start,end):
            gain=target+(gain-target)*coefficient
            for c in range(channels):
                v=samples[i*channels+c];new=round(v*gain)
                if abs(new)>abs(v):raise ValueError('Gate amplified sample')
                out.append(new)
                if low:before+=v*v;after+=new*new
    payload=encode(out,rate,channels);wav(payload,max_chunks=16)
    decoded,r,c,f=pcm(payload)
    if (r,c,f)!=(rate,channels,frames) or decoded!=out:raise ValueError('PCM roundtrip failed')
    return payload,{'sample_rate':rate,'channels':channels,'frames':frames,'low_level_frames':quiet,
        'low_level_rms_before':round(math.sqrt(before/(quiet*channels)),6) if quiet else None,
        'low_level_rms_after':round(math.sqrt(after/(quiet*channels)),6) if quiet else None,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'method':'linked-channel soft noise gate',
        'listening_verified':False,'metadata_preserved':False}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    _,_,path=validate(root,plan);_,rate,channels,frames=pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_format={'sample_rate':rate,'channels':channels,'frames':frames},
                     scope='Attenuates quiet intervals, not noise overlapping wanted sound; output audio only.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=reduce(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-noise-reduction-result-v1','status':'pcm_attenuation_verified','output':plan['output'],'sha256':sha,
            **receipt,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Noise gate unavailable; inspect PCM WAV and reviewed settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
