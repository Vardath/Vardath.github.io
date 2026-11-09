#!/usr/bin/env python3
"""Build or check the three extensions changed by the Hyperion/tours update."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'downloads/x4-updates/X4_Hyperion_Tours_Update_2026-11-10.zip'
SOURCES = [ROOT / 'downloads' / folder / name for folder, name in [
    ('x4-galactic-occupations', 'vardath_galactic_occupations'),
    ('x4-compatibility-fixes', 'vardath_compatibility_fixes'),
    ('x4-hyperion-ascendant', 'vardath_hyperion_ascendant'),
]]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = {'extensions/' + p.relative_to(src.parent).as_posix(): p
                for src in SOURCES for p in src.rglob('*') if p.is_file()}
    if not all(src.is_dir() for src in SOURCES):
        raise ValueError('Missing extension source directory')
    if not args.check:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(OUT, 'w', ZIP_DEFLATED, compresslevel=9) as archive:
            for name, path in sorted(expected.items()):
                entry = ZipInfo(name, (2026, 11, 10, 0, 0, 0))
                entry.compress_type = ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())
    with ZipFile(OUT) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive CRC error')
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise ValueError('Archive members differ from the three extension folders')
        for name, path in expected.items():
            if archive.read(name) != path.read_bytes():
                raise ValueError('Stale archive member: ' + name)
    print(f'PASS: {OUT.name}; three extensions, {len(expected)} byte-matched files')

if __name__ == '__main__':
    main()
