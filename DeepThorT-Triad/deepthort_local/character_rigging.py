"""Reviewed static mesh skinning from an explicit joint hierarchy."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import mesh_conversion as converter,scene_composition as scene
from deepthort_local.mesh_geometry import dot,sub
from deepthort_local.automated_rendering import accessor
SCHEMA='janus-character-rigging-v1'
EXTRA=('mesh','.obj')
MAX_JOINTS=32
MAX_VERTICES=20000

def checked(s):
    if not isinstance(s,dict) or set(s)!={'mesh','max_position_error','joints'}:raise ValueError('Expected mesh and reviewed rest skeleton')
    converter.checked({'mesh':s['mesh'],'max_position_error':s['max_position_error']})
    joints=s['joints']
    if not isinstance(joints,list) or not 2<=len(joints)<=MAX_JOINTS:raise ValueError('Use 2–32 joints')
    names=set();positions=[]
    for i,j in enumerate(joints):
        if not isinstance(j,dict) or set(j)!={'name','parent','position'}:raise ValueError('Invalid joint record')
        name=j['name'];parent=j['parent']
        if not isinstance(name,str) or not 1<=len(name)<=64 or not name.strip() or any(not 32<=ord(c)<=126 for c in name) or name.casefold() in names:
            raise ValueError('Use unique bounded joint names')
        names.add(name.casefold())
        if (i==0 and parent is not None) or (i>0 and (type(parent) is not int or not 0<=parent<i)):
            raise ValueError('Single root and earlier parent indices required')
        if not scene.vector(j['position'],3,-1e6,1e6):raise ValueError('Invalid rest joint position')
        p=converter.floats32(j['position'])
        if p in positions:raise ValueError('Coincident rest joints after float32 conversion')
        positions.append(p)
    return s
def distance2(a,b):
    d=sub(a,b);return dot(d,d)
def weights(v,positions):
    ranked=sorted((distance2(v,p),i) for i,p in enumerate(positions))
    (d0,i),(d1,j)=ranked[:2]
    if d0==0:
        return (i,0,0,0),(1.,0.,0.,0.)
    # Inverse squared distance to nearest two joint positions, no geodesic model.
    first=d1/(d0+d1)
    a,b=converter.floats32((first,1-first))
    if not math.isclose(a+b,1.,abs_tol=1e-7,rel_tol=0):raise ValueError('Skin weights not normalized')
    return (i,j,0,0),(a,b,0.,0.)
def rig(raw,s):
    checked(s);payload,r=converter.convert(raw,{'mesh':s['mesh'],'max_position_error':s['max_position_error']})
    doc,binary=scene.decode(payload)
    primitive=doc['meshes'][0]['primitives'][0]
    vertices=accessor(doc,binary,primitive['attributes']['POSITION'],'<3f')
    if len(vertices)>MAX_VERTICES:raise ValueError('Skinning vertex limit exceeded')
    positions=[converter.floats32(j['position']) for j in s['joints']]
    if any(math.sqrt(distance2(p,j['position']))>s['max_position_error'] for p,j in zip(positions,s['joints'])):
        raise ValueError('Joint rest position exceeds reviewed precision')
    rows=[weights(v,positions) for v in vertices]
    data=bytearray(binary)
    def append(blob,count,kind,ctype,target=None):
        if len(data)%4:raise ValueError('Unexpected alignment')
        vi=len(doc['bufferViews'])
        view={'buffer':0,'byteOffset':len(data),'byteLength':len(blob)}
        if target is not None:view['target']=target
        doc['bufferViews'].append(view);data.extend(blob)
        ai=len(doc['accessors']);doc['accessors'].append({'bufferView':vi,'byteOffset':0,'componentType':ctype,'count':count,'type':kind})
        return ai
    ji=append(b''.join(struct.pack('<4H',*a) for a,_ in rows),len(rows),'VEC4',5123,34962)
    wi=append(b''.join(struct.pack('<4f',*b) for _,b in rows),len(rows),'VEC4',5126,34962)
    matrices=[(1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,-x,-y,-z,1.) for x,y,z in positions]
    bi=append(b''.join(struct.pack('<16f',*m) for m in matrices),len(matrices),'MAT4',5126)
    primitive['attributes'].update(JOINTS_0=ji,WEIGHTS_0=wi)
    doc['nodes'][0]['skin']=0
    for i,j in enumerate(s['joints']):
        p=positions[i]
        t=p if j['parent'] is None else sub(p,positions[j['parent']])
        doc['nodes'].append({'name':j['name'],'translation':list(t)})
        if j['parent'] is not None:doc['nodes'][j['parent']+1].setdefault('children',[]).append(i+1)
    doc['scenes'][0]['nodes']=[0,1]
    doc['skins']=[{'name':'JANUS reviewed skin','skeleton':1,'joints':list(range(1,len(positions)+1)),'inverseBindMatrices':bi}]
    doc['buffers'][0]['byteLength']=len(data)
    encoded=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    out=(struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(data))+
        struct.pack('<II',len(encoded),0x4e4f534a)+encoded+
        struct.pack('<II',len(data),0x004e4942)+data)
    d,b=scene.decode(out)
    if d!=doc or b[:len(binary)]!=binary:raise ValueError('Rig geometry or document changed')
    indices=accessor(d,b,ji,'<4H');values=accessor(d,b,wi,'<4f');inverse=accessor(d,b,bi,'<16f')
    if indices!=[a for a,_ in rows] or values!=[w for _,w in rows] or inverse!=matrices:
        raise ValueError('Skin accessor roundtrip failed')
    world=[]
    for i,j in enumerate(s['joints']):
        t=d['nodes'][i+1]['translation']
        p=tuple(t) if j['parent'] is None else tuple(a+b for a,b in zip(world[j['parent']],t))
        if not all(math.isclose(a,b,abs_tol=1e-9,rel_tol=0) for a,b in zip(p,positions[i])):raise ValueError('Rest hierarchy mismatch')
        world.append(p)
    if any(any(i>=len(positions) for i in js) or any(not 0<=w<=1 for w in ws) or abs(sum(ws)-1)>1e-7 for js,ws in zip(indices,values)):
        raise ValueError('Invalid skin weight or joint index')
    used=sorted({i for js,ws in zip(indices,values) for i,w in zip(js,ws) if w>0})
    return out,{'source_sha256':r['source_sha256'],'vertices':len(vertices),'triangles':r['triangles'],
        'joint_count':len(positions),'weighted_joints':used,'unweighted_joints':sorted(set(range(len(positions)))-set(used)),
        'weight_method':'inverse squared Euclidean distance to nearest two joint positions',
        'normalized_weights_verified':True,'rest_bind_and_hierarchy_verified':True,'geometry_roundtrip_verified':True,
        'automatic_skeleton_discovery_verified':False,'deformation_quality_verified':False,'native_import_verified':False,
        'scope':'Supplied rest joint hierarchy and automatic spatial skinning; no anatomy, collision-aware/geodesic weights or pose quality.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
    validate(root,plan)
    return plan,dict(s,scope='Reviewed supplied rest skeleton, automatic nearest-two-joint weights; no deformation acceptance.')
def execute(root,plan):
    s,dst,path=validate(root,plan);out,r=rig(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-character-rigging-result-v1','status':'skin_structure_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed mesh, rest skeleton or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
