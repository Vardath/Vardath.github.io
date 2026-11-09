#!/usr/bin/env python3
"""Build/check the six current extensions as one correctly nested installation ZIP."""
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'downloads/x4-updates/X4_Hacker_Survey_Update_2026-11-09.zip'
SOURCES=[ROOT/'downloads'/folder/name for folder,name in [
 ('x4-galactic-occupations','vardath_galactic_occupations'),
 ('x4-living-factions-builders','vardath_living_factions_builders'),
 ('x4-kopis-production-cheat','vardath_kopis_production_cheat'),
 ('x4-yaki-terran-habs','vardath_yaki_terran_habs'),
 ('x4-universal-cargo-teleport','vardath_universal_cargo_teleport'),
 ('x4-station-auto-drones','vardath_station_auto_drones')]]
expected={'extensions/'+p.relative_to(src.parent).as_posix():p for src in SOURCES for p in src.rglob('*') if p.is_file()}
if '--check' not in sys.argv:
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with ZipFile(OUT,'w',ZIP_DEFLATED,compresslevel=9) as z:
  for name,p in sorted(expected.items()):
   entry=ZipInfo(name,(2026,11,8,0,0,0));entry.compress_type=ZIP_DEFLATED;entry.external_attr=0o100644<<16;z.writestr(entry,p.read_bytes())
with ZipFile(OUT) as z:
 assert z.testzip() is None,'Archive CRC error'
 assert set(z.namelist())==set(expected),'Archive paths differ from source'
 for name,p in expected.items():assert z.read(name)==p.read_bytes(),'Stale archive member '+name
print(f'PASS: {OUT.name}; {len(SOURCES)} extensions, {len(expected)} byte-matched files')
