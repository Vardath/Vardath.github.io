"""Explicit offline image-to-image generation using the existing local SD1.5 model.

The approved input is hash-bound, the output is a new project file, and no
model installation or network access is performed by this producer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.texture_pixels import decode,encode,image_module
from deepthort_local.source_security import exclusions

SCHEMA='janus-image-to-image-v1'
FIELDS={'schema','image','source_sha256','output','prompt','size','steps','strength_percent','seed'}
REF_FIELDS={'reference','reference_sha256','palette_strength_percent'}

def checked(s):
    if not isinstance(s,dict) or set(s) not in (FIELDS,FIELDS|REF_FIELDS) or s['schema']!=SCHEMA:
        raise ValueError('Invalid image-to-image request')
    if any(not isinstance(s[k],str) or not s[k] for k in ('image','output','prompt','source_sha256')):
        raise ValueError('Missing image, output, description or digest')
    if not re.fullmatch(r'[0-9a-f]{64}',s['source_sha256']) or s['image'].casefold()==s['output'].casefold():
        raise ValueError('Invalid source digest or output')
    if not s['prompt'].strip() or len(s['prompt'])>2000 or any(ord(c)<32 and c not in '\n\t' for c in s['prompt']):
        raise ValueError('Use a bounded image prompt')
    for k,lo,hi in (('steps',10,20),('strength_percent',30,90),('seed',0,4294967295)):
        if type(s[k]) is not int or not lo<=s[k]<=hi:raise ValueError('Invalid generation parameter: '+k)
    if type(s['size']) is not int or s['size'] not in (256,384,512):
        raise ValueError('Invalid generation size')
    if 'reference' in s:
        if not isinstance(s['reference'],str) or not s['reference'] or s['reference'].casefold() in (s['image'].casefold(),s['output'].casefold()):
            raise ValueError('Use a distinct palette reference')
        if not isinstance(s['reference_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['reference_sha256']):
            raise ValueError('Invalid reference digest')
        if type(s['palette_strength_percent']) is not int or not 1<=s['palette_strength_percent']<=100:
            raise ValueError('Invalid palette strength')
    return s

def reference_input(root,s,source,bound):
    if 'reference' not in s:return None,None
    path=guard.path_for(Path(root).resolve(strict=True),s['reference'],exclusions(()),{'.png'},exists=True)
    if path.samefile(source) or path.stat().st_size+source.stat().st_size>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized reference inputs')
    ref=snapshot_file(path)
    if ref['expected']!=s['reference_sha256']:raise ValueError('Reviewed reference changed')
    return path,ref

def validate(root,s):
    checked(s);root=Path(root).resolve(strict=True);exclude=exclusions(())
    source=guard.path_for(root,s['image'],exclude,{'.png'},exists=True)
    dst=guard.path_for(root,s['output'],exclude,{'.png'},exists=False)
    if source.stat().st_size>guard.MAX_INPUT:raise ValueError('Image exceeds input bound')
    bound=snapshot_file(source)
    if bound['expected']!=s['source_sha256']:raise ValueError('Reviewed image changed')
    reference_input(root,s,source,bound)
    return source,dst,bound

def review(root,image,output,prompt,size=384,steps=15,strength_percent=60,seed=0):
    root=Path(root).resolve(strict=True)
    src=guard.path_for(root,image,exclusions(()),{'.png'},exists=True)
    if src.stat().st_size>guard.MAX_INPUT:raise ValueError('Image exceeds input bound')
    s={'schema':SCHEMA,'image':image,'output':output,'prompt':prompt,'size':size,'steps':steps,
       'strength_percent':strength_percent,'seed':seed,'source_sha256':snapshot_file(src)['expected']}
    src,_,bound=validate(root,s)
    decode(guard.exact(src,bound,guard.MAX_INPUT),('RGB',))
    return s

def review_reference(root,image,reference,output,prompt,size=384,steps=15,strength_percent=60,seed=0,palette_strength_percent=80):
    s=review(root,image,output,prompt,size,steps,strength_percent,seed)
    path=guard.path_for(Path(root).resolve(strict=True),reference,exclusions(()),{'.png'},exists=True)
    if path.stat().st_size>guard.MAX_INPUT:raise ValueError('Reference exceeds input bound')
    s.update(reference=reference,reference_sha256=snapshot_file(path)['expected'],palette_strength_percent=palette_strength_percent)
    source,_,bound=validate(root,s)
    path,ref=reference_input(root,s,source,bound)
    # Check the same decoding and palette transform used during generation.
    guide(guard.exact(source,bound,guard.MAX_INPUT),guard.exact(path,ref,guard.MAX_INPUT),s)
    return s

def guide(raw,reference,s):
    from deepthort_local.image_style_transfer import generate
    return generate(raw,reference,{'image':s['image'],'reference':s['reference'],
                    'strength_percent':s['palette_strength_percent']})[0]

def diffuse(model,raw,s):
    model=Path(model).resolve(strict=True)
    if not (model/'model_index.json').is_file():raise RuntimeError('Existing optional diffusion model is not installed')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import StableDiffusionImg2ImgPipeline
    torch.set_num_threads(1)
    w,h,mode,pixels=decode(raw,('RGB',));Image=image_module();size=s['size']
    with Image.frombytes(mode,(w,h),pixels) as source:
        with source.resize((size,size),Image.Resampling.LANCZOS) as init:
            pipe=StableDiffusionImg2ImgPipeline.from_pretrained(str(model),local_files_only=True,
                use_safetensors=True,safety_checker=None,requires_safety_checker=False,torch_dtype=torch.float32)
            pipe=pipe.to('cpu');pipe.enable_attention_slicing('max')
            gen=torch.Generator(device='cpu').manual_seed(s['seed'])
            result=pipe(prompt=s['prompt'],image=init,strength=s['strength_percent']/100,
                        num_inference_steps=s['steps'],generator=gen).images
            if len(result)!=1:raise ValueError('Expected exactly one generated image')
            with result[0] as im:
                if im.size!=(size,size) or im.mode!='RGB':raise ValueError('Unexpected generated image layout')
                return encode(size,size,'RGB',im.tobytes())

def execute(root,model,s,*,backend=diffuse):
    src,dst,bound=validate(root,s)
    raw=guard.exact(src,bound,guard.MAX_INPUT)
    w,h,_,_=decode(raw,('RGB',))
    ref_path,ref_bound=reference_input(root,s,src,bound)
    initial=guide(raw,guard.exact(ref_path,ref_bound,guard.MAX_INPUT),s) if ref_path else raw
    out=backend(model,initial,s)
    if not isinstance(out,bytes) or len(out)>guard.MAX_OUTPUT:raise ValueError('Invalid generated PNG')
    ow,oh,_,pixels=decode(out,('RGB',))
    if (ow,oh)!=(s['size'],s['size']):raise ValueError('Generated dimensions differ from approved size')
    def revalidate():
        current,target,current_bound=validate(root,s)
        if (current,target,current_bound)!=(src,dst,bound):raise ValueError('Reviewed paths changed')
        if reference_input(root,s,current,current_bound)!=(ref_path,ref_bound):raise ValueError('Reviewed reference changed')
    sha=guard.publish(out,dst,revalidate)
    return {'schema':'janus-image-to-image-result-v1','status':'generated_image_pixels_verified',
            'output':s['output'],'sha256':sha,'source_sha256':s['source_sha256'],
            'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'source_dimensions':[w,h],
            'dimensions':[ow,oh],'seed':s['seed'],'strength_percent':s['strength_percent'],
            'source_unchanged':True,'visual_quality_verified':False,
            **({'reference_sha256':s['reference_sha256'],'palette_strength_percent':s['palette_strength_percent'],
                'conditioning_sha256':hashlib.sha256(initial).hexdigest(),'reference_method':'classical_palette_initialisation',
                'semantic_reference_conditioning':False} if ref_path else {})}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--model',required=True)
    p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        result=execute(a.root,a.model,json.loads(a.plan))
        print('IMAGE_TO_IMAGE_RESULT: '+json.dumps(result,sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,
            'reason':'Reviewed image-to-image generation failed; verify the local model, resource headroom and input'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
