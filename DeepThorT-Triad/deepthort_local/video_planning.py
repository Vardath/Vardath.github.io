"""Durable, reviewed script/storyboard drafts. No network, media or executable work."""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from .reasoning_council import sha
from .structured_source import strict_json

SCHEMA='deepthort-video-plan-v1'
MAX_BRIEF=3200

def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def binding(request):
    ident=request['id']
    original=request['prompt']
    if type(ident) is not int or ident<1 or not isinstance(original,str) or not original.strip().lower().startswith('/video '):
        raise ValueError('Expected an explicit video planning request')
    if request['project']=='(general)' or not request['project'] or not request['chat_id']:
        raise ValueError('Video planning requires a selected project and chat')
    if not 1<=len(original.strip()[7:].strip())<=MAX_BRIEF:
        raise ValueError('Video brief must contain 1–3200 characters; longer-form planning is not yet implemented')
    return {'request_id':ident,'project':request['project'],'chat_id':request['chat_id'],'prompt_sha256':sha(original)}

def obj(text):
    if not isinstance(text,str):raise ValueError('Missing video planning response')
    text=text.strip()
    if text.startswith('```json\n') and text.endswith('\n```'):text=text[8:-4].strip()
    value=strict_json(text)
    if not isinstance(value,dict):raise ValueError('Expected a video planning JSON object')
    return value

