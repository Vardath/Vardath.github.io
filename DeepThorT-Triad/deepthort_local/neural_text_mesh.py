"""Optional reviewed offline Shap-E text-to-mesh generation.

The native mesh must pass the existing strict static OBJ contract. No model
installation, custom pipeline code, network inference or visual quality claim.
"""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mesh_geometry import encode, MAX_VERTICES, MAX_FACES
from deepthort_local.source_security import linked
from deepthort_local.action_guards import snapshot_file
from deepthort_local.agent_contract import canonical_sha
from deepthort_local.disk_gate import require_storage

ROOT=Path(__file__).resolve().parents[1]
SCHEMA='deepthortriad-neural-text-mesh-v1'
GIB=1024**3

def checked(s):
    if not isinstance(s,dict) or set(s)!={'prompt','seed','steps','guidance'}:
        raise ValueError('Expected prompt, seed, steps and guidance')
    p=s['prompt']
    if not isinstance(p,str) or not 1<=len(p)<=300 or not p.strip() or any(ord(c)<32 for c in p):
        raise ValueError('Expected bounded nonempty text prompt')
    if type(s['seed']) is not int or not 0<=s['seed']<2**32:
        raise ValueError('Invalid seed')
    if type(s['steps']) is not int or not 16<=s['steps']<=32:
        raise ValueError('Choose 16–32 inference steps')
    g=s['guidance']
    if type(g) not in (float,int) or not math.isfinite(g) or not 1<=g<=15:
        raise ValueError('Choose guidance 1–15')
    return s

def inventory(profile='text'):
    if profile not in ('text','image'):raise ValueError('Unknown mesh model profile')
    expected_class,encoder=('ShapEPipeline','text_encoder') if profile=='text' else ('ShapEImg2ImgPipeline','image_encoder')
    base=ROOT/'models';folder=base/('shap-e-'+profile)
    if linked(base) or linked(folder) or not folder.is_dir():
        raise ValueError('Separately provision trusted local Shap-E safetensors model')
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
            if suffix not in ('.json','.txt','.safetensors','.md','.model'):
                raise ValueError('Only trusted safetensors and inert configuration supported')
            size=path.stat().st_size;total+=size
            if total>12*GIB:raise ValueError('Local model inventory exceeds bound')
            kind='stat' if suffix=='.safetensors' else 'sha256'
            if kind=='sha256' and size>8*1024**2:raise ValueError('Model configuration exceeds bound')
            files[path.relative_to(folder).as_posix()]=snapshot_file(path,kind=kind)
    if 'model_index.json' not in files:
        raise ValueError('Missing Shap-E model index')
    index=json.loads(guard.read_bound(folder/'model_index.json',8*1024**2).decode('utf8'))
    if not isinstance(index,dict) or index.get('_class_name')!=expected_class:
        raise ValueError('Expected reviewed native Shap-E pipeline configuration')
    for component in ('prior',encoder,'shap_e_renderer'):
        if not any(k.startswith(component+'/') and k.endswith('.safetensors') for k in files):
            raise ValueError('Missing component safetensors: '+component)
    return {'path':str(folder),'inventory_sha':canonical_sha(files),'bytes':total}

def validate(root,plan):
    if not isinstance(plan,dict) or 'model' not in plan:
        raise ValueError('Invalid generation approval')
    s,dst,_=guard.validate(root,{k:v for k,v in plan.items() if k!='model'},
        schema=SCHEMA,checked=checked,output_suffix='.obj')
    if plan['model']!=inventory():raise ValueError('Reviewed model inventory changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj')
    plan['model']=inventory();validate(root,plan)
    return plan,dict(s,local_model_inventory=plan['model'],
        scope='Optional CPU Shap-E text-to-mesh, one static triangle OBJ, geometry only. No downloads or remote inference. Model weight metadata and configuration hashes reviewed. Native model capacity and visual quality unverified.')

def generate(s):
    from deepthort_local.triad_job import verify_root_cap
    cap,available,total=verify_root_cap()
    if available<total//10+6*GIB or cap<8*GIB:
        raise ValueError('Insufficient protected host memory for optional mesh generation')
    for key in ('HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','DIFFUSERS_OFFLINE','OMP_NUM_THREADS','MKL_NUM_THREADS'):
        os.environ[key]='1'
    import torch
    from diffusers import ShapEPipeline
    torch.set_num_threads(1)
    pipe=ShapEPipeline.from_pretrained(str(ROOT/'models'/'shap-e-text'),
        local_files_only=True,use_safetensors=True,torch_dtype=torch.float32).to('cpu')
    with torch.inference_mode():
        output=pipe(prompt=s['prompt'],num_inference_steps=s['steps'],guidance_scale=s['guidance'],
            generator=torch.Generator(device='cpu').manual_seed(s['seed']),output_type='mesh')
    if len(output.images)!=1:raise ValueError('Expected one generated mesh')
    mesh=output.images[0]
    v,f=mesh.verts,mesh.faces
    if v.ndim!=2 or f.ndim!=2 or v.shape[1]!=3 or f.shape[1]!=3 or not 3<=v.shape[0]<=MAX_VERTICES or not 1<=f.shape[0]<=MAX_FACES:
        raise ValueError('Generated mesh exceeds existing static geometry contract')
    return v.detach().cpu().tolist(),f.detach().cpu().tolist()

def geometry(vertices,faces):
    if not isinstance(vertices,(tuple,list)) or not isinstance(faces,(tuple,list)) or not 3<=len(vertices)<=MAX_VERTICES or not 1<=len(faces)<=MAX_FACES:
        raise ValueError('Invalid generated geometry size')
    v=[];f=[];seen=set()
    for row in vertices:
        if not isinstance(row,(tuple,list)) or len(row)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e6 for x in row):
            raise ValueError('Invalid generated coordinate')
        v.append(tuple(float(x) for x in row))
    for row in faces:
        if not isinstance(row,(tuple,list)) or len(row)!=3 or any(type(x) is not int or not 0<=x<len(v) for x in row):
            raise ValueError('Invalid generated triangle index')
        key=tuple(sorted(row))
        if len(set(row))!=3 or key in seen:raise ValueError('Repeated triangle vertex or face')
        seen.add(key);f.append(tuple(row))
    return encode(v,f),len(v),len(f)

def execute(root,plan,*,backend=None):
    s,dst=validate(root,plan);require_storage(dst.parent)
    vertices,faces=(backend or generate)(s)
    payload,nv,nf=geometry(vertices,faces)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'generated_mesh_geometry_verified','output':plan['output'],
        'sha256':sha,'vertices':nv,'triangles':nf,'seed':s['seed'],'model_inventory':plan['model'],
        'geometry_roundtrip_verified':True,'material_preserved':False,'semantic_quality_verified':False,
        'manifold_verified':False,'backend':'local_shap_e' if backend is None else 'injected_fixture'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':str(e)[:300]}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
