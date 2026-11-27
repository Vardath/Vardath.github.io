"""Reviewed deterministic periodic procedural RGB texture generation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.texture_pixels import encode
SCHEMA='janus-procedural-texture-v1'
Q=65536
def integer(v,lo,hi):return type(v) is int and lo<=v<=hi
def rgb(v):return isinstance(v,list) and len(v)==3 and all(integer(x,0,255) for x in v)
def checked(s):
    if not isinstance(s,dict) or set(s)!={'size','seed','base_cells','octaves','persistence_percent','low_rgb','high_rgb'}:
        raise ValueError('Expected seeded tileable texture settings')
    if type(s['size']) is not int or s['size'] not in (64,128,256,512,1024) or not integer(s['seed'],0,2**32-1):
        raise ValueError('Invalid texture dimensions or seed')
    if not integer(s['base_cells'],2,16) or not integer(s['octaves'],1,4) or not integer(s['persistence_percent'],1,90):
        raise ValueError('Noise settings outside bounds')
    if s['base_cells']*2**(s['octaves']-1)>min(64,s['size']//2):
        raise ValueError('Frequency exceeds grid or sampling bound')
    if not rgb(s['low_rgb']) or not rgb(s['high_rgb']) or s['low_rgb']==s['high_rgb']:
        raise ValueError('Provide two distinct RGB colors')
    return s
def grid(seed,cells,octave):
    return [int.from_bytes(hashlib.sha256(f'{seed}:{octave}:{x}:{y}'.encode('ascii')).digest()[:2],'big')
            for y in range(cells) for x in range(cells)]
def axis(i,size,cells):
    a,t=divmod((i%size)*cells*Q//size,Q)
    t=t*t*(3*Q-2*t)//(Q*Q)
    return a,(a+1)%cells,t
def lerp(a,b,t):return (a*(Q-t)+b*t+Q//2)//Q
def value(g,cells,ax,ay):
    x,x1,fx=ax;y,y1,fy=ay
    return lerp(lerp(g[y*cells+x],g[y*cells+x1],fx),lerp(g[y1*cells+x],g[y1*cells+x1],fx),fy)
def sample(g,cells,x,y,size):return value(g,cells,axis(x,size,cells),axis(y,size,cells))
def generate(s):
    checked(s);n=s['size'];layers=[];weight=Q
    for octave in range(s['octaves']):
        cells=s['base_cells']*2**octave;g=grid(s['seed'],cells,octave)
        coords=[axis(i,n,cells) for i in range(n)]
        for i in range(n):
            if sample(g,cells,0,i,n)!=sample(g,cells,n,i,n) or sample(g,cells,i,0,n)!=sample(g,cells,i,n,n):
                raise ValueError('Periodic field check failed')
        layers.append((g,cells,coords,weight))
        weight=max(1,weight*s['persistence_percent']//100)
    total=sum(x[3] for x in layers)
    out=bytearray();minimum=Q;maximum=0
    palette=[bytes(lerp(a,b,t) for a,b in zip(s['low_rgb'],s['high_rgb'])) for t in range(Q)]
    for y in range(n):
        for x in range(n):
            t=sum(value(g,c,coords[x],coords[y])*w for g,c,coords,w in layers)//total
            minimum=min(minimum,t);maximum=max(maximum,t);out.extend(palette[t])
    if minimum==maximum or all(out[i:i+3]==out[:3] for i in range(0,len(out),3)):
        raise ValueError('Texture collapsed at output precision')
    data=bytes(out);raw=encode(n,n,'RGB',data)
    return raw,{'width':n,'height':n,'seed':s['seed'],'octaves':s['octaves'],
        'minimum_field':minimum,'maximum_field':maximum,'pixel_sha256':hashlib.sha256(data).hexdigest(),
        'periodic_field_verified':True,'pixel_roundtrip_verified':True,'neural_generation_used':False,
        'visual_quality_verified':False,'physical_material_verified':False,
        'scope':'Periodic deterministic smooth value noise, not semantic material synthesis.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.png')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    return plan,dict(s,scope='Seeded periodic RGB noise; no external model or tool.')
def execute(root,plan):
    s,dst,_=validate(root,plan);raw,r=generate(s)
    sha=guard.publish(raw,dst,lambda:validate(root,plan))
    return {'schema':'janus-procedural-texture-result-v1','status':'periodic_texture_pixels_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed texture settings or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
