"""Exact cross-revision delta and declared dependency checks for source reuse.

A previous test is historical evidence only. The new job must test again.
Missing provenance, changed dependencies or ambiguous model judgments fall
back to redevelopment; no file is marked complete by these helpers.
"""
from __future__ import annotations
import json
from pathlib import Path

from .agent_plan import PlanError
from .project_authority import _safe_auto_path, _sha
from .requirements_intelligence import declared_dependencies
from .specification_amendments import revision_matches,sha
from .specification_library import sections
from .task_graph import _hash

MAX_DELTA_SECTIONS=24
DELTA_CHARS=1800
MAX_DEPENDENCIES=80


def revision_delta(conversations,current_id,prior_id):
    """Prove the prior request belongs to the current immutable amendment chain."""
    history=conversations.amendment_history(current_id)
    current=conversations.get(current_id)
    prior=conversations.get(prior_id)
    if not history or not current or not prior:return None
    root=conversations.get(history[0]['root_request_id'])
    if not root:return None
    owner=(current['project'],current['chat_id'])
    if any((r['project'],r['chat_id'])!=owner for r in (root,prior)):
        return None
    root_sha=sha(root['prompt'])
    parent=root['id']
    cut=0 if prior_id==parent else None
    texts=[]
    for n,row in enumerate(history,1):
        text=row['amendment']
        if (row['ordinal']!=n or row['root_request_id']!=root['id']
            or row['parent_request_id']!=parent or row['original_sha256']!=root_sha
            or row['amendment_sha256']!=sha(text)):
            return None
        texts.append(text)
        parent=row['request_id']
        if parent==prior_id:cut=n
    if (parent!=current_id or history[-1]['effective_sha256']!=sha(current['prompt'])
        or not revision_matches(current['prompt'],root['prompt'],texts)
        or cut is None or cut==len(texts)):return None
    if cut:
        if (history[cut-1]['effective_sha256']!=sha(prior['prompt'])
            or not revision_matches(prior['prompt'],root['prompt'],texts[:cut])):return None
    elif prior['prompt']!=root['prompt']:return None
    delta=[]
    for ordinal,text in enumerate(texts[cut:],cut+1):
        spans=sections(text,DELTA_CHARS)
        for part,(a,b) in enumerate(spans,1):
            delta.append({'ordinal':ordinal,'part':part,'parts':len(spans),
                          'text':text[a:b],'sha256':sha(text[a:b])})
            if len(delta)>MAX_DELTA_SECTIONS:return None
    return {'prior_spec_sha256':sha(prior['prompt']),
            'current_spec_sha256':sha(current['prompt']),'root_sha256':root_sha,
            'prior_request_id':prior_id,'current_request_id':current_id,
            'sections':delta}


def dependency_closure(steps,path):
    graph=declared_dependencies(steps)
    if path not in graph:raise PlanError('Retention target absent from master plan')
    visited=set()
    pending=list(graph[path])
    while pending:
        rel=pending.pop()
        if rel==path:raise PlanError('Cyclic dependency on retention target')
        if rel in visited:continue
        visited.add(rel)
        if len(visited)>MAX_DEPENDENCIES:raise PlanError('Retention dependency scope exceeds bound')
        pending.extend(graph[rel])
    return sorted(visited)


def dependency_evidence(project,path,old_plan,new_plan,snapshot,current_steps):
    """All declared transitive dependencies must keep exact goals and tested bytes."""
    old_deps=dependency_closure(old_plan,path)
    new_deps=dependency_closure(new_plan,path)
    if old_deps!=new_deps:return None
    old={x['path']:x['description'] for x in old_plan}
    new={x['path']:x['description'] for x in new_plan}
    local_states={x['path']:x['state'] for x in current_steps}
    files=snapshot.get('files',{})
    engine=snapshot.get('verification',{}).get('engine_sources',{})
    root=Path(project).resolve(strict=True)
    evidence={}
    for rel in old_deps:
        if old[rel]!=new[rel] or (rel in local_states and local_states[rel] not in ('saved','verified')):
            return None
        recorded=files.get(rel) or engine.get(rel)
        if not recorded or (rel in files and rel in engine and files[rel]!=engine[rel]):
            return None
        _,target=_safe_auto_path(root,rel)
        if _sha(target)!=recorded:return None
        evidence[rel]=recorded
    return evidence


def historical_snapshot(previous,verify_node):
    """Bind the stored test snapshot to the exact passed graph receipt."""
    if not str(previous.get('detail') or '').startswith('Verified: test command exited 0'):
        return None
    try:snapshot=json.loads(previous.get('result') or '')
    except (ValueError,TypeError):return None
    if not isinstance(snapshot,dict) or snapshot.get('snapshot_schema')!='deepthort-approved-verification-v1':
        return None
    if not isinstance(snapshot.get('files'),dict):return None
    if verify_node.get('state')!='passed' or verify_node.get('evidence_sha256')!=_hash(snapshot):
        return None
    verification=snapshot.get('verification')
    if not isinstance(verification,dict):return None
    if verification.get('assurance') not in ('python_tests_passed','dotnet_tests_passed',
            'godot_gut_tests_passed','x4_static_xml_passed','editor_load_only'):
        return None
    return snapshot


def master_steps_for(job,jobs,conversations,hierarchies,index):
    key=job.get('approval_key') or ''
    if key.startswith('milestone:'):
        if hierarchies is None or index is None:raise PlanError('Master dependency plan unavailable')
        parts=key.split(':')
        req=conversations.get(int(parts[1]))
        if not req or sha(req['prompt'])[:16]!=parts[3]:raise PlanError('Prior master specification mismatch')
        item=hierarchies.milestone(index,req['id'],req['prompt'],int(parts[2]))
        if item['job_id']!=job['id'] or item['scope_prompt']!=job['prompt']:
            raise PlanError('Milestone scope mismatch')
        return item['master_steps']
    return jobs.steps(job['id'])
