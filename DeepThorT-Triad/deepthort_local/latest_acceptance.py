"""Versioned, one-click Windows acceptance checks for DeepThorT.

A shipped JSON manifest selects ONLY fixed, audited read-only probe identifiers.
It cannot supply shell commands, executable paths, scripts, network addresses,
project file writes or newly authorized actions. The next release can replace
LATEST_TEST.json to select existing probes, or add an audited probe here.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

SCHEMA = 'deepthort-latest-test-v1'
ALLOWED = frozenset({'shared_cap','triad_residency','triad_inference','concurrent_status','janus_core','triad_collaboration','production_review','task_memory','portable_skills','portable_procedures','local_mcp','mcp_calls','task_mcp','mcp_stdio','memory_governance','live_memory','application_workflow','speech_backend','visual_backend','video_render','multimedia_core','memory_core','memory_observer','workflow_doctrine','delegation','team_delegation','project_assignment','five_model_acceptance'})
STATUSES = frozenset({'passed', 'failed', 'blocked', 'inconclusive', 'cancelled'})


class LatestTestError(ValueError):
    pass


def load_test(path: str | Path) -> dict:
    """Reject unfamiliar capabilities and commands before ANY execution."""
    file = Path(path)
    if not file.is_file() or file.stat().st_size > 8192:
        raise LatestTestError('The latest test definition is missing or oversized')
    try:
        data = json.loads(file.read_text('utf-8'))
    except (OSError, ValueError) as error:
        raise LatestTestError('The latest test definition is not valid JSON') from error
    if not isinstance(data, dict) or set(data) != {'schema', 'id', 'title', 'checks'}:
        raise LatestTestError('Unsupported latest test definition fields')
    if data['schema'] != SCHEMA or not isinstance(data['id'], str) or not (1 <= len(data['id']) <= 80):
        raise LatestTestError('Unsupported latest test version')
    if not isinstance(data['title'], str) or not (1 <= len(data['title']) <= 140):
        raise LatestTestError('Invalid latest test title')
    checks = data['checks']
    if not isinstance(checks, list) or not (1 <= len(checks) <= 24):
        raise LatestTestError('Latest test needs 1–24 built-in checks')
    if any(not isinstance(value, str) or value not in ALLOWED for value in checks):
        raise LatestTestError('The test manifest requested an unknown or executable action')
    if len(checks) != len(set(checks)):
        raise LatestTestError('Duplicate test checks are forbidden')
    return data


def check_record(name: str, status: str, detail: str, *, evidence: dict | None = None) -> dict:
    if name not in ALLOWED or status not in STATUSES:
        raise LatestTestError('Invalid test result')
    # Never persist raw prompts, model response text, credentials or tool output.
    if not isinstance(detail, str): detail = str(detail)
    return {'check': name, 'status': status, 'detail': detail[:450],
            'evidence': {str(k)[:60]: v for k, v in (evidence or {}).items()
                         if str(k) in {'pid', 'primary_pid', 'council_pid', 'busy',
                                       'council_busy', 'pending_count', 'count',
                                       'available_gib', 'installed_gib', 'elapsed_seconds',
                                       'local_role', 'http_status', 'thread_cpu_cap',
                                       'janus_cycle','sentinel_cycle','janus_paused','age_seconds','models','role_results','simultaneous_roles','job_cap_bytes','available_bytes',
                                       'individual_results','concurrent_results','serial_memory_mode','memory_retries','collaboration_stages','artifact_sha256','production_stages','memory_cases'}}}


def run_checks(definition: dict, checks: dict[str, Callable[[], dict]],
               *, cancelled=None, notify=None, clock=None) -> dict:
    """Run fixed probes in manifest order; isolate per-probe failures.

    `checks` is constructed by the app; the manifest never provides Python
    code, commands or URLs. The runner itself does not invoke programs.
    """
    if not isinstance(definition, dict) or definition.get('schema') != SCHEMA:
        raise LatestTestError('Invalid latest test definition')
    started = (clock or time.monotonic)()
    results = []
    for name in definition['checks']:
        if name not in ALLOWED or name not in checks:
            raise LatestTestError('A required built-in probe is unavailable: ' + str(name))
        if cancelled and cancelled.is_set():
            results.append(check_record(name, 'cancelled', 'User stopped the latest test'))
            break
        if notify: notify(name)
        try:
            found = checks[name]()
            if not isinstance(found, dict): raise LatestTestError('Probe returned no structured result')
            item = check_record(name, found.get('status'), found.get('detail', ''),
                                evidence=found.get('evidence') if isinstance(found.get('evidence'), dict) else {})
        except Exception as error:
            item = check_record(name, 'failed', 'Probe error: ' + type(error).__name__ + ': ' + str(error)[:300])
        results.append(item)
    statuses = [item['status'] for item in results]
    outcome = ('cancelled' if 'cancelled' in statuses else 'failed' if 'failed' in statuses
               else 'blocked' if 'blocked' in statuses else 'inconclusive' if 'inconclusive' in statuses
               else 'passed')
    return {'schema': SCHEMA, 'test_id': definition['id'],
            'title': definition['title'],
            'completed_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'outcome': outcome, 'results': results,
            'elapsed_seconds': round(max(0, (clock or time.monotonic)()-started), 2)}


def save_result(folder: str | Path, result: dict) -> Path:
    """Save individual dated report and last report with atomic replacement.

    A unique filename avoids overwriting previous runs with the same timestamp.
    """
    root = Path(folder)
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True).encode('utf-8')
    if len(encoded) > 65536: raise LatestTestError('Test report exceeded the fixed size limit')
    output = root / ('LatestTest-' + stamp + '.json')
    for dest in (output, root/'latest.json'):
        handle, tmp = tempfile.mkstemp(prefix='.deepthort-test-', suffix='.tmp', dir=root)
        try:
            with os.fdopen(handle, 'wb') as f:
                f.write(encoded); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, dest)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    return output


def report_summary(result: dict) -> str:
    counts = {name: sum(x['status'] == name for x in result.get('results', []))
              for name in ('passed', 'failed', 'blocked', 'inconclusive', 'cancelled')}
    return (f"{result.get('title','Latest acceptance')} — {result.get('outcome','unknown').upper()}; "
            + ', '.join(f'{n} {counts[n]}' for n in counts if counts[n]))
