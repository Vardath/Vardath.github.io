"""Bounded convex parametric CAD extrusion: editable OpenSCAD and verified OBJ."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.mesh_geometry import encode,parse,sub,cross,dot
from deepthort_local.mesh_retopology import incidence
from deepthort_local.artifact_media_checks import obj
SCHEMA='janus-parametric-cad-v1'
def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'polygon','height_mm'}:raise ValueError('Expected polygon and extrusion height')
    p=spec['polygon'];h=spec['height_mm']
    if type(h) not in (int,float) or not math.isfinite(h) or not .01<=h<=10000:
        raise ValueError('Height outside bound')
    if not isinstance(p,list) or not 3<=len(p)<=128:raise ValueError('Use 3–128 convex polygon points')
    for v in p:
        if not isinstance(v,list) or len(v)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>10000 for x in v):
            raise ValueError('Invalid millimetre coordinates')
    if len({tuple(v) for v in p})!=len(p):raise ValueError('Duplicate polygon points')
    # Every other point must lie strictly to the left of every ordered edge.
    # This rejects concavity, self-intersections and collinear boundary vertices.
    n=len(p)
    for i in range(n):
        a,b=p[i],p[(i+1)%n]
        for j,c in enumerate(p):
            if j not in (i,(i+1)%n) and turn(a,b,c)<=1e-8:
                raise ValueError('Use strictly convex counterclockwise polygon')
    return spec
def produce(spec):
    spec=checked(spec);p=spec['polygon'];h=spec['height_mm'];n=len(p)
    vertices=[(float(x),float(y),z) for z in (0.,float(h)) for x,y in p]
    faces=[]
    for i in range(1,n-1):
        faces.extend([(0,i+1,i),(n,n+i,n+i+1)])
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,n+j),(i,n+j,n+i)])
    mesh=encode(vertices,faces);obj(mesh)
    v,f,_,_=parse(mesh)
    edges=incidence(f)
    if (v,f)!=(vertices,faces) or any(len(r)!=2 for r in edges.values()) or len(v)-len(edges)+len(f)!=2:
        raise ValueError('Closed solid geometry verification failed')
    area=math.fsum(turn(p[0],p[i],p[i+1])/2 for i in range(1,n-1))
    origin=v[0]
    volume=math.fsum(dot(sub(v[a],origin),cross(sub(v[b],origin),sub(v[c],origin)))/6 for a,b,c in f)
    if not math.isclose(volume,area*h,rel_tol=1e-9,abs_tol=1e-10):raise ValueError('Solid volume mismatch')
    # Numeric-only source template; no arbitrary user code or command execution.
    fmt=lambda x:format(x,'.17g')
    points=', '.join('['+fmt(x)+', '+fmt(y)+']' for x,y in p)
    scad=('// JANUS parametric extrusion; coordinates in millimetres\nheight = '+fmt(h)+';\nprofile = ['+points+'];\nlinear_extrude(height=height, convexity=2) polygon(points=profile);\n').encode('ascii')
    receipt={'schema':'janus-parametric-cad-result-v1','units':'mm','vertices':len(v),'triangles':len(f),
        'height_mm':h,'profile_area_mm2':area,'verified_mesh_volume_mm3':volume,
        'closed_oriented_mesh_verified':True,'editable_scad_source':True,'native_cad_import_verified':False,
        'native_scad_execution_verified':False,'manufacturing_tolerance_verified':False,
        'mesh_sha256':hashlib.sha256(mesh).hexdigest(),'scad_sha256':hashlib.sha256(scad).hexdigest()}
    files={'design.scad':scad,'design.obj':mesh,'receipt.json':json.dumps(receipt,sort_keys=True,allow_nan=False).encode('utf-8')}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr(name,data)
    payload=stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.namelist()!=list(files) or z.testzip() is not None or any(z.read(k)!=v for k,v in files.items()):
            raise ValueError('CAD bundle roundtrip failed')
    return payload,receipt
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip')
    return plan,dict(spec,scope='Editable OpenSCAD convex extrusion and independently generated closed triangular OBJ; no native CAD execution.')
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip')
def execute(root,plan):
    spec,dst,_=validate(root,plan);payload,r=produce(spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'cad_bundle_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid convex CAD specification or reviewed output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
