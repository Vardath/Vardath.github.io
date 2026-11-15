#!/usr/bin/env python3
"""Automated *experimental* X4 dress reconstruction using X4 XAC Tools 0.6.2.

Must run inside Blender 5.1 on the computer with X4 and XAC Tools installed.
This code makes *actual* mesh edits and tries to export subst_01.cat/.dat.
It fails closed when complete donor arms/legs or original XAC targets are absent.
It never rewrites the original .blend files or X4 base CAT/DAT archives.

Example:
    blender -b --python auto_edit_and_build.py -- --sources "C:/X4/blends"
"""
import argparse
import importlib
import json
import math
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector, Matrix

MOD_ID = "vardath_terran_pio_sleeveless"
MOD_NAME = "Vardath Terran / Pioneers - Sleeveless Dresses"
# Start with the files whose names suggest a formal dress. Do not indiscriminately
# replace manager, marine, pilot or Yaki outfits which might not be dresses.
CANDIDATES = (
    "terran dress 1.blend", "uniform1.blend", "uniform2.blend",
    "uniformcrew1.blend", "uniformdiplomat1.blend",
)
ARM_SEGS = ("UpperArm", "Forearm", "Hand")
LEG_SEGS = ("Thigh", "Calf", "Foot", "Toe0")


def log(message):
    print("[VARDATH CLOTHING] " + str(message), flush=True)


def addon_package():
    available = [a.module for a in bpy.context.preferences.addons if "xac" in a.module.lower()]
    for package in available + ["io_scene_x4_xac", "bl_ext.user_default.io_scene_x4_xac"]:
        try:
            return importlib.import_module(package)
        except ImportError:
            continue
    raise RuntimeError("X4 XAC Tools is not enabled in this Blender installation.")


def bone(arm, name):
    result = arm.data.bones.get(name)
    if result is None:
        raise ValueError("Missing X4 skeleton bone %r on %s" % (name, arm.name))
    return arm.matrix_world @ result.head_local


def bone_axis(arm, side, first, second):
    a = bone(arm, "Bip01 %s %s" % (side, first))
    b = bone(arm, "Bip01 %s %s" % (side, second))
    v = b - a
    if v.length < 0.05:
        raise ValueError("Invalid arm rig: %s, %s" % (first, second))
    return a, v, v.normalized()


def _limb_type(group):
    # Identifies X4 skeleton influences; the original outfit will retain its
    # own vertex groups and the donor pieces will retain their original weights.
    for side in ("L", "R"):
        for part, names in (("arm", ARM_SEGS), ("leg", LEG_SEGS)):
            if any(group.startswith("Bip01 %s %s" % (side, n)) for n in names):
                return "%s_%s" % (side, part)
    return ""


def skin_material_name(obj, index):
    if index >= len(obj.data.materials):
        return False
    m = obj.data.materials[index]
    name = ((m.get("xac_name") or "") + " " + m.name).lower() if m else ""
    return any(word in name for word in ("skin", "flesh", "naked", "nude"))


def body_meshes(arm):
    return [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.find_armature() == arm
            and getattr(o, "x4_part", "BODY") == "BODY"]


