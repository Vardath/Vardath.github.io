"""Reviewed bounded local PNG layer composition on an explicit opaque canvas."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.artifact_media_checks import png
from deepthort_local.texture_pixels import image_module,encode

SCHEMA='janus-image-composition-v1'
MAX_LAYERS=6  # specification + six distinct inputs + three host guards <= 10

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'width','height','background','layers'}:
        raise ValueError('Expected canvas dimensions, background and ordered layers')
    w,h=spec['width'],spec['height']
    if type(w) is not int or type(h) is not int or not 1<=w<=2048 or not 1<=h<=2048:
        raise ValueError('Canvas dimensions must be 1..2048')
    bg=spec['background']
    if not isinstance(bg,list) or len(bg)!=3 or any(type(v) is not int or not 0<=v<=255 for v in bg):
        raise ValueError('Background must be an RGB byte triplet')
    layers=spec['layers']
    if not isinstance(layers,list) or not 2<=len(layers)<=MAX_LAYERS:
        raise ValueError('Choose two to six ordered layers')
    seen=set()
    for layer in layers:
        if not isinstance(layer,dict) or set(layer)!={'image','x','y','width','height','opacity'}:
            raise ValueError('Each layer needs an image, position, size and opacity byte')
        image=layer['image']
        if not isinstance(image,str) or not image or image.casefold() in seen:
            raise ValueError('Use distinct PNG source paths')
        seen.add(image.casefold())
        x,y,lw,lh,o=(layer[k] for k in ('x','y','width','height','opacity'))
        if any(type(v) is not int for v in (x,y,lw,lh,o)) or not (0<=x<w and 0<=y<h and 1<=lw<=w-x and 1<=lh<=h-y and 1<=o<=255):
            raise ValueError('Layers must fit entirely within the canvas; opacity 1..255')
    return spec

def decode_layer(raw):
    png(raw)
    w,h,depth,color,_,_,_=struct.unpack('>IIBBBBB',raw[16:29])
    if not 1<=w<=2048 or not 1<=h<=2048 or depth!=8 or color not in (0,2,4,6):
        raise ValueError('Use single-frame 8-bit L, RGB, LA or RGBA PNG within 2048 pixels per side')
    Image=image_module()
    expected={0:'L',2:'RGB',4:'LA',6:'RGBA'}[color]
    with Image.open(io.BytesIO(raw),formats=['PNG']) as im:
        if im.mode!=expected or im.size!=(w,h) or getattr(im,'n_frames',1)!=1 or 'transparency' in im.info:
            raise ValueError('Unsupported PNG mode, animation or keyed transparency')
        im.verify()
    with Image.open(io.BytesIO(raw),formats=['PNG']) as im:
        im.load()
        return im.convert('RGBA')

def compose(raws,spec):
    spec=checked(spec)
    if len(raws)!=len(spec['layers']):
        raise ValueError('Layer input count mismatch')
    Image=image_module()
    w,h=spec['width'],spec['height']
    observations=[]
    with Image.new('RGBA',(w,h),tuple(spec['background'])+(255,)) as canvas:
        for raw,layer in zip(raws,spec['layers']):
            with decode_layer(raw) as source:
                original_size=list(source.size)
                target=(layer['width'],layer['height'])
                with source.resize(target,Image.Resampling.LANCZOS) if source.size!=target else source.copy() as im:
                    opacity=layer['opacity']
                    if opacity!=255:
                        with im.getchannel('A') as alpha:
                            with alpha.point([(v*opacity+127)//255 for v in range(256)]) as adjusted:
                                im.putalpha(adjusted)
                    canvas.alpha_composite(im,dest=(layer['x'],layer['y']))
                observations.append(dict(layer,source_dimensions=original_size,source_sha256=hashlib.sha256(raw).hexdigest()))
        with canvas.convert('RGB') as final:
            pixels=final.tobytes()
    payload=encode(w,h,'RGB',pixels)
    return payload,{'width':w,'height':h,'layers':observations,'pixel_sha256':hashlib.sha256(pixels).hexdigest(),
                    'pixel_roundtrip_verified':True,'visual_quality_verified':False,
                    'color_space':'encoded RGB; no ICC color transformation'}

def _paths(root,spec,exclude):
    paths=[guard.path_for(root,l['image'],exclude,{'.png'},exists=True) for l in spec['layers']]
    if len({str(p).casefold() for p in paths})!=len(paths) or any(p.stat().st_size>guard.MAX_INPUT for p in paths):
        raise ValueError('Duplicate or oversized layer input')
    return paths

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    root=Path(plan['root'])
    paths=_paths(root,spec,plan['exclude'])
    plan['guards'].extend(snapshot_file(p) for p in paths)
    spec,_,paths=validate(root,plan)
    _,result=compose([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:])],spec)
    return plan,dict(spec,layer_observations=result['layers'],pixel_sha256=result['pixel_sha256'],
                     scope='Ordered PNG placement, resizing and alpha composition onto opaque RGB; review actual visual result.')

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=MAX_LAYERS+1:
        raise ValueError('Invalid layer approval')
    spec,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    paths=_paths(Path(root).resolve(strict=True),spec,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed layer input changed')
    return spec,dst,paths

def execute(root,plan):
    spec,dst,paths=validate(root,plan)
    payload,result=compose([guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(paths,plan['guards'][1:])],spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-composition-result-v1','status':'composed_pixels_verified',
            'output':plan['output'],'sha256':sha,**result,'source_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Image composition unavailable; inspect layers, PNG files and reviewed settings'}),flush=True);return 1

if __name__=='__main__':sys.exit(main())
