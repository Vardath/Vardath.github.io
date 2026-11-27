"""Reviewed explicit image enhancement; not AI restoration or inferred detail."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import image_module

SCHEMA='janus-image-enhancement-v1'
EXTRA=('image','.png')
FACTORS=('brightness','contrast','saturation','sharpness')

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'image',*FACTORS} or not isinstance(spec['image'],str):
        raise ValueError('Expected image and explicit brightness, contrast, saturation and sharpness percentages')
    if any(type(spec[k]) is not int or not 0<=spec[k]<=300 for k in FACTORS):
        raise ValueError('Enhancement percentages must be integer 0..300; 100 is unchanged')
    return spec

def generate(raw,spec):
    checked(spec)
    from PIL import ImageEnhance
    with decode_layer(raw) as source:
        w,h=source.size
        with source.getchannel('A') as alpha:
            original_alpha=alpha.tobytes()
            image=source.convert('RGB')
            try:
                for key,enhancer in zip(FACTORS,(ImageEnhance.Brightness,ImageEnhance.Contrast,ImageEnhance.Color,ImageEnhance.Sharpness)):
                    if spec[key]!=100:
                        replacement=enhancer(image).enhance(spec[key]/100)
                        image.close();image=replacement
                image.putalpha(alpha)
                pixels=image.tobytes()
                stream=io.BytesIO();image.save(stream,format='PNG',compress_level=6);payload=stream.getvalue()
            finally:
                image.close()
        original_pixels=source.tobytes()
    with decode_layer(payload) as reopened:
        if reopened.size!=(w,h) or reopened.tobytes()!=pixels or pixels[3::4]!=original_alpha:
            raise ValueError('Decoded output differs or alpha changed')
    return payload,{'width':w,'height':h,'factors':{k:spec[k] for k in FACTORS},
                    'source_sha256':hashlib.sha256(raw).hexdigest(),'pixel_sha256':hashlib.sha256(pixels).hexdigest(),
                    'changed_pixels':sum(pixels[i:i+3]!=original_pixels[i:i+3] for i in range(0,len(pixels),4)),
                    'alpha_preserved':True,'pixel_roundtrip_verified':True,'visual_quality_verified':False,
                    'color_space':'encoded RGB; no ICC transformation; hidden RGB participates in adjustment'}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
    spec,_,path=validate(root,plan)
    _,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    return plan,dict(spec,source_dimensions=[r['width'],r['height']],changed_pixels=r['changed_pixels'],
                     scope='Fixed-order explicit RGB enhancement, original alpha preserved. No detail recovery or quality claim.')
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan)
    payload,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-enhancement-result-v1','status':'enhanced_pixels_verified','output':plan['output'],
            'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Image enhancement unavailable; inspect PNG and reviewed settings'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
