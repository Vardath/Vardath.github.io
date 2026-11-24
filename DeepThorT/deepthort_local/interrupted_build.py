"""Reconcile interrupted approved inference without replaying mutations.

The work queue, grant, task graph, latest checkpoint and current workspace
must independently agree. Recovery creates no new permission and runs no code.
"""
from __future__ import annotations
from pathlib import Path

from .project_authority import _active, _safe_auto_path, _sha
from .workspace import WorkspaceError

INTERRUPTED='Interrupted by previous shutdown; resume or cancel'


class RecoveryError(ValueError):
    pass


def validate_interrupted(job,steps,*,grants,graphs,checkpoints,cycles,enabled):
    if job.get('state')!='paused' or job.get('detail')!=INTERRUPTED:
        raise RecoveryError('Not a shutdown-interrupted inference candidate')
    if job.get('mode')!='build' or not steps:
        raise RecoveryError('No approved bounded build')
    if cycles.get(job['id']) is not None:
        raise RecoveryError('A test or repair cycle exists; do not infer a safe replay')
    grant=_active(Path(grants),job,steps,enabled)
    graph=graphs.recovery_snapshot(job,steps)
    if graph['state']!='active' or graph['active_action']:
        raise RecoveryError('Task graph is not idle and active')
    nodes={node['node']:node for node in graph['nodes']}
    if any(n['state'] in ('needs_attention','invalidated','failed') for n in nodes.values()):
        raise RecoveryError('Graph has uncertain or failed work')
    records=checkpoints.list(job['id'])
    project,paths=checkpoints._verify_binding(job,steps,records)
    latest=records[-1]
    if latest['reason'] not in ('approval_baseline','artifact_saved'):
        raise RecoveryError('Latest checkpoint is not an ordinary approved build checkpoint')
    current={rel:_sha(target) for rel,target in paths}
    if current!=latest['files']:
        raise RecoveryError('Workspace differs from the latest completed source checkpoint')
    entries={x['step_id']:x for x in grant['files']}
    if len(entries)!=len(steps):
        raise RecoveryError('Grant file-stage identity is incomplete')
    planned_seen=False
    for step in steps:
        entry=entries.get(step['id'])
        node=nodes.get(f"file:{step['id']}")
        rel,_=_safe_auto_path(project,step['path'])
        if not entry or not node or entry['path']!=rel:
            raise RecoveryError('File-stage identity differs across evidence stores')
        if step['state']=='planned':
            planned_seen=True
            if (entry.get('written_sha256') is not None or node['state']!='waiting'
                    or current[rel]!=entry.get('before_sha256')):
                raise RecoveryError('A planned file has uncertain mutation evidence')
        elif step['state']=='saved':
            if planned_seen:
                raise RecoveryError('Saved steps are not an ordered prefix')
            written=entry.get('written_sha256')
            if (not written or current[rel]!=written or node['state']!='saved'
                    or node['evidence_sha256']!=written):
                raise RecoveryError('Saved file evidence is incomplete or inconsistent')
        else:
            raise RecoveryError('File stage needs individual reconciliation')
    return {'job_id':job['id'],'saved':sum(s['state']=='saved' for s in steps),
            'planned':sum(s['state']=='planned' for s in steps)}


def resume_interrupted(jobs,graphs,checkpoints,cycles,grants,*,enabled):
    """Resume one confirmed inference; leave uncertain states untouched."""
    if not enabled:return None
    for job in jobs.interrupted_builds():
        try:
            receipt=validate_interrupted(job,jobs.steps(job['id']),grants=grants,
                graphs=graphs,checkpoints=checkpoints,cycles=cycles,enabled=True)
        except (ValueError,OSError,KeyError,TypeError):
            continue
        if jobs.requeue_interrupted_build(job['id']):
            return receipt
    return None
