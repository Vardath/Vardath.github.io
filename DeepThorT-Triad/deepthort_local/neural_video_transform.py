"""Reviewed bounded local AnimateDiff video-to-video generation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import neural_video as neural
from deepthort_local import video_trimming as video
from deepthort_local.action_guards import verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-neural-video-transform-v1'
EXTRA=('video','.mp4')
BASE={'prompt','negative_prompt','seed','size','frames','steps'}

def checked(s):
    if not isinstance(s,dict) or set(s)!=BASE|{'video','start_frame','strength_percent'}:
        raise ValueError('Expected exact clip, interval, prompt and generation settings')
    neural.checked({k:s[k] for k in BASE})
    if not isinstance(s['video'],str) or not s['video']:raise ValueError('Choose project MP4')
    if type(s['start_frame']) is not int or not 0<=s['start_frame']<=300-s['frames']:
        raise ValueError('Invalid source frame interval')
    if type(s['strength_percent']) is not int or not 30<=s['strength_percent']<=80:
        raise ValueError('Choose 30–80 percent neural transformation strength')
    return s

def validate(root,plan):
    if not isinstance(plan,dict) or 'models' not in plan or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=4:
        raise ValueError('Invalid transformation approval')
    core={k:v for k,v in plan.items() if k!='models'};core['guards']=plan['guards'][:2]
    s,dst,src=guard.validate(root,core,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    if plan['models']!=neural.models() or tuple(plan['guards'][2:])!=installed(root):
        raise ValueError('Reviewed model inventory or codec changed')
    return s,dst,src

def source_frames(raw,s,tools,folder,decode=True):
    path=Path(folder)/'source.mp4';path.write_bytes(raw)
    verify_guards(list(tools));ff,fp=(g['path'] for g in tools)
    info=video.probe(fp,path)
    start=s['start_frame'];end=start+s['frames']
    if (info['width'],info['height'])!=(256,256) or end>info['frames']:
        raise ValueError('Initial profile requires 256x256 silent H.264 and the entire selected interval')
    data=video.decode(ff,path,start,end,256,256) if decode else None
    verify_guards(list(tools))
    return data,info

def generate(s,raw):
    from PIL import Image
    torch,pipe=neural.load_pipeline(transform=True)
    stride=s['size']**2*3
    frames=[Image.frombytes('RGB',(256,256),raw[i:i+stride]) for i in range(0,len(raw),stride)]
    try:
        result=pipe(video=frames,prompt=s['prompt'],negative_prompt=s['negative_prompt'],
            height=256,width=256,strength=s['strength_percent']/100,num_inference_steps=s['steps'],
            generator=torch.Generator(device='cpu').manual_seed(s['seed']),output_type='pil')
        return neural.result_rgb(result,s)
    finally:
        for image in frames:image.close()

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4',extra=EXTRA)
    plan['models']=neural.models();plan['guards'].extend(installed(root))
    _,dst,src=validate(root,plan);require_storage(dst.parent)
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-video-review-',dir=dst.parent) as tmp:
        _,info=source_frames(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s,plan['guards'][2:],tmp,False)
    return plan,dict(s,source_format=info,local_model_inventory=plan['models'],
        scope='Prompt-guided temporal diffusion of an exact short silent clip interval, using trusted local AnimateDiff and SD1.5. Preserve frame count and rate, not exact geometry or identity. No downloads or publication.')

def execute(root,plan,*,backend=None):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    source=guard.exact(src,plan['guards'][1],guard.MAX_INPUT);tools=plan['guards'][2:]
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-video-transform-',dir=dst.parent) as tmp:
        folder=Path(tmp)
        raw,info=source_frames(source,s,tools,folder)
        stride=256*256*3
        if not isinstance(raw,bytes) or len(raw)!=stride*s['frames']:
            raise ValueError('Source frame layout differs')
        out=(backend or generate)(s,raw)
        if not isinstance(out,bytes) or len(out)!=len(raw) or out==raw:
            raise ValueError('Generated output missing, unchanged or wrong dimensions')
        if len({hashlib.sha256(out[i:i+stride]).digest() for i in range(0,len(out),stride)})<2:
            raise ValueError('Generated sequence has no frame variation')
        payload=video.encode_verified(out,(256,256),info['fps'],s['frames'],tools,folder)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'transformed_video_frames_verified','output':plan['output'],'sha256':sha,
        'source_sha256':hashlib.sha256(source).hexdigest(),'source_rgb_sha256':hashlib.sha256(raw).hexdigest(),
        'output_rgb_sha256':hashlib.sha256(out).hexdigest(),'fps':info['fps'],'frames':s['frames'],
        'width':256,'height':256,'seed':s['seed'],'strength_percent':s['strength_percent'],
        'model_inventory':plan['models'],'source_unchanged':True,'audio_supported':False,
        'identity_preservation_verified':False,'motion_quality_verified':False,
        'backend':'local_animatediff_video_to_video' if backend is None else 'injected_fixture'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
