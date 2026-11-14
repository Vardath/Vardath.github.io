#!/usr/bin/env python3
"""Deterministic extension archive; source validation before and after."""
import argparse
import json
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from validate import BASE, MOD, validate

parser=argparse.ArgumentParser()
parser.add_argument('--source-cache',type=Path)
args=parser.parse_args()
archive=BASE/'Vardath_Compatibility_Fixes_1.0.7.zip'
with tempfile.TemporaryDirectory() as tmp:
    cache=args.source_cache or Path(tmp)
    validate(cache)
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(p for p in MOD.rglob('*') if p.is_file()):
            info=ZipInfo('extensions/'+MOD.name+'/'+p.relative_to(MOD).as_posix(),date_time=(2026,11,9,0,0,0))
            info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644 << 16
            z.writestr(info,p.read_bytes())
    report=validate(cache,archive)
(BASE/'STATIC_TEST_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(archive)
