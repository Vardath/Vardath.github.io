"""Reviewed single-image local Shap-E mesh inference, not metric reconstruction."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import neural_text_mesh as mesh
from deepthort_local.disk_gate import require_storage

SCHEMA='deepthortriad-neural-image-mesh-v1'
EXTRA=('image','.png')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','seed','steps','guidance'} or not isinstance(s['image'],str) or not s['image']:
        raise ValueError('Expected project PNG, seed, steps and guidance')
    mesh.checked(dict(prompt='image',seed=s['seed'],steps=s['steps'],guidance=s['guidance']))
    return s

def decode(raw):
    from PIL import Image
    with Image.open(io.BytesIO(raw)) as im:
        if im.format!='PNG' or im.mode!='RGB' or getattr(im,'n_frames',1)!=1 or not all(64<=x<=1024 for x in im.size):
            raise ValueError('Expected a single 64–1024 px RGB PNG')
        im.load()
        return im.copy()

def validate(root,plan):
    if not isinstance(plan,dict) or 'model' not in plan:raise ValueError('Invalid image mesh approval')
    s,dst,src=guard.validate(root,{k:v for k,v in plan.items() if k!='model'},schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    if plan['model']!=mesh.inventory('image'):raise ValueError('Reviewed image mesh model changed')
    return s,dst,src

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    plan['model']=mesh.inventory('image')
    _,_,src=validate(root,plan)
    with decode(guard.exact(src,plan['guards'][1],guard.MAX_INPUT)) as im:size=list(im.size)
    return plan,dict(s,source_dimensions=size,local_model_inventory=plan['model'],
        scope='Offline CPU single-image shape estimation with optional Shap-E image model. Hidden geometry inferred, not measured; no material or metric accuracy assurance.')

def generate(s,image):
    from deepthort_local.triad_job import verify_root_cap
    cap,available,total=verify_root_cap()
    if available<total//10+6*mesh.GIB or cap<8*mesh.GIB:
        raise ValueError('Insufficient protected host memory for optional mesh generation')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import ShapEImg2ImgPipeline
    torch.set_num_threads(1)
    pipe=ShapEImg2ImgPipeline.from_pretrained(str(mesh.ROOT/'models'/'shap-e-image'),
        local_files_only=True,use_safetensors=True,torch_dtype=torch.float32).to('cpu')
    with torch.inference_mode():
        output=pipe(image=image,num_inference_steps=s['steps'],guidance_scale=s['guidance'],
            generator=torch.Generator(device='cpu').manual_seed(s['seed']),output_type='mesh')
    if len(output.images)!=1:raise ValueError('Expected one generated mesh')
    v,f=output.images[0].verts,output.images[0].faces
    if v.ndim!=2 or f.ndim!=2 or v.shape[1]!=3 or f.shape[1]!=3 or not 3<=v.shape[0]<=mesh.MAX_VERTICES or not 1<=f.shape[0]<=mesh.MAX_FACES:
        raise ValueError('Generated mesh exceeds existing static geometry contract')
    return v.detach().cpu().tolist(),f.detach().cpu().tolist()

def execute(root,plan,*,backend=None):
    s,dst,src=validate(root,plan);require_storage(dst.parent)
    raw=guard.exact(src,plan['guards'][1],guard.MAX_INPUT)
    with decode(raw) as image:
        size=list(image.size)
        vertices,faces=(backend or generate)(s,image)
    payload,nv,nf=mesh.geometry(vertices,faces)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'image_conditioned_mesh_geometry_verified','output':plan['output'],
        'sha256':sha,'vertices':nv,'triangles':nf,'seed':s['seed'],'model_inventory':plan['model'],
        'source_sha256':hashlib.sha256(raw).hexdigest(),'source_dimensions':size,'source_unchanged':True,
        'geometry_roundtrip_verified':True,'metric_accuracy_verified':False,'semantic_quality_verified':False,
        'hidden_surface_measured':False,'material_preserved':False,
        'backend':'local_shap_e_image' if backend is None else 'injected_fixture'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
