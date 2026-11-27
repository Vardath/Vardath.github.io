"""Reviewed multi-image enhancement and resize, delivered as one atomic ZIP."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.image_composition import decode_layer
from deepthort_local.image_enhancement import checked as check_enhancement,generate as enhance,FACTORS
from deepthort_local.texture_pixels import image_module

SCHEMA='janus-batch-image-processing-v1'
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.png\Z')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'images','max_edge',*FACTORS}:
        raise ValueError('Expected source/output image pairs, enhancement factors and maximum edge')
    if s['max_edge'] is not None and (type(s['max_edge']) is not int or not 1<=s['max_edge']<=2048):
        raise ValueError('Maximum edge must be null or integer 1..2048')
    if not isinstance(s['images'],list) or not 2<=len(s['images'])<=6:raise ValueError('Choose 2–6 source images')
    paths=set();names=set()
    for e in s['images']:
        if not isinstance(e,dict) or set(e)!={'image','output'} or not isinstance(e['image'],str) or not e['image']:
            raise ValueError('Invalid source/output pair')
        if not isinstance(e['output'],str) or not NAME.fullmatch(e['output']):
            raise ValueError('Choose a simple ASCII PNG output filename')
        if e['image'].casefold() in paths or e['output'].casefold() in names:raise ValueError('Duplicate source or output')
        paths.add(e['image'].casefold());names.add(e['output'].casefold())
        check_enhancement({'image':e['image'],**{k:s[k] for k in FACTORS}})
    return s
def digest(raw):return hashlib.sha256(raw).hexdigest()
def transform(raw,s,e):
    processed,r=enhance(raw,{'image':e['image'],**{k:s[k] for k in FACTORS}})
    with decode_layer(processed) as im:
        w,h=im.size;edge=s['max_edge']
        resized=edge is not None and max(w,h)>edge
        if resized:
            size=(max(1,(w*edge+max(w,h)//2)//max(w,h)),max(1,(h*edge+max(w,h)//2)//max(w,h)))
            with im.resize(size,image_module().Resampling.LANCZOS) as out:
                pixels=out.tobytes()
                stream=io.BytesIO();out.save(stream,format='PNG',compress_level=6);processed=stream.getvalue()
        else:size=im.size;pixels=im.tobytes()
    with decode_layer(processed) as result:
        if result.size!=size or result.tobytes()!=pixels:raise ValueError('Batch image decoded output mismatch')
    return processed,{'source':e['image'],'output':e['output'],'source_sha256':digest(raw),
                      'output_sha256':digest(processed),'pixel_sha256':digest(pixels),'source_dimensions':[w,h],
                      'output_dimensions':list(size),'resized':resized,'alpha_preserved_exactly':not resized}
def generate(raws,s):
    checked(s)
    if len(raws)!=len(s['images']):raise ValueError('Batch input count mismatch')
    outputs={};records=[]
    for raw,e in zip(raws,s['images']):
        payload,r=transform(raw,s,e);outputs[e['output']]=payload;records.append(r)
        if sum(map(len,outputs.values()))>guard.MAX_OUTPUT:raise ValueError('Batch output exceeds byte bound')
    manifest={'schema':'janus-batch-image-manifest-v1','specification':s,'images':records,
              'pixel_roundtrip_verified':True,'visual_quality_verified':False}
    entries={**outputs,'manifest.json':json.dumps(manifest,ensure_ascii=True,sort_keys=True,indent=2).encode('utf-8')}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED) as z:
        for name,payload in entries.items():z.writestr(zipfile.ZipInfo(name,(1980,1,1,0,0,0)),payload)
    result=stream.getvalue()
    if len(result)>guard.MAX_OUTPUT:raise ValueError('Batch archive exceeds byte bound')
    with zipfile.ZipFile(io.BytesIO(result)) as z:
        if z.namelist()!=list(entries) or z.testzip() is not None or any(z.read(n)!=p for n,p in entries.items()):
            raise ValueError('Batch archive verification failed')
    return result,manifest
def _paths(root,s,exclude):
    paths=[guard.path_for(root,e['image'],exclude,{'.png'},exists=True) for e in s['images']]
    if len({str(p).casefold() for p in paths})!=len(paths) or any(p.stat().st_size>guard.MAX_INPUT for p in paths):
        raise ValueError('Duplicate or oversized batch input')
    return paths
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    paths=_paths(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in paths)
    s,_,paths=validate(root,plan)
    _,m=generate([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:])],s)
    return plan,dict(s,manifest=m,scope='Atomic ZIP of processed PNG files; no input modifications, no automatic quality judgment.')
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=7:
        raise ValueError('Invalid batch approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.zip')
    paths=_paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed batch input changed')
    return s,dst,paths
def execute(root,plan):
    s,dst,paths=validate(root,plan)
    payload,m=generate([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:])],s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-batch-image-result-v1','status':'batch_archive_verified','output':plan['output'],
            'sha256':sha,'images':len(m['images']),'manifest':m,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Batch unavailable; inspect PNG inputs, sizes and reviewed specification'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
