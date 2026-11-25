"""v42 content-addressed, bounded source checkpoints and explicit rollback.

Never use checkpoints as authorization for an automatic write. Every snapshot
is scoped to the exact approved plan. Restore requires a GUI decision and a
complete preflight comparing disk hashes with the latest recorded checkpoint;
external edits or symlinks fail closed. Deleted/new files are quarantined, not
silently unlinked. Multi-file restore is sequential with a recorded emergency
checkpoint; a crash can require manual reconciliation, not a false atomic claim.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .project_authority import _plan_digest, _safe_auto_path
from .workspace import MAX_READ_BYTES, WorkspaceError, apply_approved_file, safe_target

MAX_CHECKPOINTS = 60
MAX_SCOPE_BYTES = 4_000_000

class CheckpointError(ValueError):
    pass


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _atomic_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='deepthort-',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _sealed(row):
    contents={key:val for key,val in row.items() if key!='seal'}
    return {**contents,'seal':_digest(json.dumps(contents,sort_keys=True,ensure_ascii=False).encode('utf-8'))}


class SourceCheckpoints:
    def __init__(self,root: str | Path):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)

    def _job_dir(self,jobid):
        if type(jobid) is not int or jobid<1:
            raise CheckpointError('Invalid approved job identifier')
        return self.root/f'job-{jobid}'

    def _binding(self,job,steps):
        if job.get('mode')!='build' or not isinstance(steps,list) or not 1<=len(steps)<=24:
            raise CheckpointError('Source checkpoints need one approved bounded build')
        project=Path(job['project']).resolve(strict=True)
        paths=[]
        seen=set()
        for step in steps:
            path,target=_safe_auto_path(project,step['path'])
            if path.casefold() in seen:
                raise CheckpointError('Repeated approved file path')
            seen.add(path.casefold())
            paths.append((path,target))
        return project,_plan_digest(job,steps),paths

    def list(self,jobid):
        folder=self._job_dir(jobid)/'revisions'
        results=[]
        if not folder.exists():return []
        for path in sorted(folder.glob('*.json')):
            try:
                data=json.loads(path.read_text('utf-8'))
                if data.get('seal')!=_sealed(data)['seal'] or data.get('job_id')!=jobid:
                    raise CheckpointError('Checkpoint seal mismatch')
                results.append(data)
            except (OSError,ValueError,KeyError) as exc:
                raise CheckpointError(f'Checkpoint manifest is corrupted: {path.name}') from exc
        return results

    def capture(self,job:dict,steps:list[dict],reason:str,*,baseline=False):
        if reason not in ('approval_baseline','artifact_saved','repair_saved',
                          'pre_rollback','restored','manual_review_save'):
            raise CheckpointError('Unknown checkpoint lifecycle event')
        project,plan,paths=self._binding(job,steps)
        folder=self._job_dir(job['id'])
        existing=self.list(job['id'])
        if baseline:
            if existing:
                raise CheckpointError('Baseline already exists; cannot silently reset original sources')
            if reason!='approval_baseline':raise CheckpointError('Incorrect baseline reason')
        elif not existing:
            raise CheckpointError('No original project baseline; source cannot be versioned safely')
        if len(existing)>=MAX_CHECKPOINTS:
            raise CheckpointError('Checkpoint quota reached; manual archival is required')
        if existing and (existing[0]['plan_sha256']!=plan or
                         existing[0]['project']!=str(project)):
            raise CheckpointError('Approved source scope changed since baseline')
        scope={};objects={};total=0
        for rel,target in paths:
            if not target.exists():
                scope[rel]=None
                continue
            if target.is_symlink() or not target.is_file():
                raise CheckpointError('Snapshot target is not a regular source file')
            if target.stat().st_size>MAX_READ_BYTES:
                raise CheckpointError('File is too large to snapshot safely')
            data=target.read_bytes()
            try:text=data.decode('utf-8')
            except UnicodeError as exc:raise CheckpointError('Binary source file cannot be checkpointed') from exc
            if '\x00' in text:raise CheckpointError('Binary source file cannot be checkpointed')
            total+=len(data)
            if total>MAX_SCOPE_BYTES:
                raise CheckpointError('Total source checkpoint exceeds 4 MB limit')
            sha=_digest(data)
            scope[rel]=sha
            objects[sha]=data
        object_dir=folder/'objects'
        for sha,data in objects.items():
            path=object_dir/sha
            if path.exists():
                if _digest(path.read_bytes())!=sha:
                    raise CheckpointError('Stored checkpoint blob corruption')
            else:
                _atomic_bytes(path,data)
        name=f'{len(existing):03d}-{uuid.uuid4().hex[:12]}'
        row={'schema':1,'id':name,'job_id':job['id'],'project':str(project),
             'plan_sha256':plan,'reason':reason,'when':datetime.now(timezone.utc).isoformat(),
             'files':scope,'source_bytes':total}
        path=folder/'revisions'/f'{name}.json'
        _atomic_bytes(path,json.dumps(_sealed(row),ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8'))
        return {**row,'file_count':len(scope),'changed_since_previous':(
            sum(existing[-1]['files'].get(p)!=sha for p,sha in scope.items()) if existing else 0)}

    def _verify_binding(self,job,steps,records):
        project,digest,paths=self._binding(job,steps)
        if not records:
            raise CheckpointError('No completed source checkpoint')
        if any(x['plan_sha256']!=digest or x['project']!=str(project) for x in records):
            raise CheckpointError('Checkpoint source plan does not match selected approved job')
        wanted={name for name,_ in paths}
        if any(set(x['files'])!=wanted for x in records):
            raise CheckpointError('Checkpoint file list is incomplete or changed')
        return project,paths

    def restore_preview(self,job,steps,checkpoint_id):
        records=self.list(job['id'])
        project,paths=self._verify_binding(job,steps,records)
        target=next((row for row in records if row['id']==checkpoint_id),None)
        if target is None:raise CheckpointError('Selected checkpoint does not exist')
        latest=records[-1]
        # Validate EVERY requested source blob before asking the user to authorize
        # a multi-file restore. A missing/corrupt blob cannot cause partial undo.
        folder=self._job_dir(job['id'])/'objects'
        for sha in target['files'].values():
            if sha is not None:
                blob=folder/sha
                if not blob.is_file() or _digest(blob.read_bytes())!=sha:
                    raise CheckpointError('Restoration source blob is missing or corrupt')
        current={}
        for rel,path in paths:
            if not path.exists():current[rel]=None
            elif path.is_file() and not path.is_symlink() and path.stat().st_size<=MAX_READ_BYTES:
                current[rel]=_digest(path.read_bytes())
            else:raise CheckpointError('Protected, large or symlink source changed')
            if current[rel]!=latest['files'][rel]:
                raise CheckpointError(f'External file change: {rel}. No rollback until reconciled')
        difference=[rel for rel in current if current[rel]!=target['files'][rel]]
        if not difference:
            raise CheckpointError('Already at the selected checkpoint; no changes to restore')
        return {'target':target,'current':current,'changed':difference,
                'new_files_to_quarantine':[p for p in difference if target['files'][p] is None],
                'existing_files_to_restore':[p for p in difference if target['files'][p] is not None],
                'preview':'Restore source only. This revokes the job automation and invalidates prior verification.'}

    def rollback(self,job,steps,checkpoint_id,*,explicit_approval=False):
        if explicit_approval is not True:
            raise CheckpointError('Restoration needs explicit GUI confirmation')
        preview=self.restore_preview(job,steps,checkpoint_id)
        target=preview['target'];project=Path(job['project']).resolve(strict=True)
        folder=self._job_dir(job['id'])
        # Save the whole original live state FIRST for crash/partial-operation recovery.
        emergency=self.capture(job,steps,'pre_rollback')
        actions=[]
        for rel in preview['changed']:
            path=safe_target(project,rel)
            expected=preview['current'][rel]
            if expected!=(_digest(path.read_bytes()) if path.exists() else None):
                raise CheckpointError(f'File changed during rollback preflight: {rel}')
            sha=target['files'][rel]
            if sha is None:
                quarantine=folder/'quarantine'/emergency['id']/rel
                quarantine.parent.mkdir(parents=True,exist_ok=True)
                if not path.is_file() or path.is_symlink():
                    raise CheckpointError('New project file cannot be quarantined safely')
                os.replace(path,quarantine)
                actions.append({'path':rel,'action':'quarantined','recovery_file':str(quarantine)})
            else:
                content=(folder/'objects'/sha).read_bytes()
                if _digest(content)!=sha:raise CheckpointError('Checkpoint source blob corrupted')
                if not content:
                    # Existing empty UTF-8 source: use the same atomic replace discipline.
                    backup=folder/'quarantine'/emergency['id']/(rel+'.replaced')
                    backup.parent.mkdir(parents=True,exist_ok=True)
                    if path.exists():shutil.copy2(path,backup)
                    _atomic_bytes(path,b'')
                else:
                    # The original approved writer retains a separate timestamped backup.
                    apply_approved_file(project,rel,content.decode('utf-8'),
                                        folder/'restore-backups',expected_existing_sha=expected)
                actions.append({'path':rel,'action':'restored','sha256':sha})
        receipt=self.capture(job,steps,'restored')
        return {'emergency':emergency['id'],'restored_checkpoint':checkpoint_id,
                'receipt':receipt['id'],'actions':actions,
                'assurance':'Source hashes restored only; tests and permissions MUST be reapproved'}


    def comparison_baseline(self,job,steps,relative):
        """Exact immutable approval baseline only; no restoration or write."""
        records=self.list(job['id'])
        self._verify_binding(job,steps,records)
        row=records[0]
        if row['reason']!='approval_baseline' or relative not in row['files']:
            raise CheckpointError('Path has no approved source baseline')
        expected=row['files'][relative]
        if expected is None:return {'checkpoint':row['id'],'sha256':None,'text':''}
        if not isinstance(expected,str) or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
            raise CheckpointError('Invalid source baseline hash')
        blob=self._job_dir(job['id'])/'objects'/expected
        if not blob.is_file() or blob.is_symlink() or blob.stat().st_size>MAX_READ_BYTES:
            raise CheckpointError('Baseline source unavailable')
        data=blob.read_bytes()
        if _digest(data)!=expected:raise CheckpointError('Baseline source corruption')
        return {'checkpoint':row['id'],'sha256':expected,'text':data.decode('utf-8')}
