"""Automatic nonoverlapping per-triangle UV atlas for plain static OBJ meshes."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mesh_geometry import parse,encode,triangle,dot,norm
from deepthort_local.artifact_media_checks import obj
SCHEMA='janus-uv-unwrapping-v1'
EXTRA=('mesh','.obj')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'mesh','tile_margin'} or not isinstance(spec['mesh'],str):
        raise ValueError('Expected plain triangulated OBJ and explicit per-tile margin')
    m=spec['tile_margin']
    if type(m) not in (int,float) or not math.isfinite(m) or not .01<=m<=.25:
        raise ValueError('Margin must be 0.01–0.25 of a tile')
    return spec
def unwrap(raw,spec):
    vertices,faces,_,_=parse(raw)
    grid=math.ceil(math.sqrt(len(faces)));margin=spec['tile_margin']
    uvs=[];uvfaces=[]
    for i,face in enumerate(faces):
        ab,ac,area2=triangle(vertices,face)
        length=norm(ab);coords=((0.0,0.0),(length,0.0),(dot(ab,ac)/length,area2/length))
        lo=min(u for u,v in coords);hi=max(u for u,v in coords);height=coords[2][1]
        size=max(hi-lo,height)
        col=i%grid;row=i//grid
        scale=(1-2*margin)/size
        # One independent tile per face; keep its shape without UV distortion within the island.
        base=len(uvs)
        for u,v in coords:
            uv=((col+margin+(u-lo)*scale)/grid,(row+margin+v*scale)/grid)
            if not col/grid<uv[0]<(col+1)/grid or not row/grid<uv[1]<(row+1)/grid:
                raise ValueError('UV tile containment failed')
            uvs.append(uv)
        uvfaces.append((base,base+1,base+2))
        a,b,c=uvs[-3:]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<=0:
            raise ValueError('UV triangle has invalid orientation or area')
    payload=encode(vertices,faces,uvs,uvfaces);obj(payload)
    v,f,u,uf=parse(payload,allow_uv=True)
    if v!=vertices or f!=faces or len(u)!=3*len(f) or len(uf)!=len(f):raise ValueError('UV mesh geometry changed')
    return payload,{'vertices':len(v),'triangles':len(f),'uv_coordinates':len(u),'atlas_grid':grid,
                    'islands':len(f),'tile_margin':margin,'source_sha256':hashlib.sha256(raw).hexdigest(),
                    'geometry_preserved':True,'nonoverlapping_tiles_verified':True,'render_verified':False,
                    'scope':'Each triangle is an independent island; no seam optimisation or uniform texel density.'}
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
    _,_,path=validate(root,plan);v,f,_,_=parse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT))
    return plan,dict(spec,vertices=len(v),triangles=len(f),atlas_grid=math.ceil(math.sqrt(len(f))),
                    scope='Plain static triangles only; one independent island per triangle.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.obj',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);payload,r=unwrap(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-uv-unwrapping-result-v1','status':'uv_atlas_verified','output':plan['output'],'sha256':sha,**r,'source_unchanged':True}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'UV unwrap unavailable; inspect plain triangle OBJ and margin'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
