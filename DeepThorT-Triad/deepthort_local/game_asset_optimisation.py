"""Reviewed bounded candidate search for static game mesh budgets."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import mesh_simplification as simple,mesh_conversion as convert
from deepthort_local.mesh_geometry import parse
from deepthort_local.mesh_retopology import incidence,MAX_FACES
SCHEMA='janus-game-asset-optimisation-v1'
EXTRA=('mesh','.obj')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'mesh','triangle_budget','vertex_budget','cell_sizes','max_displacement','max_position_error','preserve_boundary'} or not isinstance(s['mesh'],str):
        raise ValueError('Expected mesh, budgets and bounded optimisation settings')
    if type(s['triangle_budget']) is not int or not 1<=s['triangle_budget']<=MAX_FACES or type(s['vertex_budget']) is not int or not 3<=s['vertex_budget']<=20000 or type(s['preserve_boundary']) is not bool:
        raise ValueError('Invalid mesh budgets')
    sizes=s['cell_sizes']
    if not isinstance(sizes,list) or not 1<=len(sizes)<=8:raise ValueError('Provide 1–8 candidate cell sizes')
    for size in sizes:simple.checked({'mesh':s['mesh'],'cell_size':size,'max_displacement':s['max_displacement']})
    if len(set(sizes))!=len(sizes):raise ValueError('Duplicate cell sizes')
    convert.checked({'mesh':s['mesh'],'max_position_error':s['max_position_error']})
    return s

def boundary(v,edges):
    return {tuple(sorted((v[a],v[b]))) for (a,b),records in edges.items() if len(records)==1}

def optimise(raw,s):
    checked(s);v,f,_,_=parse(raw);edges=incidence(f)
    before=boundary(v,edges)
    candidates=[];attempts=[]
    def consider(mesh,cell,displacement):
        cv,cf,_,_=parse(mesh);ce=incidence(cf)
        preserved=boundary(cv,ce)==before
        if len(cf)>s['triangle_budget'] or len(cv)>s['vertex_budget']:
            raise ValueError('Budget not met')
        if s['preserve_boundary'] and not preserved:raise ValueError('Boundary changed')
        payload,report=convert.convert(mesh,{'mesh':s['mesh'],'max_position_error':s['max_position_error']})
        if report['triangles']>s['triangle_budget'] or report['output_vertices']>s['vertex_budget']:
            raise ValueError('Export budget not met')
        # Recheck the actual quantized positions and face topology in the GLB.
        from deepthort_local.scene_composition import decode
        from deepthort_local.automated_rendering import accessor
        d,b=decode(payload);p=d['meshes'][0]['primitives'][0]
        ev=accessor(d,b,p['attributes']['POSITION'],'<3f')
        ix=[x[0] for x in accessor(d,b,p['indices'],'<I')]
        ef=[tuple(ix[i:i+3]) for i in range(0,len(ix),3)]
        ee=incidence(ef)
        if s['preserve_boundary'] and boundary(ev,ee)!=before:
            raise ValueError('Float32 export changed exact requested boundary')
        candidates.append((displacement,-len(cf),cell,payload,report,preserved))
    if len(f)<=s['triangle_budget'] and len(v)<=s['vertex_budget']:
        try:consider(raw,0,0.0)
        except ValueError:attempts.append({'cell_size':0,'accepted':False})
        else:attempts.append({'cell_size':0,'accepted':True})
    if not candidates:
        for size in sorted(s['cell_sizes']):
            try:
                mesh,r=simple.simplify(raw,{'mesh':s['mesh'],'cell_size':size,'max_displacement':s['max_displacement']})
                consider(mesh,size,r['maximum_cluster_displacement'])
            except ValueError:attempts.append({'cell_size':size,'accepted':False})
            else:attempts.append({'cell_size':size,'accepted':True})
    if not candidates:raise ValueError('No candidate met reviewed geometry and budget requirements')
    displacement,_,size,payload,r,preserved=min(candidates,key=lambda x:x[:3])
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),'source_vertices':len(v),'source_triangles':len(f),
        'output_vertices':r['output_vertices'],'output_triangles':r['triangles'],'triangle_budget':s['triangle_budget'],
        'vertex_budget':s['vertex_budget'],'selected_cell_size':size,'candidate_attempts':attempts,
        'maximum_cluster_displacement':displacement,'maximum_export_position_error':r['maximum_position_error'],
        'source_and_export_manifold_checked':True,'exact_source_boundary_preserved_before_float32':preserved,
        'exact_export_boundary_required':s['preserve_boundary'],'budget_verified':True,'geometry_roundtrip_verified':True,
        'surface_error_verified':False,'topology_equivalence_verified':False,'game_engine_import_verified':False,
        'scope':'Static plain triangle geometry only; no UV, material, rig, collider, engine performance or visual-quality claim.'}

def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
    _,_,path=validate(root,plan);v,f,_,_=parse(guard.exact(path,plan['guards'][1],guard.MAX_INPUT));incidence(f)
    return plan,dict(s,source_vertices=len(v),source_triangles=len(f),scope='Bounded candidate search and static GLB budgets; not engine acceptance.')
def execute(root,plan):
    s,dst,path=validate(root,plan);payload,r=optimise(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-game-asset-optimisation-result-v1','status':'static_asset_budget_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid mesh or no reviewed candidate met asset budgets'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
