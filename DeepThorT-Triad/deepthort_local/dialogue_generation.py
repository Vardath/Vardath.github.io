"""Produce a reviewed scripted dialogue dialogue bundle with measured turn timings."""
import io
import hashlib
import json
from pathlib import Path
import time
import zipfile
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions
from .structured_source import strict_json
from .multilingual_speech import checked as checked_speech,select,synthesize_segments,RATE,MAX_SPEC
from .local_speech import WindowsSpeech,voice_record,check_cancel

def label(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in value):
        raise ValueError('Invalid dialogue label')
    return value

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'title','description','turns','pause_ms'} or not isinstance(spec['turns'],list) or not 2<=len(spec['turns'])<=8:
        raise ValueError('Expected dialogue title, description, and 2–8 scripted turns')
    label(spec['title'],160);label(spec['description'],500)
    speakers={}
    for i,row in enumerate(spec['turns']):
        if not isinstance(row,dict) or set(row)!={'speaker','culture','voice_id','text'}:raise ValueError('Invalid dialogue turn')
        name=label(row['speaker'],80)
        if name!=name.strip() or any(k.casefold()==name.casefold() and k!=name for k in speakers):raise ValueError('Ambiguous speaker label')
        identity=(row['culture'],row['voice_id'])
        if name in speakers and speakers[name]!=identity:raise ValueError('Speaker voice assignment changed')
        if any(k!=name and v==identity for k,v in speakers.items()):raise ValueError('Different named speakers need distinct voices')
        speakers[name]=identity
    if not 2<=len(speakers)<=4:raise ValueError('Dialogue needs two to four distinct scripted speakers')
    checked_speech(speech_spec(spec))
    return spec

def speech_spec(spec):
    return {'segments':[{k:r[k] for k in ('culture','voice_id','text')} for r in spec['turns']],'pause_ms':spec['pause_ms']}

def review(root,source,output,voices,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.json'},exists=True)
    guard.path_for(root,output,exclude,{'.zip'},exists=False)
    pin=snapshot_file(src);spec=checked(strict_json(guard.exact(src,pin,MAX_SPEC).decode('utf-8-sig')))
    return {'schema':'janus-dialogue-v1','root':str(root),'source':source,'output':output,'exclude':exclude,
            'guard':pin,'voices':select(voices,speech_spec(spec)),'expires_at':int(time.time())+1800},spec

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','voices','expires_at'} or plan['schema']!='janus-dialogue-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid dialogue approval')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.json'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.zip'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed script changed')
    spec=checked(strict_json(guard.exact(src,plan['guard'],MAX_SPEC).decode('utf-8-sig')))
    if not isinstance(plan['voices'],list) or len(plan['voices'])!=len(spec['turns']):raise ValueError('Missing reviewed voices')
    unique={v['id']:voice_record(v) for v in plan['voices']}
    if select(list(unique.values()),speech_spec(spec))!=plan['voices']:raise ValueError('Reviewed voice binding changed')
    return spec,dst

def render(root,plan,cancelled=None,*,approved=False,backend=None,stage=None):
    if approved is not True:raise PermissionError('Explicit dialogue approval required')
    check_cancel(cancelled);spec,dst=validate(root,plan)
    audio,timings,frames=synthesize_segments(speech_spec(spec),plan['voices'],backend or WindowsSpeech(),cancelled,stage,lambda:validate(root,plan))
    rows=[{**timing,'speaker':turn['speaker'],'text':turn['text']} for timing,turn in zip(timings,spec['turns'])]
    manifest={'schema':'janus-dialogue-result-v1','title':spec['title'],'description':spec['description'],
              'source_sha256':plan['guard']['expected'],'audio_sha256':hashlib.sha256(audio).hexdigest(),'duration_seconds':round(frames/RATE,6),
              'sample_rate':RATE,'speakers':list(dict.fromkeys(row['speaker'] for row in rows)),'turns':rows,'script_supplied':True,'listening_verified':False,'published_online':False}
    transcript=('\n\n'.join(r['speaker']+' ['+str(r['start_seconds'])+' s]:\n'+r['text'] for r in rows)+'\n').encode('utf-8')
    files={'dialogue.wav':audio,'dialogue.json':json.dumps(manifest,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii'),'transcript.txt':transcript}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Dialogue bundle exceeds output bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if set(z.namelist())!=set(files) or any(z.read(name)!=data for name,data in files.items()):raise ValueError('Dialogue bundle verification failed')
    def revalidate():
        check_cancel(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'status':'dialogue_bundle_published','output':plan['output'],'sha256':digest,'duration_seconds':manifest['duration_seconds'],
            'turns':len(rows),'files':list(files),'script_supplied':True,'listening_verified':False,'published_online':False}
