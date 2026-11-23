"""Read-only, narrowly scoped X4 vanilla references for the selected project UI.

Game installation / extracted source XML is NEVER part of the writable project.
All referenced files must be explicitly found and hashed by inspect_x4_sources.
No broad filesystem indexing, extraction, or file copying is performed here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

MAX_VISIBLE = 14
MAX_PREVIEW_BYTES = 180_000


def relevant_x4_sources(report: dict | None, *, limit: int = MAX_VISIBLE) -> list[dict]:
    """Select a small, diverse set of *observed* X4 XML, not guessed paths."""
    if not isinstance(report, dict) or not report.get('reference_dir'):
        return []
    output=[]
    seen=set()
    def add(item, role):
        if not isinstance(item, dict):
            return
        rel=item.get('file')
        digest=item.get('sha256')
        if not isinstance(rel,str) or not rel.endswith('.xml') or not isinstance(digest,str) or len(digest)!=64:
            return
        if rel.casefold() in seen:
            return
        try:
            int(digest,16)
            p=Path(rel.replace('\\','/'))
            if p.is_absolute() or not p.parts or '..' in p.parts:
                return
        except (ValueError,TypeError):
            return
        seen.add(rel.casefold())
        output.append({'file':p.as_posix(),'sha256':digest,'role':role,'reference_dir':report['reference_dir']})
    for x in report.get('ship_candidates',[]):
        if 'ship_xen_m_corvette_02_a_macro' in x.get('identifiers',[]):
            add(x,'PE ship macro — verified')
            break
    if report.get('pe_component_file') and report.get('pe_component_sha256'):
        add({'file':report['pe_component_file'],'sha256':report['pe_component_sha256']},'PE component slots — verified')
    for category,label in (('ship_candidates','Ship candidate'),('turret_candidates','Turret candidate'),
                           ('weapon_candidates','Weapon candidate'),('storage_candidates','Storage candidate'),
                           ('files','X4 library/index')):
        for candidate in report.get(category,[])[:4]:
            add(candidate,label)
            if len(output)>=max(1,min(limit,MAX_VISIBLE)):
                return output
    return output[:max(1,min(limit,MAX_VISIBLE))]


def read_verified_x4_source(entry: dict, *, max_bytes: int = MAX_PREVIEW_BYTES) -> str:
    """Only XML matching the observed hash; symlink-free, strictly read-only."""
    root=Path(entry['reference_dir']).resolve(strict=True)
    rel=Path(entry['file'])
    if (not root.is_dir() or not rel.parts or rel.is_absolute() or '..' in rel.parts
            or rel.suffix.lower()!='.xml'):
        raise ValueError('Invalid X4 source reference')
    item=root
    for part in rel.parts:
        item=item/part
        if item.is_symlink():
            raise ValueError('X4 reference symlinks cannot be inspected')
    target=item.resolve(strict=True)
    if not target.is_file() or not target.is_relative_to(root):
        raise ValueError('X4 source path escapes extracted reference directory')
    if target.stat().st_size>max_bytes:
        raise ValueError('X4 XML exceeds bounded preview allowance')
    data=target.read_bytes()
    if hashlib.sha256(data).hexdigest()!=entry['sha256']:
        raise ValueError('X4 source changed since inspection; refresh source discovery')
    content=data.decode('utf-8')
    if '\x00' in content:
        raise ValueError('X4 reference is not a text XML file')
    return content
