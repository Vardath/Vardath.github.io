"""Generate tangent-space normals from an explicitly reviewed grayscale height map."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.texture_pixels import decode,encode
SCHEMA='janus-normal-map-v1'
EXTRA=('height_map','.png')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'height_map','strength','convention','edge'} or not isinstance(spec['height_map'],str):
        raise ValueError('Expected grayscale height PNG, strength, normal convention and boundary mode')
    s=spec['strength']
    if type(s) not in (int,float) or not math.isfinite(s) or not 0<=s<=64 or spec['convention'] not in ('opengl','directx') or spec['edge'] not in ('wrap','clamp'):
        raise ValueError('Invalid normal-map options')
    return spec
def generate(raw,spec):
    w,h,mode,heights=decode(raw,('L',));out=bytearray(w*h*3);strength=spec['strength']
    wrap=spec['edge']=='wrap';ysign=1 if spec['convention']=='opengl' else -1
    for y in range(h):
        up=((y-1)%h if wrap else max(0,y-1))*w
        down=((y+1)%h if wrap else min(h-1,y+1))*w
        row=y*w
        for x in range(w):
            left=(x-1)%w if wrap else max(0,x-1)
            right=(x+1)%w if wrap else min(w-1,x+1)
            nx=(heights[row+left]-heights[row+right])*strength/510
            ny=(heights[down+x]-heights[up+x])*strength/510*ysign
            inv=1/math.sqrt(nx*nx+ny*ny+1)
            i=(row+x)*3
            out[i]=round((nx*inv+1)*127.5);out[i+1]=round((ny*inv+1)*127.5);out[i+2]=round((inv+1)*127.5)
    pixels=bytes(out);payload=encode(w,h,'RGB',pixels)
    return payload,{'width':w,'height':h,'convention':spec['convention'],'edge':spec['edge'],'strength':strength,
                    'source_sha256':hashlib.sha256(raw).hexdigest(),'pixel_sha256':hashlib.sha256(pixels).hexdigest(),
                    'pixel_roundtrip_verified':True,'render_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
    _,_,path=validate(root,plan);w,h,_,_=decode(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),('L',))
    return plan,dict(spec,source_dimensions=[w,h],scope='Tangent-space RGB normal map from supplied grayscale heights; not physical depth recovery.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-normal-map-result-v1','status':'normal_pixels_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Normal-map generation unavailable; inspect grayscale PNG, Pillow and settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
