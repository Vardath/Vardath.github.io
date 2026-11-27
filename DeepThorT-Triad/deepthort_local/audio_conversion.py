"""Reviewed local PCM WAV to FLAC/MP3 using the installed FFmpeg pair."""
from __future__ import annotations
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.tempo_detection import pcm
from deepthort_local.video_tools import find_pair

SCHEMA='janus-audio-conversion-v1'
EXTRA=('audio','.wav')
FORMATS={'flac':'.flac','mp3':'.mp3'}
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'audio','format','bitrate_kbps'} or not isinstance(spec['audio'],str) or spec['format'] not in FORMATS:
        raise ValueError('Expected WAV source and explicit FLAC or MP3 output format')
    b=spec['bitrate_kbps']
    if spec['format']=='flac':
        if b is not None:raise ValueError('Lossless FLAC requires null bitrate')
    elif type(b) is not int or b not in (128,192,256,320):raise ValueError('Choose supported MP3 bitrate')
    return spec

def installed(root):
    pair=find_pair()
    if not pair:raise ValueError('Install the local FFmpeg and FFprobe tools first')
    root=Path(root).resolve()
    if any(Path(p).resolve().is_relative_to(root) for p in pair):
        raise ValueError('Project-local executables are not accepted')
    return tuple(snapshot_file(p,kind='stat') for p in pair)

def input_pcm(raw,spec):
    samples,rate,channels,frames=pcm(raw)
    if spec['format']=='mp3' and rate not in (32000,44100,48000):
        raise ValueError('MP3 conversion requires 32, 44.1 or 48 kHz PCM')
    if sys.byteorder!='little':samples.byteswap()
    return samples.tobytes(),rate,channels,frames

def run(exe,args,payload,limit):
    opts={'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}
    result=subprocess.run([exe,*args],input=payload,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          cwd=str(Path(exe).parent),timeout=45,check=False,**opts)
    if result.returncode or not result.stdout or len(result.stdout)>limit:
        raise ValueError('Installed codec failed or exceeded output bound')
    return result.stdout

def convert(raw,spec,tools):
    verify_guards(list(tools));ff,probe=(x['path'] for x in tools)
    samples,rate,channels,frames=input_pcm(raw,spec);fmt=spec['format']
    args=['-nostdin','-hide_banner','-loglevel','error','-f','s16le','-ar',str(rate),'-ac',str(channels),
          '-i','pipe:0','-map','0:a:0','-map_metadata','-1','-threads','1']
    args+=['-c:a','flac','-sample_fmt','s16','-compression_level','5'] if fmt=='flac' else ['-c:a','libmp3lame','-b:a',str(spec['bitrate_kbps'])+'k','-write_xing','0']
    payload=run(ff,args+['-f',fmt,'pipe:1'],samples,guard.MAX_OUTPUT)
    verify_guards(list(tools))
    meta=json.loads(run(probe,['-v','error','-f',fmt,'-show_entries','stream=codec_name,sample_rate,channels','-of','json','pipe:0'],payload,65536))
    streams=meta.get('streams',[])
    if len(streams)!=1 or streams[0].get('codec_name')!=fmt or int(streams[0].get('sample_rate',0))!=rate or streams[0].get('channels')!=channels:
        raise ValueError('Encoded stream identity or format mismatch')
    decoded=run(ff,['-nostdin','-hide_banner','-loglevel','error','-f',fmt,'-i','pipe:0','-map','0:a:0',
                    '-threads','1','-c:a','pcm_s16le','-f','s16le','pipe:1'],payload,guard.MAX_INPUT+1024*1024)
    if len(decoded)%(channels*2):raise ValueError('Decoded audio frame alignment invalid')
    decoded_frames=len(decoded)//(channels*2)
    if fmt=='flac':
        if decoded!=samples:raise ValueError('Lossless PCM verification failed')
    elif abs(decoded_frames-frames)>rate*.2:
        raise ValueError('MP3 decoded duration differs beyond encoder padding allowance')
    return payload,{'codec':fmt,'sample_rate':rate,'channels':channels,'source_frames':frames,'decoded_frames':decoded_frames,
                    'source_pcm_sha256':hashlib.sha256(samples).hexdigest(),'decoded_pcm_sha256':hashlib.sha256(decoded).hexdigest(),
                    'lossless_pcm_verified':fmt=='flac','metadata_preserved':False,'listening_verified':False}

def suffix(output):
    s=Path(output).suffix.casefold()
    if s not in FORMATS.values():raise ValueError('Choose a new .flac or .mp3 output')
    return s
def review(root,source,output,exclude=()):
    s=suffix(output)
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix=s,extra=EXTRA)
    if s!=FORMATS[spec['format']]:raise ValueError('Output extension does not match requested format')
    _,_,path=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix=s,extra=EXTRA)
    _,rate,channels,frames=input_pcm(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    tools=installed(root);plan['guards'].extend(tools)
    return plan,dict(spec,installed_tools=[x['path'] for x in tools],source_format={'sample_rate':rate,'channels':channels,'frames':frames},
                     scope='Audio-only conversion; source retained, metadata not copied; MP3 is lossy.')
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Missing reviewed codec executable identities')
    s=suffix(plan['output'])
    spec,dst,path=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix=s,extra=EXTRA)
    if s!=FORMATS[spec['format']] or tuple(plan['guards'][2:])!=installed(root):
        raise ValueError('Reviewed format or installed codec changed')
    verify_guards(plan['guards'][2:])
    return spec,dst,path
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,receipt=convert(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec,plan['guards'][2:])
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-audio-conversion-result-v1','status':'decoded_audio_verified','output':plan['output'],'sha256':sha,
            **receipt,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Audio conversion unavailable; inspect reviewed PCM format, codec installation and output bounds'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
