"""Deterministic bounded vertex-cluster simplification of plain triangular OBJ."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mesh_geometry import parse,encode,triangle,sub,cross,dot,norm
from deepthort_local.artifact_media_checks import obj
SCHEMA='janus-mesh-simplification-v1'
EXTRA=('mesh','.obj')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'mesh','cell_size','max_displacement'} or not isinstance(spec['mesh'],str):
        raise ValueError('Expected plain triangular OBJ, cell size and maximum vertex displacement')
    for k in ('cell_size','max_displacement'):
        v=spec[k]
        if type(v) not in (int,float) or not math.isfinite(v) or not 1e-6<=v<=1e6:
            raise ValueError('Invalid mesh simplification distance')
    return spec
def simplify(raw,spec):
    vertices,faces,_,_=parse(raw)
    cells={};representatives=[];mapping=[];worst=0.0
    size=spec['cell_size']
    for v in vertices:
        cell=tuple(math.floor(x/size) for x in v)
        if cell not in cells:
            cells[cell]=len(representatives);representatives.append(v)
        i=cells[cell];distance=norm(sub(v,representatives[i]))
        if distance>spec['max_displacement']:raise ValueError('Cluster exceeds reviewed maximum vertex displacement')
        worst=max(worst,distance);mapping.append(i)
    surviving=[];seen=set();collapsed=duplicate=0
    for old in faces:
        new=tuple(mapping[i] for i in old)
        if len(set(new))<3:
            collapsed+=1;continue
        try:ab,ac,_=triangle(representatives,new)
        except ValueError:
            collapsed+=1;continue
        old_ab,old_ac,_=triangle(vertices,old)
        if dot(cross(old_ab,old_ac),cross(ab,ac))<=0:
            raise ValueError('Simplification would reverse a surviving triangle')
        key=tuple(sorted(new))
        if key in seen:
            duplicate+=1;continue
        seen.add(key);surviving.append(new)
    if not surviving:raise ValueError('Simplification removes every triangle')
    used=sorted({i for f in surviving for i in f});compact={i:k for k,i in enumerate(used)}
    out_v=[representatives[i] for i in used];out_f=[tuple(compact[i] for i in f) for f in surviving]
    payload=encode(out_v,out_f);obj(payload)
    v,f,_,_=parse(payload)
    if (v,f)!=(out_v,out_f) or len(f)+collapsed+duplicate!=len(faces):
        raise ValueError('Simplified mesh reconciliation failed')
    return payload,{'source_vertices':len(vertices),'source_triangles':len(faces),'output_vertices':len(v),'output_triangles':len(f),
        'collapsed_triangles':collapsed,'duplicate_triangles_removed':duplicate,
        'maximum_cluster_displacement':worst,'reviewed_maximum_displacement':spec['max_displacement'],
        'triangle_reduction_fraction':(len(faces)-len(f))/len(faces),
        'source_sha256':hashlib.sha256(raw).hexdigest(),'geometry_roundtrip_verified':True,
        'surviving_winding_checked':True,'topology_preservation_verified':False,'render_verified':False}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    _,_,path=validate(root,plan);v,f,_,_=parse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_vertices=len(v),source_triangles=len(f),
                    scope='Vertex clustering; collapsed and duplicate triangles removed. Topology and surface error are not guaranteed.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=simplify(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    status='mesh_reduction_verified' if r['output_triangles']<r['source_triangles'] or r['output_vertices']<r['source_vertices'] else 'mesh_no_reduction'
    return {'schema':'janus-mesh-simplification-result-v1','status':status,'output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Mesh simplification unavailable; inspect OBJ geometry, clustering and maximum displacement'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
