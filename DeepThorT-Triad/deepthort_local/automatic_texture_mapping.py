"""Reviewed automatic box-projected texture mapping with an embedded PNG."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local import mesh_conversion as converter,scene_composition as scene
from deepthort_local.mesh_geometry import parse,encode,triangle,cross
from deepthort_local.texture_pixels import decode as pixels
SCHEMA='janus-texture-mapping-v1'
MAX_FACES=10000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'mesh','texture','max_position_error'} or not isinstance(s['texture'],str):
        raise ValueError('Expected plain mesh, opaque PNG and position error')
    converter.checked({'mesh':s['mesh'],'max_position_error':s['max_position_error']})
    return s

def project(raw):
    v,f,_,_=parse(raw)
    if len(f)>MAX_FACES:raise ValueError('Texture mapping triangle bound exceeded')
    lo=[min(p[i] for p in v) for i in range(3)]
    hi=[max(p[i] for p in v) for i in range(3)]
    uvs=[];uvfaces=[];axes=[0,0,0]
    for face in f:
        ab,ac,_=triangle(v,face);normal=cross(ab,ac)
        axis=max(range(3),key=lambda i:abs(normal[i]));axes[axis]+=1
        a,b=[i for i in range(3) if i!=axis]
        if hi[a]<=lo[a] or hi[b]<=lo[b]:raise ValueError('Degenerate texture projection')
        base=len(uvs)
        for i in face:
            u=(v[i][a]-lo[a])/(hi[a]-lo[a])
            t=(v[i][b]-lo[b])/(hi[b]-lo[b])
            uvs.append((u,t))
        x,y,z=uvs[-3:]
        if abs((y[0]-x[0])*(z[1]-x[1])-(y[1]-x[1])*(z[0]-x[0]))<=1e-15:
            raise ValueError('Degenerate projected UV triangle')
        uvfaces.append((base,base+1,base+2))
    mapped=encode(v,f,uvs,uvfaces)
    pv,pf,pu,puf=parse(mapped,allow_uv=True)
    if (pv,pf,pu,puf)!=(v,f,uvs,uvfaces):raise ValueError('UV roundtrip changed geometry')
    return mapped,axes

def map_texture(mesh,texture,s):
    checked(s)
    width,height,mode,_=pixels(texture,('RGB','L'))
    mapped,axes=project(mesh)
    payload,r=converter.convert(mapped,{'mesh':s['mesh'],'max_position_error':s['max_position_error']})
    d,b=scene.decode(payload)
    p=d['meshes'][0]['primitives'][0]
    if 'TEXCOORD_0' not in p['attributes']:raise ValueError('Missing texture coordinates')
    view=len(d['bufferViews'])
    d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(texture)})
    d['images']=[{'bufferView':view,'mimeType':'image/png'}]
    d['samplers']=[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}]
    d['textures']=[{'sampler':0,'source':0}]
    d['materials']=[{'name':'JANUS mapped base color','pbrMetallicRoughness':{'baseColorTexture':{'index':0,'texCoord':0},'metallicFactor':0.,'roughnessFactor':1.}}]
    p['material']=0
    content=b+texture
    d['buffers'][0]['byteLength']=len(content)
    content+=b'\x00'*((-len(content))%4)
    doc=json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    doc+=b' '*((-len(doc))%4)
    out=(struct.pack('<4sII',b'glTF',2,12+8+len(doc)+8+len(content))+
        struct.pack('<II',len(doc),0x4e4f534a)+doc+
        struct.pack('<II',len(content),0x004e4942)+content)
    od,ob=scene.decode(out);iv=od['bufferViews'][od['images'][0]['bufferView']]
    tex=ob[iv['byteOffset']:iv['byteOffset']+iv['byteLength']]
    if od!=d or ob[:len(b)]!=b or tex!=texture or pixels(tex,('RGB','L'))[:3]!=(width,height,mode):
        raise ValueError('Embedded texture or geometry roundtrip mismatch')
    return out,{'mesh_sha256':hashlib.sha256(mesh).hexdigest(),'texture_sha256':hashlib.sha256(texture).hexdigest(),
        'texture_width':width,'texture_height':height,'texture_mode':mode,'triangles':r['triangles'],
        'output_vertices':r['output_vertices'],'projection_axis_face_counts':axes,
        'maximum_position_error':r['maximum_position_error'],'geometry_roundtrip_verified':True,
        'texture_embedding_verified':True,'automatic_uv_mapping_verified':True,
        'seam_optimisation_verified':False,'nonoverlap_verified':False,'render_verified':False,
        'scope':'Dominant-axis box projection, overlapping UVs possible; one opaque PNG base color, no texture painting, baking or native render claim.'}

def paths(root,s,exclude):
    a=guard.path_for(root,s['mesh'],exclude,{'.obj'},exists=True)
    b=guard.path_for(root,s['texture'],exclude,{'.png'},exists=True)
    if sum(p.stat().st_size for p in (a,b))>16*1024*1024:raise ValueError('Input byte bound exceeded')
    return [a,b]
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=3:
        raise ValueError('Invalid texture approval')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.glb')
    pp=paths(Path(root).resolve(strict=True),s,plan['exclude'])
    if any(snapshot_file(p)!=g for p,g in zip(pp,plan['guards'][1:])):raise ValueError('Reviewed mesh or texture changed')
    return s,dst,pp
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb')
    pp=paths(Path(plan['root']),s,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in pp)
    validate(root,plan)
    return plan,dict(s,scope='Automatic box projection and embedded PNG; overlaps and seams possible.')
def execute(root,plan):
    s,dst,pp=validate(root,plan)
    raw=[guard.exact(p,g,16*1024*1024) for p,g in zip(pp,plan['guards'][1:])]
    out,r=map_texture(*raw,s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-texture-mapping-result-v1','status':'mapped_texture_embedded','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed mesh, opaque PNG or mapped output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
