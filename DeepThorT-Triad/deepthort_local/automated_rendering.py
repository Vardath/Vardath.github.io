"""Bounded orthographic static-scene preview with a software depth buffer."""
from __future__ import annotations
import argparse
from array import array
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local import automatic_lighting as lighting,scene_composition as scene
from deepthort_local.mesh_geometry import sub,cross,dot,norm,triangle
from deepthort_local.texture_pixels import encode
SCHEMA='janus-automated-rendering-v1'
MAX_WORK=8_000_000

def lighting_spec(s):
    return {k:s[k] for k in ('objects','max_position_error','view_azimuth_deg','key_lux','preset')}
def rgb(v):return isinstance(v,list) and len(v)==3 and all(type(x) is int and 0<=x<=255 for x in v)
def checked(s):
    if not isinstance(s,dict) or set(s)!={'objects','max_position_error','view_azimuth_deg','key_lux','preset','elevation_deg','width','height','colors','background'}:
        raise ValueError('Expected lit scene, camera, dimensions and object colors')
    lighting.checked(lighting_spec(s))
    if not scene.number(s['elevation_deg'],-80,80) or any(type(s[k]) is not int or not 64<=s[k]<=512 for k in ('width','height')):
        raise ValueError('Camera or pixel dimensions outside bound')
    if not rgb(s['background']) or not isinstance(s['colors'],list) or len(s['colors'])!=len(s['objects']) or not all(rgb(c) for c in s['colors']):
        raise ValueError('Expected explicit RGB background and one color per object')
    return s
def mul(v,k):return tuple(x*k for x in v)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def unit(v):
    length=norm(v)
    if length<=0:raise ValueError('Zero direction')
    return mul(v,1/length)
def transform(v,node):
    p=tuple(x*s for x,s in zip(v,node['scale']))
    q=tuple(node['rotation'][:3]);w=node['rotation'][3]
    t=mul(cross(q,p),2)
    return add(add(add(p,mul(t,w)),cross(q,t)),node['translation'])
def accessor(doc,data,i,fmt):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
    start=v['byteOffset']+a.get('byteOffset',0);end=start+v['byteLength']
    if end>len(data) or v['byteLength']!=a['count']*struct.calcsize(fmt):
        raise ValueError('Unexpected scene accessor extent')
    return list(struct.iter_unpack(fmt,data[start:end]))
def edge(a,b,p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def render(raws,s):
    checked(s);payload,receipt=lighting.add_lighting(raws,lighting_spec(s))
    doc,data=scene.decode(payload);w,h=s['width'],s['height']
    az,el=map(math.radians,(s['view_azimuth_deg'],s['elevation_deg']))
    view=(math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el))
    right=unit(cross((0.,1.,0.),view));up=cross(view,right)
    projected=[];parts=[]
    for i,node in enumerate(doc['nodes'][:len(s['objects'])]):
        p=doc['meshes'][node['mesh']]['primitives'][0]
        verts=[transform(v,node) for v in accessor(doc,data,p['attributes']['POSITION'],'<3f')]
        indices=[v[0] for v in accessor(doc,data,p['indices'],'<I')]
        faces=[tuple(indices[k:k+3]) for k in range(0,len(indices),3)]
        coords=[(dot(v,right),dot(v,up),dot(v,view)) for v in verts]
        projected.extend(coords);parts.append((verts,faces,coords,s['colors'][i]))
    lo=[min(v[i] for v in projected) for i in range(3)]
    hi=[max(v[i] for v in projected) for i in range(3)]
    span=max((hi[0]-lo[0])/w,(hi[1]-lo[1])/h)
    if span<=1e-12:raise ValueError('Camera projection has no visible extent')
    scale=.85/span;cx=(lo[0]+hi[0])/2;cy=(lo[1]+hi[1])/2
    image=bytearray(bytes(s['background'])*(w*h));depth=array('d',[-math.inf])*(w*h)
    hits=work=0
    for verts,faces,coords,color in parts:
        screen=[((x-cx)*scale+w/2,h/2-(y-cy)*scale,z) for x,y,z in coords]
        for f in faces:
            a,b,c=(screen[i] for i in f);area=edge(a,b,c)
            if abs(area)<1e-9:continue
            # Two-sided flat shading, oriented toward the viewer.
            ab,ac,_=triangle(verts,f);normal=unit(cross(ab,ac))
            if dot(normal,view)<0:normal=mul(normal,-1)
            channels=[.12]*3
            for light in receipt['lights']:
                gain=max(0,-dot(normal,light['direction']))*light['intensity']/1000
                for j in range(3):channels[j]+=gain*light['color'][j]
            shaded=bytes(max(0,min(255,round(color[j]*channels[j]))) for j in range(3))
            x0=max(0,math.floor(min(a[0],b[0],c[0])));x1=min(w-1,math.ceil(max(a[0],b[0],c[0])))
            y0=max(0,math.floor(min(a[1],b[1],c[1])));y1=min(h-1,math.ceil(max(a[1],b[1],c[1])))
            work+=max(0,x1-x0+1)*max(0,y1-y0+1)
            if work>MAX_WORK:raise ValueError('Raster work bound exceeded; simplify mesh or reduce resolution')
            for y in range(y0,y1+1):
                for x in range(x0,x1+1):
                    p=(x+.5,y+.5);u=edge(b,c,p)/area;v=edge(c,a,p)/area;t=1-u-v
                    if min(u,v,t)<-1e-10:continue
                    z=u*a[2]+v*b[2]+t*c[2];i=y*w+x
                    if z>depth[i]:
                        if depth[i]==-math.inf:hits+=1
                        depth[i]=z;image[3*i:3*i+3]=shaded
    if not hits:raise ValueError('No visible triangle samples')
    raw=encode(w,h,'RGB',bytes(image))
    return raw,{'width':w,'height':h,'visible_pixels':hits,'raster_candidate_samples':work,
        'source_objects':receipt['objects'],'triangles':receipt['triangles'],
        'depth_buffer_used':True,'png_pixels_roundtrip_verified':True,'camera_projection':'orthographic',
        'render_verified':True,'native_engine_used':False,'photorealism_verified':False,'visual_quality_verified':False,
        'scope':'CPU flat-shaded two-sided static geometry preview, approximate directional lighting; no shadows, textures, PBR or animation.'}
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 2<=len(plan['guards'])<=scene.MAX_OBJECTS+1:
        raise ValueError('Invalid render approval')
    spec,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.png')
    paths=scene.paths_for(Path(root).resolve(strict=True),spec,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed scene mesh changed')
    return spec,dst,paths
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.png')
    paths=scene.paths_for(Path(plan['root']),spec,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in paths)
    validate(root,plan)
    return plan,dict(spec,scope='Bounded static orthographic preview; approximate lighting and depth occlusion, not production renderer.')
def execute(root,plan):
    spec,dst,paths=validate(root,plan);payload,r=render(scene.raws_for(paths,plan),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-automated-rendering-result-v1','status':'static_preview_rendered','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid scene, raster work bound or reviewed output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
