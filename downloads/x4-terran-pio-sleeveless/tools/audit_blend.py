#!/usr/bin/env python3
"""Blender-only, read-only audit of a loaded XAC imported .blend project.

Run as: blender -b "terran dress 1.blend" --python audit_blend.py
No geometry editing, no XAC building, no modifications to original files.
Emits JSON alongside the project for a source-grounded mesh review.
"""
from __future__ import annotations
import json
from pathlib import Path
import bpy
from mathutils import Vector


def bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return {
        "min": [round(min(p[i] for p in pts), 4) for i in range(3)],
        "max": [round(max(p[i] for p in pts), 4) for i in range(3)]
    }


def inspect_scene():
    out = {"file": bpy.data.filepath, "blender": bpy.app.version_string,
           "armatures": [], "meshes": [], "notes": []}
    for o in bpy.context.scene.objects:
        if o.type == "ARMATURE":
            out["armatures"].append({
                "name": o.name, "bones": [b.name for b in o.data.bones],
                "xac_template": o.get("xac_template"),
                "x4_game_path": o.get("x4_game_path"),
                "mod_id": getattr(getattr(o, "x4mod", None), "mod_id", None)
            })
        if o.type != "MESH":
            continue
        materials = []
        for m in o.data.materials:
            if m is not None:
                materials.append({"name": m.name,
                                  "xac_name": m.get("xac_name"),
                                  "xac_game": bool(m.get("xac_game")),
                                  "image_names": sorted({n.image.name for n in m.node_tree.nodes
                                                         if m.use_nodes and n.type == 'TEX_IMAGE'
                                                         and n.image is not None})})
        out["meshes"].append({
            "name": o.name, "part": getattr(o, "x4_part", None),
            "armature": o.find_armature().name if o.find_armature() else None,
            "vertices": len(o.data.vertices), "polygons": len(o.data.polygons),
            "vertex_groups": [g.name for g in o.vertex_groups],
            "UV_layers": [u.name for u in o.data.uv_layers],
            "materials": materials, "bounds": bounds(o),
            "has_shape_keys": bool(o.data.shape_keys),
        })
    out["notes"].extend([
        "Materials and bone groups alone cannot establish that a missing under-sleeve arm is rendered.",
        "A genuine short-sleeve edit requires the under-garment skin mesh plus appropriate weights and textures.",
        "An original XAC game path and template are required for Replace Body build mode."
    ])
    return out


if __name__ == "__main__":
    src = Path(bpy.data.filepath)
    if not src:
        raise SystemExit("Open a .blend project first.")
    result = inspect_scene()
    dest = src.with_name(src.stem + ".xac-audit.json")
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
                    encoding="utf-8")
    print("XAC-AUDIT:", dest)
