"""Exact, user-approved WinGet installations from recent read-only inspections.

Safety boundary: no local ONNX model output, search result text, website, or
stored receipt can authorize an install. This module only validates metadata
and constructs constant WinGet arguments. The desktop must obtain an explicit
fresh consent for the entire display and exact command. There is no attempt
to elevate privileges, fetch arbitrary URLs, or execute manifest instructions.

Manifest data, even a SHA256, is UNTRUSTED and not independent publisher proof.
The WinGet client is responsible for its own download hash checks; we never
pass bypass flags. Post-install validation is a separate next-stage capability.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from .online_tool_search import _safe_https, _winget, validate_package_id, SHA256_PATTERN

REVIEW_TTL = timedelta(hours=2)
INSTALLER_REQUIRED = {'msi', 'msix', 'exe', 'inno', 'nullsoft', 'burn', 'wix', 'zip', 'portable'}
VERSION_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._+\-]{0,80}\Z')


def prepare_reviewed_install(inspection: dict, *, now: datetime | None = None, which=None) -> dict:
    """Return an exact-version fixed command proposal; never execute it.

    Fails closed when inspection is missing, stale, inconclusive, or unpinned.
    The plan remains UNAPPROVED until the desktop verifies a typed consent.
    """
    if not isinstance(inspection, dict) or inspection.get('schema') != 'deepthort-winget-show-inspection-v1':
        raise ValueError('First inspect an exact package ID using Inspect package ID…')
    if inspection.get('source') != 'winget' or inspection.get('state') == 'inconclusive':
        raise ValueError('Only a completed inspection from the winget source can be reviewed')
    if inspection.get('install_authorized') is not False or inspection.get('download_authorized') is not False:
        raise ValueError('Inspection receipt must not contain preexisting authorization')
    if inspection.get('confidence') != 'UNVERIFIED CATALOG METADATA — NOT INSTALL AUTHORIZATION':
        raise ValueError('Unrecognized inspection provenance')
    if inspection.get('unsafe_urls_rejected'):
        raise ValueError('Inspection reported unsafe URLs; do not install this package')
    package_id = validate_package_id(inspection.get('package_id'))
    name = inspection.get('name')
    publisher = inspection.get('publisher')
    if not isinstance(name, str) or not 2 <= len(name) <= 130 or any(ord(c)<32 for c in name):
        raise ValueError('Inspected package name is missing or invalid')
    if not isinstance(publisher, str) or not 2 <= len(publisher) <= 160 or any(ord(c)<32 for c in publisher):
        raise ValueError('Publisher claim is missing or invalid')
    version = inspection.get('version')
    if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise ValueError('Exact package version is missing or malformed')
    manifest_hash = inspection.get('installer_sha256_manifest')
    if not isinstance(manifest_hash, str) or not SHA256_PATTERN.fullmatch(manifest_hash):
        raise ValueError('WinGet inspection lacks a full installer SHA-256; no install is allowed')
    installer_url = inspection.get('installer_url')
    if not isinstance(installer_url, str) or not _safe_https(installer_url):
        raise ValueError('Inspection lacks a valid HTTPS installer URL')
    publisher_url = inspection.get('publisher_url') or inspection.get('homepage')
    if not isinstance(publisher_url, str) or not _safe_https(publisher_url):
        raise ValueError('Inspection lacks a valid HTTPS publisher/homepage URL')
    installer_type = inspection.get('installer_type') or ''
    if not isinstance(installer_type, str) or len(installer_type) > 60 or any(ord(c) < 32 for c in installer_type):
        raise ValueError('Unrecognized installer type')
    # Unknown type can still be safe if WinGet supports it, but requiring an
    # explicit known type prevents accidentally invoking novel manifest formats.
    if installer_type and installer_type.casefold() not in INSTALLER_REQUIRED:
        raise ValueError('Installer type is not in reviewed set: '+installer_type)
    raw_time = inspection.get('observed_at')
    if not isinstance(raw_time, str):
        raise ValueError('Inspection time is missing')
    try:
        observed = datetime.fromisoformat(raw_time)
    except ValueError as exc:
        raise ValueError('Inspection timestamp is malformed') from exc
    if observed.tzinfo is None:
        raise ValueError('Inspection timestamp must specify a time zone')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or not timedelta(0) <= now - observed <= REVIEW_TTL:
        raise ValueError('Package inspection is stale or future-dated; inspect again')
    output_sha = inspection.get('output_sha256')
    if not isinstance(output_sha, str) or not SHA256_PATTERN.fullmatch(output_sha):
        raise ValueError('Inspection output digest is missing or malformed')
    # No download, upgrade or elevation bypass; use system WinGet hashing.
    argv = [_winget(which), 'install', '--id', package_id,
            '--exact', '--version', version, '--source', 'winget',
            '--scope', 'user', '--no-upgrade',
            '--accept-source-agreements', '--accept-package-agreements',
            '--disable-interactivity']
    details = {'schema':'deepthort-reviewed-install-plan-v1',
               'package_id':package_id,'name':name,'claimed_publisher':publisher,
               'version':version,'publisher_url':publisher_url,
               'installer_url':installer_url,
               'manifest_installer_sha256':manifest_hash.lower(),
               'license':inspection.get('license',''),
               'license_url':inspection.get('license_url',''),
               'inspected_at':raw_time,'inspection_output_sha256':output_sha.lower(),
               'argv':argv,'approval':False,'install_started':False,
               'scope':'user (requested; WinGet installer may still request elevation)',
               'notes':'Unverified community catalog metadata. User must independently review the publisher and license.'}
    details['plan_sha256'] = hashlib.sha256(
        json.dumps(details,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
    return details


def exact_consent_phrase(plan: dict) -> str:
    return 'INSTALL ' + plan['package_id']


def approval_receipt(plan: dict, *, consent: str, status: str) -> dict:
    """Persist a bounded audit of the one command, not reusable permission."""
    if not isinstance(plan,dict) or plan.get('schema') != 'deepthort-reviewed-install-plan-v1':
        raise ValueError('Invalid installation plan')
    expected_digest=hashlib.sha256(json.dumps(
        {key:value for key,value in plan.items() if key!='plan_sha256'},
        sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()
    if plan.get('plan_sha256')!=expected_digest:
        raise ValueError('Reviewed installation plan changed after preview')
    fixed_args=['install','--id',plan['package_id'],'--exact',
                '--version',plan['version'],'--source','winget','--scope','user',
                '--no-upgrade','--accept-source-agreements',
                '--accept-package-agreements','--disable-interactivity']
    if (not isinstance(plan.get('argv'),list) or len(plan['argv'])!=len(fixed_args)+1
        or plan['argv'][1:]!=fixed_args):
        raise ValueError('Reviewed install command differs from fixed allowed arguments')
    if consent != exact_consent_phrase(plan):
        raise ValueError('Installation requires a fresh exact typed approval')
    if status not in {'approved_not_started','launch_requested','running','completed_unverified','failed','cancelled','interrupted_unverified'}:
        raise ValueError('Invalid install state')
    return {'schema':'deepthort-reviewed-install-audit-v1',
            'package_id':plan['package_id'],'name':plan['name'],'version':plan['version'],
            'claimed_publisher':plan['claimed_publisher'],
            'inspection_output_sha256':plan['inspection_output_sha256'],
            'publisher_url':plan['publisher_url'],
            'installer_url':plan['installer_url'],
            'manifest_installer_sha256':plan['manifest_installer_sha256'],
            'plan_sha256':plan['plan_sha256'],
            'argv':list(plan['argv']),'status':status,
            'reusable_approval':False,
            'observed_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'publisher_verified_independently':False,
            'installation_verified_independently':False}
