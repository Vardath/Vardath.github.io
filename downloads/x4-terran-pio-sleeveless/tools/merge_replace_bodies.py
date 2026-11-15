#!/usr/bin/env python3
"""Safely merge *already edited* X4 XAC Tools Replace Body outputs into one extension.

This does NOT modify geometry. A source folder is one X4 XAC Tools-built
extension (with the desired same mod id), copied to a unique staging folder
before another outfit is exported. No X4 game files are overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import OrderedDict

ID = "vardath_terran_pio_sleeveless"


def read_catalog(folder: Path, name: str) -> dict[str, bytes]:
    cat, dat = folder / (name + ".cat"), folder / (name + ".dat")
    if not cat.exists() and not dat.exists():
        return {}
    if not (cat.is_file() and dat.is_file()):
        raise ValueError(f"missing half of catalog {cat} / {dat}")
    raw = dat.read_bytes()
    offset = 0
    result = OrderedDict()
    for lineno, line in enumerate(cat.read_text(encoding="utf-8").splitlines(), 1):
        fields = line.rsplit(" ", 3)
        if len(fields) != 4:
            raise ValueError(f"bad CAT entry {cat}:{lineno}")
        path, size_text, _, md5 = fields
        path = path.replace("\\", "/")
        if path.startswith("/") or ".." in path.split("/") or not path:
            raise ValueError(f"unsafe catalog virtual path {path!r}")
        size = int(size_text)
        if size < 0 or size + offset > len(raw):
            raise ValueError(f"invalid CAT entry size {path}")
        data = raw[offset:offset + size]
        offset += size
        if hashlib.md5(data).hexdigest().lower() != md5.lower():
            raise ValueError(f"CAT checksum mismatch for {path}")
        if path in result:
            raise ValueError(f"duplicate file within one catalog: {path}")
        result[path] = data
    if offset != len(raw):
        raise ValueError(f"trailing data in {dat}")
    return result


def write_catalog(folder: Path, name: str, entries: dict[str, bytes]) -> None:
    if not entries:
        return
    folder.mkdir(parents=True, exist_ok=True)
    cat, dat = folder / (name + ".cat"), folder / (name + ".dat")
    fixed_timestamp = 1794700800
    with cat.open("w", encoding="utf-8", newline="\n") as index, dat.open("wb") as datafile:
        for path, data in sorted(entries.items()):
            index.write(f"{path} {len(data)} {fixed_timestamp} {hashlib.md5(data).hexdigest()}\n")
            datafile.write(data)


def read_source(folder: Path, mod_id: str):
    c = folder / "content.xml"
    if not c.is_file():
        raise ValueError(f"missing content.xml in {folder}")
    root = ET.parse(c).getroot()
    if root.tag != "content" or root.get("id") != mod_id:
        raise ValueError(f"{folder} must be exported by XAC Tools using Mod ID {mod_id!r}")
    subst = read_catalog(folder, "subst_01")
    ext = read_catalog(folder, "ext_01")
    if not subst:
        raise ValueError(f"{folder} has no XAC replacement subst_01 catalog")
    if any(not p.lower().endswith(".xac") for p in subst):
        raise ValueError(f"{folder} substitutes non-XAC game files; refusing merge")
    for path, data in subst.items():
        if not data.startswith(b"XAC "):
            raise ValueError(f"{folder}: substituted XAC has invalid magic: {path}")
    return root, subst, ext


def merge(sources: list[Path], destination: Path, mod_id: str = ID) -> dict:
    if len(sources) < 2:
        raise ValueError("At least two individually exported outfit stages are required")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destination must be empty to prevent overwriting an installed mod")
    subst: dict[str, bytes] = {}
    ext: dict[str, bytes] = {}
    dependencies: dict[tuple, ET.Element] = {}
    for folder in sources:
        root, src_subst, src_ext = read_source(folder, mod_id)
        for dep in root.findall("dependency"):
            key = tuple(sorted(dep.attrib.items()))
            dependencies.setdefault(key, dep)
        for path, body in src_subst.items():
            if path in subst:
                if subst[path] != body:
                    raise ValueError(f"two different replacements for target {path}; choose just one")
                raise ValueError(f"duplicate XAC target across stages: {path}")
            subst[path] = body
        for path, asset in src_ext.items():
            if path in ext and ext[path] != asset:
                raise ValueError(f"conflicting material or texture asset {path}; rename it in Blender first")
            ext[path] = asset
    if len(subst) < 2:
        raise ValueError("Only one unique replacement body supplied")
    destination.mkdir(parents=True, exist_ok=True)
    content = ET.Element("content", {
        "id": mod_id, "name": "Vardath Terran and Pioneer Sleeveless Dresses",
        "author": "Vardath", "version": "100", "date": "2026-11-15",
        "save": "0", "sync": "false",
        "description": "Terran/Pioneer sleeveless shorter-skirt body mesh substitutions."
    })
    for key in sorted(dependencies):
        ET.SubElement(content, "dependency", dependencies[key].attrib)
    ET.ElementTree(content).write(destination / "content.xml", encoding="utf-8", xml_declaration=True)
    write_catalog(destination, "ext_01", ext)
    write_catalog(destination, "subst_01", subst)
    report = {
        "status": "catalogs_merged_not_runtime_tested", "mod_id": mod_id,
        "body_targets": sorted(subst), "extension_assets": sorted(ext),
        "source_stages": [str(p) for p in sources],
        "checks": ["XAC magic", "catalog checksums", "unique target paths", "asset conflicts"]
    }
    (destination / "MERGE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, action="append", required=True,
                        help="Staged XAC Tools Replace Body extension; use more than once")
    parser.add_argument("--output", type=Path, required=True,
                        help="NEW empty output folder (never an existing installed mod)")
    parser.add_argument("--mod-id", default=ID)
    args = parser.parse_args()
    print(json.dumps(merge(args.source, args.output, args.mod_id), indent=2))


if __name__ == "__main__":
    main()
