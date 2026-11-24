"""Exact-input continuation of structural model-authored planning fragments.

A resumed fragment is NOT a validated plan or an approval. The ordinary domain
validator must pass again before the user can approve a build. Distinct specs,
project roots, and X4 evidence never share partial plans.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

SCHEMA = 'deepthort-model-plan-continuation-v1'
MAX_STEPS = 24


class PlanContinuation:
    def __init__(self, state_dir: str | Path):
        self.root = Path(state_dir) / 'planning-continuations'

    def _key(self, project: str | Path, request: str, evidence: str, context: str = '') -> str:
        identity = {'schema': SCHEMA, 'project': str(Path(project).resolve()).casefold(),
                    'request': request, 'evidence': evidence, 'context_sha256': hashlib.sha256(context.encode('utf-8')).hexdigest()}
        return hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()

    def _path(self, project: str | Path, request: str, evidence: str, context: str = '') -> Path:
        return self.root / (self._key(project, request, evidence, context) + '.json')

    def load(self, project: str | Path, request: str, evidence: str, *, context: str = '') -> list[dict]:
        path = self._path(project, request, evidence, context)
        try:
            data = json.loads(path.read_text('utf-8'))
        except FileNotFoundError:
            return []
        if not isinstance(data, dict) or data.get('schema') != SCHEMA or data.get('key') != path.stem:
            raise ValueError('Saved planning continuation is invalid; it will not be reused')
        steps = data.get('steps')
        if not isinstance(steps, list) or len(steps) > MAX_STEPS:
            raise ValueError('Saved planning continuation has an invalid file count')
        # Parse with the SAME structural and workspace validator as the model.
        if not steps:
            return []
        from .agent_plan import parse_build_plan
        checked = parse_build_plan(json.dumps({'files': steps}), project, fragment=True)
        if checked != steps:
            raise ValueError('Saved planning continuation differs from its validated contents')
        return checked

    def save(self, project: str | Path, request: str, evidence: str, steps: list[dict], *, context: str = '') -> None:
        from .agent_plan import parse_build_plan
        if not 1 <= len(steps) <= MAX_STEPS:
            raise ValueError('Cannot persist an empty or oversized model plan')
        checked = parse_build_plan(json.dumps({'files': steps}), project, fragment=True)
        if checked != steps:
            raise ValueError('Cannot save an unvalidated planning fragment')
        path = self._path(project, request, evidence, context)
        self.root.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.plan-', suffix='.tmp', dir=str(self.root))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'schema': SCHEMA, 'key': path.stem, 'steps': checked}, f,
                          ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def clear(self, project: str | Path, request: str, evidence: str, *, context: str = '') -> None:
        self._path(project, request, evidence, context).unlink(missing_ok=True)
