"""Recover missing fixed verification executables using observed local evidence.

This is not a model-selected shell or installer pathway. Only an existing
approved build, its exact test profile, and the standing catalog policy can
lead to a bounded probe or install. No source repair substitutes for a
missing executable.
"""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
from pathlib import Path
import shutil

from .computer_inventory import INSTALL_CATALOG
from .software_autonomy import already_attempted,make_plan

PROBE_AGE=timedelta(days=1)


def missing_verifier(project,command,*,which=None):
    root=Path(project)
    resolver=which or shutil.which
    if command:
        executable=command[0]
        if Path(executable).is_absolute():
            if Path(executable).is_file():return None
        elif resolver(executable):return None
        if executable in ('npm','npm.cmd'):return 'Node.js'
        if executable=='dotnet':return '.NET SDK'
        if (root/'project.godot').is_file():return 'Godot'
        return 'unknown fixed executable'
    if (root/'project.godot').is_file():return 'Godot'
    return None


def recovery_action(name,policy,history,probe,*,now=None):
    """Determine one next operation without running anything.

    A probe must precede installation. A failed version check does not prove
    absence and must not trigger repeated installs. A completed or interrupted
    installer requires fresh independent observation instead of replay.
    """
    if policy.get('enabled') is not True or policy.get('catalog_only') is not True or policy.get('source')!='winget':
        return 'blocked','Routine catalog software management is disabled'
    if name not in INSTALL_CATALOG:
        return 'blocked','Missing verifier is not in the approved installation catalog'
    current=now or datetime.now(timezone.utc)
    pkg=INSTALL_CATALOG[name][0]
    prior=history.get(pkg+':install')
    recent=already_attempted(prior,pkg,'install',now=current)
    def timestamp(row):
        try:
            value=datetime.fromisoformat(row['observed_at'])
            return value if value.tzinfo is not None else None
        except (ValueError,TypeError,KeyError):return None
    when=timestamp(probe) if isinstance(probe,dict) else None
    installed=timestamp(prior) if isinstance(prior,dict) else None
    if not when or not timedelta(0)<=current-when<PROBE_AGE or (installed and when<installed):
        return 'probe','Locate and independently check the required executable'
    if probe.get('tool')!=name:
        return 'probe','Previous capability receipt belongs to another tool'
    status=probe.get('status')
    if status=='version_verified':
        return 'restore','Restore verified executable discovery for this session'
    if status!='not_found':
        return 'blocked','Executable located or probe failed; inspect capability rather than reinstall blindly'
    if recent:
        return 'blocked','Previous catalog installation attempt is within its cooldown'
    return 'install','Independent probe did not locate the required catalog tool'


def install_plan(name,project,policy,history,probe,*,which=None,now=None):
    action,_=recovery_action(name,policy,history,probe,now=now)
    if action!='install':raise ValueError('Missing-tool evidence does not authorize catalog installation')
    return make_plan(name,'install',str(project),which=which)
