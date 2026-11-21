"""Conservative, human-approved project file access for DeepThorT desktop.

No autonomous writes. No files outside the selected workspace, including symlink targets.
"""
from __future__ import annotations
import difflib
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

SKIP_DIRS = frozenset({'.git', '.venv', 'venv', 'node_modules', 'models', 'dist',
                       'build', '__pycache__', '.next', '.cache', '.idea', '.vs'})
MAX_READ_BYTES = 180_000
MAX_WRITE_BYTES = 220_000

class WorkspaceError(ValueError):
    pass


def safe_target(root: str | Path, relative: str, *, must_exist: bool = False) -> Path:
    """Resolve path and reject traversal, absolute paths and symlink escapes."""
    if not isinstance(relative, str) or not relative.strip() or '\x00' in relative:
        raise WorkspaceError('A relative file path is required')
    rel = Path(relative.replace('\\', '/'))
    if rel.is_absolute() or rel.anchor or '..' in rel.parts or '.' == relative.strip():
        raise WorkspaceError('Choose a file inside the selected project')
    base = Path(root).expanduser().resolve(strict=True)
    if not base.is_dir():
        raise WorkspaceError('Project folder is missing')
    target = (base / rel).resolve(strict=False)
    try:
        target.relative_to(base)
    except ValueError:
        raise WorkspaceError('File escapes the selected project') from None
    if target == base:
        raise WorkspaceError('Select a file, not the project folder')
    if must_exist and (not target.is_file() or target.is_symlink()):
        raise WorkspaceError('File not found or unsupported')
    return target


def list_project_files(root: str | Path, *, limit: int = 600) -> list[str]:
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise WorkspaceError('Project folder is missing')
    result: list[str] = []
    for directory, dirs, filenames in os.walk(base, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and
                         not d.startswith('.') and not (Path(directory) / d).is_symlink())
        for filename in sorted(filenames):
            if filename.startswith('.'):
                continue
            path = Path(directory) / filename
            if path.is_symlink() or not path.is_file():
                continue
            if path.stat().st_size > MAX_READ_BYTES:
                continue
            result.append(path.relative_to(base).as_posix())
            if len(result) >= limit:
                return result
    return result


def read_project_file(root: str | Path, relative: str) -> str:
    target = safe_target(root, relative, must_exist=True)
    if target.stat().st_size > MAX_READ_BYTES:
        raise WorkspaceError('File too large for the gaming-safe code preview')
    try:
        text = target.read_text(encoding='utf-8')
    except (UnicodeError, OSError) as exc:
        raise WorkspaceError(f'Not a readable UTF-8 text file: {exc}') from exc
    if '\x00' in text:
        raise WorkspaceError('Binary files cannot be edited')
    return text


def strip_single_code_fence(response: str) -> str:
    """Accept plain text or one fenced code block; reject ambiguous prose+blocks."""
    s = response.strip()
    if not s.startswith('```'):
        if '```' in s:
            raise WorkspaceError('Model mixed prose with code; revise before applying')
        return response
    lines = s.splitlines(keepends=True)
    if len(lines) < 3 or not lines[0].startswith('```'):
        raise WorkspaceError('Invalid code block')
    if not lines[-1].strip() == '```' or any(line.lstrip().startswith('```') for line in lines[1:-1]):
        raise WorkspaceError('Multiple or unfinished code blocks; revise first')
    return ''.join(lines[1:-1])


def diff_preview(old: str, new: str, relative: str) -> str:
    return ''.join(difflib.unified_diff(old.splitlines(keepends=True),
                                        new.splitlines(keepends=True),
                                        fromfile='before/'+relative,
                                        tofile='after/'+relative)) or '(no changes)'


def apply_approved_file(root: str | Path, relative: str, contents: str,
                        backup_root: str | Path) -> Path:
    """Write only after GUI approval, with a time-stamped backup of an existing file."""
    if not isinstance(contents, str) or not contents.strip() or len(contents.encode('utf-8')) > MAX_WRITE_BYTES:
        raise WorkspaceError('Proposed file is empty or exceeds 220 KB')
    target = safe_target(root, relative)
    if target.exists() and not target.is_file():
        raise WorkspaceError('Target is not a regular file')
    if target.exists():
        previous = read_project_file(root, relative)
        if previous == contents:
            return target
        archive = Path(backup_root).resolve() / datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f') / relative
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, archive)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name+'.deepthort-tmp')
    if tmp.exists():
        raise WorkspaceError('An unfinished temporary file already exists; inspect it manually')
    try:
        with tmp.open('x', encoding='utf-8', newline='') as f:
            f.write(contents)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target
