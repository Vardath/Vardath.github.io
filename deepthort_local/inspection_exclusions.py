"""Per-project project-file inspection exclusions (NOT deletion or work approval).

Only this file in DeepThorT's own state folder changes. Source files in the
selected project or installed game are never moved, deleted, or overwritten.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

SCHEMA = 'deepthort-project-inspection-exclusions-v1'
MAX_EXCLUSIONS = 4096


def project_identity(root: str | Path) -> str:
    return hashlib.sha256(str(Path(root).resolve()).casefold().encode('utf-8')).hexdigest()


def normalized_relative(path: str) -> str:
    if not isinstance(path, str) or not path.strip() or '\x00' in path:
        raise ValueError('Select an actual project file')
    value = path.replace('\\', '/')
    parts = value.split('/')
    if any(p in ('', '.', '..') for p in parts) or value.startswith('/') or ':' in parts[0]:
        raise ValueError('Only a project-relative file can be excluded')
    if len(value) > 4096:
        raise ValueError('Project-relative file name too long')
    return value.casefold()


class InspectionExclusions:
    def __init__(self, state_file: str | Path):
        self.path = Path(state_file)

    def _load(self) -> dict:
        try:
            value = json.loads(self.path.read_text('utf-8'))
        except FileNotFoundError:
            return {'schema': SCHEMA, 'projects': {}}
        if not isinstance(value, dict) or value.get('schema') != SCHEMA or not isinstance(value.get('projects'), dict):
            raise ValueError('Inspection exclusion store is damaged; refusing to overwrite it')
        return value

    def paths(self, root: str | Path) -> set[str]:
        records = self._load().get('projects', {}).get(project_identity(root), [])
        if not isinstance(records, list):
            raise ValueError('Invalid project inspection exclusion list')
        return {normalized_relative(p) for p in records}

    def _save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.inspection-', suffix='.json', dir=str(self.path.parent))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, sort_keys=True)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def exclude(self, root: str | Path, relative: str) -> None:
        name = normalized_relative(relative)
        data = self._load()
        key = project_identity(root)
        selected = set(self.paths(root))
        selected.add(name)
        if len(selected) > MAX_EXCLUSIONS:
            raise ValueError('Inspection exclusion limit reached')
        data['projects'][key] = sorted(selected)
        self._save(data)

    def restore(self, root: str | Path, relative: str | None = None) -> None:
        data = self._load()
        key = project_identity(root)
        if relative is None:
            data['projects'].pop(key, None)
        else:
            selected = set(self.paths(root))
            selected.discard(normalized_relative(relative))
            if selected:
                data['projects'][key] = sorted(selected)
            else:
                data['projects'].pop(key, None)
        self._save(data)

    def filter(self, root: str | Path, candidates: list[str]) -> list[str]:
        excluded = self.paths(root)
        return [p for p in candidates if normalized_relative(p) not in excluded]
