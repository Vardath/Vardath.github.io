"""Reviewed static multi-object glTF scene composition using existing mesh conversion."""
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
from deepthort_local.mesh_conversion import convert
from deepthort_local.artifact_media_checks import glb
SCHEMA='janus-scene-composition-v1'
MAX_OBJECTS=6
MAX_TOTAL_INPUT=16*1024*1024
def number(x,lo,hi):return type(x) in (int,float) and math.isfinite(x) and lo<=x<=hi
def vector(x,n,lo,hi):return isinstance(x,list) and len(x)==n and all(number(v,lo,hi) for v in x)
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'objects','max_position_error'} or not number(spec['max_position_error'],1e-12,1):
        raise ValueError('Expected objects and local mesh precision limit')
    objects=spec['objects']
    if not isinstance(objects,list) or not 1<=len(objects)<=MAX_OBJECTS:raise ValueError('Expected 1–6 objects')
    names=set()
    for item in objects:
        if not isinstance(item,dict) or set(item)!={'name','mesh','translation','rotation_xyzw','scale'}:
            raise ValueError('Invalid scene object')
        name=item['name']
        if not isinstance(name,str) or not 1<=len(name)<=64 or not name.strip() or any(ord(c)<32 or ord(c)>126 for c in name) or name.casefold() in names:
            raise ValueError('Use distinct bounded ASCII object names')
        names.add(name.casefold())
        if not isinstance(item['mesh'],str) or not vector(item['translation'],3,-10000,10000) or not vector(item['scale'],3,.001,1000):
            raise ValueError('Invalid object path or transform')
        q=item['rotation_xyzw']
        if not vector(q,4,-1,1) or not math.isclose(math.sqrt(sum(v*v for v in q)),1,rel_tol=0,abs_tol=1e-6):
            raise ValueError('Provide normalized XYZW rotation quaternion')
    return spec
def decode(payload):
    glb(payload,max_json=1024*1024,max_chunks=2)
    jl,jk=struct.unpack_from('<II',payload,12)
    doc=json.loads(payload[20:20+jl]);offset=20+jl
    bl,bk=struct.unpack_from('<II',payload,offset);data=payload[offset+8:]
    if jk!=0x4e4f534a or bk!=0x004e4942 or bl!=len(data):raise ValueError('Invalid embedded scene')
    return doc,data
def compose(raws,spec):
    checked(spec);objects=spec['objects']
    if len(raws)!=len(objects) or sum(len(r) for r in raws)>MAX_TOTAL_INPUT:raise ValueError('Scene input bound exceeded')
    binary=bytearray();views=[];accessors=[];meshes=[];nodes=[];records=[];segments=[]
    triangles=0;vertex_count=0
    for raw,item in zip(raws,objects):
        # Reuse exact existing local geometry and UV/float32 checks.
        payload,receipt=convert(raw,{'mesh':item['mesh'],'max_position_error':spec['max_position_error']})
        doc,data=decode(payload)
        triangles+=receipt['triangles'];vertex_count+=receipt['output_vertices']
        if triangles>20000 or vertex_count>40000:raise ValueError('Combined scene geometry exceeds bound')
        base=len(binary);view_base=len(views);accessor_base=len(accessors)
        binary.extend(data);segments.append((base,data))
        views.extend(dict(v,byteOffset=v.get('byteOffset',0)+base) for v in doc['bufferViews'])
        accessors.extend(dict(a,bufferView=a['bufferView']+view_base) for a in doc['accessors'])
        p=doc['meshes'][0]['primitives'][0]
        attrs={k:v+accessor_base for k,v in p['attributes'].items()}
        meshes.append({'name':item['name'],'primitives':[dict(p,attributes=attrs,indices=p['indices']+accessor_base)]})
        q=item['rotation_xyzw'];length=math.sqrt(sum(v*v for v in q))
        node={'name':item['name'],'mesh':len(meshes)-1,'translation':item['translation'],
              'rotation':[v/length for v in q],'scale':item['scale']}
        nodes.append(node)
        records.append({'name':item['name'],'mesh':item['mesh'],'source_sha256':receipt['source_sha256'],
            'triangles':receipt['triangles'],'vertices':receipt['output_vertices'],'uvs_preserved':receipt['uvs_preserved'],
            'maximum_local_position_error':receipt['maximum_position_error'],'transform':node})
    doc={'asset':{'version':'2.0','generator':'JANUS reviewed scene composition'},'scene':0,
        'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':meshes,
        'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
    encoded=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    payload=(struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))+
        struct.pack('<II',len(encoded),0x4e4f534a)+encoded+
        struct.pack('<II',len(binary),0x004e4942)+bytes(binary))
    parsed,data=decode(payload)
    if parsed!=doc or any(data[start:start+len(part)]!=part for start,part in segments):
        raise ValueError('Scene document or geometry segments changed')
    # Verify each independently converted accessor now resolves within its own segment.
    for mesh,(start,part) in zip(parsed['meshes'],segments):
        p=mesh['primitives'][0]
        for i in [p['indices'],*p['attributes'].values()]:
            a=parsed['accessors'][i];v=parsed['bufferViews'][a['bufferView']]
            if not start<=v['byteOffset'] or v['byteOffset']+v['byteLength']>start+len(part):
                raise ValueError('Scene accessor points outside its object geometry')
    return payload,{'objects':records,'object_count':len(nodes),'triangles':triangles,'vertices':vertex_count,
        'node_transforms_verified':True,'geometry_segments_verified':True,'editable_separate_nodes':True,
        'axis_conversion_applied':False,'collision_checked':False,'render_verified':False,
        'scope':'Separate static mesh nodes with explicit TRS and retained local UVs; no materials, lighting, collision or animation.'}
def paths_for(root,spec,exclude):
    paths=[guard.path_for(root,item['mesh'],exclude,{'.obj'},exists=True) for item in spec['objects']]
    if sum(p.stat().st_size for p in paths)>MAX_TOTAL_INPUT:raise ValueError('Scene source bytes exceed bound')
    return paths
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 2<=len(plan['guards'])<=MAX_OBJECTS+1:
        raise ValueError('Invalid scene approval')
    spec,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.glb')
    paths=paths_for(Path(root).resolve(strict=True),spec,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed scene mesh changed')
    return spec,dst,paths
def raws_for(paths,plan):return [guard.exact(p,g,MAX_TOTAL_INPUT) for p,g in zip(paths,plan['guards'][1:])]
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb')
    paths=paths_for(Path(plan['root']),spec,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in paths)
    spec,_,paths=validate(root,plan)
    return plan,dict(spec,scope='Separate static GLB mesh nodes; transforms, geometry and UVs checked; no render or collision acceptance.')
def execute(root,plan):
    spec,dst,paths=validate(root,plan);payload,r=compose(raws_for(paths,plan),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-scene-composition-result-v1','status':'static_scene_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed mesh, transform or scene output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
