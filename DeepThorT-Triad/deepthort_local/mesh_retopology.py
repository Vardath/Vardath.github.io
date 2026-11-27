"""Bounded topology-aware planar edge flips for strict triangular OBJ."""
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

SCHEMA='janus-mesh-retopology-v1'
EXTRA=('mesh','.obj')
MAX_FACES=10000
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'mesh','passes','min_quality_gain'} or not isinstance(spec['mesh'],str):
        raise ValueError('Expected triangular OBJ and bounded planar edge-flip settings')
    if type(spec['passes']) is not int or not 1<=spec['passes']<=5:raise ValueError('Pass count outside bound')
    g=spec['min_quality_gain']
    if type(g) not in (int,float) or not math.isfinite(g) or not .0001<=g<=.25:raise ValueError('Quality gain outside bound')
    return spec
def edge(a,b):return (min(a,b),max(a,b))
def incidence(faces):
    if len(faces)>MAX_FACES:raise ValueError('Retopology face bound exceeded')
    edges={};seen=set()
    for i,f in enumerate(faces):
        key=tuple(sorted(f))
        if key in seen:raise ValueError('Duplicate triangles; repair mesh first')
        seen.add(key)
        for j in range(3):
            a,b=f[j],f[(j+1)%3]
            k=edge(a,b);edges.setdefault(k,[]).append((i,a,b,f[(j+2)%3]))
    for records in edges.values():
        if len(records)>2 or (len(records)==2 and records[0][1:3]!=records[1][1:3][::-1]):
            raise ValueError('Nonmanifold edge or inconsistent winding; repair first')
    # Reject bow-tie vertices: each incident face fan must be connected.
    fans={}
    for idx,f in enumerate(faces):
        for v in f:fans.setdefault(v,set()).add(idx)
    adjacency={v:{} for v in fans}
    for (a,b),records in edges.items():
        if len(records)==2:
            i,j=records[0][0],records[1][0]
            for v in (a,b):
                adjacency[v].setdefault(i,set()).add(j);adjacency[v].setdefault(j,set()).add(i)
    for v,ids in fans.items():
        start=next(iter(ids));visited={start};stack=[start]
        while stack:
            for j in adjacency[v].get(stack.pop(),()):
                if j not in visited:visited.add(j);stack.append(j)
        if visited!=ids:raise ValueError('Disconnected vertex fan; repair first')
    return edges
def quality(vertices,f):
    a,b,c=(vertices[i] for i in f);ab,ac,area=triangle(vertices,f)
    return 2*math.sqrt(3)*area/(dot(ab,ab)+dot(ac,ac)+dot(sub(c,b),sub(c,b)))
def propose(vertices,faces,edges,records,gain):
    (i,a,b,c),(j,_,_,d)=records
    if c==d or edge(c,d) in edges:return None
    old1,old2=faces[i],faces[j]
    new1,new2=(c,a,d),(c,d,b)
    ab,ac,area=triangle(vertices,old1);normal=cross(ab,ac)
    extent=max(norm(sub(vertices[x],vertices[y])) for x in (a,b,c,d) for y in (a,b,c,d))
    # Exact planar profile within conservative floating-point relative tolerance.
    if abs(dot(normal,sub(vertices[d],vertices[a])))>area*extent*1e-10:return None
    try:
        na,nb,area1=triangle(vertices,new1);nc,nd,area2=triangle(vertices,new2)
        ea,eb,old_area2=triangle(vertices,old2)
    except ValueError:return None
    if any(dot(normal,n)<=0 for n in (cross(na,nb),cross(nc,nd),cross(ea,eb))):return None
    if abs(area1+area2-area-old_area2)>1e-9*(area+old_area2):return None
    before=min(quality(vertices,old1),quality(vertices,old2))
    after=min(quality(vertices,new1),quality(vertices,new2))
    if after-before<gain:return None
    return i,j,new1,new2
def retopologize(raw,spec):
    spec=checked(spec);vertices,faces,_,_=parse(raw)
    edges=incidence(faces);original_boundary={e for e,v in edges.items() if len(v)==1}
    original_edges=len(edges);initial=min(quality(vertices,f) for f in faces)
    flips=0
    for _ in range(spec['passes']):
        # Disjoint face flips with reserved new diagonals in one deterministic sweep.
        # Rebuild topology at each pass rather than use stale neighbor incidence.
        edges=incidence(faces);changed=set();reserved=set();count=0
        for key,records in sorted(edges.items()):
            if len(records)!=2 or any(r[0] in changed for r in records):continue
            pair=propose(vertices,faces,edges,records,spec['min_quality_gain'])
            if pair is None:continue
            i,j,f,g=pair;diagonal=edge(records[0][3],records[1][3])
            if diagonal in reserved:continue
            faces[i]=f;faces[j]=g;changed.update((i,j));reserved.add(diagonal);count+=1
        flips+=count
        if not count:break
    final_edges=incidence(faces)
    if len(final_edges)!=original_edges or {e for e,v in final_edges.items() if len(v)==1}!=original_boundary:
        raise ValueError('Boundary or edge count changed')
    final=min(quality(vertices,f) for f in faces)
    if final+1e-12<initial:raise ValueError('Triangle quality regressed')
    payload=encode(vertices,faces);obj(payload)
    v,f,_,_=parse(payload)
    if v!=vertices or f!=faces:raise ValueError('Mesh roundtrip failed')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),'vertices':len(v),'triangles':len(f),
        'edges':len(final_edges),'boundary_edges':len(original_boundary),'flipped_edges':flips,
        'minimum_triangle_quality_before':initial,'minimum_triangle_quality_after':final,
        'boundary_preserved':True,'manifold_vertex_fans_checked':True,'geometry_roundtrip_verified':True,
        'quad_retopology_verified':False,'animation_topology_verified':False,'render_verified':False,
        'scope':'Planar local edge flips only; no quad remeshing, curved-surface remeshing, UV or rig preservation.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    _,_,path=validate(root,plan);v,f,_,_=parse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT));incidence(f)
    return plan,dict(spec,vertices=len(v),triangles=len(f),scope='Improve planar triangular connectivity while preserving positions and boundary; not general retopology.')
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=retopologize(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-mesh-retopology-result-v1','status':'planar_retopology_verified' if r['flipped_edges'] else 'no_eligible_edge_flip',
        'output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid mesh, connectivity or reviewed output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
