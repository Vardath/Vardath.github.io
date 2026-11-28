"""Owner-reviewed optional local XTTS reference-conditioned speech, never auto-installed."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.neural_speech import inspect,stopped
from deepthort_local.tempo_detection import pcm
from deepthort_local.source_security import linked
from deepthort_local.structured_source import strict_json

SCHEMA='janus-consent-voice-cloning-v1'
EXTRA=('reference','.wav')
LANGUAGES=frozenset('en es fr de it pt pl tr ru nl cs ar zh-cn ja hu ko hi'.split())
FILES=('config.json','model.pth','vocab.json','speakers_xtts.pth')
MEMORY_LIMIT=5*1024**3
MAX_WAV=4*1024**2

def checked(s):
    if not isinstance(s,dict) or set(s)!={'reference','engine','model_directory','language','text','consent'}:
        raise ValueError('Expected reference, installed engine, model directory, language, text and consent')
    if any(not isinstance(s[k],str) or not 1<=len(s[k])<=500 for k in ('reference','engine','model_directory')):
        raise ValueError('Invalid paths')
    if not isinstance(s['language'],str) or s['language'] not in LANGUAGES:raise ValueError('Unsupported XTTS language')
    text=s['text']
    if not isinstance(text,str) or not text.strip() or len(text)>500 or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in text):
        raise ValueError('Use bounded plain text')
    c=s['consent']
    if not isinstance(c,dict) or set(c)!={'basis','scope','non_deceptive'} or c['basis'] not in ('own_voice','documented_speaker_permission') or c['non_deceptive'] is not True:
        raise ValueError('Own voice or documented speaker permission and non-deceptive use required')
    scope=c['scope']
    if not isinstance(scope,str) or not scope.strip() or len(scope)>300 or any(ord(x)<32 for x in scope):
        raise ValueError('Describe the permitted use')
    return s

def regular_external(root,p,directory=False):
    p=Path(p)
    if not p.is_absolute() or p.resolve(strict=True)!=p or p.is_relative_to(root) or any(linked(x) for x in (p,*p.parents)):
        raise ValueError('Select trusted installed files outside the project, not linked paths')
    if not (p.is_dir() if directory else p.is_file()):raise ValueError('Installed path missing')
    return p

def installed(root,s):
    root=Path(root).resolve(strict=True)
    engine=regular_external(root,s['engine'])
    model=regular_external(root,s['model_directory'],True)
    if engine.name.casefold()!='tts.exe':raise ValueError('Select installed Coqui TTS CLI (tts.exe)')
    files=[regular_external(root,model/name) for name in FILES]
    limits=(32*1024**2,1024**2,3*1024**3,8*1024**2,128*1024**2)
    for path,limit in zip([engine,*files],limits):
        if not 1<=path.stat().st_size<=limit:raise ValueError('Installed asset exceeds bound')
    # Large checkpoints are stat-pinned, not cryptographically authenticated.
    pins=[snapshot_file(path,kind='stat' if path.suffix=='.pth' else 'sha256') for path in [engine,*files]]
    config=strict_json(guard.exact(files[0],pins[1],1024**2).decode('utf-8-sig'))
    if not isinstance(config,dict) or config.get('model')!='xtts' or not isinstance(config.get('audio'),dict) or config['audio'].get('output_sample_rate')!=24000:
        raise ValueError('Use a compatible trusted XTTS model with 24 kHz output')
    languages=config.get('languages')
    if not isinstance(languages,list) or s['language'] not in languages:raise ValueError('Language unavailable in reviewed model')
    return pins

def reference(raw):
    samples,rate,ch,frames=pcm(raw)
    if ch!=1 or not 16000<=rate<=48000 or not 6*rate<=frames<=20*rate:
        raise ValueError('Use 6–20 seconds of mono PCM16 reference speech at 16–48 kHz')
    if max(abs(x) for x in samples)<250 or sum(abs(x)>=100 for x in samples)<frames*.01:
        raise ValueError('Reference silent or nearly silent')
    return {'sample_rate':rate,'frames':frames,'duration_seconds':frames/rate,'sha256':hashlib.sha256(raw).hexdigest()}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=7:
        raise ValueError('Missing reference and installed tool identities')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    if installed(root,s)!=plan['guards'][2:]:raise ValueError('Installed engine or model changed')
    return s,dst,src

def command(s,ref,out):
    return [s['engine'],'--model_path',s['model_directory'],'--config_path',str(Path(s['model_directory'])/'config.json'),
            '--device','cpu','--speaker_wav',str(ref),'--language_idx',s['language'],'--text',s['text'],'--out_path',str(out)]

class XTTS:
    def render(self,s,raw,cancelled=None):
        if os.name!='nt':raise RuntimeError('Capped Windows auxiliary engine required')
        from deepthort_local.triad_job import verify_root_cap,child_server
        cap,available,total=verify_root_cap()
        if cap<MEMORY_LIMIT or available<total//10+MEMORY_LIMIT:raise RuntimeError('Insufficient existing resource budget for optional voice engine')
        with tempfile.TemporaryDirectory(prefix='janus-xtts-') as temp:
            folder=Path(temp);ref=folder/'reference.wav';out=folder/'speech.wav';log=folder/'engine.log'
            ref.write_bytes(raw)
            with child_server(command(s,ref,out),folder,log,memory_limit=MEMORY_LIMIT) as (_,alive):
                deadline=time.monotonic()+180
                while alive():
                    stopped(cancelled)
                    if time.monotonic()>=deadline:raise TimeoutError('Local voice synthesis timed out')
                    if any(x.exists() and x.stat().st_size>limit for x,limit in ((out,MAX_WAV),(log,1024**2))):
                        raise ValueError('Engine output exceeds bound')
                    time.sleep(.1)
                if alive.code()!=0:raise RuntimeError('Installed XTTS engine failed')
            stopped(cancelled)
            if not out.is_file() or linked(out):raise ValueError('No regular WAV produced')
            return guard.read_bound(out,MAX_WAV)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.wav',extra=EXTRA)
    plan['guards'].extend(installed(root,s))
    _,_,path=validate(root,plan);info=reference(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(s,reference_format=info,installed_guards=plan['guards'][2:],
        scope='Explicit speaker permission and trusted installed XTTS required. Checkpoint stat guards are not authentication. No download, publication, speaker identification or independent consent verification.')

def execute(root,plan,*,backend=None,approved=False,cancelled=None):
    if approved is not True:raise PermissionError('Explicit consent and exact synthesis approval required')
    stopped(cancelled);s,dst,path=validate(root,plan)
    raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT);info=reference(raw)
    verify_guards(plan['guards'])
    payload=(backend or XTTS()).render(s,raw,cancelled)
    if not isinstance(payload,bytes) or len(payload)>MAX_WAV:raise ValueError('Output exceeds bound')
    evidence=inspect(payload,24000)
    def revalidate():
        stopped(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'schema':SCHEMA,'status':'reference_conditioned_wav_verified','output':plan['output'],'sha256':digest,
        'reference_sha256':info['sha256'],'consent_basis':s['consent']['basis'],'consent_attested':True,
        'consent_independently_verified':False,'speaker_identity_verified':False,'similarity_verified':False,
        'intelligibility_verified':False,'source_unchanged':True,'checkpoint_content_authenticated':False,**evidence}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan),approved=True),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed consent-based voice synthesis unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
