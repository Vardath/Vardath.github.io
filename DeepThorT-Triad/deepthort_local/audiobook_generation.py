"""Reviewed chapter-oriented short audiobook production, reusing local speech synthesis."""
import hashlib
import io
import json
from pathlib import Path
import time
import zipfile
from . import typed_project_tool as guard
from .action_guards import snapshot_file
from .source_security import exclusions
from .structured_source import strict_json
from .local_speech import WindowsSpeech,check_cancel
from .multilingual_speech import checked as checked_speech,select,synthesize_segments,MAX_SPEC,RATE,MAX_SECONDS
from .podcast_generation import label

def speech_spec(spec,chapter):
    return {'segments':[{'culture':spec['culture'],'voice_id':spec['voice_id'],'text':text} for text in chapter['passages']],
            'pause_ms':spec['pause_ms']}

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'title','author','culture','voice_id','chapters','pause_ms'} or not isinstance(spec['chapters'],list) or not 1<=len(spec['chapters'])<=6:
        raise ValueError('Expected bounded manuscript and one exact narrator')
    label(spec['title'],160);label(spec['author'],160)
    titles=set();count=total=0
    for chapter in spec['chapters']:
        if not isinstance(chapter,dict) or set(chapter)!={'title','passages'} or not isinstance(chapter['passages'],list) or not 1<=len(chapter['passages'])<=4:raise ValueError('Invalid chapter')
        title=label(chapter['title'],120)
        if title.casefold() in titles:raise ValueError('Chapter titles must be distinct')
        titles.add(title.casefold());checked_speech(speech_spec(spec,chapter))
        count+=len(chapter['passages']);total+=sum(len(x) for x in chapter['passages'])
    if count>12 or total>6000:raise ValueError('Short audiobook manuscript exceeds bound')
    return spec

def voice_selection(voices,spec):
    return select(voices,speech_spec(spec,spec['chapters'][0]))[0]

def review(root,source,output,voices,exclude=()):
    root=Path(root).resolve(strict=True);exclude=exclusions(exclude)
    src=guard.path_for(root,source,exclude,{'.json'},exists=True)
    guard.path_for(root,output,exclude,{'.zip'},exists=False)
    pin=snapshot_file(src);spec=checked(strict_json(guard.exact(src,pin,MAX_SPEC).decode('utf-8-sig')))
    return {'schema':'janus-audiobook-v1','root':str(root),'source':source,'output':output,'exclude':exclude,'guard':pin,
            'voice':voice_selection(voices,spec),'expires_at':int(time.time())+1800},spec

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guard','voice','expires_at'} or plan['schema']!='janus-audiobook-v1' or plan['root']!=str(root) or exclusions(plan['exclude'])!=plan['exclude'] or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Invalid audiobook review')
    src=guard.path_for(root,plan['source'],plan['exclude'],{'.json'},exists=True)
    dst=guard.path_for(root,plan['output'],plan['exclude'],{'.zip'},exists=False)
    if snapshot_file(src)!=plan['guard']:raise ValueError('Reviewed manuscript changed')
    spec=checked(strict_json(guard.exact(src,plan['guard'],MAX_SPEC).decode('utf-8-sig')))
    if voice_selection([plan['voice']],spec)!=plan['voice']:raise ValueError('Narrator binding changed')
    return spec,dst

def render(root,plan,cancelled=None,*,approved=False,backend=None,stage=None):
    if approved is not True:raise PermissionError('Explicit audiobook approval required')
    check_cancel(cancelled);spec,dst=validate(root,plan)
    backend=backend or WindowsSpeech();files={};rows=[];frames=0;completed=0
    for i,chapter in enumerate(spec['chapters'],1):
        check_cancel(cancelled);validate(root,plan)
        count=len(chapter['passages'])
        payload,timing,n=synthesize_segments(speech_spec(spec,chapter),[plan['voice']]*count,backend,cancelled,
                                              (lambda j:stage(completed+j)) if stage else None,lambda:validate(root,plan))
        if frames+n>RATE*MAX_SECONDS:raise ValueError('Combined short audiobook exceeds duration bound')
        name=f'chapter-{i:02d}.wav';files[name]=payload
        rows.append({'chapter':i,'title':chapter['title'],'file':name,'start_seconds':round(frames/RATE,6),'duration_seconds':round(n/RATE,6),
                     'sha256':hashlib.sha256(payload).hexdigest(),'passage_timings':timing})
        frames+=n;completed+=count
    manifest={'schema':'janus-audiobook-result-v1','title':spec['title'],'author':spec['author'],'voice':plan['voice'],
              'source_sha256':plan['guard']['expected'],'duration_seconds':round(frames/RATE,6),'sample_rate':RATE,'chapters':rows,
              'manuscript_supplied':True,'listening_verified':False,'published_online':False}
    files['book.json']=json.dumps(manifest,ensure_ascii=True,allow_nan=False,indent=2).encode('ascii')
    files['manuscript.txt']=('\n\n'.join([spec['title'],spec['author']]+[c['title']+'\n\n'+'\n\n'.join(c['passages']) for c in spec['chapters']])+'\n').encode('utf-8')
    check_cancel(cancelled)
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for name,payload in files.items():z.writestr(name,payload)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Audiobook bundle exceeds byte bound')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if set(z.namelist())!=set(files) or any(z.read(k)!=v for k,v in files.items()):raise ValueError('Audiobook bundle verification failed')
    def revalidate():
        check_cancel(cancelled);validate(root,plan)
    digest=guard.publish(payload,dst,revalidate)
    return {'status':'audiobook_bundle_published','output':plan['output'],'sha256':digest,'chapters':len(rows),
            'duration_seconds':manifest['duration_seconds'],'files':list(files),'listening_verified':False,'published_online':False}
