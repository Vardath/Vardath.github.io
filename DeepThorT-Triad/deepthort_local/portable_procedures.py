"""Explicitly shared, evidence-bound command templates; no execution authority."""
from __future__ import annotations
import json
import re
import hashlib
from pathlib import Path
from .artifact_types import artifact_type
from .tool_workflows import digest
from .tool_acquisition import ToolAcquisition
from .workspace import safe_target

SCHEMA='deepthort-portable-procedure-v1'
MAX_SHARED=128
PARAMETERS={'{{input}}','{{output}}','{{project}}'}

def fmt(path):
    value=artifact_type(path)['format']
    if not re.fullmatch(r'[a-z0-9]{1,20}',value):raise ValueError('Unsupported format')
    return value

def template_args(args):
    ToolAcquisition._validate_args(args)
    if args.count('{{output}}')!=1 or args.count('{{input}}')>1:
        raise ValueError('A portable template needs exactly one output and at most one input')
    for arg in args:
        # Deliberately exclude all literal paths, free-form text, scripts,
        # key=value expressions and credentials-shaped switches. The user
        # also reviews every retained literal before publication.
        if arg in PARAMETERS:continue
        if not re.fullmatch(r'(?:-{1,2}[A-Za-z][A-Za-z0-9_-]{0,39}|[A-Za-z][A-Za-z0-9_-]{0,31}|[0-9]{1,9}(?:\.[0-9]{1,6})?)',arg):
            raise ValueError('Literal arguments must be simple flags, enums or numbers; parameterise paths first')
        if re.search(r'(?i)password|secret|credential|token|api[-_]?key|auth',arg):
            raise ValueError('Credential-like arguments cannot be shared')
    return args

def validate(row):
    if not isinstance(row,dict) or set(row)!={'schema','version','tool','args','input_format','output_format','executable_signature','help_sha','source_evidence'} or row['schema']!=SCHEMA:
        raise ValueError('Invalid portable procedure')
    for k in ('version','executable_signature','help_sha','source_evidence'):
        if not isinstance(row[k],str) or not re.fullmatch(r'[a-f0-9]{64}',row[k]):raise ValueError('Invalid evidence hash')
    if not isinstance(row['tool'],str) or not re.fullmatch(r'[A-Za-z0-9 ._+()-]{1,60}',row['tool']):
        raise ValueError('Invalid tool name')
    args=template_args(row['args'])
    for k in ('input_format','output_format'):
        if not isinstance(row[k],str) or not re.fullmatch(r'[a-z0-9]{1,20}',row[k]):raise ValueError('Invalid format')
    if row['output_format']=='none' or (row['input_format']!='none')!=('{{input}}' in args):
        raise ValueError('Parameter format mismatch')
    if digest({k:v for k,v in row.items() if k!='version'})!=row['version']:
        raise ValueError('Portable procedure fingerprint changed')
    return row

