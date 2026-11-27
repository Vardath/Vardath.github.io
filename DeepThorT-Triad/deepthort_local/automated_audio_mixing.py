"""Reviewed automatic RMS-based level balancing and bounded stereo summation."""
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
from deepthort_local.action_guards import snapshot_file
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.artifact_media_checks import wav

SCHEMA='janus-automated-audio-mixing-v1'
MAX_SECONDS=30
MAX_TRACKS=6
MAX_BYTES=48000*MAX_SECONDS*4+65536
def number(v,lo,hi):
    return type(v) in (float,int) and math.isfinite(v) and lo<=v<=hi
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'tracks','target_rms_dbfs','max_boost_db','peak_dbfs'}:
        raise ValueError('Expected reviewed tracks and explicit auto-balance limits')
    for key,lo,hi in (('target_rms_dbfs',-36,-12),('max_boost_db',0,12),('peak_dbfs',-12,-1)):
        if not number(spec[key],lo,hi):raise ValueError('Mix setting outside bounds: '+key)
    tracks=spec['tracks']
    if not isinstance(tracks,list) or not 2<=len(tracks)<=MAX_TRACKS:raise ValueError('Expected 2–6 tracks')
    seen=set()
    for t in tracks:
        if not isinstance(t,dict) or set(t)!={'audio','offset_ms','trim_db','pan'} or not isinstance(t['audio'],str) or t['audio'].casefold() in seen:
            raise ValueError('Expected distinct track paths')
        seen.add(t['audio'].casefold())
        if type(t['offset_ms']) is not int or not 0<=t['offset_ms']<=10000 or not number(t['trim_db'],-24,6) or not number(t['pan'],-1,1):
            raise ValueError('Track trim, offset or pan outside bounds')
    return spec
def db(rms):
    return 20*math.log10(rms/32768) if rms else None
def prepare(raws,spec):
    spec=checked(spec)
    if len(raws)!=len(spec['tracks']):raise ValueError('Track count differs')
    items=[];rate=None;end=0
    for raw,t in zip(raws,spec['tracks']):
        if not isinstance(raw,bytes) or len(raw)>MAX_BYTES:raise ValueError('Track bytes exceed bound')
        samples,r,c,n=pcm(raw)
        if rate is not None and r!=rate:raise ValueError('All tracks need matching sample rates')
        rate=r;offset=round(t['offset_ms']*r/1000);end=max(end,offset+n)
        if end>MAX_SECONDS*rate:raise ValueError('Mix duration exceeds 30 seconds')
        rms=math.sqrt(sum(v*v for v in samples)/len(samples));level=db(rms)
        # Never amplify silence or extremely quiet noise; require useful audio on every track.
        if level is None or level < -60:raise ValueError('Silent or nearly silent track; review source')
        automatic=max(-36,min(spec['max_boost_db'],spec['target_rms_dbfs']-level))
        # Trim is explicit, and automatic boost is independently bounded.
        gain=10**((automatic+t['trim_db'])/20)
        if c==1:
            angle=(t['pan']+1)*math.pi/4;gl,gr=gain*math.cos(angle),gain*math.sin(angle)
        else:
            gl=gain*(1-max(0,t['pan']));gr=gain*(1+min(0,t['pan']))
        record={'audio':t['audio'],'sha256':hashlib.sha256(raw).hexdigest(),'source_channels':c,
                'source_frames':n,'offset_frames':offset,'source_rms_dbfs':round(level,6),
                'automatic_gain_db':round(automatic,6),'trim_db':t['trim_db'],'pan':t['pan']}
        items.append((samples,c,n,offset,gl,gr,record))
    return items,rate,end
def mix(raws,spec):
    items,rate,frames=prepare(raws,spec)
    left=array('d',[0])*frames;right=array('d',[0])*frames
    for s,c,n,offset,gl,gr,_ in items:
        for i in range(n):
            left[offset+i]+=s[i*c]*gl
            right[offset+i]+=s[i*c+c-1]*gr
    peak=max(max(abs(v) for v in left),max(abs(v) for v in right))
    if not math.isfinite(peak) or peak<=0:raise ValueError('Silent or nonfinite mix')
    ceiling=math.floor(32767*10**(spec['peak_dbfs']/20))
    gain=min(1,ceiling/peak)
    samples=array('h',(round(v*gain) for pair in zip(left,right) for v in pair))
    if not any(samples):raise ValueError('Mixed signal below PCM resolution')
    payload=encode(samples,rate,2);wav(payload,max_chunks=16)
    decoded,r,c,n=pcm(payload)
    if (r,c,n)!=(rate,2,frames) or decoded!=samples:raise ValueError('Mixed PCM roundtrip failed')
    return payload,{'sample_rate':rate,'channels':2,'frames':frames,'duration_seconds':frames/rate,
        'tracks':[v[-1] for v in items],'shared_headroom_gain':gain,'peak_pcm':max(abs(v) for v in samples),
        'output_rms_dbfs':round(db(math.sqrt(sum(v*v for v in samples)/len(samples))),6),
        'method':'whole-track RMS matching with bounded gain, explicit trim/pan/offset and shared peak attenuation',
        'perceptual_balance_verified':False,'listening_verified':False,'lufs_verified':False}
def paths_for(root,spec,exclude):
    paths=[guard.path_for(root,t['audio'],exclude,{'.wav'},exists=True) for t in spec['tracks']]
    if len(set(paths))!=len(paths) or any(p.stat().st_size>MAX_BYTES for p in paths):raise ValueError('Repeated or oversized audio source')
    return paths
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=MAX_TRACKS+1:
        raise ValueError('Invalid mix approval')
    spec,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.wav')
    paths=paths_for(Path(root).resolve(strict=True),spec,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed track changed')
    return spec,dst,paths
def raws_for(paths,plan):
    return [guard.exact(p,g,MAX_BYTES) for p,g in zip(paths,plan['guards'][1:])]
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav')
    paths=paths_for(Path(plan['root']),spec,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in paths)
    spec,_,paths=validate(root,plan);items,rate,frames=prepare(raws_for(paths,plan),spec)
    return plan,dict(spec,track_observations=[v[-1] for v in items],duration_seconds=frames/rate,
        scope='Automatic whole-track RMS balance with explicit controls; not perceptual mixing or LUFS.')
def execute(root,plan):
    spec,dst,paths=validate(root,plan);payload,report=mix(raws_for(paths,plan),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-automated-audio-mixing-result-v1','status':'mixed_pcm_verified','output':plan['output'],
            'sha256':sha,'source_unchanged':True,**report}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed audio tracks, mix settings or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