def edit_uniform(arm):
    """Trim cloth below a plane above the knee and remove cloth over both arms.

    Importer coordinate system: +Z up; bone locations are derived from the
    armature instead of hard-coding skirt measurements in world coordinates.
    """
    knee = (bone(arm, "Bip01 L Calf").z + bone(arm, "Bip01 R Calf").z) / 2
    hip = bone(arm, "Bip01 Pelvis").z
    if not 0.2 < hip - knee < 1.0:
        raise ValueError("Unexpected hip-to-knee length, refusing automatic cut")
    # 16% of thigh length above the knee, a shorter skirt rather than a micro skirt.
    hem = knee + 0.16 * (hip - knee)
    arms = [bone_axis(arm, s, "UpperArm", "Forearm") for s in ("L", "R")]
    out = {"knee_height": round(knee, 4), "hem_height": round(hem, 4),
           "skirt_faces_removed": 0, "sleeve_faces_removed": 0, "meshes": []}

    for obj in body_meshes(arm):
        original_count = len(obj.data.polygons)
        if original_count < 8:
            continue
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        # Split triangles at each cut before deleting exposed-cloth faces.
        # No body skin is removed when the original material marks it as skin.
        planes = [
            (Vector((0, 0, hem)), Vector((0, 0, 1))),
            *[(head + axis * 0.12, direction) for head, axis, direction in arms],
        ]
        for world_co, world_n in planes:
            local_co = obj.matrix_world.inverted() @ world_co
            local_n = (obj.matrix_world.transposed().to_3x3() @ world_n).normalized()
            bmesh.ops.bisect_plane(
                bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
                dist=0.00001, plane_co=local_co, plane_no=local_n)
        skirt = []
        sleeves = []
        for face in list(bm.faces):
            if skin_material_name(obj, face.material_index):
                continue
            p = obj.matrix_world @ face.calc_center_median()
            if p.z < hem:
                skirt.append(face)
                continue
            for shoulder, vec, direction in arms:
                along = (p - shoulder).dot(direction)
                radial = ((p - shoulder) - direction * along).length
                # Sleeve: outside the shoulder seam, within 22cm of upper arm
                # axis, and no farther than the elbow + part of forearm.
                if (0.12 * vec.length < along < 1.7 * vec.length
                        and radial < 0.22):
                    sleeves.append(face)
                    break
        # The two lists are disjoint. Preserve any original skin-tagged material.
        if skirt or sleeves:
            bmesh.ops.delete(bm, geom=skirt + sleeves, context="FACES")
            bm.to_mesh(obj.data)
            obj.data.update()
        bm.free()
        out["skirt_faces_removed"] += len(skirt)
        out["sleeve_faces_removed"] += len(sleeves)
        out["meshes"].append({"name": obj.name, "original_faces": original_count,
                              "skirt_removed": len(skirt),
                              "sleeve_removed": len(sleeves),
                              "remaining_faces": len(obj.data.polygons)})
    if not out["skirt_faces_removed"] or not out["sleeve_faces_removed"]:
        raise ValueError(
            "No verified skirt or sleeve faces removed. The source is likely not a "
            "dress; nothing will be installed. Review the audit / garment geometry.")
    return out


def append_donor_objects(filepath):
    """Append, do not link: X4 skin materials and vertex weights remain editable."""
    with bpy.data.libraries.load(str(filepath), link=False) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None]
    for o in objs:
        if not o.users_collection:
            bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    arms = [o for o in objs if o.type == "ARMATURE"]
    if not arms:
        raise ValueError("yishabody.blend does not contain an armature")
    return objs, arms[0]


def keep_limb_faces(src):
    counts = {key: 0 for key in ("L_arm", "R_arm", "L_leg", "R_leg")}
    accepted = set()
    names = {g.index: g.name for g in src.vertex_groups}
    for poly in src.data.polygons:
        by_region = {key: 0.0 for key in counts}
        for vid in poly.vertices:
            for grp in src.data.vertices[vid].groups:
                part = _limb_type(names.get(grp.group, ""))
                if part in by_region:
                    by_region[part] += grp.weight / max(1, len(poly.vertices))
        if not by_region:
            continue
        key = max(by_region, key=by_region.get)
        if by_region[key] >= 0.45:
            accepted.add(poly.index)
            counts[key] += 1
    return accepted, counts


