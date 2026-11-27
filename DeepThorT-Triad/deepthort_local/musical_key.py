"""Bounded local musical key candidates from PCM spectral pitch-class evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.tempo_detection import pcm

SCHEMA='janus-musical-key-v1'
EXTRA=('audio','.wav')
NOTES=('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
# Published Krumhansl–Kessler tonal profile values, in tonic-relative pitch order.
MAJOR=(6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88)
MINOR=(6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17)
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','channel'} or not isinstance(spec['audio'],str) or spec['channel'] not in ('left','right'):
        raise ValueError('Expected PCM WAV and explicit left/right channel')
    return spec
def power(samples,coefficient):
    s1=s2=0.0
    for x in samples:
        s0=x+coefficient*s1-s2;s2=s1;s1=s0
    return max(0.0,s1*s1+s2*s2-coefficient*s1*s2)
def correlation(a,b):
    am=sum(a)/len(a);bm=sum(b)/len(b)
    da=[x-am for x in a];db=[x-bm for x in b]
    denom=math.sqrt(sum(x*x for x in da)*sum(x*x for x in db))
    return sum(x*y for x,y in zip(da,db))/denom if denom else 0.0
def rank(chroma):
    out=[]
    for tonic in range(12):
        for mode,profile in (('major',MAJOR),('minor',MINOR)):
            rotated=[profile[(i-tonic)%12] for i in range(12)]
            out.append({'tonic':NOTES[tonic],'mode':mode,'score':round(correlation(chroma,rotated),6)})
    return sorted(out,key=lambda x:(-x['score'],x['tonic'],x['mode']))
def classify(chroma):
    peak=max(chroma,default=0.0)
    active=sum(v>=peak*.15 for v in chroma) if peak>0 else 0
    if active<4:return {'status':'insufficient_pitch_classes','key':None,'candidates':[],'active_pitch_classes':active,'score_margin':None}
    candidates=rank(chroma);best,second=candidates[:2];margin=round(best['score']-second['score'],6)
    confident=best['score']>=.5 and margin>=.04
    return {'status':'key_estimate' if confident else 'ambiguous_key','key':{'tonic':best['tonic'],'mode':best['mode']} if confident else None,
            'candidates':candidates[:5],'active_pitch_classes':active,'score_margin':margin}
def estimate(raw,spec):
    samples,rate,channels,frames=pcm(raw)
    channel=0 if spec['channel']=='left' else 1
    if channel>=channels:raise ValueError('Requested channel absent')
    # Average consecutive samples to bound spectral cost; inspect at approximately 8 kHz.
    decimation=max(1,round(rate/8000));effective=rate/decimation
    size=round(effective*.5);span=size*decimation
    windows=frames//span
    count=min(windows,60)
    indices=sorted({round(i*(windows-1)/max(1,count-1)) for i in range(count)})
    weights=[.5-.5*math.cos(2*math.pi*i/(size-1)) for i in range(size)]
    bins=[(midi%12,2*math.cos(2*math.pi*(440*2**((midi-69)/12))/effective)) for midi in range(36,84)]
    chroma=[0.0]*12;accepted=0
    for idx in indices:
        start=idx*span
        block=[]
        for i,w in enumerate(weights):
            offset=(start+i*decimation)*channels+channel
            avg=sum(samples[offset+j*channels] for j in range(decimation))/decimation
            block.append(avg*w)
        if max(map(abs,block),default=0)<100:continue
        values=[0.0]*12
        for pitch,coef in bins:values[pitch]=max(values[pitch],power(block,coef))
        peak=max(values)
        if not peak:continue
        # Ignore weak leakage and normalize individual windows, so loudness alone does not select key.
        for i,v in enumerate(values):
            if v>=peak*.12:chroma[i]+=v/peak
        accepted+=1
    if accepted<3:classification={'status':'insufficient_audio_evidence','key':None,'candidates':[],'active_pitch_classes':0,'score_margin':None}
    else:classification=classify(chroma)
    total=sum(chroma)
    return {'schema':'janus-musical-key-report-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'sample_rate':rate,'channel':spec['channel'],'duration_seconds':round(frames/rate,6),
            'examined_windows':len(indices),'accepted_windows':accepted,
            'pitch_class_distribution':{n:round(v/total,6) if total else 0.0 for n,v in zip(NOTES,chroma)},
            'method':'half-second Hann-windowed Goertzel powers, C2–B5, major/minor profile correlation',
            'scope':'Estimated global tonal centre only. Scores are profile correlations, not calibrated probabilities. Modulation, detuning and complex music require listening.',**classification}
def review(root,source,output,exclude=()):
    return guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);report=estimate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    payload=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode()
    if json.loads(payload)!=report:raise ValueError('Key report roundtrip failed')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-musical-key-result-v1','status':report['status'],'output':plan['output'],'sha256':sha,'key':report['key'],'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Key analysis unavailable; inspect supported WAV format and channel'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
