"""Bind approved external tool workflows to exact roadmap boundaries.

A boundary is after N verified code milestones and before N+1. Tool
outputs are supplementary artifacts, not replacements for code stages.
Both scheduler and manual milestone approval consult the same gate.
"""
from __future__ import annotations
import json
from pathlib import Path
from .roadmap_runs import manifest as roadmap_manifest,eligible_successor
from .tool_workflows import digest
from .workflow_design import current_source


def make_binding(run,request,hierarchies,index,workflow,after):
    roadmap=roadmap_manifest(hierarchies,index,request)
    if not run or run['state'] not in ('active','paused') or run['manifest_sha256']!=roadmap['manifest_sha256']:
        raise ValueError('Approve the exact roadmap before attaching a tool workflow')
    if type(after) is not int or not 0<=after<=len(roadmap['schedule']):
        raise ValueError('Invalid roadmap boundary')
    if workflow['project']!=roadmap['project'] or workflow.get('specification',{}).get('request_id')!=request['id']:
        raise ValueError('Workflow belongs to a different project or specification')
    planned={s['path'].casefold() for m in roadmap['schedule'] for s in m['steps']}
    for stage in workflow['stages']:
        if stage['output'].casefold() in planned:
            raise ValueError('Tool output collides with an approved code file; revise the plan explicitly')
    return {'request_id':request['id'],'manifest_sha256':roadmap['manifest_sha256'],
            'after':after,'project':roadmap['project']}


def boundary_open(link,request,run,conversations,hierarchies,index,jobs):
    if not run or run['state']!='active':return False
    if link['manifest_sha256']!=run['manifest_sha256'] or link['project']!=run['project']:
        raise ValueError('Roadmap authorization changed')
    state=eligible_successor(run,request,conversations,hierarchies,index,jobs)
    if state is None:return False
    if state['complete']:
        return link['after']==hierarchies.status(index,request['id'],request['prompt'])['milestones_total']
    return state['milestone']['ordinal']==link['after']+1


def check_complete(workflows,run):
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha'] or manifest['project']!=run['project']:
        raise ValueError('Linked workflow manifest changed')
    rows=workflows.stages(run['id'])
    if len(rows)!=len(manifest['stages']):raise ValueError('Linked workflow stage count changed')
    for ordinal,(stage,row) in enumerate(zip(manifest['stages'],rows),1):
        if row['ordinal']!=ordinal or row['state']!='checked':
            raise ValueError('Linked workflow lacks checked output')
        workflows._check_receipt(run['project'],stage,row)
    if manifest.get('recovery'):
        from .workflow_recovery import verify_recovery
        verify_recovery(workflows,manifest['recovery'],run['project'])


def gate(workflows,request_id,manifest_sha,before):
    """Return a human-readable blocker for any required earlier boundary."""
    runs=workflows.roadmap_members(request_id)
    replacements={}
    for run in runs:
        m=json.loads(run['manifest'])
        parent=m.get('recovery',{}).get('workflow_id')
        if parent is not None:replacements[parent]=run['id']
    for run in runs:
        m=json.loads(run['manifest']);link=m['roadmap']
        if link['manifest_sha256']!=manifest_sha:
            raise ValueError('Linked workflow refers to a different roadmap approval')
        if link['after']>=before:continue
        if run['id'] in replacements:continue
        if run['state']!='complete':
            return f"Roadmap waiting for tool workflow #{run['id']} ({run['state']}) after milestone {link['after']}"
        check_complete(workflows,run)
        from .asset_import_probe import required_imports
        pending=required_imports(workflows,run)
        if pending:
            item=pending[0]
            return f"Roadmap waiting for {item['tool']} import of {item['output']} ({item['status']})"
    return None
