"""Persistent, explicitly approved serial tool workflows.

Workflow stage and JANUS action are committed in one SQLite transaction.
Commands are frozen from learned recipes; future inputs must be exact
outputs of earlier stages. This is not a process or filesystem sandbox.
"""
from __future__ import annotations
import hashlib
import io
import json
import sqlite3
import tomllib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from .workspace import safe_target
from .action_guards import snapshot_file,verify_guards,validate_guards
from .janus_engine import utc_now
from .tool_acquisition import _approved_result,signature
from .structured_source import strict_json

MAX_STAGES=12
MAX_ARTIFACT=16_000_000


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def archive_scope(stream,suffix):
    with zipfile.ZipFile(stream) as z:
        entries=z.infolist()
        if not entries or len(entries)>4000 or sum(x.file_size for x in entries)>64_000_000:
            raise ValueError('Archive exceeds validation bounds')
        names=set()
        for entry in entries:
            name=entry.filename.replace('\\','/')
            if name.startswith('/') or ':' in name or '..' in name.split('/') or name.casefold() in names:
                raise ValueError('Archive contains unsafe or duplicate path')
            names.add(name.casefold())
            if entry.flag_bits&1 or (entry.external_attr>>16)&0o170000==0o120000:
                raise ValueError('Archive contains encrypted or symlink member')
        if suffix=='.apk' and 'androidmanifest.xml' not in names:raise ValueError('APK missing AndroidManifest.xml')
        if suffix=='.aab' and 'base/manifest/androidmanifest.xml' not in names:raise ValueError('AAB missing base manifest')
        if z.testzip() is not None:raise ValueError('Archive CRC failed')
    return 'archive structure and CRC (not installability)'


def artifact(root,relative):
    path=safe_target(root,relative,must_exist=True)
    size=path.stat().st_size
    if size>MAX_ARTIFACT:
        from .large_artifacts import verify_large_artifact
        return verify_large_artifact(path,archive_scope)
    if not 0<size<=MAX_ARTIFACT:raise ValueError('Artifact empty or exceeds check bound')
    data=path.read_bytes()
    if not 0<len(data)<=MAX_ARTIFACT:raise ValueError('Artifact size changed')
    suffix=path.suffix.casefold()
    scope='nonempty bytes only'
    if suffix in ('.xml','.svg'):
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise ValueError('XML DTD/entity not supported')
        ET.fromstring(data);scope='XML parse'
    elif suffix=='.json':
        strict_json(data.decode('utf-8-sig'));scope='JSON parse and unique keys'
    elif suffix=='.toml':
        tomllib.loads(data.decode('utf-8'));scope='TOML parse'
    elif suffix in ('.zip','.apk','.aab','.jar'):
        scope=archive_scope(io.BytesIO(data),suffix)
    else:
        from .artifact_media_checks import media_scope
        scope=media_scope(suffix,data) or scope
    return {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'scope':scope}


def freeze(acquisition,project,steps,*,continuation=False):
    root=Path(project).resolve(strict=True)
    if not (1 if continuation else 2)<=len(steps)<=MAX_STAGES:raise ValueError('Invalid workflow stage count')
    result=[]
    outputs={}
    protected=set()
    for item in steps:
        if set(item)!={'recipe_id','input'}:raise ValueError('Invalid workflow stage')
        row=acquisition._recipe_row(item['recipe_id'],root)
        args=json.loads(row['args_json'])
        rel=item['input']
        if bool(rel)!=('{{input}}' in args):raise ValueError('Recipe input must match its placeholder')
        if not row['artifact'] or '{{output}}' not in args:
            raise ValueError('Every workflow stage needs an explicit output placeholder and artifact')
        dest=safe_target(root,row['artifact'])
        if dest.exists() or dest.is_symlink():raise ValueError('Workflow outputs must be new files')
        out=str(dest.relative_to(root)).replace('\\','/')
        key=out.casefold()
        if key in outputs or key in protected:raise ValueError('Workflow output collides with another stage')
        input_rel=''
        predecessor=None
        guards=[]
        if rel:
            source=safe_target(root,rel)
            input_rel=str(source.relative_to(root)).replace('\\','/')
            predecessor=outputs.get(input_rel.casefold())
            if predecessor is None:
                guards.append(snapshot_file(source))
                protected.add(input_rel.casefold())
            if input_rel.casefold()==key:raise ValueError('In-place operations are not eligible')
        argv=acquisition._build_recipe_command(row,input_rel,allow_future_input=predecessor is not None)
        guards.append(snapshot_file(argv[0],kind='stat'))
        if row['script_path']:
            script=safe_target(root,row['script_path'],must_exist=True)
            script_key=str(script.relative_to(root)).replace('\\','/').casefold()
            if script_key in outputs or script_key==key:raise ValueError('Output collides with a script')
            protected.add(script_key)
            guards.append(snapshot_file(script))
        guards.append(snapshot_file(dest,kind='absent'))
        validate_guards(guards)
        result.append({'recipe_id':int(row['id']),'title':row['title'],'tool':row['name'],
                       'argv':argv,'input':input_rel,'predecessor':predecessor,'output':out,'guards':guards})
        outputs[key]=len(result)
    return {'project':str(root),'stages':result}


