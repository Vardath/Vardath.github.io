#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import xml.etree.ElementTree as ET
base=Path(__file__).resolve().parent;mod=base/'vardath_universal_cargo_teleport';files=sorted(p for p in mod.rglob('*') if p.is_file())
for p in files:
    if p.suffix=='.xml':ET.parse(p)
target=base/(mod.name+'_TEST.zip')
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        info=ZipInfo(p.relative_to(base).as_posix(),(2026,11,7,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
with ZipFile(target) as z:
    assert z.testzip() is None
    assert set(z.namelist())=={p.relative_to(base).as_posix() for p in files}
    for p in files:assert z.read(p.relative_to(base).as_posix())==p.read_bytes()
print('PASS:',target.name,'source/ZIP parity')
