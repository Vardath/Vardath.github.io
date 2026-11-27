"""Reviewed conservative repair of plain triangular OBJ."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mesh_geometry import numeric,index,triangle,encode,parse
from deepthort_local.mesh_retopology import incidence,MAX_FACES
from deepthort_local.artifact_media_checks import obj

SCHEMA='janus-mesh-repair-v1'
EXTRA=('mesh','.obj')
MAX_VERTICES=10000

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'mesh'} or not isinstance(spec['mesh'],str):
        raise ValueError('Expected project-relative plain triangular OBJ')
    return spec

def read_mesh(raw):
    # Admit defective faces for cleanup, but do not discard unsupported attributes.
    if not raw or len(raw)>guard.MAX_INPUT:raise ValueError('OBJ outside byte bound')
    vertices=[];faces=[]
    for line in raw.decode('utf-8-sig').splitlines():
        if len(line)>512:raise ValueError('OBJ line outside bound')
        parts=line.split('#',1)[0].split()
        if not parts:continue
        kind,*values=parts
        if kind=='v':
            if len(vertices)>=MAX_VERTICES:raise ValueError('Vertex bound exceeded')
            vertices.append(numeric(values,3,1e6))
        elif kind=='f':
            if len(faces)>=MAX_FACES or len(values)!=3:raise ValueError('Use bounded triangular OBJ')
            faces.append(tuple(index(v,len(vertices)) for v in values))
        else:raise ValueError('Only plain v/f records supported')
    if not vertices or not faces:raise ValueError('Mesh needs vertices and faces')
    return vertices,faces

def orient(faces):
    edges={}
    for i,f in enumerate(faces):
        for a,b in zip(f,f[1:]+f[:1]):
            entries=edges.setdefault((min(a,b),max(a,b)),[])
            entries.append((i,a<b))
            if len(entries)>2:raise ValueError('Nonmanifold edge requires manual repair')
    links=[[] for _ in faces]
    for records in edges.values():
        if len(records)==2:
            (i,di),(j,dj)=records
            links[i].append((j,di==dj));links[j].append((i,di==dj))
    flags={};components=0
    for start in range(len(faces)):
        if start in flags:continue
        components+=1;flags[start]=False;queue=deque([start])
        while queue:
            i=queue.popleft()
            for j,flip in links[i]:
                expected=flags[i]^flip
                if j in flags:
                    if flags[j]!=expected:raise ValueError('Nonorientable surface requires manual repair')
                else:flags[j]=expected;queue.append(j)
    out=[(f[0],f[2],f[1]) if flags[i] else f for i,f in enumerate(faces)]
    edges=incidence(out)
    return out,sum(flags.values()),components,sum(len(x)==1 for x in edges.values())

def repair(raw,spec):
    checked(spec);vertices,faces=read_mesh(raw)
    unique=[];mapping=[];lookup={}
    for v in vertices:
        if v not in lookup:
            lookup[v]=len(unique);unique.append(v)
        mapping.append(lookup[v])
    retained=[];seen=set();degenerate=duplicates=0
    for face in faces:
        f=tuple(mapping[i] for i in face)
        try:triangle(unique,f)
        except ValueError:degenerate+=1;continue
        key=tuple(sorted(f))
        if key in seen:duplicates+=1;continue
        seen.add(key);retained.append(f)
    if not retained:raise ValueError('No valid triangles remain')
    oriented,flips,components,boundaries=orient(retained)
    used=sorted({i for f in oriented for i in f})
    remap={i:j for j,i in enumerate(used)}
    out_v=[unique[i] for i in used]
    out_f=[tuple(remap[i] for i in f) for f in oriented]
    payload=encode(out_v,out_f);obj(payload)
    v,f,_,_=parse(payload);verified_edges=incidence(f)
    if (v,f)!=(out_v,out_f) or len(f)+degenerate+duplicates!=len(faces):
        raise ValueError('Repair output reconciliation failed')
    if sum(len(x)==1 for x in verified_edges.values())!=boundaries:
        raise ValueError('Boundary reconciliation failed')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),
        'source_vertices':len(vertices),'source_triangles':len(faces),
        'output_vertices':len(v),'output_triangles':len(f),
        'exact_duplicate_vertices_welded':len(vertices)-len(unique),
        'unused_vertices_removed':len(unique)-len(v),'degenerate_triangles_removed':degenerate,
        'duplicate_triangles_removed':duplicates,'winding_flips':flips,'face_components':components,
        'remaining_boundary_edges':boundaries,'manifold_edges_and_vertex_fans_checked':True,
        'geometry_roundtrip_verified':True,'watertight_edge_topology':boundaries==0,
        'self_intersections_checked':False,'outward_orientation_verified':False,
        'render_verified':False,'scope':'Exact coordinate weld and triangle cleanup, consistent winding only; no hole filling, self-intersection repair or attribute preservation.'}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    _,_,path=validate(root,plan)
    v,f=read_mesh(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,source_vertices=len(v),source_triangles=len(f),
        scope='Exact vertex welding, remove invalid/duplicate triangles and correct relative winding; reject unresolved nonmanifold topology.')
def execute(root,plan):
    spec,dst,path=validate(root,plan)
    payload,r=repair(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    changed=any(r[k] for k in ('exact_duplicate_vertices_welded','unused_vertices_removed','degenerate_triangles_removed','duplicate_triangles_removed','winding_flips'))
    return {'schema':'janus-mesh-repair-result-v1','status':'mesh_cleanup_verified' if changed else 'no_eligible_repair',
        'output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid input or unresolved mesh topology; inspect source and reviewed output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
