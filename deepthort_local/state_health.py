"""Read-only bounded crash-recovery checks for the local DeepThorT state.

The report is metadata, not a database backup and not a repair operation. It
must never contain raw prompts, SQL row data, environment variables or secrets.
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

MAX_DATABASES=30
MIN_FREE_BYTES=150_000_000


def inspect_state(state: str | Path) -> dict:
    root=Path(state)
    result={'disk_free_bytes': None, 'disk_low': False, 'databases_checked': 0,
            'databases': [], 'issues': []}
    try:
        free=shutil.disk_usage(root if root.exists() else root.parent).free
        result['disk_free_bytes']=int(free)
        if free<MIN_FREE_BYTES:
            result['disk_low']=True
            result['issues'].append('Storage is below 150 MB available; avoid new builds or model downloads')
    except OSError:
        result['issues'].append('Could not inspect free storage')
    if not root.is_dir():
        result['issues'].append('Local state folder missing')
        return result
    for p in sorted(root.glob('*.sqlite3'))[:MAX_DATABASES]:
        if p.is_symlink() or not p.is_file():
            continue
        record={'name':p.name[:100], 'bytes':None, 'quick_check':'unavailable'}
        try:
            record['bytes']=p.stat().st_size
            # URI read-only mode prevents accidental repairs/creation. Query one
            # integrity finding only; timeouts on locked databases are reported.
            conn=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)
            try:
                conn.execute('PRAGMA busy_timeout=1000')
                check=conn.execute('PRAGMA quick_check(1)').fetchone()
                record['quick_check']='ok' if check and check[0]=='ok' else 'failed'
            finally:conn.close()
            if record['quick_check']!='ok':
                result['issues'].append('A state database failed integrity inspection: '+p.name[:100])
        except (sqlite3.Error,OSError,ValueError):
            record['quick_check']='error_or_locked'
            result['issues'].append('A state database could not be inspected: '+p.name[:100])
        result['databases'].append(record)
    result['databases_checked']=len(result['databases'])
    return result
