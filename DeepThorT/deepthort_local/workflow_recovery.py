"""Evidence-bound continuations for blocked tool workflows.

A continuation is a new manifest, not a mutation of prior approval. Keep
checked outputs and logs intact; do not delete uncertain partial outputs.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from .workspace import safe_target
from .tool_workflows import digest


def recovery_snapshot(workflows,ident):
    run=workflows.get(ident)
    if not run or run['state']!='blocked':
        raise ValueError('Only a blocked workflow can be recovered')
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha'] or manifest['project']!=run['project']:
        raise ValueError('Original workflow manifest changed')
    # A second failure must retain all ancestor evidence, not just the
    # immediate successful prefix. The ancestry is bounded and checked below.
    inherited=manifest.get('recovery')
    if inherited:
        verify_recovery(workflows,inherited,run['project'])
        if inherited['depth']>=3:raise ValueError('Recovery depth limit reached; inspect manually')
    rows=workflows.stages(ident)
    stages=manifest['stages']
    if len(rows)!=len(stages):raise ValueError('Workflow stages changed')
    prefix=[]
    remaining=[]
    failure=None
    for ordinal,(stage,row) in enumerate(zip(stages,rows),1):
        if row['ordinal']!=ordinal:raise ValueError('Stage order changed')
        if row['state']=='checked':
            if remaining:raise ValueError('Checked stage after an incomplete stage')
            receipt=workflows._check_receipt(run['project'],stage,row)
            prefix.append({'ordinal':ordinal,'output':stage['output'],'receipt':receipt})
        else:
            remaining.append({'ordinal':ordinal,'title':stage['title'],'tool':stage['tool'],
                              'input':stage['input'],'output':stage['output']})
            if failure is None:
                action=workflows.janus.action(row['action_id']) if row['action_id'] else None
                if action and action['status'] in ('approved','running'):
                    raise ValueError('Wait for the previous action to terminate')
                failure={'ordinal':ordinal,'detail':run['detail'],'status':action['status'] if action else 'not_dispatched',
                         'returncode':action.get('returncode') if action else None}
                if action and action.get('output_file'):
                    log=Path(action['output_file'])
                    if log.is_file() and not log.is_symlink() and log.stat().st_size<=8_000_000:
                        data=log.read_bytes()
                        failure['log_sha256']=hashlib.sha256(data).hexdigest()
                        # Bounded diagnostic excerpt, never executable instructions.
                        failure['log_tail']=data[-1800:].decode('utf-8',errors='replace')
                target=safe_target(run['project'],stage['output'])
                failure['partial_output_present']=target.exists() or target.is_symlink()
    if failure is None:raise ValueError('No incomplete workflow stage')
    return {'workflow_id':ident,'manifest_sha':run['manifest_sha'],
            'depth':1+(inherited['depth'] if inherited else 0),
            'specification':manifest.get('specification'),'prefix':prefix,
            'remaining':remaining,'failure':failure}


def verify_recovery(workflows,binding,project):
    if not isinstance(binding,dict) or not 1<=binding.get('depth',0)<=3:
        raise ValueError('Invalid recovery binding')
    run=workflows.get(binding['workflow_id'])
    if not run or run['project']!=project:raise ValueError('Recovery belongs to another project')
    if recovery_snapshot(workflows,binding['workflow_id'])!=binding:
        raise ValueError('Recovery evidence changed; replan instead of replaying')
    return True


def next_recovery(workflows,conversations,drafts,project):
    """Find one unattempted blocked spec-bound workflow with valid evidence."""
    from .workflow_design import current_source
    runs=workflows.list(project)
    used={json.loads(r['manifest']).get('recovery',{}).get('workflow_id') for r in runs}
    for run in runs:
        if run['state']!='blocked' or run['id'] in used:continue
        try:
            snapshot=recovery_snapshot(workflows,run['id'])
            binding=snapshot['specification']
            if not binding or not current_source(binding,conversations):continue
            if not drafts.recovery_seen(run['id']):return snapshot
        except (ValueError,OSError,KeyError,TypeError):continue
    return None
