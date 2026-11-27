"""Reviewed multilingual narration using exact installed local desktop voices."""
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import time
import wave
from . import typed_project_tool as guard
from .source_security import exclusions
from .action_guards import snapshot_file
from .local_speech import WindowsSpeech,voice_record,inspect_audio,check_cancel
from .structured_source import strict_json

RATE=22050
MAX_SEGMENTS=8
MAX_TEXT=4000
MAX_SECONDS=300
MAX_SPEC=65536
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'segments','pause_ms'} or not isinstance(spec['segments'],list) or not 1<=len(spec['segments'])<=MAX_SEGMENTS or type(spec['pause_ms']) is not int or not 0<=spec['pause_ms']<=2000:
        raise ValueError('Expected bounded language segments and explicit pause milliseconds')
    total=0
    for row in spec['segments']:
        if not isinstance(row,dict) or set(row)!={'culture','voice_id','text'}:raise ValueError('Expected exact culture, voice ID and text')
        culture,ident,text=(row[k] for k in ('culture','voice_id','text'))
        if not isinstance(culture,str) or not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){1,3}',culture):raise ValueError('Use exact regional language culture')
        if not isinstance(ident,str) or not ident.strip() or len(ident)>400 or any(ord(c)<32 for c in ident):raise ValueError('Invalid installed voice identity')
        if not isinstance(text,str) or not text.strip() or len(text)>1000 or any((ord(c)<32 and c not in '\n\t') or 0xd800<=ord(c)<=0xdfff for c in text):raise ValueError('Invalid bounded plain text')
        total+=len(text)
    if total>MAX_TEXT:raise ValueError('Text exceeds bound')
    return spec

def select(voices,spec):
    voices=[voice_record(v) for v in voices]
    selected=[]
    for row in spec['segments']:
        matches=[v for v in voices if v['id']==row['voice_id'] and v['culture'].casefold()==row['culture'].casefold()]
        if len(matches)!=1 or sum(v['name']==matches[0]['name'] for v in voices)!=1:raise ValueError('Exact installed voice missing or ambiguous')
        selected.append(matches[0])
    return selected

def review(root,source,output,voices,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.json'},exists=True)
    guard.path_for(root,output,exclude,{'.wav'},exists=False)
    pin=snapshot_file(src)
    spec=checked(strict_json(guard.exact(src,pin,MAX_SPEC).decode('utf-8-sig')))
    return {'schema':'janus-multilingual-speech-v1','root':str(root),'source':source,'output':output,'exclude':exclude,
            'guard':pin,'voices':select(voices,spec),'expires_at':int(time.time())+1800},spec

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','voices','expires_at'} or plan['schema']!='janus-multilingual-speech-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid or expired narration approval')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.json'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.wav'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed narration changed')
    spec=checked(strict_json(guard.exact(src,plan['guard'],MAX_SPEC).decode('utf-8-sig')))
    if not isinstance(plan['voices'],list) or len(plan['voices'])!=len(spec['segments']):raise ValueError('Missing reviewed voice binding')
    # Deduplicate repeated voice metadata before checking each exact selection.
    unique={v['id']:voice_record(v) for v in plan['voices']}
    if select(list(unique.values()),spec)!=plan['voices']:raise ValueError('Invalid reviewed voice binding')
    return spec,dst

def render(root,plan,cancelled=None,*,approved=False,backend=None,stage=None):
    if approved is not True:raise PermissionError('Explicit multilingual speech approval required')
    check_cancel(cancelled);spec,dst=validate(root,plan)
    backend=backend or WindowsSpeech()
    if select(backend.voices(cancelled),spec)!=plan['voices']:raise ValueError('Installed voice identity changed')
    pause=round(RATE*spec['pause_ms']/1000);pieces=[];receipts=[];frames=0
    with tempfile.TemporaryDirectory(prefix='janus-multilingual-') as temp:
        for i,(row,voice) in enumerate(zip(spec['segments'],plan['voices']),1):
            check_cancel(cancelled);validate(root,plan)
            if stage:stage(i)
            path=Path(temp)/f'segment-{i}.wav'
            actual=backend.synthesize(row['text'],voice,path,cancelled)
            evidence=inspect_audio(path)
            if actual!=evidence:raise ValueError('Synthesis evidence changed')
            with wave.open(str(path),'rb') as f:
                data=f.readframes(f.getnframes())
            if len(data)!=evidence['frames']*2:raise ValueError('Truncated speech segment')
            if frames+evidence['frames']+(pause if i>1 else 0)>RATE*MAX_SECONDS:raise ValueError('Combined narration exceeds duration bound')
            if i>1:pieces.append(b'\0'*(2*pause));frames+=pause
            receipts.append({'segment':i,'culture':voice['culture'],'voice_id':voice['id'],'start_seconds':round(frames/RATE,6),
                             'duration_seconds':evidence['duration_seconds'],'sha256':evidence['sha256']})
            pieces.append(data);frames+=evidence['frames']
    check_cancel(cancelled)
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(b''.join(pieces))
    payload=out.getvalue()
    def revalidate():
        check_cancel(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'schema':'janus-multilingual-speech-result-v1','status':'wav_published','output':plan['output'],'sha256':digest,
            'segments':receipts,'duration_seconds':round(frames/RATE,6),'translation_performed':False,'pronunciation_verified':False,'neural_voice_claimed':False}
