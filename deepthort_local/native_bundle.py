"""Hash-bound native asset staging; never overwrite workspace files."""
from __future__ import annotations
import hashlib
import io
import os
from pathlib import Path
import re
import stat
import tempfile
import zipfile
from .workspace import safe_target

MAX_BUNDLE_BYTES=100_000_000
MAX_MEMBERS=2000
_ALLOWED=re.compile(r'[a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*')
_RESERVED={'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),
           *(f'LPT{i}' for i in range(1,10))}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def inspect_bundle(blob,package):
    """Read only generated extension members; never extract arbitrary ZIP paths."""
    if not isinstance(blob,bytes) or len(blob)>MAX_BUNDLE_BYTES:
        raise ValueError('Native bundle exceeds size limit')
    if not re.fullmatch(r'[a-z0-9_][a-z0-9_-]*',package):
        raise ValueError('Explicit extension identifier required')
    result={}
    seen=set()
    total=0
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        members=archive.infolist()
        if len(members)>MAX_MEMBERS:
            raise ValueError('Too many native bundle members')
        for member in members:
            name=member.filename
            total+=member.file_size
            if total>MAX_BUNDLE_BYTES:
                raise ValueError('Uncompressed native bundle exceeds limit')
            if (member.is_dir() or stat.S_ISLNK(member.external_attr>>16)
                    or member.flag_bits&1 or '\\' in name):
                raise ValueError('Unsupported native bundle member')
            if name.casefold() in seen:
                raise ValueError('Duplicate native bundle member')
            seen.add(name.casefold())
            if name in ('Preview_MainHull_and_Rock.obj','Attachment_measurements.json'):
                continue
            parts=name.split('/')
            if (len(parts)<3 or parts[0]!=package or parts[1] not in ('assets','index')
                    or any(not _ALLOWED.fullmatch(p) or p.split('.')[0].upper() in _RESERVED for p in parts)):
                raise ValueError('Unexpected native bundle path: '+name)
            relative='/'.join(parts[1:])
            if not relative.startswith('assets/') and relative not in ('index/macros.xml','index/components.xml'):
                raise ValueError('Unexpected native registry: '+relative)
            data=archive.read(member)
            if not data:
                raise ValueError('Empty native asset: '+relative)
            result[relative]=data
    if not {'index/macros.xml','index/components.xml'}<=result.keys() or not any(
            p.startswith('assets/') and p.endswith('.xmf') for p in result):
        raise ValueError('Native bundle lacks required registry or geometry members')
    return result


def review_bundle(blob,package,project):
    root=Path(project).resolve(strict=True)
    members=inspect_bundle(blob,package)
    files={}
    conflicts=[]
    matching=0
    for relative,data in sorted(members.items()):
        target=safe_target(root,relative)
        checksum=digest(data)
        files[relative]=checksum
        if target.exists():
            if target.is_file() and target.stat().st_size==len(data) and file_digest(target)==checksum:
                matching+=1
            else:
                conflicts.append(relative)
    return {'project':str(root),'package':package,'bundle_sha256':digest(blob),
            'files':files,'matching':matching,'conflicts':conflicts}


def materialize_bundle(blob,package,project,approved_review):
    """Resume matching assets; create missing files atomically without replacing."""
    current=review_bundle(blob,package,project)
    for key in ('project','package','bundle_sha256','files'):
        if current[key]!=approved_review.get(key):
            raise ValueError('Native bundle or destination changed after review')
    if current['conflicts']:
        raise ValueError('Existing files differ; no native files written: '+', '.join(current['conflicts'][:6]))
    root=Path(current['project'])
    members=inspect_bundle(blob,package)
    created=0
    for relative,data in sorted(members.items()):
        target=safe_target(root,relative)
        checksum=current['files'][relative]
        if target.exists():
            if target.is_file() and target.stat().st_size==len(data) and file_digest(target)==checksum:
                continue
            raise ValueError('Destination changed during native import: '+relative)
        target.parent.mkdir(parents=True,exist_ok=True)
        target=safe_target(root,relative)
        fd,name=tempfile.mkstemp(prefix='.deepthort-native-',suffix='.tmp',dir=target.parent)
        tmp=Path(name)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if file_digest(tmp)!=checksum:
                raise ValueError('Native temporary file checksum mismatch')
            try:
                os.link(tmp,target)
                created+=1
            except FileExistsError:
                if not target.is_file() or target.is_symlink() or file_digest(target)!=checksum:
                    raise ValueError('Destination changed during native import: '+relative)
        finally:
            tmp.unlink(missing_ok=True)
    final=review_bundle(blob,package,root)
    if final['conflicts'] or final['matching']!=len(final['files']):
        raise ValueError('Native artifact verification incomplete')
    return {'created':created,'verified':final['matching'],'bundle_sha256':final['bundle_sha256']}
