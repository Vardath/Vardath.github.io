"""Reviewed region-guided grayscale colourisation with encoded luma preservation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.texture_pixels import decode,encode
SCHEMA='janus-image-colourisation-v1'
COEFF=(2126,7152,722)

def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','regions'} or not isinstance(s['image'],str):
        raise ValueError('Expected grayscale PNG and reviewed color regions')
    rs=s['regions']
    if not isinstance(rs,list) or not 1<=len(rs)<=4:raise ValueError('Use 1–4 distinct region masks')
    paths={s['image'].casefold()}
    for r in rs:
        if not isinstance(r,dict) or set(r)!={'mask','rgb','strength_percent'} or not isinstance(r['mask'],str) or r['mask'].casefold() in paths:
            raise ValueError('Invalid or duplicate mask')
        paths.add(r['mask'].casefold())
        c=r['rgb']
        if not isinstance(c,list) or len(c)!=3 or not all(type(v) is int and 0<=v<=255 for v in c) or max(c)==min(c):
            raise ValueError('Expected a chromatic RGB triplet')
        if type(r['strength_percent']) is not int or not 1<=r['strength_percent']<=100:raise ValueError('Invalid strength')
    return s
def luma(rgb):return sum(a*b for a,b in zip(rgb,COEFF))/10000
def palette(r):
    color=r['rgb'];mean=luma(color)
    offsets=[v-mean for v in color]
    result=[]
    for y in range(256):
        strength=r['strength_percent']/100
        for v in offsets:
            if v>0:strength=min(strength,(255-y)/v)
            elif v<0:strength=min(strength,-y/v)
        c=bytes(max(0,min(255,round(y+strength*v))) for v in offsets)
        if abs(luma(c)-y)>.500001:raise ValueError('Luma preservation check failed')
        result.append(c)
    return result
def generate(raw,masks,s):
    checked(s);w,h,_,gray=decode(raw,('L',))
    if len(masks)!=len(s['regions']) or w*h>1024*1024:raise ValueError('Mask count or pixel bound exceeded')
    labels=bytearray(w*h);counts=[]
    for i,mask in enumerate(masks,1):
        mw,mh,_,values=decode(mask,('L',))
        if (mw,mh)!=(w,h) or any(v not in (0,255) for v in values) or not any(values):
            raise ValueError('Use nonempty same-size binary grayscale masks')
        count=0
        for j,v in enumerate(values):
            if v:
                if labels[j]:raise ValueError('Overlapping color regions')
                labels[j]=i;count+=1
        counts.append(count)
    palettes=[[bytes((v,v,v)) for v in range(256)]]+[palette(r) for r in s['regions']]
    pixels=b''.join(palettes[label][v] for label,v in zip(labels,gray))
    changed=sum(pixels[i*3:i*3+3]!=bytes((v,v,v)) for i,v in enumerate(gray))
    if not changed:raise ValueError('Selected region shades cannot receive visible color')
    error=max(abs(luma(pixels[i*3:i*3+3])-v) for i,v in enumerate(gray))
    if error>.500001 or any(pixels[i*3:i*3+3]!=bytes((v,v,v)) for i,v in enumerate(gray) if not labels[i]):
        raise ValueError('Luma or unmasked region verification failed')
    out=encode(w,h,'RGB',pixels)
    return out,{'width':w,'height':h,'region_pixels':counts,'changed_pixels':changed,'maximum_encoded_luma_error':error,
        'unmasked_grayscale_preserved':True,'pixel_roundtrip_verified':True,'source_sha256':hashlib.sha256(raw).hexdigest(),
        'mask_sha256':[hashlib.sha256(m).hexdigest() for m in masks],
        'historical_color_verified':False,'semantic_color_inferred':False,'visual_quality_verified':False,
        'scope':'Explicit region masks and palette chroma with gamut-limited Rec.709 encoded luma; no automatic semantic or historical colour recovery.'}
def paths(root,s,exclude):
    pp=[guard.path_for(root,x,exclude,{'.png'},exists=True) for x in [s['image'],*(r['mask'] for r in s['regions'])]]
    if len({str(p).casefold() for p in pp})!=len(pp) or sum(p.stat().st_size for p in pp)>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized inputs')
    return pp
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 3<=len(plan['guards'])<=6:
        raise ValueError('Invalid colourisation approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(pp)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:])):
        raise ValueError('Reviewed image or masks changed')
    return s,dst,pp
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    pp=paths(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in pp)
    validate(root,plan)
    return plan,dict(s,scope='Explicit regional chroma, not historical color inference.')
def execute(root,plan):
    s,dst,pp=validate(root,plan);raws=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:])]
    out,r=generate(raws[0],raws[1:],s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-colourisation-result-v1','status':'regional_colour_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed grayscale image, regions or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
