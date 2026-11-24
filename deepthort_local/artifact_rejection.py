"""Preserve rejected output bytes and allow a separately approved continuation.

Only a recorded measurable acceptance mismatch of a successful approved action
qualifies. A durable intent precedes a no-overwrite hard-link move. An
interrupted move is never implicitly retried; the same explicit review can
finish it. This is not a filesystem sandbox.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from .workspace import safe_target
from .tool_workflows import digest,artifact
from .tool_acquisition import _approved_result
from .action_guards import snapshot_file,verify_guards

def rejection(workflows,ident):
    run=workflows.get(ident)
    if not run or run['state']!='blocked':return None
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha'] or manifest['project']!=run['project']:
        raise ValueError('Rejected workflow manifest changed')
    rows=workflows.stages(ident)
    for ordinal,(stage,row) in enumerate(zip(manifest['stages'],rows),1):
        if row['state']=='checked':
            workflows._check_receipt(run['project'],stage,row)
            continue
        if row['state']!='rejected':return None
        rec=json.loads(row['receipt'])
        task=manifest.get('mixed_task')
        if not task or task['output']!=stage['output'] or task.get('acceptance')!=rec['rejection']['checks']:
            raise ValueError('Rejected acceptance contract changed')
        action=workflows.janus.action(row['action_id'])
        _,log_sha,_=_approved_result(action,stage['argv'],run['project'],kind='tool')
        if rec['log_sha256']!=log_sha:raise ValueError('Rejected process log changed')
        verify_guards([g for g in json.loads(action['input_guards_json']) if g['kind']!='absent'])
        root=Path(run['project'])
        source=safe_target(root,stage['output'])
        target=source.with_name('.'+source.stem+'.deepthort-rejected-'+str(ident)+'-'+str(ordinal)+source.suffix)
        relative=target.relative_to(root).as_posix()
        if safe_target(root,relative)!=target:raise ValueError('Unsafe archive path')
        plan={'workflow_id':ident,'ordinal':ordinal,'project':str(root),'manifest_sha':run['manifest_sha'],
              'source':stage['output'],'archive':relative,'artifact':rec['artifact'],
              'rejection':rec['rejection'],'specification':manifest.get('specification')}
        if 'archive' in rec:
            if rec['archive']!=relative or artifact(root,relative)!=rec['artifact']:
                raise ValueError('Preserved rejected output changed')
            return {**plan,'archived':True}
        if rec.get('archive_intent') not in (None,relative):raise ValueError('Archive intent changed')
        # If interrupted after creating the hard link, allow a new explicit
        # review only of the same bytes. Never adopt a pre-existing archive.
        if target.exists():
            if rec.get('archive_intent')!=relative or artifact(root,relative)!=rec['artifact']:
                raise ValueError('Archive destination already exists')
            if source.exists() and not os.path.samefile(source,target):
                raise ValueError('Archive and original are different files')
        if source.exists():
            if artifact(root,stage['output'])!=rec['artifact']:
                raise ValueError('Rejected artifact changed since check')
        elif not target.exists():raise ValueError('Rejected artifact is missing')
        return {**plan,'archived':False}
    return None

def preserve(workflows,plan,*,user_approved=False):
    if user_approved is not True:raise PermissionError('Explicit rejection archive approval required')
    if workflows.busy():raise ValueError('Wait for active workflow processes')
    if rejection(workflows,plan['workflow_id'])!=plan or plan['archived']:
        raise ValueError('Rejection archive review changed')
    root=Path(plan['project']);source=safe_target(root,plan['source']);dest=safe_target(root,plan['archive'])
    with workflows.janus.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current=db.execute('SELECT state,receipt FROM tool_workflow_stages WHERE workflow_id=? AND ordinal=?',
                            (plan['workflow_id'],plan['ordinal'])).fetchone()
        if not current or current[0]!='rejected':raise ValueError('Rejected stage changed')
        rec=json.loads(current[1])
        rec['archive_intent']=plan['archive']
        db.execute('UPDATE tool_workflow_stages SET receipt=? WHERE workflow_id=? AND ordinal=?',
                   (json.dumps(rec),plan['workflow_id'],plan['ordinal']))
    # No overwrite: create a same-volume hard link to the exact rejected file.
    # If unsupported, leave the source untouched. The intent permits recovery
    # from interruption between link and unlink, but not an unapproved retry.
    if source.exists():
        if snapshot_file(source)['expected']!=plan['artifact']['sha256']:
            raise ValueError('Rejected artifact changed before archiving')
        if not dest.exists():os.link(source,dest)
        if not os.path.samefile(source,dest) or snapshot_file(dest)['expected']!=plan['artifact']['sha256']:
            raise ValueError('Archive does not match rejected output')
        if snapshot_file(source)['expected']!=plan['artifact']['sha256']:
            raise ValueError('Rejected artifact changed before releasing path')
        source.unlink()
    if source.exists() or artifact(root,plan['archive'])!=plan['artifact']:
        raise ValueError('Rejected output archive could not be verified')
    rec['archive']=plan['archive']
    with workflows.janus.connect() as db:
        db.execute('UPDATE tool_workflow_stages SET receipt=? WHERE workflow_id=? AND ordinal=? AND state=\'rejected\'',
                   (json.dumps(rec),plan['workflow_id'],plan['ordinal']))
    return dest