def text_field(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or '\x00' in value:
        raise ValueError('Invalid video planning text field')
    return value

def outline(value):
    if set(value)!={'title','audience','language','style','aspect','target_seconds','scenes'}:
        raise ValueError('Invalid video outline fields')
    for name,limit in [('title',140),('audience',120),('language',60),('style',180)]:
        text_field(value[name],limit)
    if value['aspect'] not in ('16:9','9:16','1:1'):
        raise ValueError('Unsupported video aspect')
    if type(value['target_seconds']) is not int or not 15<=value['target_seconds']<=300:
        raise ValueError('Initial video draft supports target durations of 15–300 seconds')
    if not isinstance(value['scenes'],list) or not 1<=len(value['scenes'])<=8:
        raise ValueError('Initial video draft supports 1–8 scenes')
    for scene in value['scenes']:
        if not isinstance(scene,dict) or set(scene)!={'title','intent'}:
            raise ValueError('Invalid scene outline')
        text_field(scene['title'],100);text_field(scene['intent'],180)
    return value

def scene_script(value):
    if set(value)!={'narration','visual','asset_source','research_needed'}:
        raise ValueError('Invalid scene script fields')
    text_field(value['narration'],1000);text_field(value['visual'],450)
    if value['asset_source'] not in ('stock','generate','either','provided'):
        raise ValueError('Invalid visual sourcing intent')
    if not isinstance(value['research_needed'],list) or len(value['research_needed'])>4:
        raise ValueError('Invalid research needs')
    for item in value['research_needed']:text_field(item,180)
    return value

def create_plan(client,council,request,*,review,cancelled=None,stage=None):
    source=binding(request); original=request['prompt']
    def check():
        if cancelled and cancelled():raise ValueError('Video planning cancelled')
    def approve(value,focus):
        check()
        result=review(value,focus)
        if not isinstance(result,dict) or result.get('accepted') is not True:
            raise ValueError('Sentinel did not accept video draft against the brief')
        check()
    def ask(role,prompt,key,tokens):
        check()
        if len(prompt)>7500:raise ValueError('Video planning input exceeds local context budget')
        reply=council._run(client,role=role,session='video-'+str(source['request_id']),
                            evidence_sha=sha(canonical([source,key,prompt])),prompt=prompt,stage=stage,max_tokens=tokens)
        check()
        return obj(reply)
    draft=outline(ask('JANUS_VIDEO_OUTLINE',
        'Create a storyboard outline for the exact video brief below. No rendering or factual research has happened. '
        'Preserve stated language, target duration, aspect, audience and visual style. If unspecified use a 60 second 16:9 draft. '
        'Current planning supports 15–300 seconds and 1–8 scenes; do not silently change a requested duration. '
        'Return ONLY JSON with title, audience, language, style, aspect, target_seconds (integer), scenes (list of objects each with title and intent). '
        'Keep scene titles and intents short; do not include source URLs or unsupported factual claims.\nEXACT USER BRIEF:\n'+original,
        'outline',640))
    approve(draft,'Video production outline')
    scripts=[]
    for number,entry in enumerate(draft['scenes'],1):
        previous=scripts[-1]['narration'][-300:] if scripts else ''
        prompt=('Write spoken narration and visual directions for just this numbered scene of the accepted storyboard. '
                'Use the user-requested language and style. Match the intended approximate duration; actual timings will come from synthesized audio later. '
                'Distinguish claims needing research from fictional or illustrative content. Do not invent sources, licenses or assert images have been acquired. '
                'Return ONLY JSON with narration (spoken text), visual (specific shot description), asset_source (stock, generate, either, or provided), '
                'research_needed (list of unresolved claims or empty list). No markdown.\n'
                'EXACT USER BRIEF:\n'+original+'\nSTORYBOARD:\n'+canonical(draft)
                +'\nSCENE '+str(number)+': '+canonical(entry)+'\nPREVIOUS NARRATION END:\n'+previous)
        script=scene_script(ask('JANUS_VIDEO_SCENE',prompt,['scene',number,sha(canonical(draft))],640))
        approve({'scene':number,'outline':entry,'script':script},f'Video scene {number} narration and imagery')
        scripts.append({'scene':number,**script})
    check()
    return {'schema':SCHEMA,'binding':source,'outline':draft,'scripts':scripts,
            'status':'reviewed_draft','rendered':False,'assets_acquired':False,'audio_generated':False}

def validate_plan(request,plan):
    if (not isinstance(plan,dict) or set(plan)!={'schema','binding','outline','scripts','status','rendered','assets_acquired','audio_generated'}
        or plan['schema']!=SCHEMA or plan['binding']!=binding(request) or plan['status']!='reviewed_draft'
        or any(plan[k] is not False for k in ('rendered','assets_acquired','audio_generated'))):
        raise ValueError('Video plan identity or state changed')
    outline(plan['outline'])
    if not isinstance(plan['scripts'],list) or len(plan['scripts'])!=len(plan['outline']['scenes']):
        raise ValueError('Incomplete scene scripts')
    for n,row in enumerate(plan['scripts'],1):
        if not isinstance(row,dict) or type(row.get('scene')) is not int or row['scene']!=n:
            raise ValueError('Video scene sequence changed')
        scene_script({k:v for k,v in row.items() if k!='scene'})
    return plan

def save_plan(folder,request,plan):
    validate_plan(request,plan)
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    dest=folder/f"request-{request['id']}.json"
    payload=canonical({'plan':plan,'sha256':sha(canonical(plan))}).encode('utf-8')
    if len(payload)>65536:raise ValueError('Video manifest exceeds storage bound')
    if dest.exists():
        if dest.read_bytes()!=payload:raise ValueError('Existing video plan differs; use a new request')
        return dest
    fd,temp=tempfile.mkstemp(prefix='.video-',suffix='.tmp',dir=folder)
    try:
        with os.fdopen(fd,'wb') as f:f.write(payload);f.flush();os.fsync(f.fileno())
        os.replace(temp,dest)
    finally:
        if os.path.exists(temp):os.unlink(temp)
    return dest

def load_plan(path,request):
    path=Path(path)
    if path.stat().st_size>65536:raise ValueError('Video plan exceeds storage bound')
    data=strict_json(path.read_text('utf-8'))
    if not isinstance(data,dict) or set(data)!={'plan','sha256'} or data['sha256']!=sha(canonical(data['plan'])):
        raise ValueError('Video plan integrity check failed')
    return validate_plan(request,data['plan'])

def describe(plan,path):
    o=plan['outline']
    lines=['Reviewed video planning draft — NOT a rendered video.',o['title'],
           f"{o['target_seconds']}s target (not measured), {o['aspect']}, {o['language']}",
           'Saved local manifest: '+str(path),'']
    for entry,row in zip(o['scenes'],plan['scripts']):
        lines.extend([f"Scene {row['scene']}: {entry['title']}",'Narration: '+row['narration'],
            'Visual: '+row['visual'],'Asset sourcing intent: '+row['asset_source']])
        if row['research_needed']:lines.append('Research needed: '+ '; '.join(row['research_needed']))
        lines.append('')
    lines.append('No images, narration audio or video have been generated; factual claims and asset rights still need verification.')
    return '\n'.join(lines)
