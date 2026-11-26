"""Exact, bounded interactive source editing using the existing backup writer."""
from __future__ import annotations
import hashlib
from pathlib import Path
from .workspace import safe_target,apply_approved_file,MAX_READ_BYTES,MAX_WRITE_BYTES,WorkspaceError,diff_preview
from .staged_source import validate_source

def digest(raw):return hashlib.sha256(raw).hexdigest()

def snapshot(root,relative,*,allow_missing=False):
    project=Path(root).resolve(strict=True)
    target=safe_target(project,relative)
    rel=target.relative_to(project).as_posix()
    if any(part.startswith('.') or part.casefold() in ('state','models','runtime','backups','node_modules','__pycache__') for part in rel.split('/')):
        raise WorkspaceError('Protected or hidden path is not an interactive edit target')
    if target.suffix.casefold() in ('.exe','.dll','.msi','.lnk','.sys','.com','.scr'):
        raise WorkspaceError('Executable or binary format is not a source edit target')
    if not target.exists():
        if not allow_missing:raise WorkspaceError('Select an existing source file')
        raw=b'';sha=None
    else:
        if not target.is_file() or target.stat().st_size>MAX_READ_BYTES:raise WorkspaceError('Source exceeds bounded regular file limit')
        raw=target.read_bytes()
        if len(raw)>MAX_READ_BYTES:raise WorkspaceError('Source exceeds bounded read limit')
        sha=digest(raw)
    try:text=raw.decode('utf-8-sig')
    except UnicodeError as exc:raise WorkspaceError('Only UTF-8 source files can be edited') from exc
    if '\0' in text:raise WorkspaceError('Binary source cannot be edited')
    # Preserve existing newline convention and BOM; refuse mixed/bare CR rather than silently rewrite.
    rest=text.replace('\r\n','')
    if '\r' in rest or ('\r\n' in text and '\n' in rest):
        raise WorkspaceError('Mixed or bare-CR newlines require an external editor')
    return {'project':str(project),'path':rel,'sha':sha,'text':text.replace('\r\n','\n'),
            'newline':'\r\n' if '\r\n' in text else '\n','bom':raw.startswith(b'\xef\xbb\xbf')}

def prepare(base,text):
    if not isinstance(text,str) or not text.strip() or '\0' in text:
        raise WorkspaceError('Empty or binary changes are not accepted')
    text=text.replace('\r\n','\n')
    if '\r' in text:raise WorkspaceError('Invalid newline in editor')
    if text==base['text']:raise WorkspaceError('No source changes to approve')
    rendered=('\ufeff' if base['bom'] else '')+text.replace('\n',base['newline'])
    if len(rendered.encode('utf-8'))>MAX_WRITE_BYTES:raise WorkspaceError('Edited source exceeds write limit')
    checked=validate_source(base['path'],text)
    return {'base':base,'text':text,'rendered':rendered,'diff':diff_preview(base['text'],text,base['path']),
            'candidate_sha':digest(rendered.encode('utf-8')),'syntax_checked':checked}

def save(review,backup_root):
    base=review['base']
    actual=snapshot(base['project'],base['path'],allow_missing=base['sha'] is None)
    if actual!=base:raise WorkspaceError('Source changed after editing began; reopen and review current source')
    if prepare(base,review['text'])!=review:raise WorkspaceError('Approved edit changed')
    dest=apply_approved_file(base['project'],base['path'],review['rendered'],backup_root,expected_existing_sha=base['sha'])
    if digest(dest.read_bytes())!=review['candidate_sha']:raise WorkspaceError('Saved bytes differ; inspect backup and current source')
    return dest
