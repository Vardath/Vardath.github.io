"""Reviewed bounded alpha-aware image upscaling; no neural detail recovery."""
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
SCHEMA='janus-image-upscaling-v1'
EXTRA=('image','.png')
def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','scale','method','sharpen_percent'} or not isinstance(s['image'],str):
        raise ValueError('Expected reviewed image and upscale settings')
    if type(s['scale']) is not int or s['scale'] not in (2,3,4) or s['method'] not in ('nearest','bicubic','lanczos'):
        raise ValueError('Invalid upscale factor or method')
    if type(s['sharpen_percent']) is not int or not 0<=s['sharpen_percent']<=100:
        raise ValueError('Invalid sharpening amount')
    if s['method']=='nearest' and s['sharpen_percent']:raise ValueError('Nearest-neighbor pixel art must not be sharpened')
    return s
def dimensions(size,s):
    w,h=(v*s['scale'] for v in size)
    if max(w,h)>2048:raise ValueError('Upscaled dimensions exceed 2048')
    return w,h
def generate(raw,s):
    checked(s);Image=image_module()
    from PIL import ImageFilter
    with decode_layer(raw) as im:
        w,h=dimensions(im.size,s);original_size=list(im.size)
        method={'nearest':Image.Resampling.NEAREST,'bicubic':Image.Resampling.BICUBIC,'lanczos':Image.Resampling.LANCZOS}[s['method']]
        # Pillow uses premultiplied alpha internally for non-nearest RGBA resampling.
        with im.resize((w,h),method) as enlarged:
            with enlarged.getchannel('A') as alpha:
                alpha_pixels=alpha.tobytes()
                if s['sharpen_percent']:
                    # Sharpen premultiplied channels to avoid hidden RGB bleeding across transparent edges.
                    with enlarged.convert('RGBa') as premul:
                        channels=premul.split()
                        try:
                            with Image.merge('RGB',channels[:3]) as rgb:
                                with rgb.filter(ImageFilter.UnsharpMask(radius=1,percent=s['sharpen_percent'],threshold=3)) as sharp:
                                    src=sharp.tobytes()
                            bounded=bytes(min(c,alpha_pixels[i//3]) for i,c in enumerate(src))
                            with Image.frombytes('RGB',(w,h),bounded) as bounded_rgb:
                                parts=bounded_rgb.split()
                                try:
                                    with Image.merge('RGBa',(*parts,alpha)) as pre:
                                        with pre.convert('RGBA') as final:
                                            pixels=final.tobytes();stream=io.BytesIO();final.save(stream,format='PNG',compress_level=6)
                                finally:
                                    for p in parts:p.close()
                        finally:
                            for c in channels:c.close()
                else:
                    pixels=enlarged.tobytes();stream=io.BytesIO();enlarged.save(stream,format='PNG',compress_level=6)
    payload=stream.getvalue()
    with decode_layer(payload) as reopened:
        if reopened.size!=(w,h) or reopened.tobytes()!=pixels or pixels[3::4]!=alpha_pixels:
            raise ValueError('Upscaled pixel or alpha roundtrip failed')
    return payload,{'source_dimensions':original_size,'width':w,'height':h,'scale':s['scale'],'method':s['method'],
        'sharpen_percent':s['sharpen_percent'],'source_sha256':hashlib.sha256(raw).hexdigest(),
        'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'resampled_alpha_preserved':True,
        'pixel_roundtrip_verified':True,'neural_super_resolution_used':False,'detail_recovery_verified':False,
        'visual_quality_verified':False,'scope':'Classical interpolation and optional bounded sharpening; not learned super-resolution.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png',extra=EXTRA)
    _,_,path=validate(root,plan)
    with decode_layer(guard.exact(path,plan['guards'][1],guard.MAX_INPUT)) as im:
        return plan,dict(s,source_dimensions=list(im.size),output_dimensions=list(dimensions(im.size,s)),scope='Classical bounded upscale, no inferred detail.')
def execute(root,plan):
    s,dst,path=validate(root,plan);payload,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-upscaling-result-v1','status':'upscaled_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed PNG, upscale or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
