#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import subprocess, sys
base=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(base/"tools/validate.py")],check=True)
src=base/"patches/gt_fleet_view.lua"
dst=base/"GT_Fleet_UI_Hotfix_1.0.zip"
with ZipFile(dst, "w", ZIP_DEFLATED,compresslevel=9) as z:
    info=ZipInfo("extensions/galaxy_trader/ui/gt_fleet_view.lua",(2026,11,13,0,0,0))
    info.compress_type=ZIP_DEFLATED
    info.external_attr=0o100644<<16
    z.writestr(info,src.read_bytes())
subprocess.run([sys.executable,str(base/"tools/validate.py"),"--zip"],check=True)
print(dst)
