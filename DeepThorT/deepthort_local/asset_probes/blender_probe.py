# Fixed DeepThorT application import probe, not model-generated.
import bpy
import json
import sys
from pathlib import Path

def main():
    args=sys.argv[sys.argv.index('--')+1:]
    if len(args)!=1:raise RuntimeError('Expected one approved input')
    path=Path(args[0])
    if path.suffix.lower()=='.png':
        image=bpy.data.images.load(str(path),check_existing=False)
        w,h=image.size
        if not w or not h or not len(image.pixels):raise RuntimeError('Image not loaded')
        result={'kind':'image','width':int(w),'height':int(h)}
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if path.suffix.lower()=='.obj':
            if bpy.ops.wm.obj_import(filepath=str(path))!={'FINISHED'}:raise RuntimeError('OBJ import failed')
        elif path.suffix.lower()=='.glb':
            if bpy.ops.import_scene.gltf(filepath=str(path))!={'FINISHED'}:raise RuntimeError('GLB import failed')
        else:raise RuntimeError('Unsupported import')
        meshes=[obj for obj in bpy.context.scene.objects if obj.type=='MESH']
        vertices=sum(len(obj.data.vertices) for obj in meshes)
        if not meshes or not vertices:raise RuntimeError('No mesh geometry imported')
        result={'kind':'mesh','meshes':len(meshes),'vertices':vertices}
    print('DEEPTHORT_ASSET_PROBE '+json.dumps(result),flush=True)

if __name__=='__main__':main()