class ToolWorkflows:
    def __init__(self,janus):
        self.janus=janus
        with janus.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tool_workflows(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                    manifest TEXT NOT NULL, manifest_sha TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'active', detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tool_workflow_stages(
                    workflow_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                    action_id INTEGER UNIQUE, state TEXT NOT NULL DEFAULT 'planned',
                    receipt TEXT, PRIMARY KEY(workflow_id,ordinal),
                    FOREIGN KEY(workflow_id) REFERENCES tool_workflows(id));
            """)

    def get(self,ident):
        with self.janus.connect() as db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT * FROM tool_workflows WHERE id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def approve(self,manifest,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Whole workflow must be explicitly approved')
        if manifest.get('mixed_task') and 'acceptance' in manifest['mixed_task']:
            from .mixed_roadmap import require_output
            require_output(manifest['mixed_task'],manifest)
        if manifest.get('recovery'):
            from .workflow_recovery import verify_recovery
            verify_recovery(self,manifest['recovery'],manifest['project'])
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if manifest.get('recovery'):
                parent=manifest['recovery']['workflow_id']
                # Unique successor even across duplicate UI approval or restart.
                for existing in db.execute('SELECT manifest FROM tool_workflows WHERE project=?',(manifest['project'],)):
                    if json.loads(existing[0]).get('recovery',{}).get('workflow_id')==parent:
                        raise ValueError('A continuation has already been approved for this failed workflow')
            ident=db.execute('INSERT INTO tool_workflows(project,manifest,manifest_sha,created_at) VALUES(?,?,?,?)',
                    (manifest['project'],json.dumps(manifest,ensure_ascii=False),digest(manifest),utc_now())).lastrowid
            db.executemany('INSERT INTO tool_workflow_stages(workflow_id,ordinal) VALUES(?,?)',
                           [(ident,i) for i in range(1,len(manifest['stages'])+1)])
        return ident

    def list(self,project=None):
        with self.janus.connect() as db:
            db.row_factory=sqlite3.Row
            if project is None:rows=db.execute('SELECT * FROM tool_workflows ORDER BY id DESC LIMIT 100')
            else:rows=db.execute('SELECT * FROM tool_workflows WHERE project=? ORDER BY id DESC LIMIT 100',(str(Path(project).resolve()),))
            return [dict(row) for row in rows]

    def stages(self,ident):
        with self.janus.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM tool_workflow_stages WHERE workflow_id=? ORDER BY ordinal',(ident,))]

    def roadmap_members(self,request_id):
        with self.janus.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute("SELECT * FROM tool_workflows WHERE json_extract(manifest,'$.roadmap.request_id')=? ORDER BY id",(request_id,))]

    def busy(self):
        with self.janus.connect() as db:
            return bool(db.execute("""SELECT 1 FROM tool_workflow_stages s JOIN janus_actions a ON a.id=s.action_id
                WHERE a.status IN ('approved','running') LIMIT 1""").fetchone())

    def stop(self,ident):
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("UPDATE tool_workflows SET state='cancelled',detail='User stopped workflow' WHERE id=? AND state='active'",(ident,))
            db.execute("""UPDATE janus_actions SET cancel_requested=1,
                status=CASE WHEN status='approved' THEN 'cancelled' ELSE status END
                WHERE status IN ('approved','running') AND id IN
                (SELECT action_id FROM tool_workflow_stages WHERE workflow_id=?)""",(ident,))

    def _check_receipt(self,project,stage,row):
        rec=json.loads(row['receipt'])
        action=self.janus.action(row['action_id'])
        if not action:raise ValueError('Missing prior action')
        _,log_sha,_=_approved_result(action,stage['argv'],project,kind='tool')
        verify_guards([g for g in json.loads(action['input_guards_json']) if g['kind']!='absent'])
        if rec['log_sha256']!=log_sha or rec['artifact']!=artifact(project,stage['output']):
            raise ValueError('Prior checked output or process log changed')
        run=self.get(row['workflow_id'])
        manifest=json.loads(run['manifest'])
        if digest(manifest)!=run['manifest_sha']:raise ValueError('Acceptance manifest changed')
        from .artifact_acceptance import stage_acceptance
        expected=stage_acceptance(project,stage,manifest.get('mixed_task'),rec['artifact'])
        if rec.get('acceptance')!=expected:raise ValueError('Artifact acceptance receipt missing or changed')
        return rec

    def tick(self,*,enabled=True,conversations=None,roadmap_ready=None,before_dispatch=None,priority=None):
        if not enabled or self.janus.status().get('paused'):return None
        runs=list(reversed(self.list()))
        def scope(run):
            try:return dict(project=run['project'],chat_id=(json.loads(run['manifest']).get('specification') or {}).get('chat_id',''),id=run['id'])
            except (ValueError,TypeError,KeyError):return dict(project=run['project'],chat_id='',id=run['id'])
        if priority is not None:runs.sort(key=lambda r:priority.key(scope(r)))
        for run in runs:
            if run['state']!='active':continue
            if priority is not None and not priority.allowed(scope(run)) and not any(r['state']=='dispatched' for r in self.stages(run['id'])):continue
            ident=run['id']
            try:
                manifest=json.loads(run['manifest'])
                if digest(manifest)!=run['manifest_sha'] or manifest['project']!=run['project']:
                    raise ValueError('Approved workflow manifest changed')
                if manifest.get('specification'):
                    from .workflow_design import current_source
                    if conversations is None or not current_source(manifest['specification'],conversations):
                        self.stop(ident)
                        return f'Workflow #{ident}: specification superseded; remaining operations cancelled'
                if manifest.get('recovery'):
                    from .workflow_recovery import verify_recovery
                    verify_recovery(self,manifest['recovery'],run['project'])
                if manifest.get('roadmap') and (roadmap_ready is None or not roadmap_ready(manifest['roadmap'])):
                    continue
                project=run['project'];rows=self.stages(ident);stages=manifest['stages']
                if len(rows)!=len(stages):raise ValueError('Workflow stage count changed')
                prior={}
                for ordinal,(stage,row) in enumerate(zip(stages,rows),1):
                    if row['ordinal']!=ordinal:raise ValueError('Workflow stage order changed')
                    if row['state']=='checked':
                        prior[ordinal]=self._check_receipt(project,stage,row)
                        continue
                    if row['state']=='dispatched':
                        action=self.janus.action(row['action_id'])
                        if not action:raise ValueError('Workflow action missing')
                        if action['status'] in ('approved','running'):return None
                        _,log_sha,_=_approved_result(action,stage['argv'],project,kind='tool')
                        # Recheck the executable, original source and predecessor
                        # inputs AFTER execution too; the new output must exist.
                        verify_guards([g for g in json.loads(action['input_guards_json']) if g['kind']!='absent'])
                        receipt={'log_sha256':log_sha,'artifact':artifact(project,stage['output'])}
                        from .artifact_acceptance import stage_acceptance,AcceptanceMismatch
                        try:
                            checked=stage_acceptance(project,stage,manifest.get('mixed_task'),receipt['artifact'])
                        except AcceptanceMismatch as error:
                            # Distinguish a real property mismatch from an
                            # interrupted process or unverifiable file.
                            receipt['rejection']={'detail':str(error),'checks':manifest['mixed_task']['acceptance']}
                            with self.janus.connect() as db:
                                db.execute('BEGIN IMMEDIATE')
                                db.execute("UPDATE tool_workflow_stages SET state='rejected',receipt=? WHERE workflow_id=? AND ordinal=? AND state='dispatched'",
                                           (json.dumps(receipt),ident,ordinal))
                                db.execute("UPDATE tool_workflows SET state='blocked',detail=? WHERE id=? AND state='active'",
                                           (str(error)[:500],ident))
                            return f'Workflow #{ident} blocked: {error}'
                        if checked is not None:receipt['acceptance']=checked
                        with self.janus.connect() as db:
                            db.execute("UPDATE tool_workflow_stages SET state='checked',receipt=? WHERE workflow_id=? AND ordinal=? AND state='dispatched'",
                                       (json.dumps(receipt),ident,ordinal))
                        return f'Workflow #{ident} stage {ordinal}: {receipt["artifact"]["scope"]} checked'
                    if row['state']!='planned':raise ValueError('Unknown workflow stage state')
                    if priority is not None and not priority.allowed(scope(run)):return None
                    guards=list(stage['guards'])
                    if stage['predecessor'] is not None:
                        producer=prior.get(stage['predecessor'])
                        if not producer:raise ValueError('Missing verified predecessor output')
                        pin=snapshot_file(safe_target(project,stage['input'],must_exist=True))
                        if pin['expected']!=producer['artifact']['sha256']:raise ValueError('Predecessor bytes changed')
                        guards.append(pin)
                    validate_guards(guards);verify_guards(guards)
                    if before_dispatch is not None and manifest.get('specification'):
                        if not before_dispatch(run,manifest,ordinal,stage,guards):return None
                        # No approval or guard may be inherited from memory review.
                        if not current_source(manifest['specification'],conversations):
                            self.stop(ident)
                            return f'Workflow #{ident}: specification changed during memory review'
                        if manifest.get('roadmap') and (roadmap_ready is None or not roadmap_ready(manifest['roadmap'])):return None
                        verify_guards(guards)
                    with self.janus.connect() as db:
                        db.execute('BEGIN IMMEDIATE')
                        current=db.execute('SELECT state,manifest_sha FROM tool_workflows WHERE id=?',(ident,)).fetchone()
                        if current!=('active',run['manifest_sha']):return None
                        # Both action insertion and its workflow receipt are atomic.
                        if db.execute("SELECT 1 FROM janus_actions WHERE status IN ('approved','running') LIMIT 1").fetchone():return None
                        slot=db.execute('SELECT state,action_id FROM tool_workflow_stages WHERE workflow_id=? AND ordinal=?',(ident,ordinal)).fetchone()
                        if slot!=('planned',None):return None
                        action_id=db.execute("""INSERT INTO janus_actions(kind,label,cwd,argv_json,approved_at,approval_source,input_guards_json)
                            VALUES('tool',?,?,?,?,'desktop-user-confirmation',?)""",
                            (f'Workflow #{ident} stage {ordinal}',project,json.dumps(stage['argv']),utc_now(),json.dumps(guards))).lastrowid
                        db.execute("UPDATE tool_workflow_stages SET state='dispatched',action_id=? WHERE workflow_id=? AND ordinal=?",
                                   (action_id,ident,ordinal))
                    return f'Workflow #{ident} stage {ordinal} queued as JANUS action #{action_id}'
                with self.janus.connect() as db:
                    db.execute("UPDATE tool_workflows SET state='complete',detail='All declared outputs checked; functional acceptance not established' WHERE id=? AND state='active'",(ident,))
                return f'Workflow #{ident}: all declared outputs checked (not functional acceptance)'
            except (ValueError,OSError,KeyError,TypeError,ET.ParseError,zipfile.BadZipFile) as error:
                with self.janus.connect() as db:
                    db.execute("UPDATE tool_workflows SET state='blocked',detail=? WHERE id=? AND state='active'",(str(error)[:500],ident))
                return f'Workflow #{ident} blocked: {error}'
        return None
