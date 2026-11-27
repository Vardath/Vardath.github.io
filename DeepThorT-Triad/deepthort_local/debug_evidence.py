"""Resolve recorded Python traceback frames against current indexed project sources."""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from .repository_index import _read,IndexCancelled
FRAME=re.compile(r'^\s*File "([^"\r\n]{1,500})", line ([1-9][0-9]{0,6})(?:, in ([^\r\n]{1,120}))?\s*$')
MAX_LOG=24000

def candidates(root,diagnostic,rows,exclude=(),cancelled=None):
    """Only exact project-relative or in-project absolute paths; no basename guesses."""
    if not isinstance(diagnostic,str):raise ValueError('Diagnostic text required')
    root=Path(root).resolve(strict=True)
    hits=[];seen=set()
    for line in reversed(diagnostic[-MAX_LOG:].splitlines()):
        if cancelled and cancelled():raise IndexCancelled('Debug evidence cancelled')
        match=FRAME.fullmatch(line)
        if not match:continue
        path=Path(match[1]);n=int(match[2])
        # Resolve neither an external path nor a symlink outside the root.
        if path.is_absolute():
            try:relative=path.relative_to(root).as_posix()
            except ValueError:continue
        else:
            relative=match[1].replace('\\','/')
        if relative not in rows or not relative.endswith('.py') or (relative,n) in seen:continue
        seen.add((relative,n))
        try:
            raw=_read(root,relative,exclude);digest=hashlib.sha256(raw).hexdigest()
            if digest!=rows[relative][0]:continue
            lines=raw.decode('utf-8-sig').splitlines()
            if not 1<=n<=len(lines):continue
            source=lines[n-1]
            if len(source)>240 or any(ord(c)<32 and c!='\t' for c in source):continue
            # No exact old source hash is available in a text traceback. Mark
            # current bytes as current evidence, never as failure-time proof.
            hits.append({'path':relative,'sha256':digest,'line':n,'source':source,
                'scope':'current source at reported frame; failure-time identity unverified'})
        except (OSError,ValueError):continue
        if len(hits)>=3:break
    return hits