def transplant_limb_geometry(donor_obj, donor_arm, target_arm):
    """Attach donor arms and legs with mapped bind-pose coordinates and weights."""
    selected, counts = keep_limb_faces(donor_obj)
    if len(selected) < 80:
        return None, counts
    obj = donor_obj.copy()
    obj.data = donor_obj.data.copy()
    bpy.context.scene.collection.objects.link(obj)
    obj.name = "Vardath_bare_limbs_" + donor_obj.name

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.index_update()
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in list(bm.faces) if f.index not in selected],
                     context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    if not obj.data.polygons:
        bpy.data.objects.remove(obj, do_unlink=True)
        return None, counts

    group_names = {g.index: g.name for g in obj.vertex_groups}
    transforms = {}
    for name in group_names.values():
        sb = donor_arm.data.bones.get(name)
        tb = target_arm.data.bones.get(name)
        if sb is not None and tb is not None:
            source_mat = donor_arm.matrix_world @ sb.matrix_local
            target_mat = target_arm.matrix_world @ tb.matrix_local
            transforms[name] = target_mat @ source_mat.inverted()
    if not transforms:
        bpy.data.objects.remove(obj, do_unlink=True)
        raise ValueError("No compatible donor/target bones; cannot rig exposed limbs.")

    donor_world = donor_obj.matrix_world.copy()
    inv_target = target_arm.matrix_world.inverted()
    unmapped = 0
    for v in obj.data.vertices:
        old = donor_world @ v.co
        weighted = Vector((0, 0, 0))
        norm = 0.0
        for g in v.groups:
            name = group_names.get(g.group, "")
            if name in transforms:
                weighted += (transforms[name] @ old) * g.weight
                norm += g.weight
        if norm > 1e-5:
            v.co = inv_target @ (weighted / norm)
        else:
            unmapped += 1
    if unmapped > 0.02 * len(obj.data.vertices):
        bpy.data.objects.remove(obj, do_unlink=True)
        raise ValueError("Too many donor vertices with incompatible bone weights.")

    obj.parent = target_arm
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = target_arm.matrix_world.copy()
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE":
            modifier.object = target_arm
    if not any(m.type == "ARMATURE" for m in obj.modifiers):
        obj.modifiers.new("Armature", "ARMATURE").object = target_arm
    obj.x4_part = "BODY"
    return obj, counts


def add_exposed_limbs(target_arm, donor_path):
    _, donor_arm = append_donor_objects(donor_path)
    stats = {key: 0 for key in ("L_arm", "R_arm", "L_leg", "R_leg")}
    added = []
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or obj.find_armature() != donor_arm:
            continue
        new, counts = transplant_limb_geometry(obj, donor_arm, target_arm)
        if new is not None:
            added.append(new.name)
            for key in counts:
                stats[key] += counts[key]
    # Each exposed limb needs substantial skin surface; reject invisible arms.
    if any(n < 40 for n in stats.values()):
        raise ValueError("Donor does not cover all four limbs adequately: " + repr(stats))
    return {"donor": str(donor_path), "new_meshes": added, "limb_faces": stats}


def choose_armature():
    candidates = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"
                  and o.get("x4_game_path") and o.get("xac_template")]
    if not candidates:
        raise ValueError("This .blend has no XAC-imported body armature with original game path")
    # An isolated uniform scene normally has only one XAC armature.
    candidates.sort(key=lambda o: len(body_meshes(o)), reverse=True)
    return candidates[0]


def sources_in(directory):
    def lookup(name):
        p = directory / name
        if p.is_file():
            return p
        matches = list(directory.rglob(name))
        return matches[0] if matches else None
    donor = lookup("yishabody.blend")
    if donor is None:
        raise ValueError("Cannot find yishabody.blend in the supplied source folder")
    sources = [lookup(name) for name in CANDIDATES]
    return donor, [p for p in sources if p is not None]


