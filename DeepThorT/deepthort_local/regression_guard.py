"""Regression impact reporting and source stability checks for real project tests.

Declared dependencies determine affected source and test intentions; the existing
fixed project-wide test profile is deliberately retained. A planned test is
not evidence it executed. Source hashes are observed before and after the test.
"""
from __future__ import annotations
import json
from pathlib import Path
from .agent_plan import PlanError
from .requirements_intelligence import declared_dependencies
from .acceptance_contracts import _TEST_PATH
from .project_authority import _safe_auto_path,_sha
from .reasoning_council import sha

MAX_REGRESSION_FILES=10000


def affected_paths(master_steps,changed):
    graph=declared_dependencies(master_steps)
    changed=set(changed)
    if not changed.issubset(graph):raise PlanError('Unknown changed path in regression scope')
    reverse={path:[] for path in graph}
    for path,deps in graph.items():
        for dep in deps:reverse[dep].append(path)
    pending=list(changed)
    affected=set(changed)
    while pending:
        for dependent in reverse[pending.pop()]:
            if dependent not in affected:
                affected.add(dependent);pending.append(dependent)
    return sorted(affected)


def scope_for(job,jobs,conversations,hierarchies,index):
    current=jobs.steps(job['id'])
    protected={s['path'] for s in current}
    master=current
    trace=[]
    key=job.get('approval_key') or ''
    if key.startswith('milestone:'):
        _,root_id,ordinal,digest=key.split(':')
        ordinal=int(ordinal)
        req=conversations.get(int(root_id))
        if not req or sha(req['prompt'])[:16]!=digest:
            raise PlanError('Regression scope has no matching master specification')
        root,_,milestones,master=hierarchies._checked(index,req['id'],req['prompt'])
        if root['project']!=str(Path(job['project']).resolve()) or root['chat_id']!=job['chat_id']:
            raise PlanError('Regression scope belongs to a different project')
        if not 1<=ordinal<=len(milestones) or milestones[ordinal-1]['job_id']!=job['id']:
            raise PlanError('Regression scope is not bound to the current milestone')
        for m in milestones[:ordinal-1]:
            prior=jobs.get(m['job_id']) if m['job_id'] else None
            if not prior or prior['state']!='complete':
                raise PlanError('Predecessor must pass before successor regression testing')
            protected.update(s['path'] for s in json.loads(m['steps_json']))
        trace=hierarchies.coverage(index,req['id'],req['prompt'])
    affected=set(affected_paths(master,[s['path'] for s in current]))
    sections={row['section_ordinal'] for row in trace if row['path'] in affected}
    related={row['path'] for row in trace if row['section_ordinal'] in sections}
    tests=sorted(path for path in affected|related if _TEST_PATH.search(path))
    root=Path(job['project']).resolve(strict=True)
    available=[]
    pending=[]
    for path in tests:
        _,target=_safe_auto_path(root,path)
        if target.is_file():
            protected.add(path);available.append(path)
        else:pending.append(path)
    return {'job_id':job['id'],'project':str(root),'protected':sorted(protected),
            'affected':sorted(affected),'linked_tests_present':available,
            'linked_tests_pending':pending,'selection':'fixed project-wide verification profile'}


def capture(scope):
    paths=scope['protected']
    if not 1<=len(paths)<=MAX_REGRESSION_FILES:
        raise PlanError('Regression fingerprint scope exceeds bound')
    root=Path(scope['project']).resolve(strict=True)
    files={}
    for path in paths:
        rel,target=_safe_auto_path(root,path)
        digest=_sha(target)
        if not digest:raise PlanError('Regression source missing: '+rel)
        files[rel]=digest
    return files


def stable(scope,before,after):
    return before==after and before==capture(scope)
