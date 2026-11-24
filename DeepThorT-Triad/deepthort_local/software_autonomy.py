"""Project-triggered routine software management; no per-tool chat confirmation.

An explicit user preference controls automatic work from a *fixed local catalog*.
Neither Qwen output nor network search results are executable arguments. Windows
UAC is owned by Windows; never request elevation, suppress UAC, or use hash bypass.
An installer exit code is not independent proof of a working application.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .computer_inventory import INSTALL_CATALOG, plan_tool_needs
from .diagnostic_evidence import read_snapshot, save_snapshot

POLICY_SCHEMA='deepthort-routine-software-policy-v1'
AUDIT_SCHEMA='deepthort-routine-software-audit-v1'
# Project submissions alone cannot authorize arbitrary third-party code, scripts,
# packages or paths. Only the explicit, local, reviewed catalog is eligible.
MAX_ACTIONS_PER_REQUEST=3
MIN_FREE_BYTES=1024**3
UPGRADE_COOLDOWN=timedelta(days=14)
RETRY_COOLDOWN=timedelta(days=1)
VALID_STATES={'launch_requested','completed_unverified','failed','interrupted_unverified',
              'deferred','blocked'}


def default_policy() -> dict:
    # This release is specifically requested to operate with routine software
    # autonomy. The control is visible and independently switchable at any time.
    return {'schema':POLICY_SCHEMA,'enabled':True,'allow_upgrades':True,
            'catalog_only':True,'source':'winget','revision':1}


def load_policy(path: Path) -> dict:
    path=Path(path)
    if not path.exists():
        return default_policy()
    row=read_snapshot(path)
    if not isinstance(row,dict) or row.get('schema')!=POLICY_SCHEMA or \
       type(row.get('enabled')) is not bool or type(row.get('allow_upgrades')) is not bool or \
       row.get('catalog_only') is not True or row.get('source')!='winget':
        # Corrupt existing policy must fail closed, not silently grant authority.
        return {**default_policy(),'enabled':False,'allow_upgrades':False}
    return {**default_policy(),'enabled':row['enabled'],
            'allow_upgrades':row['allow_upgrades']}


def set_policy(path: Path, *, enabled: bool, allow_upgrades: bool=True) -> dict:
    if type(enabled) is not bool or type(allow_upgrades) is not bool:
        raise ValueError('Software management policy flags must be boolean')
    row={**default_policy(),'enabled':enabled,'allow_upgrades':allow_upgrades}
    if not save_snapshot(Path(path),row):
        raise OSError('Could not persist routine software management preference')
    return row


def automatic_command(name: str, action: str, *, which=None) -> list[str]:
    if name not in INSTALL_CATALOG:
        raise ValueError('Automatic management accepts only locally curated tool names')
    if action not in ('install','upgrade'):
        raise ValueError('Automatic software operation must be install or upgrade')
    finder=which or shutil.which
    binary=finder('winget.exe') or finder('winget')
    if not binary:
        raise FileNotFoundError('Windows Package Manager (winget) is unavailable')
    binary=str(binary)
    if not binary or binary.startswith('-'):
        raise ValueError('Invalid WinGet executable')
    package_id=INSTALL_CATALOG[name][0]
    # Never use --all, --force, --ignore-security-hash, --override, --scope,
    # --silent or elevation-bypass flags. The installer and Windows UAC retain
    # their native interaction for any privileged installation.
    return [binary,action,'--id',package_id,'--exact','--source','winget',
            '--accept-source-agreements','--accept-package-agreements',
            '--disable-interactivity']


def make_plan(name: str, action: str, project: str, *, which=None) -> dict:
    if not isinstance(project,str) or not project or len(project)>1024:
        raise ValueError('A selected project is required for automatic tool work')
    argv=automatic_command(name,action,which=which)
    details={'schema':'deepthort-routine-software-plan-v1','name':name,
             'package_id':INSTALL_CATALOG[name][0], 'operation':action,
             'project':project, 'argv':argv,'authorization':'standing local routine-tool policy',
             'independent_install_verified':False}
    details['plan_sha256']=hashlib.sha256(json.dumps(details,sort_keys=True).encode()).hexdigest()
    return details


def verify_plan(plan: dict, *, which=None) -> None:
    if not isinstance(plan,dict) or plan.get('schema')!='deepthort-routine-software-plan-v1':
        raise ValueError('Unrecognized routine software plan')
    digest=plan.get('plan_sha256')
    payload={k:v for k,v in plan.items() if k!='plan_sha256'}
    if not isinstance(digest,str) or hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()!=digest:
        raise ValueError('Routine software plan was modified after preparation')
    if plan.get('package_id')!=INSTALL_CATALOG.get(plan.get('name'),('',))[0]:
        raise ValueError('Software catalog entry changed')
    if plan.get('argv')!=automatic_command(plan['name'],plan['operation'],which=which):
        raise ValueError('Software command was modified after planning')


def audit_record(plan: dict, status: str, *, exit_code=None) -> dict:
    if status not in VALID_STATES:
        raise ValueError('Invalid routine software operation status')
    verify_plan(plan,which=lambda exe:plan['argv'][0] if exe=='winget.exe' else None)
    return {'schema':AUDIT_SCHEMA,'plan_sha256':plan['plan_sha256'],
            'package_id':plan['package_id'],'name':plan['name'],'operation':plan['operation'],
            'project':plan['project'],'argv':list(plan['argv']),'status':status,
            'exit_code':exit_code,'reusable_approval':False,
            'observed_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'independent_install_verified':False}


def already_attempted(audit: dict|None, package_id: str, operation: str,
                     *, now: datetime|None=None) -> bool:
    if not isinstance(audit,dict) or audit.get('schema')!=AUDIT_SCHEMA:
        return False
    if audit.get('package_id')!=package_id or audit.get('operation')!=operation:
        return False
    try:
        observed=datetime.fromisoformat(audit['observed_at'])
        if observed.tzinfo is None: return True
    except (TypeError,KeyError,ValueError):
        return True
    elapsed=(now or datetime.now(timezone.utc))-observed
    if elapsed<timedelta(0):return True
    if audit.get('status') in {'launch_requested','interrupted_unverified','completed_unverified'}:
        return elapsed<(UPGRADE_COOLDOWN if operation=='upgrade' else RETRY_COOLDOWN)
    return elapsed<RETRY_COOLDOWN


def project_tool_plans(prompt: str, inventory: dict, project: str, policy: dict,
                       history: dict|None=None, *, which=None, now=None) -> list[dict]:
    if not isinstance(policy,dict) or policy.get('schema')!=POLICY_SCHEMA or \
        policy.get('enabled') is not True or policy.get('catalog_only') is not True or \
        policy.get('source')!='winget':
        return []
    if not isinstance(inventory,dict) or not isinstance(prompt,str) or not prompt.strip():
        return []
    results=[]
    history=history if isinstance(history,dict) else {}
    for need in plan_tool_needs(prompt,inventory):
        name=need['name']
        if name not in INSTALL_CATALOG:
            continue
        action='upgrade' if need['found'] else 'install'
        if action=='upgrade' and not policy.get('allow_upgrades'):continue
        id=INSTALL_CATALOG[name][0]
        if already_attempted(history.get(id+':'+action),id,action,now=now):continue
        results.append(make_plan(name,action,project,which=which))
        if len(results)>=MAX_ACTIONS_PER_REQUEST:break
    return results
