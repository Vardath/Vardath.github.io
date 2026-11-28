"""Reusable designed local voice presets and rendered audition, not new neural weights."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.local_speech import WindowsSpeech,voice_record,inspect_audio
from deepthort_local.multilingual_speech import checked as check_speech,select
from deepthort_local.voice_transformation import checked as check_effects,transform
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-custom-voice-design-v1'
EFFECT_KEYS={'speed_percent','ring_hz','ring_depth_percent','lowpass_hz'}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'name','voice','text','effects'}:
        raise ValueError('Expected named voice design, installed voice, audition text and effects')
    name=s['name']
    if not isinstance(name,str) or not name.strip() or len(name)>80 or any(ord(c)<32 for c in name):
        raise ValueError('Invalid design name')
    v=voice_record(s['voice'])
    check_speech({'segments':[{'culture':v['culture'],'voice_id':v['id'],'text':s['text']}],'pause_ms':0})
    e=s['effects']
    if not isinstance(e,dict) or set(e)!=EFFECT_KEYS:raise ValueError('Expected exact reviewed voice effects')
    check_effects(dict(e,audio='generated.wav'))
    return s

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    return plan,dict(s,scope='Exact installed generic voice plus reviewed varispeed, ring and tone settings; reusable JSON preset and verified WAV audition. Synthesized text must fit 5–20 seconds; no neural training or identity imitation.')

def canonical(value):
    return (json.dumps(value,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2)+'\n').encode('ascii')

def execute(root,plan,*,backend=None):
    s,dst,_=validate(root,plan);require_storage(dst.parent)
    backend=backend or WindowsSpeech()
    v=s['voice'];selection={'segments':[{'culture':v['culture'],'voice_id':v['id'],'text':s['text']}],'pause_ms':0}
    if select(backend.voices(None),selection)!=[v]:raise ValueError('Exact reviewed voice missing or changed')
    with tempfile.TemporaryDirectory(prefix='.janus-voice-design-',dir=dst.parent) as temp:
        path=Path(temp)/'speech.wav'
        observed=backend.synthesize(s['text'],v,path,None)
        if inspect_audio(path)!=observed:raise ValueError('Synthesis evidence changed')
        raw=guard.read_bound(path,guard.MAX_INPUT)
        if hashlib.sha256(raw).hexdigest()!=observed['sha256']:raise ValueError('Synthesis bytes changed')
        audio,effects=transform(raw,dict(s['effects'],audio='generated.wav'))
    # Preset is directly reusable as a typed input; only its audition text need change.
    preset=canonical(s)
    receipt={'schema':SCHEMA,'name':s['name'],'voice':v,'preset_sha256':hashlib.sha256(preset).hexdigest(),
             'audition_sha256':hashlib.sha256(audio).hexdigest(),'original_speech_sha256':observed['sha256'],
             'effects':effects,'new_neural_voice_trained':False,'voice_cloning':False,
             'identity_similarity_verified':False,'listening_verified':False}
    files={'voice-design.json':preset,'audition.wav':audio,'receipt.json':canonical(receipt)}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Voice bundle exceeds bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.namelist()!=list(files) or any(z.read(k)!=v for k,v in files.items()):
            raise ValueError('Voice design bundle verification failed')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'voice_design_audition_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed voice design unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
