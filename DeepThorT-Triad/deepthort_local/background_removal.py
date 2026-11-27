"""Reviewed color-key or user-mask PNG background removal; no inferred segmentation."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import decode,image_module

SCHEMA='janus-background-removal-v1'
def rgb(value):
    if not isinstance(value,list) or len(value)!=3 or any(type(x) is not int or not 0<=x<=255 for x in value):
        raise ValueError('Expected explicit RGB byte triplet')
    return value
def checked(s):
    if not isinstance(s,dict) or not isinstance(s.get('image'),str) or not isinstance(s.get('mode'),str):
        raise ValueError('Expected image and removal mode')
    if s['mode']=='color_key':
        if set(s)!={'image','mode','key','tolerance','feather'}:raise ValueError('Expected color-key specification')
        rgb(s['key']);t,f=s['tolerance'],s['feather']
        if type(t) is not int or type(f) is not int or not 0<=t<=254 or not 0<=f<=255-t:
            raise ValueError('Invalid color-key tolerance or feather')
    elif s['mode']=='mask':
        if set(s)!={'image','mode','mask'} or not isinstance(s['mask'],str) or s['mask'].casefold()==s['image'].casefold():
            raise ValueError('Expected distinct grayscale PNG mask')
    else:raise ValueError('Use color_key or mask')
    return s

def encode_rgba(w,h,data):
    stream=io.BytesIO()
    with image_module().frombytes('RGBA',(w,h),data) as im:im.save(stream,format='PNG',compress_level=6)
    payload=stream.getvalue()
    with decode_layer(payload) as im:
        if im.size!=(w,h) or im.tobytes()!=data:raise ValueError('Decoded RGBA mismatch')
    return payload

def generate(raw,s,mask=None):
    checked(s)
    with decode_layer(raw) as im:
        w,h=im.size;original=im.tobytes()
    if s['mode']=='mask':
        if mask is None:raise ValueError('Missing reviewed mask')
        mw,mh,_,values=decode(mask,('L',))
        if (mw,mh)!=(w,h):raise ValueError('Mask dimensions must exactly match source')
    elif mask is not None:raise ValueError('Unexpected mask')
    else:values=None
    out=bytearray(original);removed=partial=changed=0
    for i in range(w*h):
        j=i*4
        if values is not None:keep=values[i]
        else:
            d=max(abs(original[j+k]-s['key'][k]) for k in range(3))
            t,f=s['tolerance'],s['feather']
            keep=0 if d<=t else 255 if not f or d>=t+f else ((d-t)*255+f//2)//f
        alpha=(original[j+3]*keep+127)//255
        out[j+3]=alpha
        removed+=alpha==0;partial+=0<alpha<255;changed+=alpha!=original[j+3]
    payload=encode_rgba(w,h,bytes(out))
    return payload,{'width':w,'height':h,'transparent_pixels':removed,'partial_alpha_pixels':partial,'changed_alpha_pixels':changed,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'mask_sha256':hashlib.sha256(mask).hexdigest() if mask is not None else None,
        'pixel_sha256':hashlib.sha256(out).hexdigest(),'rgb_preserved':True,'pixel_roundtrip_verified':True,
        'semantic_segmentation':False,'visual_quality_verified':False}

def _paths(root,s,exclude):
    names=[s['image']]+([s['mask']] if s['mode']=='mask' else [])
    paths=[guard.path_for(root,n,exclude,{'.png'},exists=True) for n in names]
    if len({str(p).casefold() for p in paths})!=len(paths) or any(p.stat().st_size>guard.MAX_INPUT for p in paths):
        raise ValueError('Duplicate or oversized source')
    return paths
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards']) not in (2,3):
        raise ValueError('Invalid removal approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    paths=_paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed removal source changed')
    return s,dst,paths
def _render(root,plan):
    s,dst,paths=validate(root,plan)
    raws=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:])]
    payload,r=generate(raws[0],s,raws[1] if len(raws)==2 else None)
    return payload,r,dst
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    plan['guards'].extend(snapshot_file(p) for p in _paths(Path(plan['root']),s,plan['exclude']))
    _,r,_=_render(root,plan)
    return plan,dict(s,verification=r,scope='Explicit color key or supplied grayscale mask; no subject recognition. Existing alpha is multiplied, not replaced.')
def execute(root,plan):
    payload,r,dst=_render(root,plan)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-background-removal-result-v1','status':'background_alpha_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Background removal unavailable; inspect image, mask and reviewed settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
