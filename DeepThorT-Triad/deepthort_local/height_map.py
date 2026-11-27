"""Derive an explicit grayscale height texture from supplied image intensity."""
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
SCHEMA='janus-height-map-v1'
EXTRA=('image','.png')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'image','channel','black','white','gamma','invert'} or not isinstance(spec['image'],str):
        raise ValueError('Expected image, channel, levels, gamma and inversion')
    b,w,g=spec['black'],spec['white'],spec['gamma']
    if (type(b) is not int or type(w) is not int or not 0<=b<w<=255 or type(g) not in (int,float)
        or not math.isfinite(g) or not .1<=g<=5 or type(spec['invert']) is not bool
        or spec['channel'] not in ('luma','red','green','blue','gray')):
        raise ValueError('Invalid height-map settings')
    return spec
def pixels(raw,spec):
    w,h,mode,data=decode(raw,('L','RGB'))
    channel=spec['channel']
    if mode=='L':
        if channel not in ('gray','luma'):raise ValueError('RGB channel requested for grayscale image')
        intensity=data
    else:
        if channel=='gray':raise ValueError('Choose luma or explicit RGB channel')
        if channel=='luma':
            # Rec. 709 coefficients applied to encoded 8-bit values, not recovered scene depth.
            intensity=bytes((2126*data[i]+7152*data[i+1]+722*data[i+2]+5000)//10000 for i in range(0,len(data),3))
        else:intensity=data[('red','green','blue').index(channel)::3]
    b,white,gamma=spec['black'],spec['white'],spec['gamma']
    lut=[]
    for v in range(256):
        level=max(0,min(1,(v-b)/(white-b)))
        height=round(255*level**gamma)
        lut.append(255-height if spec['invert'] else height)
    out=intensity.translate(bytes(lut))
    return w,h,mode,out
def generate(raw,spec):
    w,h,mode,out=pixels(raw,spec)
    payload=encode(w,h,'L',out)
    return payload,{'width':w,'height':h,'source_mode':mode,'minimum':min(out),'maximum':max(out),
                    'source_sha256':hashlib.sha256(raw).hexdigest(),'pixel_sha256':hashlib.sha256(out).hexdigest(),
                    'pixel_roundtrip_verified':True,'physical_depth_recovered':False,'render_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
    _,_,path=validate(root,plan);w,h,mode,data=pixels(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,source_dimensions=[w,h],source_mode=mode,preview_height_range=[min(data),max(data)],
                     scope='Image intensity remapping only; no physical or AI-estimated depth recovery.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-height-map-result-v1','status':'height_pixels_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Height-map generation unavailable; inspect PNG, Pillow and reviewed settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
