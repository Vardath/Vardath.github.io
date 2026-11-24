"""Bounded, non-sensitive snapshots of read-only engine inspection for support ZIPs.

Do not copy the raw inventory: it contains hostnames, disk layout, absolute local
paths and potentially project-supplied document text.  Only record actual
inspection states, game-source IDs, counts and explicit unknowns. These
snapshots never certify successful gameplay or execution.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PureWindowsPath
from typing import Any

_MAX_READ = 96_000


def _display_path(raw: Any) -> dict:
    if not isinstance(raw, str) or not raw.strip():
        return {'selected': False, 'basename': '', 'fingerprint': ''}
    path = PureWindowsPath(raw) if ('\\' in raw or (len(raw) >= 2 and raw[1] == ':')) else Path(raw)
    return {'selected': True, 'basename': path.name[:110],
            'fingerprint': hashlib.sha256(raw.encode('utf-8', errors='replace')).hexdigest()[:16]}


def _source_entries(value):
    # Identifiers are vanilla X4 XML IDs, not source content or arbitrary file paths.
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:6]:
        if not isinstance(item, dict):
            continue
        ids = item.get('identifiers') if isinstance(item.get('identifiers'), list) else []
        result.append({'file': str(item.get('file', ''))[:160],
                       'identifiers': [str(v)[:150] for v in ids[:3]],
                       'sha256_prefix': str(item.get('sha256', ''))[:16]})
    return result


def summarize_x4_report(report: dict | None, *, game_dir='', reference_dir='', project_dir='') -> dict:
    if not isinstance(report, dict):
        return {'inspected': False, 'project': _display_path(project_dir),
                'game_configured': _display_path(game_dir),
                'reference_configured': _display_path(reference_dir),
                'interpretation': 'No completed source inspection was available for the export'}
    result = {
        'inspected': True,
        'project': _display_path(project_dir),
        'game': _display_path(report.get('game_dir') or game_dir),
        'reference': _display_path(report.get('reference_dir') or reference_dir),
        'paired_catalog_count': len(report.get('catalogs') or []),
        'pe_macro_verified': report.get('pe_macro_verified') is True,
        'pe_component_verified': report.get('pe_component_verified') is True,
        'ready_for_planning': report.get('ready_for_planning') is True,
        'candidate_counts': {key: len(report.get(key) or []) for key in
                             ('ship_candidates', 'weapon_candidates', 'turret_candidates', 'storage_candidates')},
        'blocked_reasons': [str(s)[:320] for s in (report.get('blocked_reasons') or [])[:12]],
        'pe_slots': [{'name': str(s.get('name',''))[:100], 'tags': str(s.get('tags',''))[:160]}
                     for s in (report.get('pe_component_connections') or [])[:12] if isinstance(s, dict)],
        'pe_component_file': str(report.get('pe_component_file', ''))[:200],
        'pe_component_sha256_prefix': str(report.get('pe_component_sha256', ''))[:16],
        'candidate_evidence': {key: _source_entries(report.get(key)) for key in
                               ('ship_candidates', 'weapon_candidates', 'turret_candidates')},
        'interpretation': 'Read-only candidate inspection; no weapon compatibility or in-game behavior proven',
    }
    if 'can_offer_extraction' in report:
        result['can_offer_extraction'] = report['can_offer_extraction'] is True
    if 'catalog_tool' in report:
        result['catalog_tool_present'] = bool(report['catalog_tool'])
    return result


def summarize_inventory(inventory: dict | None) -> dict:
    if not isinstance(inventory, dict):
        return {'scanned': False, 'interpretation': 'No completed Computer & Tools scan available'}
    tools = inventory.get('tools') or []
    preflight = inventory.get('engine_preflight')
    result = {'scanned': True,
              'tools_detected': sum(bool(x.get('found')) for x in tools if isinstance(x, dict)),
              'drive_count': len(inventory.get('drives') or []),
              'project': _display_path(inventory.get('project_folder')),
              'interpretation': 'Read-only detection, not execution or build success'}
    if isinstance(preflight, dict):
        links = preflight.get('x4_reference_links')
        result['engine_preflight'] = {
            'engine': str(preflight.get('engine','unknown'))[:60],
            'static_issues': preflight.get('static_issues'),
            'static_pending': preflight.get('static_pending'),
            'static_clean': preflight.get('static_clean') is True,
            'missing_prerequisites': [str(s)[:280] for s in (preflight.get('missing_prerequisites') or [])[:12]],
            'tool_presence': {str(k)[:70]: bool(v) for k, v in (preflight.get('tools') or {}).items()},
        }
        if isinstance(links, dict):
            result['engine_preflight']['x4_reference_links'] = {
                key: links.get(key) for key in ('resolved_vanilla_count','resolved_local_count',
                            'unresolved_count','vanilla_index_available','gameplay_verified')
                if key in links}
    return result


def matches_project(snapshot: dict | None, project_dir) -> bool:
    return bool(isinstance(snapshot, dict) and snapshot.get('project') == _display_path(str(project_dir or '')))


def save_snapshot(path: Path, data: dict) -> bool:
    """Persist only scrubbed, non-sensitive inspection metadata across restarts."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        temp.replace(path)
        return True
    except OSError:
        # A read-only or full disk must not break the desktop event queue.
        return False


def read_snapshot(path: Path) -> dict | None:
    try:
        if not path.is_file() or path.stat().st_size > _MAX_READ:
            return None
        data = json.loads(path.read_text('utf-8'))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None
