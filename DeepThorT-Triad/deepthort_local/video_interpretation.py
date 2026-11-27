"""Reviewed sparse visual interpretation of bounded local MP4 clips.

Reuse the existing offline Florence caption model; never claim continuous
video comprehension, audio interpretation or verified semantic accuracy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import probe,decode
from deepthort_local.disk_gate import require_storage
from deepthort_local.triad_profiles import ROOT

SCHEMA='janus-video-interpretation-v1'
EXTRA=('video','.mp4')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'video','frames'} or not isinstance(s['video'],str):
        raise ValueError('Expected video and explicit sampled frame indices')
    f=s['frames']
    if not isinstance(f,list) or not 1<=len(f)<=4 or any(type(i) is not int or not 0<=i<300 for i in f) or f!=sorted(set(f)):
        raise ValueError('Choose 1–4 strictly increasing frame indices below 300')
    return s

def runtime(root):
    node=shutil.which('node')
    if not node:raise ValueError('Existing local vision Node runtime required')
    node=Path(node).resolve(strict=True)
    script=(ROOT/'vision_caption.mjs').resolve(strict=True)
    if node.is_relative_to(Path(root).resolve()) or script.is_relative_to(Path(root).resolve()):
        raise ValueError('Project-local runtime refused')
    return [*installed(root),snapshot_file(node,kind='stat'),snapshot_file(script)]

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=6:
        raise ValueError('Missing exact video and runtime guards')
    s,dst,src=guard.validate(root,dict(plan,guards=plan['guards'][:2]),schema=SCHEMA,
        checked=checked,output_suffix='.json',extra=EXTRA)
    if plan['guards'][2:]!=runtime(root):raise ValueError('Reviewed runtime changed')
    return s,dst,src

def captions(paths,tools):
    verify_guards(tools)
    node,script=(g['path'] for g in tools[-2:])
    opts={'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}
    r=subprocess.run([node,script,*map(str,paths)],cwd=str(ROOT),stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=900,check=False,**opts)
    if r.returncode or len(r.stdout)>65536 or len(r.stderr)>1024*1024:
        raise ValueError('Offline vision engine failed; inspect model installation and resource headroom')
    result=[]
    for line in r.stdout.decode('utf-8',errors='strict').splitlines():
        if line.startswith('IMAGE_CAPTION_JSON: '):
            x=json.loads(line.split(': ',1)[1])
            if len(result)>=len(paths) or x.get('image')!=str(paths[len(result)]):
                raise ValueError('Unexpected caption frame identity')
            result.append(x.get('caption'))
    verify_guards(tools)
    return result

def inspect(raw,s,tools,folder,*,interpret=False,captioner=captions):
    checked(s);verify_guards(tools)
    folder=Path(folder);path=folder/'source.mp4';path.write_bytes(raw)
    ff,fp=(g['path'] for g in tools[:2]);meta=probe(fp,path)
    if s['frames'][-1]>=meta['frames']:raise ValueError('Sample frame outside source')
    receipt={'source_sha256':hashlib.sha256(raw).hexdigest(),'source_format':meta,
        'requested_frames':s['frames'],'scope':'Sparse sampled visual observations only',
        'audio_interpreted':False,'continuous_motion_interpreted':False,'semantic_accuracy_verified':False}
    if not interpret:return receipt
    from deepthort_local.texture_pixels import image_module
    Image=image_module();paths=[];observations=[]
    for i in s['frames']:
        rgb=decode(ff,path,i,i+1,meta['width'],meta['height'])
        sample=folder/f'frame-{i}.png'
        with Image.frombytes('RGB',(meta['width'],meta['height']),rgb) as im:
            im.save(sample,format='PNG')
        paths.append(sample)
        observations.append({'frame':i,'seconds':i/meta['fps'],
            'rgb_sha256':hashlib.sha256(rgb).hexdigest(),
            'png_sha256':hashlib.sha256(sample.read_bytes()).hexdigest()})
    values=captioner(paths,tools)
    if not isinstance(values,list) or len(values)!=len(paths) or any(
        not isinstance(c,str) or not c.strip() or len(c)>2000 or any(ord(x)<32 and x not in '\\n\\t' for x in c)
        for c in values):raise ValueError('Missing or invalid sampled-frame descriptions')
    for row,p,c in zip(observations,paths,values):
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['png_sha256']:raise ValueError('Sample changed during interpretation')
        row['caption']=c
    verify_guards(tools)
    receipt.update(observations=observations,caption_model='Florence-2-base-ft (local)',
        native_caption_engine_invoked=captioner is captions,decoded_frame_identity_verified=True)
    return receipt

def operation(root,plan,interpret=False,captioner=captions):
    s,dst,src=validate(root,plan)
    raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.janus-video-read-',dir=dst.parent) as tmp:
        return inspect(raw,s,plan['guards'][2:],tmp,interpret=interpret,captioner=captioner)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    plan['guards'].extend(runtime(root))
    return plan,dict(s,observations=operation(root,plan),scope='Sampled silent H.264 video; offline captions after approval, no audio or continuous interpretation.')

def execute(root,plan,*,captioner=captions):
    _,dst,_=validate(root,plan)
    result=operation(root,plan,True,captioner)
    payload=(json.dumps(result,ensure_ascii=False,indent=2)+'\\n').encode('utf-8')
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-video-interpretation-result-v1','status':'sampled_visual_observations',
        'output':plan['output'],'sha256':sha,'source_unchanged':True,
        'samples':len(result['observations']),'semantic_accuracy_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform=='win32':
            from deepthort_local.triad_job import verify_root_cap
            verify_root_cap()
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Video interpretation unavailable; inspect reviewed clip, local vision installation and shared cap'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
