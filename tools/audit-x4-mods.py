#!/usr/bin/env python3
"""Checks XML, documented command attributes, manifest identity, UI files, and source/ZIP packaging.
Does not assert how gameplay features are implemented.
"""
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
DROOT = ROOT / "downloads"
EXTS = (
    "x4-living-factions-builders",
    "x4-yaki-terran-habs",
    "x4-kopis-production-cheat",
    "x4-faction-invincible",
    "x4-station-auto-drones",
    "x4-universal-cargo-teleport",
    "x4-galactic-occupations",
)
report = {"commit": None, "mods": {}, "errors": [], "warnings": [], "caveats": [
    "Static tests cannot establish that the game executes MD cues, Lua events, or overrides.",
    "No installed 9.00 vanilla/DLC catalogs or actual mod load-order are available to resolve XPath patches against the effective merged game.",
    "Historical XSDs, when available, may not match the player's current X4 build."
]}

def note(level, mod, issue):
    report[level].append({"mod": mod, "issue": issue})

ids, scripts, custom_defs = {}, {}, set()
files_by_mod = {}
api=json.loads((DROOT/'x4-galactic-occupations/tools/api_contracts.json').read_text())

for folder in EXTS:
    top = DROOT / folder
    mods = [p for p in top.iterdir() if p.is_dir() and (p/"content.xml").exists()]
    if len(mods) != 1:
        note("errors", folder, f"Expected one extension source folder, got {len(mods)}")
        continue
    mod = mods[0]
    items = sorted(p for p in mod.rglob("*") if p.is_file())
    files_by_mod[folder] = (mod, items)
    status = report["mods"][folder] = {"id": mod.name, "files": len(items), "xml": 0, "diffs": 0, "md": 0, "aiscripts": 0, "lua": 0, "zip": "not checked"}
    try:
        manifest = ET.parse(mod / "content.xml").getroot()
        ident = manifest.attrib.get("id")
        if manifest.tag != "content" or ident != mod.name: note("errors", folder, "Bad content.xml manifest identifier")
        if ident in ids: note("errors", folder, "Duplicate extension ID with " + ids[ident])
        ids[ident] = folder
        if manifest.find("./dependency[@version]") is None:
            note("warnings", folder, "No X4 version dependency declared")
    except Exception as e:
        note("errors", folder, f"Bad content.xml: {e}")
    for p in items:
        rel = str(p.relative_to(mod))
        if p.suffix.lower() == ".xml":
            status["xml"] += 1
            try: root = ET.parse(p).getroot()
            except Exception as e:
                note("errors", folder, f"XML parse failed {rel}: {e}")
                continue
            if root.tag == "diff":
                status["diffs"] += 1
                for op in root:
                    if op.tag not in ("add", "remove", "replace"):
                        note("errors", folder, f"Unexpected XML diff operation {op.tag} in {rel}")
                    sel = op.attrib.get("sel")
                    if not sel: note("errors", folder, f"Missing selector in {rel}")
                    if sel and "\n" in sel: note("warnings", folder, f"Multiline XPath sel in {rel}")
            elif root.tag == "mdscript":
                status["md"] += 1
                name = root.attrib.get("name")
                if name in scripts: note("errors", folder, f"Duplicate MD name {name}, first in {scripts[name]}")
                scripts[name] = f"{folder}/{rel}"
            elif root.tag == "aiscript": status["aiscripts"] += 1
            for node in root.iter():
                if node.tag == 'create_order' and 'default' in node.attrib and 'immediate' in node.attrib:
                    note('errors',folder,f'{rel}: create_order cannot specify default and immediate together')
                if ('md' in p.relative_to(mod).parts or 'aiscripts' in p.relative_to(mod).parts) and node.tag in api['commands']:
                    definition=api['commands'][node.tag]
                    context='aiscripts' if 'aiscripts' in p.relative_to(mod).parts else 'md'
                    status['api_commands']=status.get('api_commands',0)+1
                    if context not in definition['contexts']: note('errors',folder,f'{rel}: {node.tag} invalid in {context}')
                    extra=set(node.attrib)-set(definition['attributes'])
                    if extra: note('errors',folder,f'{rel}: {node.tag} unknown attributes {sorted(extra)}')
                    missing=[key for key,value in definition['attributes'].items() if value.get('required') and key not in node.attrib]
                    if missing: note('errors',folder,f'{rel}: {node.tag} missing required {missing}')
                if root.tag=='addon' and node.tag=='file':
                    if not (mod/node.get('name','')).is_file(): note('errors',folder,f'{rel}: missing UI Lua {node.get("name")}')
                if node.tag in ("macro", "component") and "name" in node.attrib:
                    custom_defs.add(node.attrib["name"])
                if node.tag == "ware" and "id" in node.attrib:
                    custom_defs.add(node.attrib["id"])
        elif p.suffix.lower() == ".lua":
            status["lua"] += 1
            if not p.read_text().strip(): note("errors", folder, f"Empty Lua file: {rel}")
            if p.read_text().count("RegisterEvent(") < 1:
                note("warnings", folder, f"Lua file has no RegisterEvent hook: {rel}")
    archive = top / f"{mod.name}_TEST.zip"
    archive_prefix = f"{mod.name}/"
    if folder == 'x4-galactic-occupations':
        archive=top/'Galactic_Occupations_0.3.2_DEV.zip'
        archive_prefix='extensions/'+archive_prefix
    try:
        with ZipFile(archive) as z:
            bad = z.testzip()
            want = {archive_prefix+p.relative_to(mod).as_posix() for p in items}
            got = set(z.namelist())
            if bad: note("errors", folder, f"ZIP checksum failed: {bad}")
            if want != got: note("errors", folder, f"ZIP paths differ: missing={sorted(want-got)}, extra={sorted(got-want)}")
            for p in items:
                key=archive_prefix+p.relative_to(mod).as_posix()
                if key in got and z.read(key) != p.read_bytes():
                    note("errors", folder, f"ZIP is STALE, differs from source: {p.relative_to(mod)}")
            status["zip"]="byte-for-byte checked"
    except (BadZipFile, FileNotFoundError) as e:
        note("errors", folder, f"ZIP unreadable: {e}")
    validator = top / "validate.py"
    if folder == 'x4-galactic-occupations': validator=top/'tools/validate.py'
    if not validator.exists():
        status['validator']={'returncode':0,'output':'Generic archive, XML and API checks above; no extension-local validator'}
        continue
    run = subprocess.run([sys.executable, str(validator)], capture_output=True, text=True)
    status["validator"] = {"returncode":run.returncode, "output":(run.stdout + run.stderr)[-1200:]}
    if run.returncode:
        note("errors", folder, f"Validator failed: {run.stderr[-900:] or run.stdout[-900:]}")

# Cross-mod ID collisions and custom source-ref checks.
for folder,(mod,items) in files_by_mod.items():
    for p in items:
        if p.suffix.lower() != ".xml": continue
        content=p.read_text()
        for candidate in set(re.findall(r"\b(?:macro|ware)\.(vardath_[A-Za-z0-9_]+)\b", content)):
            if candidate not in custom_defs and candidate not in ids:
                note("warnings", folder, f"Unresolved Vardath custom reference {candidate} in {p.relative_to(mod)}")
    # Distinguish scripts that only check XML structure vs genuine engine tests.
    report["mods"][folder]["runtime_verified"] = False

bundle=subprocess.run([sys.executable,str(ROOT/'tools/package-x4-update.py'),'--check'],capture_output=True,text=True)
report['update_bundle']={'returncode':bundle.returncode,'output':bundle.stdout+bundle.stderr}
if bundle.returncode: note('errors','update-bundle','Combined update ZIP failed integrity checks')
report['command_provenance']=api['provenance']
report['reviewed_source']='Current worktree; X4 runtime unavailable'
print(json.dumps(report, indent=2))
out = ROOT/"x4-audit-report.json"
out.write_text(json.dumps(report, indent=2)+"\n")
sys.exit(1 if report["errors"] else 0)
