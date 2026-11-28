"""Bounded multitrack visual timeline compositor. No audio or arbitrary filters."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode,encode_verified,MAX_RENDER_RGB
from deepthort_local.texture_pixels import image_module
from deepthort_local.disk_gate import require_storage

SCHEMA='janus-video-timeline-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'width','height','fps','duration_frames','background','tracks'}:
        raise ValueError('Expected canvas, duration and ordered visual tracks')
    w,h,fps,n=(s[k] for k in ('width','height','fps','duration_frames'))
    if any(type(i) is not int for i in (w,h,fps,n)) or not 1<=w<=640 or not 1<=h<=480 or fps not in (24,25,30) or not 1<=n<=120:
        raise ValueError('Invalid canvas, frame rate or timeline duration')
    bg=s['background']
    if not isinstance(bg,list) or len(bg)!=3 or any(type(i) is not int or not 0<=i<=255 for i in bg):
        raise ValueError('Expected RGB background')
    tracks=s['tracks']
    if not isinstance(tracks,list) or not 1<=len(tracks)<=3:raise ValueError('Choose 1–3 bottom-to-top visual tracks')
    names=set();sources=set();count=0
    for t in tracks:
        if not isinstance(t,dict) or set(t)!={'name','clips'} or not isinstance(t['name'],str) or not t['name'].strip() or len(t['name'])>80 or any(ord(c)<32 for c in t['name']) or t['name'].casefold() in names:
            raise ValueError('Use distinct bounded track names')
        names.add(t['name'].casefold())
        if not isinstance(t['clips'],list) or not 1<=len(t['clips'])<=4:raise ValueError('Track requires clips')
        last=0
        for c in t['clips']:
            if not isinstance(c,dict) or set(c)!={'video','start_frame','end_frame','at','x','y','opacity'} or not isinstance(c['video'],str) or c['video'].casefold() in sources:
                raise ValueError('Choose distinct source clips with explicit timeline placement')
            a,b,at,x,y,o=(c[k] for k in ('start_frame','end_frame','at','x','y','opacity'))
            if any(type(i) is not int for i in (a,b,at,x,y,o)) or not 0<=a<b<=300 or not last<=at or at+b-a>n or not 0<=x<w or not 0<=y<h or not 0<=o<=100:
                raise ValueError('Invalid or overlapping clip placement')
            last=at+b-a;sources.add(c['video'].casefold());count+=1
    if not 1<=count<=4:raise ValueError('At most four distinct source clips across all tracks')
    return s

def clips(s):return [c for t in s['tracks'] for c in t['clips']]

def paths(root,s,exclude):
    pp=[guard.path_for(root,c['video'],exclude,{'.mp4'},exists=True) for c in clips(s)]
    if any(p.stat().st_size>guard.MAX_INPUT for p in pp) or any(a.samefile(b) for i,a in enumerate(pp) for b in pp[:i]):
        raise ValueError('Duplicate or oversized timeline sources')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 4<=len(plan['guards'])<=7:
        raise ValueError('Invalid timeline approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.mp4')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(plan['guards'])!=len(pp)+3 or tuple(plan['guards'][-2:])!=installed(root) or any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:-2])):
        raise ValueError('Reviewed clip or codec changed')
    return s,dst,pp

def composite(s,rows):
    Image=image_module();w,h,n=s['width'],s['height'],s['duration_frames'];out=bytearray()
    for i in range(n):
        with Image.new('RGB',(w,h),tuple(s['background'])) as canvas:
            for c,m,raw in rows:
                offset=i-c['at']
                if not 0<=offset<c['end_frame']-c['start_frame'] or not c['opacity']:continue
                cw,ch=m['width'],m['height'];stride=cw*ch*3
                with Image.frombytes('RGB',(cw,ch),raw[offset*stride:(offset+1)*stride]) as frame:
                    xy=(c['x'],c['y'])
                    if c['opacity']==100:canvas.paste(frame,xy)
                    else:
                        with canvas.crop((xy[0],xy[1],xy[0]+cw,xy[1]+ch)) as below:
                            with Image.blend(below,frame,c['opacity']/100) as blend:canvas.paste(blend,xy)
            out.extend(canvas.tobytes())
    return out

def observe(raws,s,tools,folder,*,render):
    checked(s);folder=Path(folder);verify_guards(tools);ff,fp=(g['path'] for g in tools)
    cs=clips(s)
    if len(raws)!=len(cs):raise ValueError('Timeline source count mismatch')
    rows=[];records=[];budget=0
    for i,(raw,c) in enumerate(zip(raws,cs)):
        path=folder/f'input-{i}.mp4';path.write_bytes(raw)
        m=probe(fp,path);w,h=m['width'],m['height']
        if m['fps']!=s['fps'] or c['end_frame']>m['frames'] or c['x']+w>s['width'] or c['y']+h>s['height']:
            raise ValueError('Source frame rate, interval or placement exceeds reviewed canvas')
        budget+=(c['end_frame']-c['start_frame'])*w*h*3
        if budget>MAX_RENDER_RGB:raise ValueError('Timeline decoded source budget exceeded')
        record=dict(c,source_format=m,source_sha256=hashlib.sha256(raw).hexdigest())
        if render:
            frames=decode(ff,path,c['start_frame'],c['end_frame'],w,h)
            rows.append((c,m,frames));record['source_rgb_sha256']=hashlib.sha256(frames).hexdigest()
        records.append(record)
    result={'tracks':[t['name'] for t in s['tracks']],'clips':records,'width':s['width'],'height':s['height'],
        'frames':s['duration_frames'],'fps':s['fps'],'audio_supported':False,'interactive_editor':False}
    if not render:return None,result
    selected=composite(s,rows)
    payload=encode_verified(selected,(s['width'],s['height']),s['fps'],s['duration_frames'],tools,folder)
    result.update(decoded_rgb_sequence_verified=True,selected_rgb_sha256=hashlib.sha256(selected).hexdigest(),visual_playback_verified=False)
    return payload,result

def operation(root,plan,render):
    s,dst,pp=validate(root,plan);raws=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:-2])]
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-timeline-',dir=dst.parent) as tmp:
        return observe(raws,s,plan['guards'][-2:],tmp,render=render)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    plan['guards'].extend(snapshot_file(p) for p in paths(Path(plan['root']),s,plan['exclude']))
    plan['guards'].extend(installed(root))
    _,result=operation(root,plan,False)
    return plan,dict(s,observations=result,scope='Ordered visual track compositing; no audio or interactive timeline.')

def execute(root,plan):
    _,dst,_=validate(root,plan);payload,r=operation(root,plan,True)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-video-timeline-result-v1','status':'timeline_pixels_verified','output':plan['output'],
        'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed visual timeline or source'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