def save_build(source, donor, output, addon, game, cache):
    # open_mainfile does not modify the saved file; all edits are in a new scene.
    bpy.ops.wm.open_mainfile(filepath=str(source))
    arm = choose_armature()
    target = arm.get("x4_game_path")
    # XAC Tools is the sole authority for X4 target paths and original templates.
    xac_index = addon.catalog.index(game)
    if target.lower() not in xac_index:
        raise ValueError("Cannot find the source XAC in this installed game: " + target)
    trimmed = edit_uniform(arm)
    donor_report = add_exposed_limbs(arm, donor)
    bpy.context.view_layer.objects.active = arm
    arm.x4mod.mod_id = MOD_ID
    arm.x4mod.mod_name = MOD_NAME
    arm.x4mod.mode = "REPLACE"
    arm.x4mod.target = target
    # No original Blender or game files are touched. XAC Tools writes staged CAT/DAT.
    addon.character.build(bpy.context, arm, arm.x4mod, game, cache, addon.save,
                          mod_dir=str(output))
    if not (output/"subst_01.cat").is_file() or not (output/"subst_01.dat").is_file():
        raise ValueError("XAC build did not produce a replacement catalog")
    report = {"blend": str(source), "target": target, "dress": trimmed, "limbs": donor_report}
    return report


def run(sources):
    source_dir = sources.resolve()
    donor, candidates = sources_in(source_dir)
    if not candidates:
        raise ValueError("No dress/uniform .blend candidates found alongside donor.")
    addon = addon_package()
    game = Path(addon.panel.game_dir(bpy.context)).resolve()
    cache = addon.panel.cache_dir(bpy.context)
    output = game / "extensions" / MOD_ID
    if output.exists():
        raise ValueError("Refusing to replace an existing extension: " + str(output))
    log("Using X4 game: " + str(game))
    log("Input projects: " + ", ".join(p.name for p in candidates))
    attempted = []
    reports = []
    seen_targets = set()
    # XAC tool's build() produces one replacement per stage. Merge later to
    # avoid the one-extension-per-outfit overwrite problem.
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    from merge_replace_bodies import read_catalog, merge
    with tempfile.TemporaryDirectory(prefix="vardath_x4_clothes_") as temp:
        td = Path(temp)
        stages = []
        for idx, source in enumerate(candidates):
            stage = td / ("outfit_%02d" % idx)
            try:
                result = save_build(source, donor, stage, addon, str(game), cache)
                target_key = result["target"].lower()
                if target_key in seen_targets:
                    log("Skipping duplicate outfit target: " + result["target"])
                    continue
                entries = read_catalog(stage, "subst_01")
                if target_key not in {k.lower() for k in entries}:
                    raise ValueError("Replacement catalog does not contain expected game path")
                seen_targets.add(target_key)
                stages.append(stage)
                reports.append(result)
                log("Edited and exported " + result["target"])
            except Exception as error:
                attempted.append({"source": str(source), "error": str(error)})
                log("Not exported " + source.name + ": " + str(error))
        if not stages:
            raise ValueError("No valid model substitutions produced. " + json.dumps(attempted))
        # Complete a single-target mod too: Terran and Pioneer characters can
        # share the same torso model and require only one replacement.
        if len(stages) == 1:
            shutil.copytree(stages[0], output)
        else:
            merge(stages, output, MOD_ID)
        if not read_catalog(output, "subst_01"):
            raise ValueError("No XAC replacements in final mod")
    zipbase = source_dir / "Vardath_Terran_PIO_Sleeveless_Dresses"
    zipfile = shutil.make_archive(str(zipbase), "zip",
                                  root_dir=str(game / "extensions"), base_dir=MOD_ID)
    report = {"status": "built_requires_in_game_visual_validation",
              "mod_path": str(output), "zip": zipfile, "models": reports,
              "skipped": attempted}
    report_file = source_dir / "Vardath_Terran_PIO_Sleeveless_build_report.json"
    report_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    log("Built the extension in " + str(output))
    log("ZIP created at " + zipfile)
    log("IMPORTANT: inspect the exposed limbs, textures and animations in-game.")
    return report


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", required=True, type=Path)
    parsed = parser.parse_args(args)
    try:
        run(parsed.sources)
    except Exception:
        traceback.print_exc()
        # Refuse silent false-success and let the caller see the actual error.
        raise SystemExit(1)


if __name__ == "__main__":
    main()
