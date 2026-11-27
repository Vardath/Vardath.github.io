"""Reviewed automatic three-point directional lighting for composed glTF scenes."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file
from deepthort_local import scene_composition as scene
SCHEMA='janus-automatic-lighting-v1'
EXT='KHR_lights_punctual'
def scene_spec(spec):
    return {'objects':spec['objects'],'max_position_error':spec['max_position_error']}
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'objects','max_position_error','view_azimuth_deg','key_lux','preset'}:
        raise ValueError('Expected reviewed scene and lighting settings')
    scene.checked(scene_spec(spec))
    if not scene.number(spec['view_azimuth_deg'],-180,180) or not scene.number(spec['key_lux'],1,20000) or spec['preset'] not in ('neutral','warm','cool'):
        raise ValueError('Lighting settings outside bound')
    return spec
def facing(azimuth,elevation):
    # glTF uses +Y up; a directional lamp emits along its local -Z.
    az,el=map(math.radians,(azimuth,elevation))
    d=(-math.sin(az)*math.cos(el),-math.sin(el),-math.cos(az)*math.cos(el))
    # Shortest arc from (0,0,-1) to target direction.
    q=(d[1],-d[0],0.,1.-d[2])
    length=math.sqrt(sum(v*v for v in q))
    if length<1e-12:raise ValueError('Degenerate light orientation')
    x,y,z,w=(v/length for v in q)
    actual=(-2*(x*z+y*w),-2*(y*z-x*w),-(1-2*(x*x+y*y)))
    if max(abs(a-b) for a,b in zip(d,actual))>1e-10:
        raise ValueError('Light orientation mismatch')
    return [x,y,z,w],list(d)
def add_lighting(raws,spec):
    checked(spec)
    payload,receipt=scene.compose(raws,scene_spec(spec))
    doc,binary=scene.decode(payload)
    nodes=doc['nodes'];old_nodes=list(nodes)
    colors={'neutral':([1.,1.,1.],[1.,1.,1.],[1.,1.,1.]),
            'warm':([1.,.87,.72],[.78,.86,1.],[1.,.95,.85]),
            'cool':([.78,.88,1.],[1.,.95,.87],[.78,.91,1.])}[spec['preset']]
    lights=[];records=[]
    for i,(name,az,el,factor) in enumerate((('Key',45,38,1.),('Fill',-50,23,.45),('Rim',155,48,.8))):
        q,d=facing(spec['view_azimuth_deg']+az,el)
        light={'name':name,'type':'directional','color':colors[i],'intensity':spec['key_lux']*factor}
        lights.append(light)
        index=len(nodes)
        nodes.append({'name':'JANUS '+name+' light','rotation':q,'extensions':{EXT:{'light':i}}})
        doc['scenes'][0]['nodes'].append(index)
        records.append({'node':index,'direction':d,**light})
    doc['extensionsUsed']=[EXT];doc['extensionsRequired']=[EXT]
    doc['extensions']={EXT:{'lights':lights}}
    encoded=json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    encoded+=b' '*((-len(encoded))%4)
    result=(struct.pack('<4sII',b'glTF',2,12+8+len(encoded)+8+len(binary))+
        struct.pack('<II',len(encoded),0x4e4f534a)+encoded+
        struct.pack('<II',len(binary),0x004e4942)+binary)
    parsed,data=scene.decode(result)
    if parsed!=doc or data!=binary or parsed['nodes'][:len(old_nodes)]!=old_nodes:
        raise ValueError('Lighting roundtrip changed scene geometry')
    return result,{**receipt,'lights':records,'lighting_extension':EXT,'lighting_metadata_verified':True,
        'scene_geometry_unchanged':True,'preset':spec['preset'],'view_azimuth_deg':spec['view_azimuth_deg'],
        'render_verified':False,'exposure_or_shadow_quality_verified':False,
        'scope':'Automatic view-relative three-point directional light rig; no native rendering or photometric quality acceptance.'}
def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or not 2<=len(plan['guards'])<=scene.MAX_OBJECTS+1:
        raise ValueError('Invalid lighting approval')
    spec,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.glb')
    paths=scene.paths_for(Path(root).resolve(strict=True),spec,plan['exclude'])
    if len(paths)!=len(plan['guards'])-1 or any(snapshot_file(p)!=g for p,g in zip(paths,plan['guards'][1:])):
        raise ValueError('Reviewed scene mesh changed')
    return spec,dst,paths
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.glb')
    paths=scene.paths_for(Path(plan['root']),spec,plan['exclude']);plan['guards'].extend(snapshot_file(p) for p in paths)
    validate(root,plan)
    return plan,dict(spec,scope='View-relative directional key, fill and rim rig; no rendered quality claim.')
def execute(root,plan):
    spec,dst,paths=validate(root,plan);payload,r=add_lighting(scene.raws_for(paths,plan),spec)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-automatic-lighting-result-v1','status':'scene_lighting_metadata_verified','output':plan['output'],'sha256':sha,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(60,60))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed lighting, scene or output'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
