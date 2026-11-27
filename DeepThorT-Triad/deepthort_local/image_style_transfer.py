"""Reviewed classical reference palette transfer; no neural style synthesis."""
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

SCHEMA='janus-image-style-transfer-v1'
MAX_PIXELS=1024*1024

def checked(s):
    if not isinstance(s,dict) or set(s)!={'image','reference','strength_percent'}:
        raise ValueError('Expected image, reference and strength')
    if any(not isinstance(s[k],str) or not s[k] for k in ('image','reference')) or s['image'].casefold()==s['reference'].casefold():
        raise ValueError('Use two distinct image paths')
    if type(s['strength_percent']) is not int or not 1<=s['strength_percent']<=100:
        raise ValueError('Strength must be 1–100')
    return s

def histogram(values):
    counts=[0]*256
    for v in values:counts[v]+=1
    return counts

def mapping(source,target):
    # For each occupied source tone, use its empirical midrank and the
    # corresponding reference quantile. Integer comparisons avoid float ties.
    a=histogram(source);b=histogram(target)
    na,nb=len(source),len(target)
    cumulative=0; j=0; target_cumulative=b[0]; lut=[]
    for n in a:
        rank=(2*cumulative+n)*nb
        while j<255 and (2*na*target_cumulative<rank or not b[j]):
            j+=1;target_cumulative+=b[j]
        lut.append(j)
        cumulative+=n
    return lut

def generate(raw,reference,s):
    checked(s)
    w,h,_,pixels=decode(raw,('RGB',))
    rw,rh,_,ref=decode(reference,('RGB',))
    if w*h>MAX_PIXELS or rw*rh>MAX_PIXELS:
        raise ValueError('Both inputs must be at most one megapixel')
    strength=s['strength_percent']
    luts=[]
    for c in range(3):
        mapped=mapping(pixels[c::3],ref[c::3])
        luts.append(bytes((v*(100-strength)+mapped[v]*strength+50)//100 for v in range(256)))
    if any(any(a>b for a,b in zip(lut,lut[1:])) for lut in luts):
        raise ValueError('Nonmonotonic transfer')
    out_pixels=bytearray(len(pixels))
    for c,lut in enumerate(luts):out_pixels[c::3]=pixels[c::3].translate(lut)
    out=encode(w,h,'RGB',bytes(out_pixels))
    changed=sum(pixels[i:i+3]!=out_pixels[i:i+3] for i in range(0,len(pixels),3))
    return out,{'width':w,'height':h,'reference_width':rw,'reference_height':rh,
        'changed_pixels':changed,'strength_percent':strength,'spatial_layout_preserved':True,
        'monotonic_channel_mapping_verified':True,'pixel_roundtrip_verified':True,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'reference_sha256':hashlib.sha256(reference).hexdigest(),
        'neural_style_transfer':False,'visual_quality_verified':False,
        'scope':'Independent RGB empirical quantile palette transfer; no texture, semantic or learned artistic style transfer.'}

def paths(root,s,exclude):
    pp=[guard.path_for(root,s[k],exclude,{'.png'},exists=True) for k in ('image','reference')]
    if pp[0].samefile(pp[1]) or sum(p.stat().st_size for p in pp)>guard.MAX_INPUT:
        raise ValueError('Duplicate or oversized inputs')
    return pp

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Invalid style approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:])):
        raise ValueError('Reviewed image or reference changed')
    return s,dst,pp

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    pp=paths(Path(plan['root']),s,plan['exclude'])
    plan['guards'].extend(snapshot_file(p) for p in pp)
    validate(root,plan)
    return plan,dict(s,scope='Classical reference RGB palette transfer only, not learned style synthesis.')

def execute(root,plan):
    s,dst,pp=validate(root,plan)
    raw,ref=[guard.exact(p,g,guard.MAX_INPUT) for p,g in zip(pp,plan['guards'][1:])]
    out,r=generate(raw,ref,s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-image-style-transfer-result-v1','status':'reference_palette_pixels_verified',
            'output':plan['output'],'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed image, reference or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
