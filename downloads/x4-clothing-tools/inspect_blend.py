#!/usr/bin/env python3
"""Read-only inventory and workbench previews of one already-open .blend file.

Run by Blender in background:
  blender -b "file.blend" --python inspect_blend.py -- --out "folder"
This script never calls save_mainfile or modifies its input file.
"""
import bpy
import json
import math
import sys
import traceback
from pathlib import Path
from mathutils import Vector

def arg_after(flag, default=None):
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if flag in args and args.index(flag)+1 < len(args):
        return args[args.index(flag)+1]
    return default

OUTPUT=Path(arg_after('--out',str(Path.cwd()/'X4_Clothing_Audit'))).resolve()
OUTPUT.mkdir(parents=True,exist_ok=True)
INPUT=Path(bpy.data.filepath)
SLUG=INPUT.stem.replace(' ','_')
audit={'file':INPUT.name,'blender_version':bpy.app.version_string,'objects':[],
       'materials':[],'images':[],'custom_scene_properties':{},'previews':[],'warnings':[]}

def simple(x):
    if isinstance(x,(str,bool,int,float)) or x is None: return x
    if hasattr(x,'to_list'): return x.to_list()
    return str(x)[:300]

def custom(obj):
    try: return {str(k):simple(obj.get(k)) for k in obj.keys() if not str(k).startswith('_')}
    except Exception: return {}

def bounds_world(obj):
    try:
        corners=[obj.matrix_world @ Vector(v) for v in obj.bound_box]
        return ([round(min(p[i] for p in corners),5) for i in range(3)],
                [round(max(p[i] for p in corners),5) for i in range(3)])
    except Exception: return (None,None)

mesh_objs=[]
for ob in sorted(bpy.data.objects,key=lambda x:x.name):
    info={'name':ob.name,'type':ob.type,'hidden_render':bool(ob.hide_render),
          'hidden_viewport':bool(ob.hide_viewport),'custom_properties':custom(ob)}
    if ob.type=='MESH':
        m=ob.data
        mesh_objs.append(ob)
        lo,hi=bounds_world(ob)
        info.update(vertices=len(m.vertices),polygons=len(m.polygons),
                    edges=len(m.edges),bounds_min=lo,bounds_max=hi,
                    vertex_groups=[g.name for g in ob.vertex_groups],
                    armature_modifiers=[(x.object.name if x.object else None)
                        for x in ob.modifiers if x.type=='ARMATURE'],
                    material_slots=[s.material.name if s.material else None for s in ob.material_slots],
                    shape_keys=([k.name for k in m.shape_keys.key_blocks] if m.shape_keys else []))
    if ob.type=='ARMATURE':
        info.update(bones=[b.name for b in ob.data.bones],
                    armature_bone_count=len(ob.data.bones))
    audit['objects'].append(info)

for mat in bpy.data.materials:
    audit['materials'].append({'name':mat.name,'blend_method':getattr(mat,'surface_render_method',None),
       'diffuse_color':[round(float(x),4) for x in mat.diffuse_color],
       'custom_properties':custom(mat)})
for img in bpy.data.images:
    audit['images'].append({'name':img.name,
        'source':img.source,'packed':img.packed_file is not None,
        'filepath':Path(bpy.path.abspath(img.filepath)).name if img.filepath else '',
        'size':list(img.size)})
try:
    audit['custom_scene_properties']=custom(bpy.context.scene)
except Exception: pass

print('[X4 AUDIT]',INPUT.name,'mesh objects',len(mesh_objs),
      'total vertices',sum(len(x.data.vertices) for x in mesh_objs),flush=True)

def preview(direction,label):
    # Workbench pictures are geometric previews, not textured in-game renders.
    # All changes here live in memory, and we never save the .blend source.
    valid=[o for o in mesh_objs if len(o.data.vertices)>=25]
    if not valid:
        audit['warnings'].append('No model-like mesh (>24 vertices) to preview.')
        return
    pairs=[bounds_world(o) for o in valid]
    pairs=[p for p in pairs if p[0] is not None and p[1] is not None]
    if not pairs: return
    mn=Vector([min(p[0][i] for p in pairs) for i in range(3)])
    mx=Vector([max(p[1][i] for p in pairs) for i in range(3)])
    size=mx-mn
    if max(size)<=1e-7:return
    center=(mn+mx)/2
    # Temporary camera added only to opened scene in memory.
    sc=bpy.context.scene
    camdata=bpy.data.cameras.new('X4_AUDIT_TEMP_CAMERA')
    cam=bpy.data.objects.new('X4_AUDIT_TEMP_CAMERA',camdata)
    sc.collection.objects.link(cam)
    sc.camera=cam
    cam.location=center+direction.normalized()*max(10.0,size.length*3)
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    camdata.type='ORTHO'
    camdata.ortho_scale=max(size.z*1.28,size.x*1.5,size.y*1.5,0.2)
    sc.render.engine='BLENDER_WORKBENCH'
    sc.display.shading.light='STUDIO'
    sc.display.shading.color_type='MATERIAL'
    sc.display.shading.show_cavity=True
    sc.render.resolution_x=576
    sc.render.resolution_y=768
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.render.film_transparent=False
    # Restore models hidden by an export pipeline just for preview.
    for o in valid:
        o.hide_render=False
    output=OUTPUT/(SLUG+'_'+label+'.png')
    sc.render.filepath=str(output)
    try:
        bpy.ops.render.render(write_still=True)
        audit['previews'].append(output.name)
    except Exception:
        audit['warnings'].append('Preview '+label+' failed: '+traceback.format_exc()[-1000:])
    finally:
        bpy.data.objects.remove(cam,do_unlink=True)
        bpy.data.cameras.remove(camdata,do_unlink=True)

# Render no more than one view for each uploaded file; fuller previews for
# likely dress/uniform targets. Time and disk use are intentionally bounded.
try:
    if len(mesh_objs)>0:
        preview(Vector((0,-1,0)),'front')
        if 'dress' in SLUG.lower() or 'uniform' in SLUG.lower():
            preview(Vector((1,0,0)),'side')
except Exception:
    audit['warnings'].append('Preview subsystem error: '+traceback.format_exc()[-1000:])

target=OUTPUT/(SLUG+'.json')
target.write_text(json.dumps(audit,indent=2,ensure_ascii=False,default=simple),encoding='utf-8')
print('[X4 AUDIT] Saved',target,'previews',audit['previews'],flush=True)
