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


def _stat_identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)


def _windows_handle_identity(f):
    """Compare actual handles using the same Windows native file ID API.

    Path stat and descriptor fstat may report different IDs or timestamp
    representations on Windows (including 128-bit path inode values).
    FileIdInfo supplies volume identity and the full 128-bit file ID.
    """
    import ctypes
    import msvcrt
    from ctypes import wintypes
    class FileIdInfo(ctypes.Structure):
        _fields_=[('volume',ctypes.c_ulonglong),('identifier',ctypes.c_ubyte*16)]
    info=FileIdInfo()
    query=ctypes.WinDLL('kernel32',use_last_error=True).GetFileInformationByHandleEx
    query.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
    query.restype=wintypes.BOOL
    if not query(msvcrt.get_osfhandle(f.fileno()),18,ctypes.byref(info),ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    identifier=bytes(info.identifier)
    if not any(identifier):raise ValueError('Windows file identity unavailable')
    stat=os.fstat(f.fileno())
    return (info.volume,identifier,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)


def _file_digest(path: Path) -> str:
    _regular(path)
    before=path.stat()
    if before.st_size > MAX_HASH_BYTES:
        raise ValueError('File exceeds approved hash-check limit')
    h = hashlib.sha256()
    total=0
    with path.open('rb') as f:
        if os.name=='nt':
            handle_before=_windows_handle_identity(f)
            # Compare like with like: path snapshots separately, and two
            # opened handles through the native identity API. Do not weaken
            # the content digest or allow an unidentified file.
            with path.open('rb') as current:
                if _windows_handle_identity(current)!=handle_before:
                    raise ValueError('File changed while opening for hash check')
            if handle_before[2]!=before.st_size or _stat_identity(path.stat())!=_stat_identity(before):
                raise ValueError('File changed while opening for hash check')
        else:
            handle_before=_stat_identity(os.fstat(f.fileno()))
            if handle_before!=_stat_identity(before):
                raise ValueError('File changed while opening for hash check')
        while True:
            chunk=f.read(min(1024*1024,MAX_HASH_BYTES-total+1))
            if not chunk:break
            total+=len(chunk)
            if total>MAX_HASH_BYTES:
                raise ValueError('File exceeds approved hash-check limit')
            h.update(chunk)
        after_handle=(_windows_handle_identity(f) if os.name=='nt' else _stat_identity(os.fstat(f.fileno())))
        if total!=before.st_size or after_handle!=handle_before:
            raise ValueError('File changed during hash check')
        _regular(path)
        if os.name=='nt':
            with path.open('rb') as current:
                if _windows_handle_identity(current)!=handle_before:
                    raise ValueError('File replaced during hash check')
    _regular(path)
    if _stat_identity(path.stat())!=_stat_identity(before):
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
