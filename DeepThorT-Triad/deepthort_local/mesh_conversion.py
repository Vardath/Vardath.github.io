"""Convert a strict static triangular OBJ to self-contained glTF 2.0 GLB."""
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
from deepthort_local.mesh_geometry import parse,triangle,sub,cross,dot,norm
from deepthort_local.artifact_media_checks import glb

SCHEMA='janus-mesh-conversion-v1'
EXTRA=('mesh','.obj')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'mesh','max_position_error'} or not isinstance(spec['mesh'],str):
        raise ValueError('Expected static OBJ and explicit maximum position error')
    e=spec['max_position_error']
    if type(e) not in (int,float) or not math.isfinite(e) or not 1e-12<=e<=1.0:
        raise ValueError('Position error must be 1e-12–1 source units')
    return spec
def floats32(values):
    return struct.unpack('<'+'f'*len(values),struct.pack('<'+'f'*len(values),*values))
def convert(raw,spec):
    vertices,faces,uvs,uvfaces=parse(raw,allow_uv=True)
    if uvs and any(not 0<=v<=1 for uv in uvs for v in uv):
        raise ValueError('Initial converter supports UV coordinates in the unit square only')
    mapping={};positions=[];textures=[];indices=[];expected_faces=[];worst=0.0;worst_uv=0.0
    for fi,face in enumerate(faces):
        out=[]
        for ci,vi in enumerate(face):
            ti=uvfaces[fi][ci] if uvs else None
            key=(vi,ti)
            if key not in mapping:
                mapping[key]=len(positions)
                p=floats32(vertices[vi]);error=norm(sub(p,vertices[vi]))
                if error>spec['max_position_error']:raise ValueError('Float32 exceeds reviewed maximum position error')
                worst=max(worst,error);positions.append(p)
                if uvs:
                    # OBJ bottom-left UV origin -> glTF top-left origin.
                    source=(uvs[ti][0],1-uvs[ti][1]);uv=floats32(source)
                    err=norm(sub(uv,source))
                    if err>1e-6:raise ValueError('Float32 UV error exceeds bound')
                    worst_uv=max(worst_uv,err);textures.append(uv)
            out.append(mapping[key])
        face32=tuple(out)
        ab,ac,_=triangle(positions,face32)
        old_ab,old_ac,_=triangle(vertices,face)
        if dot(cross(ab,ac),cross(old_ab,old_ac))<=0:raise ValueError('Float32 would reverse triangle winding')
        expected_faces.append(face32);indices.extend(out)
    binary=bytearray();views=[];accessors=[]
    def add(data,count,typ,component,target,limits=None):
        if len(binary)%4:raise ValueError('Misaligned binary payload')
        view=len(views);views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data),'target':target})
        binary.extend(data)
        a={'bufferView':view,'byteOffset':0,'componentType':component,'count':count,'type':typ}
        if limits:a.update(min=limits[0],max=limits[1])
        idx=len(accessors);accessors.append(a);return idx
    pos=add(b''.join(struct.pack('<3f',*v) for v in positions),len(positions),'VEC3',5126,34962,
            ([min(v[i] for v in positions) for i in range(3)],[max(v[i] for v in positions) for i in range(3)]))
    attributes={'POSITION':pos}
    if uvs:attributes['TEXCOORD_0']=add(b''.join(struct.pack('<2f',*v) for v in textures),len(textures),'VEC2',5126,34962)
    ia=add(b''.join(struct.pack('<I',i) for i in indices),len(indices),'SCALAR',5125,34963,([min(indices)],[max(indices)]))
    doc={'asset':{'version':'2.0','generator':'JANUS reviewed mesh conversion'},
         'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
         'meshes':[{'primitives':[{'attributes':attributes,'indices':ia,'mode':4}]}],
         'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
    encoded=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    payload=(struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))
             +struct.pack('<II',len(encoded),0x4e4f534a)+encoded
             +struct.pack('<II',len(binary),0x004e4942)+bytes(binary))
    glb(payload,max_json=1024*1024,max_chunks=2)
    # Reopen the actual emitted bytes: validate the document and decode the
    # exact accessor views, not merely the objects used to generate them.
    jl,jk=struct.unpack_from('<II',payload,12);parsed=json.loads(payload[20:20+jl])
    off=20+jl;bl,bk=struct.unpack_from('<II',payload,off);data=payload[off+8:]
    if jk!=0x4e4f534a or bk!=0x004e4942 or bl!=len(data) or parsed!=doc:raise ValueError('GLB roundtrip document mismatch')
    def read_accessor(i,fmt):
        a=parsed['accessors'][i];v=parsed['bufferViews'][a['bufferView']]
        start=v['byteOffset']+a['byteOffset'];end=start+v['byteLength']
        stride=struct.calcsize(fmt)
        if end>len(data) or v['byteLength']!=a['count']*stride:raise ValueError('GLB accessor extent mismatch')
        return list(struct.iter_unpack(fmt,data[start:end]))
    read_pos=read_accessor(pos,'<3f')
    read_indices=[v[0] for v in read_accessor(ia,'<I')]
    if read_pos!=positions or read_indices!=indices or any(i>=len(read_pos) for i in read_indices):
        raise ValueError('GLB vertex/index roundtrip mismatch')
    if uvs and read_accessor(attributes['TEXCOORD_0'],'<2f')!=textures:raise ValueError('GLB UV roundtrip mismatch')
    if [tuple(read_indices[i:i+3]) for i in range(0,len(read_indices),3)]!=expected_faces:raise ValueError('Triangle order changed')
    return payload,{'source_vertices':len(vertices),'output_vertices':len(positions),'triangles':len(faces),
        'source_unused_vertices':len(vertices)-len({i for f in faces for i in f}),
        'uvs_preserved':bool(uvs),'uv_v_axis_flipped':bool(uvs),'maximum_position_error':worst,'maximum_uv_error':worst_uv if uvs else None,
        'source_sha256':hashlib.sha256(raw).hexdigest(),'geometry_roundtrip_verified':True,
        'surviving_winding_checked':True,'axis_conversion_applied':False,'render_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
    _,_,path=validate(root,plan);v,f,u,_=parse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),allow_uv=True)
    return plan,dict(spec,source_vertices=len(v),triangles=len(f),has_uvs=bool(u),
                    scope='Static OBJ to embedded GLB; unchanged geometric axes, UV V flip; no materials, normals or animation.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=convert(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-mesh-conversion-result-v1','status':'glb_geometry_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'GLB conversion unavailable; inspect OBJ geometry, UVs and reviewed precision'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
