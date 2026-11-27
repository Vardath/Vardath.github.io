"""Reviewed rotation keyframes on an explicitly supplied skinned hierarchy."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import character_rigging as rig,scene_composition as scene,mesh_conversion as converter
from deepthort_local.automated_rendering import accessor
from deepthort_local.mesh_geometry import dot
SCHEMA='janus-skeletal-animation-v1'
EXTRA=('mesh','.obj')
def rig_spec(s):return {k:s[k] for k in ('mesh','max_position_error','joints')}
def tracks_checked(tracks,joint_count):
    if not isinstance(tracks,list) or not 1<=len(tracks)<=joint_count:raise ValueError('Expected distinct joint tracks')
    seen=set();total=0;duration=0.
    for t in tracks:
        if not isinstance(t,dict) or set(t)!={'joint','times','rotations_xyzw'} or type(t['joint']) is not int or not 0<=t['joint']<joint_count or t['joint'] in seen:
            raise ValueError('Invalid or duplicate rotation track')
        seen.add(t['joint']);times=t['times'];qs=t['rotations_xyzw']
        if not isinstance(times,list) or not 2<=len(times)<=256 or not isinstance(qs,list) or len(qs)!=len(times):
            raise ValueError('Expected 2–256 paired keyframes per track')
        total+=len(times)
        if total>2048 or not all(scene.number(x,0,300) for x in times) or times[0]!=0:
            raise ValueError('Keyframe count or time outside bound')
        ts=converter.floats32(times)
        if any(a>=b for a,b in zip(ts,ts[1:])):raise ValueError('Times must strictly increase after float32 conversion')
        duration=max(duration,ts[-1])
        for q in qs:
            if not scene.vector(q,4,-1,1) or not math.isclose(math.sqrt(dot(q,q)),1,rel_tol=0,abs_tol=1e-6):
                raise ValueError('Expected normalized XYZW quaternion')
    return total,duration
def checked(s):
    if not isinstance(s,dict) or set(s)!={'mesh','max_position_error','joints','name','tracks'}:raise ValueError('Expected rig and reviewed keyframe tracks')
    rig.checked(rig_spec(s))
    if not isinstance(s['name'],str) or not 1<=len(s['name'])<=64 or not s['name'].strip() or any(not 32<=ord(c)<=126 for c in s['name']):
        raise ValueError('Invalid animation name')
    tracks_checked(s['tracks'],len(s['joints']))
    return s
def quaternions(qs):
    out=[]
    for q in qs:
        q=tuple(x/math.sqrt(dot(q,q)) for x in q)
        if out and dot(q,out[-1])<0:q=tuple(-x for x in q)
        q=converter.floats32(q)
        if abs(dot(q,q)-1)>2e-7:raise ValueError('Quaternion precision check failed')
        out.append(q)
    return out
def animate(raw,s):
    checked(s);count,duration=tracks_checked(s['tracks'],len(s['joints']))
    original,r=rig.rig(raw,rig_spec(s));doc,binary=scene.decode(original);data=bytearray(binary)
    old_nodes=list(doc['nodes']);old_skins=list(doc['skins'])
    def append(rows,fmt,typ,limits=None):
        vi=len(doc['bufferViews']);blob=b''.join(struct.pack(fmt,*row) for row in rows)
        doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(blob)})
        data.extend(blob);ai=len(doc['accessors'])
        a={'bufferView':vi,'byteOffset':0,'componentType':5126,'count':len(rows),'type':typ}
        if limits:a.update(min=[limits[0]],max=[limits[1]])
        doc['accessors'].append(a);return ai
    animation={'name':s['name'],'samplers':[],'channels':[]};expected=[]
    for t in s['tracks']:
        times=[(x,) for x in converter.floats32(t['times'])];qs=quaternions(t['rotations_xyzw'])
        ia=append(times,'<f','SCALAR',(times[0][0],times[-1][0]));oa=append(qs,'<4f','VEC4')
        animation['channels'].append({'sampler':len(animation['samplers']),'target':{'node':t['joint']+1,'path':'rotation'}})
        animation['samplers'].append({'input':ia,'output':oa,'interpolation':'LINEAR'})
        expected.append((ia,oa,times,qs))
    doc['animations']=[animation];doc['buffers'][0]['byteLength']=len(data)
    j=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8');j+=b' '*((-len(j))%4)
    payload=(struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(data))+
        struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data)
    d,b=scene.decode(payload)
    if d!=doc or b[:len(binary)]!=binary or d['nodes']!=old_nodes or d['skins']!=old_skins:
        raise ValueError('Animation changed rest rig')
    for ia,oa,times,qs in expected:
        if accessor(d,b,ia,'<f')!=times or accessor(d,b,oa,'<4f')!=qs:raise ValueError('Animation accessor roundtrip failed')
    return payload,{**r,'animation_name':s['name'],'track_count':len(s['tracks']),'keyframe_count':count,
        'duration_seconds':duration,'animation_accessors_verified':True,'rest_skin_preserved':True,
        'native_playback_verified':False,'motion_quality_verified':False,
        'scope':'Explicit local rotation keyframes with linear glTF quaternion interpolation; no motion capture, IK, root motion or playback acceptance.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb',extra=EXTRA)
    validate(root,plan)
    return plan,dict(s,scope='Explicit reviewed local joint rotation tracks, no arbitrary script execution.')
def execute(root,plan):
    s,dst,path=validate(root,plan);out,r=animate(guard.exact(path,plan['guards'][1],guard.MAX_INPUT),s)
    sha=guard.publish(out,dst,lambda:validate(root,plan))
    return {'schema':'janus-skeletal-animation-result-v1','status':'skeletal_animation_structure_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed rig, keyframes or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
