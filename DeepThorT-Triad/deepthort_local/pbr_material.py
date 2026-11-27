"""Reviewed PBR texture bundle derived from explicit height and material settings."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import normal_map
from deepthort_local.texture_pixels import decode,encode
SCHEMA='janus-pbr-material-v1'
EXTRA=('height_map','.png')
def rgb(v):return isinstance(v,list) and len(v)==3 and all(type(x) is int and 0<=x<=255 for x in v)
def checked(s):
    if not isinstance(s,dict) or set(s)!={'height_map','low_rgb','high_rgb','roughness_low','roughness_high','metallic','strength','edge'}:
        raise ValueError('Expected height and explicit PBR channel settings')
    normal_map.checked({'height_map':s['height_map'],'strength':s['strength'],'edge':s['edge'],'convention':'opengl'})
    if not rgb(s['low_rgb']) or not rgb(s['high_rgb']):raise ValueError('Invalid base color endpoints')
    if any(type(s[k]) is not int or not 0<=s[k]<=255 for k in ('roughness_low','roughness_high','metallic')):
        raise ValueError('Invalid linear material channel value')
    return s
def mix(a,b,t):return (a*(255-t)+b*t+127)//255
def generate(raw,s):
    checked(s);w,h,_,heights=decode(raw,('L',))
    if max(w,h)>1024:raise ValueError('PBR texture dimension exceeds 1024')
    palette=[bytes(mix(a,b,i) for a,b in zip(s['low_rgb'],s['high_rgb'])) for i in range(256)]
    mr=[bytes((255,mix(s['roughness_low'],s['roughness_high'],i),s['metallic'])) for i in range(256)]
    base=encode(w,h,'RGB',b''.join(palette[t] for t in heights))
    packed=encode(w,h,'RGB',b''.join(mr[t] for t in heights))
    normal,nr=normal_map.generate(raw,{'height_map':s['height_map'],'strength':s['strength'],'edge':s['edge'],'convention':'opengl'})
    files={'base_color.png':base,'normal.png':normal,'metallic_roughness.png':packed,'height.png':raw}
    receipt={'schema':'janus-pbr-material-result-v1','width':w,'height':h,'height_sha256':hashlib.sha256(raw).hexdigest(),
        'maps':{'base_color':{'file':'base_color.png','color_space':'sRGB'},
                'normal':{'file':'normal.png','color_space':'linear','convention':'OpenGL +Y tangent space'},
                'metallic_roughness':{'file':'metallic_roughness.png','color_space':'linear','red':'constant 255 (not measured occlusion)','green':'roughness','blue':'metallic'},
                'height':{'file':'height.png','color_space':'linear'}},
        'settings':s,'file_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in files.items()},
        'normal_pixel_verification':nr['pixel_roundtrip_verified'],'physical_properties_measured':False,
        'ambient_occlusion_baked':False,'render_verified':False,'visual_quality_verified':False}
    files['material.json']=json.dumps(receipt,sort_keys=True,allow_nan=False).encode('utf-8')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for k,v in files.items():z.writestr(k,v)
    payload=stream.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('PBR bundle exceeds output limit')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.namelist()!=list(files) or z.testzip() is not None or any(z.read(k)!=v for k,v in files.items()):
            raise ValueError('Material bundle roundtrip failed')
    return payload,dict(receipt,bundle_roundtrip_verified=True)
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,path=validate(root,plan);w,h,_,_=decode(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),('L',))
    if max(w,h)>1024:raise ValueError('PBR texture dimension exceeds 1024')
    return plan,dict(s,source_dimensions=[w,h],scope='Explicit height-derived color and roughness, constant metallic, OpenGL normal; not measured PBR properties.')
def execute(root,plan):
    s,dst,path=validate(root,plan);payload,r=generate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'pbr_map_bundle_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed height map, PBR settings or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
