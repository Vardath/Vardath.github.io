"""Explicit, durable authority for reversible operations inside ONE approved build.

A standing preference is not a shell permission. Each grant is bound to an
already approved job and its exact file plan. Existing file hashes are pinned
before the first automatic write. Model text, chat and remote documentation
cannot create grants. SHA receipts detect accidental corruption, not hostile
tampering by software running as the same Windows user.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .diagnostic_evidence import read_snapshot, save_snapshot
from .workspace import MAX_READ_BYTES, safe_target

POLICY_SCHEMA = 'deepthort-project-work-policy-v1'
GRANT_SCHEMA = 'deepthort-project-job-grant-v1'
GRANT_DAYS = 30
DENIED_PARTS = frozenset({
    '.git', '.github', '.venv', '.vs', '.idea', '.cache', 'state', 'models',
    'node_modules', 'cache', 'dist', 'build', '__pycache__', 'backups'
})
DENIED_SUFFIXES = frozenset({
    '.exe', '.dll', '.msi', '.msp', '.bat', '.cmd', '.ps1', '.com', '.scr',
    '.sys', '.lnk', '.reg', '.pif', '.vbs', '.vbe', '.wsf', '.hta'
})


class GrantError(ValueError):
    """An unattended action is outside the explicit reviewed job boundary."""


def default_policy() -> dict:
    return {'schema': POLICY_SCHEMA, 'enabled': True, 'revision': 1}


def load_policy(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return default_policy()
    row = read_snapshot(path)
    if not isinstance(row, dict) or row.get('schema') != POLICY_SCHEMA or type(row.get('enabled')) is not bool:
        return {**default_policy(), 'enabled': False}
    return {**default_policy(), 'enabled': row['enabled']}


def set_policy(path: Path, enabled: bool) -> dict:
    if type(enabled) is not bool:
        raise GrantError('Project authority setting must be a boolean')
    row = {**default_policy(), 'enabled': enabled}
    if not save_snapshot(Path(path), row):
        raise OSError('Project work setting was not saved')
    return row


def _sha(path: Path) -> str | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_READ_BYTES:
        raise GrantError('Existing target is not an eligible bounded regular file')
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
    return h.hexdigest()


def _safe_auto_path(project: Path, name: str) -> tuple[str, Path]:
    dest = safe_target(project, name)
    rel = dest.relative_to(project).as_posix()
    parts = rel.replace('\\', '/').split('/')
    if any(part.casefold() in DENIED_PARTS or part.startswith('.') for part in parts):
        raise GrantError('Protected/hidden project paths require manual file review')
    if dest.suffix.casefold() in DENIED_SUFFIXES:
        raise GrantError('Executable/install/script launch formats require separate review')
    return rel, dest


def _plan_digest(job: dict, steps: list[dict]) -> str:
    payload = {
        'job_id': job.get('id'), 'approval_key': job.get('approval_key'),
        'project': str(Path(job['project']).resolve(strict=True)),
        'chat_id': job.get('chat_id'),
        'steps': [[s.get('id'), s.get('sequence'), s.get('path'), s.get('description')]
                  for s in steps]
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _seal(row: dict) -> dict:
    clean = {k: v for k, v in row.items() if k != 'record_sha256'}
    return {**clean, 'record_sha256': hashlib.sha256(
        json.dumps(clean, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def _read_grant(folder: Path, job_id: int) -> dict | None:
    row = read_snapshot(Path(folder) / f'job-{int(job_id)}.json')
    if not isinstance(row, dict) or row.get('schema') != GRANT_SCHEMA:
        return None
    if row.get('record_sha256') != _seal(row)['record_sha256']:
        return None
    return row


def _write_grant(folder: Path, row: dict) -> None:
    if not save_snapshot(Path(folder) / f"job-{int(row['job_id'])}.json", _seal(row)):
        raise OSError('Job authority was not durably saved')


def issue_grant(folder: Path, job: dict, steps: list[dict]) -> dict:
    """Called ONLY after the GUI's existing explicit project-plan approval."""
    if job.get('mode') != 'build' or job.get('state') != 'queued':
        raise GrantError('Only a queued, explicitly approved build can receive unattended authority')
    if not isinstance(job.get('id'), int) or not job.get('project') or not job.get('chat_id'):
        raise GrantError('Incomplete job identity')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 24:
        raise GrantError('Unattended grants require 1..24 exact file steps')
    project = Path(job['project']).resolve(strict=True)
    paths, seen = [], set()
    for step in steps:
        relative, target = _safe_auto_path(project, step['path'])
        if relative.casefold() in seen:
            raise GrantError('Duplicate automatic file target')
        seen.add(relative.casefold())
        paths.append({'path': relative, 'step_id': step['id'],
                      'before_sha256': _sha(target), 'written_sha256': None})
    existing = _read_grant(folder, job['id'])
    if existing is not None:
        raise GrantError('A previous grant exists; revoke it instead of renewing silently')
    now = datetime.now(timezone.utc)
    row = {
        'schema': GRANT_SCHEMA, 'job_id': job['id'], 'project': str(project),
        'approval_key': job.get('approval_key'), 'plan_sha256': _plan_digest(job, steps),
        'issued_at': now.isoformat(), 'expires_at': (now + timedelta(days=GRANT_DAYS)).isoformat(),
        'active': True, 'revoked_at': None, 'files': paths,
        'events': [{'kind': 'approved_plan', 'at': now.isoformat(), 'count': len(paths)}],
        'assurance': 'approved bounded paths; source hash checks; backups; fixed test profiles',
    }
    _write_grant(folder, row)
    return row


