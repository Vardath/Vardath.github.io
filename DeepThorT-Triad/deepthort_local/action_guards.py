"""Pinned file preconditions for *already user-approved* JANUS processes.

Checks are re-evaluated immediately before a child process is spawned. They
protect against ordinary edits, application upgrades, and queued stale work;
they are not a security sandbox against hostile code or filesystem races.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

MAX_GUARDS = 10
MAX_HASH_BYTES = 32_000_000
_SHA = re.compile(r'^[0-9a-f]{64}$')


def _regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError('Pinned file missing or is a symlink')


def _stat_digest(path: Path) -> str:
    _regular(path)
    s = path.stat()
    value = [str(path.resolve()).casefold(), s.st_size, s.st_mtime_ns]
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def _file_digest(path: Path) -> str:
    _regular(path)
    def identity(s):
        return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    before=path.stat()
    if before.st_size > MAX_HASH_BYTES:
        raise ValueError('File exceeds approved hash-check limit')
    h = hashlib.sha256()
    total=0
    with path.open('rb') as f:
        if identity(os.fstat(f.fileno()))!=identity(before):
            raise ValueError('File changed while opening for hash check')
        while True:
            chunk=f.read(min(1024*1024,MAX_HASH_BYTES-total+1))
            if not chunk:break
            total+=len(chunk)
            if total>MAX_HASH_BYTES:
                raise ValueError('File exceeds approved hash-check limit')
            h.update(chunk)
        if total!=before.st_size or identity(os.fstat(f.fileno()))!=identity(before):
            raise ValueError('File changed during hash check')
    _regular(path)
    if identity(path.stat())!=identity(before):
        raise ValueError('File changed during hash check')
    return h.hexdigest()


def snapshot_file(path: str | Path, *, kind: str = 'sha256') -> dict:
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Pinned paths must be absolute')
    if kind == 'absent':
        if path.exists() or path.is_symlink():
            raise ValueError('Output appeared since approval')
        return {'path': str(path), 'kind': 'absent'}
    if kind not in ('sha256', 'stat'):
        raise ValueError('Unknown file precondition')
    return {'path': str(path), 'kind': kind,
            'expected': _file_digest(path) if kind == 'sha256' else _stat_digest(path)}


def validate_guards(guards: list[dict] | None) -> list[dict]:
    if guards is None:
        return []
    if not isinstance(guards, list) or len(guards) > MAX_GUARDS:
        raise ValueError('Too many execution preconditions')
    seen = set()
    for item in guards:
        if not isinstance(item, dict) or set(item) not in ({'path', 'kind'}, {'path', 'kind', 'expected'}):
            raise ValueError('Invalid execution precondition')
        p = item.get('path')
        k = item.get('kind')
        if not isinstance(p, str) or len(p) > 1024 or '\0' in p or not Path(p).is_absolute():
            raise ValueError('Pinned file path must be absolute')
        if p.casefold() in seen:
            raise ValueError('Duplicate execution precondition')
        seen.add(p.casefold())
        if k == 'absent':
            if 'expected' in item:
                raise ValueError('Absent-file precondition has unexpected digest')
        elif k in ('sha256', 'stat'):
            if not isinstance(item.get('expected'), str) or not _SHA.fullmatch(item['expected']):
                raise ValueError('Invalid file precondition digest')
        else:
            raise ValueError('Invalid execution precondition type')
    return guards


def verify_guards(guards: list[dict]) -> None:
    validate_guards(guards)
    for item in guards:
        path = Path(item['path'])
        kind = item['kind']
        if kind == 'absent':
            if path.exists() or path.is_symlink():
                raise ValueError(f'Approved output target changed before execution: {path.name}')
            continue
        try:
            digest = _file_digest(path) if kind == 'sha256' else _stat_digest(path)
        except (OSError, ValueError) as exc:
            raise ValueError(f'Approved file unavailable before execution: {path.name}') from exc
        if digest != item['expected']:
            raise ValueError(f'Approved file changed before execution: {path.name}')
