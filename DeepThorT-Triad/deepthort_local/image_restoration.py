"""Reviewed impulse-noise restoration with optional explicit scratch mask."""
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
SCHEMA='janus-image-restoration-v1'
def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','mask','threshold','passes'} or not isinstance(s['image'],str) or (s['mask'] is not None and not isinstance(s['mask'],str)):
        raise ValueError('Expected image, optional grayscale damage mask and restoration settings')
    if type(s['threshold']) is not int or not 16<=s['threshold']<=255 or type(s['passes']) is not int or not 1<=s['passes']<=3:
        raise ValueError('Restoration threshold or passes outside bound')
    if s['mask'] is not None and s['passes']!=1:raise ValueError('Masked restoration uses one independent pass')
    return s
def paths(root,s,exclude):
    out=[guard.path_for(root,s['image'],exclude,{'.png'},exists=True)]
    if s['mask'] is not None:out.append(guard.path_for(root,s['mask'],exclude,{'.png'},exists=True))
    if len({str(p).casefold() for p in out})!=len(out) or any(p.stat().st_size>guard.MAX_INPUT for p in out):
        raise ValueError('Duplicate or oversized input')
    return out
def generate(raw,mask_raw,s):
    checked(s);Image=image_module()
    with decode_layer(raw) as im:
        w,h=im.size;original=im.tobytes()
    if w*h>1024*1024:raise ValueError('Restoration exceeds one megapixel bound')
    if any(a!=255 for a in original[3::4]):
        raise ValueError('Initial restoration supports opaque images only')
    if (s['mask'] is None)!=(mask_raw is None):raise ValueError('Mask input does not match reviewed specification')
    mask=None
    if mask_raw is not None:
        mw,mh,_,mask=decode(mask_raw,('L',))
        if (mw,mh)!=(w,h) or any(v not in (0,255) for v in mask) or not any(mask):
            raise ValueError('Use a nonempty same-size binary damage mask')
        if sum(v==255 for v in mask)>w*h//4:raise ValueError('Damage mask exceeds one-quarter image bound')
    pixels=original
    for _ in range(s['passes']):
        out=bytearray(pixels)
        if mask is None:
            from PIL import ImageFilter
            with Image.frombytes('RGBA',(w,h),pixels) as rgba:
                with rgba.convert('RGB') as rgb:
                    with rgb.filter(ImageFilter.MedianFilter(3)) as median:
                        med=median.tobytes()
            for i in range(w*h):
                at=i*4;m=i*3
                if max(abs(pixels[at+c]-med[m+c]) for c in range(3))>=s['threshold']:
                    out[at:at+3]=med[m:m+3]
        else:
            for i,m in enumerate(mask):
                if not m:continue
                x,y=i%w,i//w;neighbors=[]
                for dy in range(-3,4):
                    for dx in range(-3,4):
                        nx,ny=x+dx,y+dy
                        if 0<=nx<w and 0<=ny<h and mask[ny*w+nx]==0:
                            neighbors.append((1/(dx*dx+dy*dy),4*(ny*w+nx)))
                if not neighbors:raise ValueError('Mask has an interior beyond the local repair radius')
                total=sum(a for a,_ in neighbors)
                out[4*i:4*i+3]=bytes(round(sum(a*pixels[j+c] for a,j in neighbors)/total) for c in range(3))
        pixels=bytes(out)
    if mask is not None and any(pixels[4*i:4*i+4]!=original[4*i:4*i+4] for i,v in enumerate(mask) if not v):
        raise ValueError('Repair changed unmasked pixels')
    if pixels[3::4]!=original[3::4]:raise ValueError('Unexpected alpha change')
    stream=io.BytesIO()
    with Image.frombytes('RGBA',(w,h),pixels) as im:im.save(stream,format='PNG',compress_level=6)
    payload=stream.getvalue()
    with decode_layer(payload) as im:
        if im.size!=(w,h) or im.tobytes()!=pixels:raise ValueError('Restored PNG roundtrip mismatch')
    return payload,{'width':w,'height':h,'method':'masked local interpolation' if mask is not None else 'thresholded median impulse suppression',
        'changed_pixels':sum(pixels[i:i+4]!=original[i:i+4] for i in range(0,len(pixels),4)),
        'source_sha256':hashlib.sha256(raw).hexdigest(),'mask_sha256':hashlib.sha256(mask_raw).hexdigest() if mask_raw else None,
        'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'pixel_roundtrip_verified':True,'alpha_preserved':True,
        'unmasked_pixels_preserved':True if mask is not None else None,'historical_detail_recovered':False,
        'neural_restoration_used':False,'visual_quality_verified':False,
        'scope':'Classical impulse-noise suppression or explicitly masked small scratch repair; reconstructed pixels are estimates.'}
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards']) not in (2,3):raise ValueError('Invalid restoration approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    p=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(p)!=len(plan['guards'])-1 or any(snapshot_file(x)!=g for x,g in zip(p,plan['guards'][1:])):raise ValueError('Reviewed restoration input changed')
    return s,dst,p
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    p=paths(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(x) for x in p)
    validate(root,plan)
    return plan,dict(s,scope='Classical local repair; reconstructed content is an estimate, not historical recovery.')
def execute(root,plan):
    s,dst,p=validate(root,plan);raws=[guard.exact(x,g,guard.MAX_INPUT) for x,g in zip(p,plan['guards'][1:])]
    payload,r=generate(raws[0],raws[1] if len(raws)==2 else None,s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-restoration-result-v1','status':'restored_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed image, damage mask or restoration output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
