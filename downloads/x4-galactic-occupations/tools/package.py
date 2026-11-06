#!/usr/bin/env python3
"""Create deterministic, correctly nested X4 extension ZIP; validate before and after."""
from pathlib import Path
import subprocess
import sys
import zipfile

base = Path(__file__).resolve().parents[1]
mod = base / 'vardath_galactic_occupations'
archive = base / 'Galactic_Occupations_0.2.0_DEV.zip'
subprocess.run([sys.executable,str(base/'tools/validate.py')],check=True)
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for path in sorted(p for p in mod.rglob('*') if p.is_file()):
        info = zipfile.ZipInfo('extensions/'+path.relative_to(mod.parent).as_posix(),date_time=(2026,11,6,0,0,0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        output.writestr(info,path.read_bytes())
subprocess.run([sys.executable,str(base/'tools/validate.py'),'--zip',str(archive),'--report',str(base/'STATIC_TEST_RESULTS.json')],check=True)
print(archive)
