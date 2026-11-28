"""Bounded, explicit read-only Studio artifact inspection; never executes a file."""
from __future__ import annotations
import hashlib
import os
import stat
from pathlib import Path
from .workspace import MAX_READ_BYTES, safe_target, WorkspaceError

PREVIEW_CHARS = 12000
TEXT_SUFFIXES = frozenset({'.txt','.md','.csv','.tsv','.json','.ipynb','.svg','.obj','.gltf'})
RECENT_JOB_LIMIT = 20
MATCH_LIMIT = 5


def inspect_bytes(root, relative):
    target = safe_target(root, relative, must_exist=True)
    first = target.stat()
    if not stat.S_ISREG(first.st_mode):
        raise WorkspaceError('Not a regular file')
    if first.st_size > MAX_READ_BYTES:
        return {'size':first.st_size,'suffix':target.suffix,'sha256':None,'preview':None,
                'note':'File exceeds the existing gaming-safe inspection limit; no contents read.'}
    with target.open('rb') as stream:
        start = os.fstat(stream.fileno())
        if not stat.S_ISREG(start.st_mode) or start.st_size > MAX_READ_BYTES:
            raise WorkspaceError('File changed before inspection')
        data = stream.read(MAX_READ_BYTES+1)
        end = os.fstat(stream.fileno())
    final = safe_target(root, relative, must_exist=True).stat()
    def identity(value):
        return (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
    if len(data)>MAX_READ_BYTES or len(data)!=start.st_size or not (
            identity(first)==identity(start)==identity(end)==identity(final)):
        raise WorkspaceError('File changed during inspection; refresh and inspect again')
    preview = None
    note = 'Binary or unsupported preview format; no decoding or execution.'
    if target.suffix.casefold() in TEXT_SUFFIXES:
        try:
            decoded = data.decode('utf-8-sig')
        except UnicodeError:
            note = 'Not valid UTF-8; no text preview.'
        else:
            if '\x00' not in decoded:
                # Plain text only, with control characters made visible rather than interpreted.
                preview = ''.join(c if c.isprintable() or c in '\n\t\r' else
                                  '\\x%02x'%ord(c) for c in decoded[:PREVIEW_CHARS])
                note = ('Text preview truncated at 12,000 characters.' if len(decoded)>PREVIEW_CHARS
                        else 'Complete UTF-8 text preview.')
    return {'size':len(data),'suffix':target.suffix,'sha256':hashlib.sha256(data).hexdigest(),
            'preview':preview,'note':note}


def matching_checkpoints(project, relative, digest, jobs, checkpoints):
    """Report exact matching sealed source manifests, not author or test claims."""
    if not digest:return []
    resolved = str(Path(project).resolve(strict=True))
    result = []
    for job in jobs.items(project,limit=RECENT_JOB_LIMIT):
        if job.get('project')!=project or job.get('mode')!='build':continue
        if not any(step.get('path')==relative for step in jobs.steps(job['id'])):continue
        for row in reversed(checkpoints.list(job['id'])):
            if row.get('project')!=resolved or row.get('job_id')!=job['id']:continue
            if row.get('files',{}).get(relative)!=digest:continue
            result.append((job['id'],row['id'],row['reason']))
            if len(result)>=MATCH_LIMIT:return result
    return result
