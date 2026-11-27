"""Reviewed alpha-composite background replacement for bounded PNG sources."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local.background_removal import rgb
from deepthort_local.image_composition import decode_layer
from deepthort_local.texture_pixels import encode,image_module

SCHEMA='janus-background-replacement-v1'
def checked(s):
    if not isinstance(s,dict) or not isinstance(s.get('foreground'),str):
        raise ValueError('Expected foreground and replacement background')
    if s.get('mode')=='solid':
        if set(s)!={'foreground','mode','color'}:raise ValueError('Expected solid background color')
        rgb(s['color'])
    elif s.get('mode')=='image':
        if set(s)!={'foreground','mode','background','fit'} or not isinstance(s['background'],str) or s['background'].casefold()==s['foreground'].casefold() or s['fit'] not in ('exact','stretch'):
            raise ValueError('Expected distinct background image and exact or stretch fit')
    else:raise ValueError('Use solid or image mode')
    return s

def generate(raw,s,background=None):
    checked(s);Image=image_module()
    with decode_layer(raw) as front:
        w,h=front.size
        with front.getchannel('A') as alpha:
            if alpha.getextrema()[0]==255:raise ValueError('Foreground is opaque; remove its background first')
            visible_bg=sum(v<255 for v in alpha.tobytes())
        if s['mode']=='solid':
            if background is not None:raise ValueError('Unexpected background image')
            back=Image.new('RGBA',(w,h),tuple(s['color'])+(255,))
            dimensions=None
        else:
            if background is None:raise ValueError('Missing background image')
            with decode_layer(background) as source:
                dimensions=list(source.size)
                with source.getchannel('A') as a:
                    if a.getextrema()!=(255,255):raise ValueError('Replacement background must be opaque')
                if source.size!=(w,h) and s['fit']=='exact':raise ValueError('Exact fit requires matching dimensions')
                back=source.resize((w,h),Image.Resampling.LANCZOS) if source.size!=(w,h) else source.copy()
        with back:
            with Image.alpha_composite(back,front) as combined:
                with combined.convert('RGB') as final:
                    pixels=final.tobytes()
    payload=encode(w,h,'RGB',pixels)
    return payload,{'width':w,'height':h,'background_source_dimensions':dimensions,'background_visible_pixels':visible_bg,
        'foreground_sha256':hashlib.sha256(raw).hexdigest(),'background_sha256':hashlib.sha256(background).hexdigest() if background is not None else None,
        'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'pixel_roundtrip_verified':True,
        'semantic_segmentation':False,'visual_quality_verified':False}

def _paths(root,s,exclude):
    names=[s['foreground']]+([s['background']] if s['mode']=='image' else [])
    paths=[guard.path_for(root,n,exclude,{'.png'},exists=True) for n in names]
    if len({str(p).casefold() for p in paths})!=len(paths) or any(p.stat().st_size>guard.MAX_INPUT for p in paths):
        raise ValueError('Duplicate or oversized source')
    return paths
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards']) not in (2,3):
        raise ValueError('Invalid replacement approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    paths=_paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed replacement source changed')
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
    return plan,dict(s,verification=r,scope='Composite an already transparent foreground over an opaque solid or PNG background; no inferred segmentation.')
def execute(root,plan):
    payload,r,dst=_render(root,plan)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-background-replacement-result-v1','status':'background_composite_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Background replacement unavailable; inspect transparent foreground, opaque background and reviewed fit'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
