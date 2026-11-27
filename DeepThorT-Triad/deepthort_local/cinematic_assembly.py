"""Reviewed short cinematic assembly: actual video shots, transitions and exact audio.

Uses existing bounded frame editor and codec checks. No autonomous publication,
arbitrary filter/command execution, rights clearance or cinematic quality claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import video_trimming as video
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.tempo_detection import pcm
from deepthort_local.noise_reduction import encode
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-cinematic-assembly-v1'
RATE=48000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'title','sequence','soundtrack','audio_start_ms'}:
        raise ValueError('Expected title, reviewed shot sequence, soundtrack and exact audio start')
    if not isinstance(s['title'],str) or not 1<=len(s['title'].strip())<=120 or any(ord(c)<32 for c in s['title']):
        raise ValueError('Invalid production title')
    if not isinstance(s['soundtrack'],str) or not s['soundtrack']:
        raise ValueError('Choose a prepared mono/stereo PCM WAV soundtrack')
    start=s['audio_start_ms']
    if type(start) is not int or not 0<=start<=30000:raise ValueError('Invalid audio start')
    seq=video.checked(s['sequence'])
    if len(seq['clips']) not in (2,3) or set(seq)-{'clips','fps','transitions'}:
        raise ValueError('Choose 2–3 matched shots with cuts or crossfades; no upscale or interpolation')
    return s

def paths(root,s,exclude):
    pp=[guard.path_for(root,c['video'],exclude,{'.mp4'},exists=True) for c in s['sequence']['clips']]
    pp.append(guard.path_for(root,s['soundtrack'],exclude,{'.wav'},exists=True))
    if any(x.stat().st_size>guard.MAX_INPUT for x in pp) or any(x.samefile(y) for i,x in enumerate(pp) for y in pp[:i]):
        raise ValueError('Duplicate or oversized production input')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards']) not in (6,7):
        raise ValueError('Invalid production approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(pp)+3!=len(plan['guards']) or tuple(plan['guards'][-2:])!=installed(root):
        raise ValueError('Reviewed shot count or codec changed')
    if any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:-2])):
        raise ValueError('Reviewed cinematic input changed')
    return s,dst,pp

def soundtrack(raw,s,frames):
    samples,rate,channels,n=pcm(raw)
    if rate!=RATE or channels not in (1,2):raise ValueError('Soundtrack requires 48 kHz PCM16 WAV')
    fps=s['sequence']['fps'];start=s['audio_start_ms']*48
    count=frames*(RATE//fps)
    if not count or start+count>n:raise ValueError('Soundtrack does not cover entire reviewed timeline')
    chosen=samples[start*channels:(start+count)*channels]
    if not any(chosen):raise ValueError('Selected soundtrack is silent')
    payload=encode(chosen,RATE,channels)
    if pcm(payload)!=(chosen,RATE,channels,count):raise ValueError('Selected soundtrack PCM roundtrip failed')
    if sys.byteorder!='little':chosen.byteswap()
    return payload,chosen.tobytes(),channels,count

def mux(folder,tools,meta,wav,expected,channels,count):
    folder=Path(folder);ff,fp=(g['path'] for g in tools)
    (folder/'soundtrack.wav').write_bytes(wav)
    verify_guards(list(tools))
    video.run(ff,['-nostdin','-hide_banner','-loglevel','error','-xerror','-n','-protocol_whitelist','file',
        '-f','mov','-enable_drefs','0','-use_absolute_path','0','-i','sequence.mp4',
        '-protocol_whitelist','file','-f','wav','-i','soundtrack.wav','-map','0:v:0','-map','1:a:0',
        '-c:v','copy','-c:a','alac','-threads','1','-map_metadata','-1','-movflags','+faststart','film.mp4'],folder)
    out=folder/'film.mp4';payload=guard.read_bound(out,guard.MAX_OUTPUT)
    data=json.loads(video.run(fp,['-v','error','-protocol_whitelist','file','-f','mov','-enable_drefs','0','-use_absolute_path','0',
        '-count_frames','-show_streams','-show_format','-of','json',out.name],folder))
    streams=data['streams']
    if len(streams)!=2:raise ValueError('Expected one picture and one soundtrack stream')
    v=next((x for x in streams if x['codec_type']=='video'),{})
    a=next((x for x in streams if x['codec_type']=='audio'),{})
    if (v.get('codec_name')!='h264' or (v.get('width'),v.get('height'))!=(meta['width'],meta['height'])
            or int(v.get('nb_read_frames',-1))!=meta['frames'] or v.get('avg_frame_rate')!=str(meta['fps'])+'/1'
            or a.get('codec_name')!='alac' or int(a.get('sample_rate',0))!=RATE or a.get('channels')!=channels):
        raise ValueError('Muxed stream format differs')
    actual=video.decode(ff,out,0,meta['frames'],meta['width'],meta['height'])
    if hashlib.sha256(actual).hexdigest()!=meta['selected_rgb_sha256']:raise ValueError('Muxed picture differs from verified sequence')
    audio=video.run(ff,['-nostdin','-hide_banner','-loglevel','error','-xerror','-protocol_whitelist','file',
        '-f','mov','-enable_drefs','0','-use_absolute_path','0','-i',out.name,'-map','0:a:0','-vn',
        '-threads','1','-c:a','pcm_s16le','-f','s16le','pipe:1'],folder,len(expected))
    if audio!=expected or len(audio)!=count*channels*2:raise ValueError('Muxed soundtrack differs from exact selected PCM')
    verify_guards(list(tools))
    return payload

def operation(root,plan,render):
    s,dst,pp=validate(root,plan)
    raws=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:-2])]
    tools=plan['guards'][-2:];require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-cinema-',dir=dst.parent) as tmp:
        folder=Path(tmp)
        _,meta=video.observe(raws[:-1],s['sequence'],tools,folder,render=render)
        n=meta['frames'] if render else meta['output_frames']
        wav,expected,channels,count=soundtrack(raws[-1],s,n)
        receipt={'title':s['title'],'sequence':meta,'soundtrack_sha256':hashlib.sha256(raws[-1]).hexdigest(),
            'selected_audio_sha256':hashlib.sha256(expected).hexdigest(),'audio_frames':count,
            'audio_channels':channels,'audio_sample_rate':RATE,'duration_seconds':n/s['sequence']['fps'],
            'publication_rights_verified':False,'cinematic_quality_verified':False}
        if not render:return None,receipt
        payload=mux(folder,tools,meta,wav,expected,channels,count)
        return payload,dict(receipt,exact_picture_and_audio_verified=True)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    plan['guards'].extend(snapshot_file(p) for p in paths(Path(plan['root']),s,plan['exclude']))
    plan['guards'].extend(installed(root));_,r=operation(root,plan,False)
    return plan,dict(s,observations=r,scope='Assemble reviewed local shots and prepared soundtrack into short silent-source H.264/ALAC MP4 with exact frame/sample matching. No source generation, rights clearance or automatic publication.')

def execute(root,plan):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'cinematic_picture_audio_verified','output':plan['output'],'sha256':sha,
            'sources_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
