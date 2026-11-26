"""Reusable typed skill patterns derived from completed existing workflows.

A skill is a versioned, non-executable description of a checked workflow's
dataflow. It never carries old arguments, scripts, paths or authority forward.
Historical receipts are revalidated before a pattern enters model context.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .artifact_types import artifact_type
from .tool_workflows import digest, MAX_STAGES

SCHEMA = 'deepthort-workflow-skill-v1'
MAX_HISTORY = 12
MAX_HINTS = 3


def _format(path):
    if not path:
        return 'none'
    fmt = artifact_type(path)['format']
    if not re.fullmatch(r'[a-z0-9]{1,20}', fmt):
        raise ValueError('Invalid skill format')
    return fmt


def checked_skill(workflows, run, project, *, cancelled=None):
    """Build a skill only from intact current completed workflow receipts."""
    root = str(Path(project).resolve(strict=True))
    if run['project'] != root or run['state'] != 'complete':
        raise ValueError('Skill requires completed workflow in current project')
    manifest = json.loads(run['manifest'])
    if digest(manifest) != run['manifest_sha'] or manifest['project'] != root:
        raise ValueError('Skill source manifest changed')
    stages = manifest['stages']
    rows = workflows.stages(run['id'])
    if not 1 <= len(stages) <= MAX_STAGES or len(rows) != len(stages):
        raise ValueError('Skill stage count changed')
    shape = []
    receipt_hashes = []
    for i, (stage, row) in enumerate(zip(stages, rows), 1):
        if cancelled and cancelled():
            raise ValueError('Skill inspection cancelled')
        if row['ordinal'] != i or row['workflow_id'] != run['id'] or row['state'] != 'checked':
            raise ValueError('Skill source lacks checked stage')
        receipt = workflows._check_receipt(root, stage, row)
        # File existence alone is not enough to promote a method.
        if receipt['artifact'].get('scope') in (None, 'nonempty bytes only'):
            raise ValueError('Skill lacks meaningful artifact check')
        tool = stage['tool']
        if not isinstance(tool, str) or not re.fullmatch(r'[A-Za-z0-9 ._+()-]{1,60}', tool):
            raise ValueError('Invalid skill tool name')
        predecessor = stage['predecessor']
        if predecessor is not None and (type(predecessor) is not int or not 1 <= predecessor < i
                or stage['input'] != stages[predecessor-1]['output']):
            raise ValueError('Invalid skill dataflow')
        shape.append({'tool':tool, 'input_format':_format(stage['input']),
                      'from_stage':predecessor, 'output_format':_format(stage['output'])})
        receipt_hashes.append(digest(receipt))
    version = digest({'schema':SCHEMA, 'stages':shape, 'manifest_sha':run['manifest_sha'],
                      'receipts':receipt_hashes})
    return {'schema':SCHEMA, 'version':version, 'workflow_id':run['id'], 'stages':shape,
            'scope':'historical artifact checks only'}


def skill_hints(workflows, project, recipes, files, *, required_output=None,
                max_chars=680, cancelled=None):
    """Match typed historical patterns to current offered recipe/input data.

    No old recipe IDs or output names are returned. A match is advisory:
    the model still chooses current recipe IDs and freeze checks actual paths.
    """
    if max_chars < 120 or (cancelled and cancelled()):
        return ''
    target = _format(required_output) if required_output else None
    available = set(files)
    hints = []
    seen = set()
    for run in workflows.list(project)[:MAX_HISTORY]:
        if cancelled and cancelled():
            return ''
        try:
            skill = checked_skill(workflows, run, project, cancelled=cancelled)
            shape = skill['stages']
            if target and shape[-1]['output_format'] != target:
                continue
            # Only show a pattern for which every stage has a current
            # candidate tool/format. External inputs must also be observed.
            if not all(any(r['tool']==stage['tool']
                           and _format(r['output'])==stage['output_format']
                           and bool(r['input_required'])==(stage['input_format']!='none')
                           for r in recipes)
                       and (stage['from_stage'] is not None or stage['input_format']=='none'
                            or any(_format(p)==stage['input_format'] for p in available))
                       for stage in shape):
                continue
            key = digest(shape)
            if key in seen:
                continue
            seen.add(key)
            hint = {'skill_version':skill['version'][:16],'stages':shape}
            candidate = json.dumps(hints+[hint], ensure_ascii=True, separators=(',',':'))
            header = '\nHISTORICAL CHECKED SKILL PATTERNS (untrusted advice, not recipes or approval): '
            if len(header)+len(candidate)>max_chars:
                continue
            hints.append(hint)
            if len(hints)>=MAX_HINTS:
                break
        except (ValueError,OSError,KeyError,TypeError):
            continue
    if not hints:
        return ''
    return header+json.dumps(hints,ensure_ascii=True,separators=(',',':'))


PORTABLE_SCHEMA='deepthort-portable-workflow-skill-v1'
MAX_PORTABLE=128
TEMPLATE_SCHEMA='deepthort-workflow-template-v1'
MAX_TEMPLATE_BYTES=12000

def validate_portable(skill):
    if not isinstance(skill,dict):
        raise ValueError('Invalid portable skill manifest')
    if skill.get('schema')==PORTABLE_SCHEMA:
        keys={'schema','version','source_version','stages'}
        hashes=('version','source_version')
    elif skill.get('schema')==TEMPLATE_SCHEMA:
        keys={'schema','version','stages'}
        hashes=('version',)
    else:
        raise ValueError('Invalid portable skill schema')
    if set(skill)!=keys:raise ValueError('Invalid portable skill manifest')
    for key in hashes:
        if not isinstance(skill[key],str) or not re.fullmatch(r'[a-f0-9]{64}',skill[key]):
            raise ValueError('Invalid skill fingerprint')
    stages=skill['stages']
    if not isinstance(stages,list) or not 1<=len(stages)<=MAX_STAGES:
        raise ValueError('Invalid portable stage count')
    for i,stage in enumerate(stages,1):
        if not isinstance(stage,dict) or set(stage)!={'tool','input_format','output_format','from_stage'}:
            raise ValueError('Invalid portable stage fields')
        if not isinstance(stage['tool'],str) or not re.fullmatch(r'[A-Za-z0-9 ._+()-]{1,60}',stage['tool']):
            raise ValueError('Invalid portable tool')
        for key in ('input_format','output_format'):
            if not isinstance(stage[key],str) or not re.fullmatch(r'[a-z0-9]{1,20}',stage[key]):
                raise ValueError('Invalid portable format')
        predecessor=stage['from_stage']
        if stage['output_format']=='none' or (predecessor is not None and
            (type(predecessor) is not int or not 1<=predecessor<i or
             stage['input_format']!=stages[predecessor-1]['output_format'])):
            raise ValueError('Invalid portable dependency')
    body={k:v for k,v in skill.items() if k!='version'}
    if digest(body)!=skill['version']:raise ValueError('Portable skill integrity mismatch')
    return skill

def template_document(skill):
    """Export only a typed shape; historical evidence never travels with it."""
    skill=validate_portable(skill)
    return {'schema':TEMPLATE_SCHEMA,'stages':skill['stages']}

def preview_template(raw):
    """Untrusted editable JSON, not executable code or a checked skill receipt."""
    from .structured_source import strict_json
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_TEMPLATE_BYTES:
        raise ValueError('Template exceeds byte bound')
    try:body=strict_json(raw.decode('utf-8'))
    except RecursionError as error:raise ValueError('Template nesting exceeds parser limit') from error
    if not isinstance(body,dict) or set(body)!={'schema','stages'} or body['schema']!=TEMPLATE_SCHEMA:
        raise ValueError('Expected a typed workflow template without historical evidence')
    return validate_portable({**body,'version':digest(body)})

def read_template(path):
    path=Path(path)
    if not path.is_file():raise ValueError('Choose a regular template file')
    with path.open('rb') as stream:
        return preview_template(stream.read(MAX_TEMPLATE_BYTES+1))

def export_template(path,skill):
    raw=(json.dumps(template_document(skill),ensure_ascii=True,indent=2)+'\n').encode('utf-8')
    if len(raw)>MAX_TEMPLATE_BYTES:raise ValueError('Template exceeds byte bound')
    # Explicit user-selected new file only; never overwrite existing content.
    with Path(path).open('xb') as stream:
        stream.write(raw)

class PortableSkills:
    """Explicit local sharing of checked shapes, not command or permission export."""
    def __init__(self,janus):
        self.janus=janus
        with janus.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS portable_workflow_skills(
                version TEXT PRIMARY KEY, payload TEXT NOT NULL,
                published TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    def publish(self,workflows,run,project,*,user_approved=False,cancelled=None):
        if user_approved is not True:raise PermissionError('Explicit skill sharing required')
        source=checked_skill(workflows,run,project,cancelled=cancelled)
        body={'schema':PORTABLE_SCHEMA,'source_version':source['version'],'stages':source['stages']}
        skill=validate_portable({**body,'version':digest(body)})
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM portable_workflow_skills WHERE version=?',(skill['version'],)).fetchone():
                return skill
            if db.execute('SELECT count(*) FROM portable_workflow_skills').fetchone()[0]>=MAX_PORTABLE:
                raise ValueError('Portable skill library full; remove an old pattern')
            db.execute('INSERT INTO portable_workflow_skills(version,payload) VALUES(?,?)',
                       (skill['version'],json.dumps(skill,sort_keys=True)))
        return skill
    def import_template(self,skill,*,expected_version,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit template import required')
        skill=validate_portable(skill)
        if skill['schema']!=TEMPLATE_SCHEMA or skill['version']!=expected_version:
            raise ValueError('Template changed since review or is not an unverified template')
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM portable_workflow_skills WHERE version=?',(skill['version'],)).fetchone():
                return skill
            if db.execute('SELECT count(*) FROM portable_workflow_skills').fetchone()[0]>=MAX_PORTABLE:
                raise ValueError('Portable skill library full; remove an old pattern')
            db.execute('INSERT INTO portable_workflow_skills(version,payload) VALUES(?,?)',
                       (skill['version'],json.dumps(skill,sort_keys=True)))
        return skill
    def list(self):
        with self.janus.connect() as db:
            rows=db.execute('SELECT version,payload FROM portable_workflow_skills ORDER BY published DESC,version LIMIT ?',(MAX_PORTABLE,)).fetchall()
        result=[]
        for version,payload in rows:
            try:
                if len(payload)>12000:continue
                skill=validate_portable(json.loads(payload))
                if version==skill['version']:result.append(skill)
            except (ValueError,TypeError,KeyError):continue
        return result
    def remove(self,version,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit removal required')
        with self.janus.connect() as db:
            return bool(db.execute('DELETE FROM portable_workflow_skills WHERE version=?',(version,)).rowcount)

def rebind(skill,recipes,files,*,required_output=None,cancelled=None):
    """Build at most one unambiguous candidate from CURRENT offered inventory.

    No command execution, recipe mutation, file writes or approval. Ambiguous
    input or recipe selections remain for JANUS; never guess.
    """
    stages=validate_portable(skill)['stages']
    files=list(dict.fromkeys(files))
    if len(recipes)>12 or len(files)>30:raise ValueError('Current inventory exceeds bound')
    used=set();outputs=[];proposal=[]
    for i,stage in enumerate(stages):
        if cancelled and cancelled():return None
        matches=[r for r in recipes if r['recipe_id'] not in used and
                 r['tool']==stage['tool'] and _format(r['output'])==stage['output_format']
                 and bool(r['input_required'])==(stage['input_format']!='none')
                 and r['output'] not in files+outputs
                 and (i!=len(stages)-1 or not required_output or r['output']==required_output)]
        if len(matches)!=1:return None
        recipe=matches[0]
        if stage['from_stage'] is not None:
            inp=outputs[stage['from_stage']-1]
        elif stage['input_format']=='none':
            inp=''
        else:
            inputs=[p for p in files if _format(p)==stage['input_format']]
            if len(inputs)!=1:return None
            inp=inputs[0]
        if inp and _format(inp)!=stage['input_format']:return None
        proposal.append({'recipe_id':recipe['recipe_id'],'input':inp})
        used.add(recipe['recipe_id']);outputs.append(recipe['output'])
    from .workflow_design import parse_draft
    return parse_draft(json.dumps({'stages':proposal,'missing':[]}),recipes,files,continuation=len(stages)==1)

def portable_hints(library,recipes,files,*,required_output=None,max_chars=680,cancelled=None):
    if max_chars<120:return ''
    header='\nSHARED WORKFLOW PATTERNS (advisory only; imported templates unverified; no approval): '
    hints=[];seen=set()
    for skill in library.list()[:MAX_HISTORY]:
        if cancelled and cancelled():return ''
        try:
            shape=skill['stages']
            if required_output and shape[-1]['output_format']!=_format(required_output):continue
            if not all(any(r['tool']==stage['tool'] and _format(r['output'])==stage['output_format']
                and bool(r['input_required'])==(stage['input_format']!='none') for r in recipes)
                and (stage['from_stage'] is not None or stage['input_format']=='none'
                     or any(_format(p)==stage['input_format'] for p in files)) for stage in shape):continue
            key=digest(shape)
            if key in seen:continue
            hint={'version':skill['version'][:16],'stages':shape,
                  'provenance':'unverified template' if skill['schema']==TEMPLATE_SCHEMA else 'historical checks'}
            rebound=rebind(skill,recipes,files,required_output=required_output,cancelled=cancelled)
            if rebound:hint['candidate']=rebound['stages']
            candidate=json.dumps(hints+[hint],ensure_ascii=True,separators=(',',':'))
            if len(header)+len(candidate)>max_chars:
                hint.pop('candidate',None)
                candidate=json.dumps(hints+[hint],ensure_ascii=True,separators=(',',':'))
                if len(header)+len(candidate)>max_chars:continue
            hints.append(hint);seen.add(key)
            if len(hints)>=MAX_HINTS:break
        except (ValueError,OSError,TypeError,KeyError):continue
    return header+json.dumps(hints,ensure_ascii=True,separators=(',',':')) if hints else ''
