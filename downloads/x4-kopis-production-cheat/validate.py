#!/usr/bin/env python3
"""Lightweight packaging integrity only: no feature/regression assertions.

Game behavior must be checked using X4 itself and its debug.log.
"""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
name = "vardath_kopis_production_cheat"
source = root / name
archive = root / (name + "_TEST.zip")

if not source.is_dir():
    raise SystemExit(f"Missing extension folder: {source}")
items = sorted(p for p in source.rglob("*") if p.is_file())
if not items or not (source / "content.xml").is_file():
    raise SystemExit(f"Missing files or content.xml in {source}")
manifest = ET.parse(source / "content.xml").getroot()
if manifest.tag != "content" or manifest.get("id") != name:
    raise SystemExit("Malformed content.xml identifier")
for item in items:
    if item.suffix.lower() == ".xml":
        ET.parse(item)
if not archive.is_file():
    raise SystemExit(f"Missing packaged ZIP: {archive}")
with ZipFile(archive) as packed:
    if (bad := packed.testzip()) is not None:
        raise SystemExit(f"ZIP checksum error: {bad}")
    expected = {name + "/" + p.relative_to(source).as_posix() for p in items}
    actual = set(packed.namelist())
    if actual != expected:
        raise SystemExit("ZIP paths do not match source folder")
    for item in items:
        member = name + "/" + item.relative_to(source).as_posix()
        if packed.read(member) != item.read_bytes():
            raise SystemExit(f"ZIP contains stale source: {member}")
print(f"PASS: {name}; {len(items)} source files, XML parse and ZIP integrity")