def _active(folder: Path, job: dict, steps: list[dict], enabled: bool) -> dict:
    if not enabled:
        raise GrantError('Unattended project work is disabled')
    if job.get('mode') != 'build':
        raise GrantError('Not an approved build')
    row = _read_grant(folder, job.get('id', 0))
    if not row or row.get('active') is not True:
        raise GrantError('No active durable authority for this job')
    if row.get('plan_sha256') != _plan_digest(job, steps):
        raise GrantError('Approved plan or job identity changed')
    if row.get('project') != str(Path(job['project']).resolve(strict=True)):
        raise GrantError('Project folder changed')
    try:
        expires = datetime.fromisoformat(row['expires_at'])
        if expires.tzinfo is None or datetime.now(timezone.utc) >= expires:
            raise GrantError('Job grant expired')
    except (KeyError, TypeError, ValueError) as exc:
        raise GrantError('Grant has no valid expiry') from exc
    if len(row.get('files') or []) != len(steps):
        raise GrantError('Granted file count does not match current plan')
    return row


def authorize_file(folder: Path, job: dict, steps: list[dict],
                   step: dict, *, enabled: bool) -> dict:
    """Return a checked existing-file hash for apply_approved_file's race guard."""
    row = _active(folder, job, steps, enabled)
    if job.get('state') != 'running' or step.get('state') != 'planned':
        raise GrantError('File stage is no longer awaiting model generation')
    project = Path(job['project']).resolve(strict=True)
    relative, target = _safe_auto_path(project, step['path'])
    matching = [x for x in row['files'] if x.get('path') == relative
                and x.get('step_id') == step.get('id')]
    if len(matching) != 1 or matching[0].get('written_sha256') is not None:
        raise GrantError('File is not an unwritten approved stage')
    before = matching[0]['before_sha256']
    if _sha(target) != before:
        raise GrantError('File changed since the full project plan was approved')
    return {'before_sha256': before, 'path': relative}


def record_file(folder: Path, job: dict, steps: list[dict], step: dict,
                *, enabled: bool) -> dict:
    """Persist evidence of one completed file write, never code correctness."""
    row = _active(folder, job, steps, enabled)
    project = Path(job['project']).resolve(strict=True)
    relative, target = _safe_auto_path(project, step['path'])
    entry = next((x for x in row['files'] if x['path'] == relative
                  and x['step_id'] == step['id']), None)
    if not entry or entry['written_sha256'] is not None:
        raise GrantError('File stage is absent or already recorded')
    sha = _sha(target)
    if not sha:
        raise GrantError('Expected source file was not saved')
    entry['written_sha256'] = sha
    row['events'].append({'kind': 'file_saved_unverified', 'path': relative,
                          'sha256': sha, 'at': datetime.now(timezone.utc).isoformat()})
    _write_grant(folder, row)
    return {'path': relative, 'sha256': sha}


def recognized_test_command(argv: list[str], project: Path) -> bool:
    """Exact bounded profiles already offered by the desktop, no shell recipe."""
    if not isinstance(argv, list) or not argv or any(not isinstance(a, str) for a in argv):
        return False
    project = Path(project).resolve(strict=True)
    if argv == [sys.executable, '-m', 'unittest', 'discover']:
        return True
    if argv == ['npm.cmd' if sys.platform == 'win32' else 'npm', 'test']:
        return True
    if argv == ['dotnet', 'test', '--no-restore']:
        return True
    if (len(argv) == 4 and argv[0] == sys.executable
        and Path(argv[1]).name == 'engine_acceptance_cli.py'
        and Path(argv[2]).resolve() == project and argv[3] == '--summary'):
        return True
    if len(argv) < 6 or not argv[0] or argv[0].startswith('-'):
        return False
    if argv[1:4] != ['--headless', '--path', str(project)]:
        return False
    if argv[4:] == ['--editor', '--quit']:
        return True
    return (len(argv) == 8 and argv[4:6] == ['-s', 'addons/gut/gut_cmdln.gd']
            and argv[6].startswith('-gdir=res://') and '..' not in argv[6]
            and argv[7] == '-ginclude_subdirs') or (
            len(argv) == 9 and argv[4:6] == ['-s', 'addons/gut/gut_cmdln.gd']
            and argv[6].startswith('-gdir=res://') and '..' not in argv[6]
            and argv[7:] == ['-ginclude_subdirs', '-gexit'])


def authorize_test(folder: Path, job: dict, steps: list[dict],
                   argv: list[str], *, enabled: bool) -> bool:
    row = _active(folder, job, steps, enabled)
    if job.get('state') != 'waiting_verification' or not steps or any(
            step.get('state') != 'saved' for step in steps):
        raise GrantError('File stages are not all saved and awaiting verification')
    project = Path(job['project']).resolve(strict=True)
    if not recognized_test_command(argv, project):
        raise GrantError('Test command does not match a fixed supported profile')
    for entry in row['files']:
        target = _safe_auto_path(project, entry['path'])[1]
        if not entry.get('written_sha256') or _sha(target) != entry['written_sha256']:
            raise GrantError('A generated source file changed or lacks saved-file evidence')
    return True


def revoke_grant(folder: Path, job_id: int) -> bool:
    row = _read_grant(folder, job_id)
    if row is None or row.get('active') is not True:
        return False
    row['active'] = False
    row['revoked_at'] = datetime.now(timezone.utc).isoformat()
    row['events'].append({'kind': 'revoked', 'at': row['revoked_at']})
    _write_grant(folder, row)
    return True
