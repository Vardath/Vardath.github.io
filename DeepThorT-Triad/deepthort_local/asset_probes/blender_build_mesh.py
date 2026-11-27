# Fixed JANUS Blender producer, not model-generated or imported project code.
import bpy
import hashlib
import json
import sys
from pathlib import Path

def digest(vertices,faces):
    raw=json.dumps([vertices,faces],separators=(',',':'),allow_nan=False).encode('ascii')
    return hashlib.sha256(raw).hexdigest()

def main():
    args=sys.argv[sys.argv.index('--')+1:]
    if len(args)!=2:raise RuntimeError('Expected exact staged JSON and new blend destination')
    src,dst=map(Path,args)
    if dst.exists():raise RuntimeError('Refusing existing staged output')
    packet=json.loads(src.read_text('utf-8'))
    v,f=packet['vertices'],packet['faces']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    mesh=bpy.data.meshes.new('JANUS_Mesh')
    mesh.from_pydata(v,[],f);mesh.update()
    if mesh.validate(verbose=False):raise RuntimeError('Blender changed validated geometry')
    item=bpy.data.objects.new('JANUS_Mesh',mesh);bpy.context.scene.collection.objects.link(item)
    bpy.context.view_layer.objects.active=item;item.select_set(True)
    if bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=False)!={'FINISHED'}:
        raise RuntimeError('Blend save failed')
    if bpy.ops.wm.open_mainfile(filepath=str(dst),load_ui=False,use_scripts=False)!={'FINISHED'}:
        raise RuntimeError('Blend reload failed')
    objects=list(bpy.context.scene.objects)
    if len(objects)!=1 or objects[0].type!='MESH':raise RuntimeError('Unexpected scene objects')
    data=objects[0].data
    observed_v=[[float(x) for x in p.co] for p in data.vertices]
    observed_f=[list(p.vertices) for p in data.polygons]
    if observed_v!=v or observed_f!=f:raise RuntimeError('Reloaded geometry differs')
    print('JANUS_BLEND_VERIFIED '+json.dumps({'vertices':len(v),'triangles':len(f),'geometry_sha256':digest(observed_v,observed_f)},sort_keys=True),flush=True)

if __name__=='__main__':main()
