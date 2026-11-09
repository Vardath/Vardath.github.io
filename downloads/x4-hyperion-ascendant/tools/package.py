#!/usr/bin/env python3
import argparse,json,tempfile
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from validate import BASE,MOD,validate

p=argparse.ArgumentParser();p.add_argument('--source-cache',type=Path);a=p.parse_args()
archive=BASE/'Hyperion_Ascendant_1.0.1.zip'
with tempfile.TemporaryDirectory() as tmp:
    cache=a.source_cache or Path(tmp);validate(cache)
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for source in sorted(x for x in MOD.rglob('*') if x.is_file()):
            info=ZipInfo('extensions/'+MOD.name+'/'+source.relative_to(MOD).as_posix(),date_time=(2026,11,10,0,0,0))
            info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644 << 16;z.writestr(info,source.read_bytes())
    report=validate(cache,archive)
(BASE/'STATIC_TEST_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
print(archive)
