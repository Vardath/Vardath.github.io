"""Reviewed local AnimateDiff generation using optional, trusted SD1.5 components.

No installation, remote inference or custom pipeline code. Frame verification is
not semantic or motion-quality acceptance. Native Windows model runs are required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.source_security import linked
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.audio_conversion import installed
from deepthort_local.video_trimming import encode_verified
from deepthort_local.disk_gate import require_storage
from deepthort_local.agent_contract import canonical_sha

SCHEMA='deepthortriad-neural-video-v1'
ROOT=Path(__file__).resolve().parents[1]
GIB=1024**3

def checked(s):
    if not isinstance(s,dict) or set(s)!={'prompt','negative_prompt','seed','size','frames','steps'}:
        raise ValueError('Expected prompt, negative prompt, seed, size, frames and steps')
    for k in ('prompt','negative_prompt'):
        v=s[k]
        if not isinstance(v,str) or len(v)>1000 or any(ord(c)<32 and c not in '\n\t' for c in v):
            raise ValueError('Invalid bounded video prompt')
    if not s['prompt'].strip():raise ValueError('Nonempty prompt required')
    for k,lo,hi in (('seed',0,2**32-1),('steps',10,20),('frames',8,16)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid '+k)
    if type(s['size']) is not int or s['size']!=256:raise ValueError('Initial CPU profile is 256x256 only')
    return s

def models():
    base=ROOT/'models'
    paths=(base/'stable-diffusion-v1-5',base/'animatediff-motion-adapter')
    if linked(base) or not base.is_dir():raise ValueError('Trusted local model directory required')
    receipts=[]
    for folder,required in zip(paths,('model_index.json','config.json')):
        if linked(folder) or not folder.is_dir():raise ValueError('Install the optional trusted local video components separately')
        if not (folder/required).is_file():raise ValueError('Missing local model configuration')
        files={};total=0;entries=0
        for directory,dirs,names in os.walk(folder,followlinks=False):
            here=Path(directory)
            entries+=len(dirs)+len(names)
            if entries>256:raise ValueError('Model inventory exceeds bound')
            for name in tuple(dirs):
                path=here/name
                if linked(path):raise ValueError('Linked model directory')
                if name=='.cache':dirs.remove(name)
                elif name.startswith('.'):raise ValueError('Unexpected model directory')
            for name in names:
                path=here/name
                if linked(path) or not path.is_file():raise ValueError('Unsafe model member')
                suffix=path.suffix.lower()
                if suffix not in ('.json','.txt','.safetensors','.model','.md'):
                    raise ValueError('Unsupported local model member; safetensors weights required')
                size=path.stat().st_size;total+=size
                if total>12*GIB:raise ValueError('Local model inventory exceeds bound')
                kind='stat' if suffix=='.safetensors' else 'sha256'
                if kind=='sha256' and size>8*1024**2:raise ValueError('Model configuration exceeds bound')
                files[path.relative_to(folder).as_posix()]=snapshot_file(path,kind=kind)
        if required not in files or not any(k.endswith('.safetensors') for k in files):
            raise ValueError('Missing trusted local safetensors weights')
        receipts.append({'path':str(folder),'inventory_sha':canonical_sha(files),'bytes':total})
    return receipts

def validate(root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','root','source','output','exclude','guards','expires_at','models'} or len(plan.get('guards',[]))!=3:
        raise ValueError('Invalid video generation approval')
    core={k:v for k,v in plan.items() if k!='models'};core['guards']=plan['guards'][:1]
    s,dst,_=guard.validate(root,core,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    if plan['models']!=models() or tuple(plan['guards'][1:])!=installed(root):
        raise ValueError('Reviewed video model or codec inventory changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.mp4')
    plan['models']=models();plan['guards'].extend(installed(root));validate(root,plan)
    return plan,dict(s,local_model_inventory=plan['models'],
        scope='Trusted local SD1.5 and separately provisioned AnimateDiff motion adapter. CPU-only short silent clip at 24 fps. No downloads, remote services, custom pipeline code or model replacement. Native performance and visual quality unverified.')

def load_pipeline(*,transform=False):
    from deepthort_local.triad_job import verify_root_cap
    cap,available,total=verify_root_cap()
    if available<total//10+4*GIB or cap<5*GIB:
        raise ValueError('Insufficient protected host memory for optional video generation')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import AnimateDiffPipeline,MotionAdapter
    if transform:
        from diffusers import AnimateDiffVideoToVideoPipeline
        pipeline_class=AnimateDiffVideoToVideoPipeline
    else:pipeline_class=AnimateDiffPipeline
    torch.set_num_threads(1)
    adapter=MotionAdapter.from_pretrained(str(ROOT/'models'/'animatediff-motion-adapter'),
        local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
    pipe=pipeline_class.from_pretrained(str(ROOT/'models'/'stable-diffusion-v1-5'),
        motion_adapter=adapter,local_files_only=True,use_safetensors=True,torch_dtype=torch.float32)
    pipe=pipe.to('cpu');pipe.enable_attention_slicing('max')
    pipe.enable_vae_slicing()
    return torch,pipe

def generate(s):
    torch,pipe=load_pipeline()
    result=pipe(prompt=s['prompt'],negative_prompt=s['negative_prompt'],height=s['size'],width=s['size'],
        num_frames=s['frames'],num_inference_steps=s['steps'],
        generator=torch.Generator(device='cpu').manual_seed(s['seed']),output_type='pil')
    return result_rgb(result,s)

def result_rgb(result,s):
    if len(result.frames)!=1:raise ValueError('Expected one generated clip')
    frames=result.frames[0]
    if len(frames)!=s['frames']:raise ValueError('Generated frame count mismatch')
    chunks=[]
    for image in frames:
        if image.mode!='RGB' or image.size!=(s['size'],s['size']):
            raise ValueError('Generated frame layout mismatch')
        chunks.append(image.tobytes())
    return b''.join(chunks)

def execute(root,plan,*,backend=None):
    s,dst=validate(root,plan);tools=plan['guards'][1:]
    require_storage(dst.parent);verify_guards(tools)
    raw=(backend or generate)(s)
    stride=s['size']**2*3
    if not isinstance(raw,bytes) or len(raw)!=stride*s['frames']:
        raise ValueError('Generated RGB frame buffer mismatch')
    if len({hashlib.sha256(raw[i:i+stride]).digest() for i in range(0,len(raw),stride)})<2:
        raise ValueError('Generated sequence has no frame variation')
    with tempfile.TemporaryDirectory(prefix='.deepthortriad-neural-video-',dir=dst.parent) as tmp:
        payload=encode_verified(raw,(s['size'],s['size']),24,s['frames'],tools,Path(tmp))
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'generated_video_frames_verified','output':plan['output'],
            'sha256':sha,'rgb_sequence_sha256':hashlib.sha256(raw).hexdigest(),
            'frames':s['frames'],'width':s['size'],'height':s['size'],'fps':24,
            'seed':s['seed'],'model_inventory':plan['models'],'frame_variation_verified':True,
            'semantic_quality_verified':False,'motion_quality_verified':False,'audio_supported':False,
            'backend':'local_animatediff' if backend is None else 'injected_fixture'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,
            'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