class PortableProcedures:
    def __init__(self,acquisition):
        self.acquisition=acquisition
        with acquisition._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS portable_procedures(
                version TEXT PRIMARY KEY,payload TEXT NOT NULL,created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

    def preview(self,recipe_id,project,janus):
        root=Path(project).resolve(strict=True)
        rec=self.acquisition._recipe_row(recipe_id,root)
        if rec['script_path'] or rec['script_source']:raise ValueError('Script-bearing recipes remain project-local')
        args=template_args(json.loads(rec['args_json']))
        if not rec['artifact'] or not rec['action_id']:raise ValueError('Procedure needs an approved artifact-producing execution')
        observed=self.acquisition.reconcile(recipe_id,root,janus)
        if observed['status']!='artifact_produced' or observed.get('artifact_scope') in (None,'nonempty bytes only'):
            raise ValueError('Current meaningful artifact evidence is required')
        rec=self.acquisition._recipe_row(recipe_id,root)
        # Reconstruct the original exact argv from its typed placeholders.
        # Do not store the expanded paths or source recipe ID in shared memory.
        argv=json.loads(rec['approved_argv'])
        if len(argv)!=len(args)+1:raise ValueError('Original command does not match the template')
        inp=''
        if '{{input}}' in args:
            inp=Path(argv[1+args.index('{{input}}')]).resolve(strict=True).relative_to(root).as_posix()
        if self.acquisition._build_recipe_command(rec,inp)!=argv:
            raise ValueError('Original approved arguments no longer match')
        help_record=self.acquisition.probe_evidence(rec['name'],janus)
        if not help_record:raise ValueError('Current approved application help is required')
        body={'schema':SCHEMA,'tool':rec['name'],'args':args,
              'input_format':fmt(inp) if inp else 'none','output_format':fmt(rec['artifact']),
              'executable_signature':rec['executable_signature'],'help_sha':help_record['sha256'],
              'source_evidence':digest([rec['action_id'],rec['log_sha'],observed['artifact_sha256'],observed['artifact_scope']])}
        return validate({**body,'version':digest(body)})

    def publish(self,recipe_id,project,janus,*,expected_version,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit template publication required')
        row=self.preview(recipe_id,project,janus)
        if row['version']!=expected_version:raise ValueError('Source evidence changed since review')
        with self.acquisition._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM portable_procedures WHERE version=?',(row['version'],)).fetchone():return row
            if db.execute('SELECT count(*) FROM portable_procedures').fetchone()[0]>=MAX_SHARED:raise ValueError('Shared procedure library full')
            db.execute('INSERT INTO portable_procedures(version,payload) VALUES(?,?)',(row['version'],json.dumps(row,sort_keys=True)))
        return row

    def list(self):
        with self.acquisition._db() as db:
            rows=db.execute('SELECT version,payload FROM portable_procedures ORDER BY created DESC,version LIMIT ?',(MAX_SHARED,)).fetchall()
        result=[]
        for version,payload in rows:
            try:
                if len(payload)>12000:continue
                row=validate(json.loads(payload))
                if row['version']==version:result.append(row)
            except (ValueError,TypeError,KeyError):continue
        return result

    def remove(self,version,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit removal required')
        with self.acquisition._db() as db:
            return bool(db.execute('DELETE FROM portable_procedures WHERE version=?',(version,)).rowcount)

    def current(self,row,janus):
        validate(row)
        tool=self.acquisition.tool(row['tool'])
        if tool['executable_signature']!=row['executable_signature']:
            raise ValueError('Application changed; relearn and verify the procedure for this version')
        help_record=self.acquisition.probe_evidence(row['tool'],janus)
        if not help_record or help_record['sha256']!=row['help_sha']:
            raise ValueError('Approved help changed; relearn or republish checked evidence')

    def bind(self,version,project,output,janus,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit creation of a new candidate required')
        row=next((r for r in self.list() if r['version']==version),None)
        if not row:raise ValueError('Shared procedure not found')
        self.current(row,janus)
        root=Path(project).resolve(strict=True)
        target=safe_target(root,output)
        if target.exists() or target.is_symlink() or fmt(output)!=row['output_format']:
            raise ValueError('Choose a new project-relative output with the checked format')
        relative=target.relative_to(root).as_posix()
        title='Shared '+row['tool']+' '+row['version'][:10]+' '+hashlib.sha256(relative.encode()).hexdigest()[:12]
        raw=json.dumps({'title':title,'purpose':'Adapt historical checked command to new project; execution and output unverified.',
                        'args':row['args'],'artifact':relative})
        # No prior action, evidence, script, or approvals are inserted.
        return self.acquisition.propose_recipe_for_goal(row['tool'],root,'Rebind shared procedure',raw,
            insert_only=True,portable_input_format='' if row['input_format']=='none' else row['input_format'])

    def hints(self,tool,output,janus,*,max_chars=600):
        if max_chars<180:return ''
        header='\nHISTORICAL SHARED COMMAND TEMPLATES (advice only; validate goal and review new candidate): '
        rows=[]
        for row in self.list():
            if row['tool']!=tool or row['output_format']!=fmt(output):continue
            try:self.current(row,janus)
            except (ValueError,OSError,KeyError):continue
            hint={k:row[k] for k in ('args','input_format','output_format')}
            text=json.dumps(rows+[hint],ensure_ascii=True,separators=(',',':'))
            if len(header)+len(text)>max_chars:continue
            rows.append(hint)
            if len(rows)>=3:break
        return header+json.dumps(rows,ensure_ascii=True,separators=(',',':')) if rows else ''
