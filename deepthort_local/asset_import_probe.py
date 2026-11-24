"""Explicitly approved application import smoke tests for checked artifacts.

Fixed bundled scripts only. A successful import does not establish rendering,
project integration, gameplay or safe execution of untrusted native assets.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .workspace import safe_target
from .action_guards import snapshot_file,verify_guards,validate_guards
from .tool_workflows import digest
from .tool_acquisition import _approved_result
from .janus_engine import utc_now

PROBE_ROOT=Path(__file__).resolve().parent/'asset_probes'
SUPPORTED={'Blender':{'.obj','.glb','.png'},'Godot':{'.glb','.png'}}
MARKER='DEEPTHORT_ASSET_PROBE '

def validate_imports(output,tools):
    if not isinstance(tools,list) or not 1<=len(tools)<=2:
        raise ValueError('Expected one or two required application imports')
    suffix=Path(output).suffix.casefold()
    if any(not isinstance(t,str) or suffix not in SUPPORTED.get(t,set()) for t in tools):
        raise ValueError('Unsupported required application import for artifact')
    if len(set(tools))!=len(tools):raise ValueError('Duplicate import requirement')
    return sorted(tools)

def required_imports(workflows,run):
    """Return unmet approved application checks for this exact completed run.

    A failed, stale, interrupted or unrelated probe never satisfies a gate.
    Do not generate another producer merely because an import is outstanding.
    """
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha'] or manifest['project']!=run['project']:
        raise ValueError('Import requirement manifest changed')
    task=manifest.get('mixed_task') or {}
    if 'imports' not in task:return []
    tools=validate_imports(task['output'],task['imports'])
    if run['state']!='complete':raise ValueError('Import gate needs a completed producer')
    stages=manifest['stages']
    ordinals=[i for i,s in enumerate(stages,1) if s['output']==task['output']]
    if len(ordinals)!=1:raise ValueError('Import requirement output is missing or ambiguous')
    ordinal=ordinals[0]
    rows=workflows.stages(run['id'])
    if len(rows)!=len(stages) or rows[ordinal-1]['state']!='checked':
        raise ValueError('Import requirement has no checked artifact')
    receipt=workflows._check_receipt(run['project'],stages[ordinal-1],rows[ordinal-1])['artifact']
    store=AssetProbes(workflows)
    pending=[]
    for tool in tools:
        candidates=store.for_requirement(run['id'],ordinal,tool)
        status='needs_approval'
        for action_id,approved in candidates:
            if (approved.get('manifest_sha')!=run['manifest_sha'] or approved.get('project')!=run['project']
                or approved.get('output')!=task['output'] or approved.get('artifact_sha256')!=receipt['sha256']
                or approved.get('specification')!=manifest.get('specification')):
                continue
            try:result=store.result(action_id)
            except (ValueError,OSError,KeyError,TypeError):
                if status=='needs_approval':status='invalid_or_stale'
                continue
            if result.get('import_verified') is True:
                break
            if status=='needs_approval':status=result['status']
        else:
            pending.append({'workflow_id':run['id'],'ordinal':ordinal,'tool':tool,
                            'output':task['output'],'status':status})
    return pending

def plan(workflows,acquisition,workflow_id,ordinal,tool):
    run=workflows.get(workflow_id)
    if not run or run['state']!='complete':raise ValueError('Select a completed checked workflow')
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha']:raise ValueError('Workflow manifest changed')
    if type(ordinal) is not int or not 1<=ordinal<=len(manifest['stages']):
        raise ValueError('Invalid artifact stage')
    row=workflows.stages(workflow_id)[ordinal-1]
    if row['state']!='checked':raise ValueError('Artifact lacks a checked stage receipt')
    stage=manifest['stages'][ordinal-1]
    receipt=workflows._check_receipt(run['project'],stage,row)['artifact']
    target=safe_target(run['project'],stage['output'],must_exist=True)
    if target.suffix.casefold() not in SUPPORTED.get(tool,set()):
        raise ValueError('Unsupported application and artifact format combination')
    template=command_template(acquisition,run['project'],stage['output'],tool)
    pin=snapshot_file(target)
    if pin['expected']!=receipt['sha256']:raise ValueError('Checked artifact changed')
    guards=[template['guards'][0],pin,*template['guards'][1:]]
    validate_guards(guards)
    return {'workflow_id':workflow_id,'ordinal':ordinal,'manifest_sha':run['manifest_sha'],
            'specification':manifest.get('specification'),'project':run['project'],'tool':tool,
            'output':stage['output'],'artifact_sha256':receipt['sha256'],'argv':template['argv'],'guards':guards}

def command_template(acquisition,project,output,tool):
    target=safe_target(project,output)
    if target.suffix.casefold() not in SUPPORTED.get(tool,set()):
        raise ValueError('Unsupported application and artifact format combination')
    exe=Path(acquisition.tool(tool)['executable']).resolve(strict=True)
    guards=[snapshot_file(exe,kind='stat')]
    if tool=='Blender':
        script=PROBE_ROOT/'blender_probe.py'
        argv=[str(exe),'--background','--factory-startup','--disable-autoexec','--python-exit-code','19',
              '--python',str(script),'--',str(target)]
    else:
        script=PROBE_ROOT/'godot_probe.gd'
        config=PROBE_ROOT/'project.godot'
        guards.append(snapshot_file(config))
        argv=[str(exe),'--headless','--path',str(PROBE_ROOT),'--script',str(script),'--',str(target)]
    guards.append(snapshot_file(script))
    validate_guards(guards)
    return {'tool':tool,'output':output,'argv':argv,'guards':guards}

def import_templates(acquisition,manifest):
    task=manifest.get('mixed_task') or {}
    if not task.get('imports'):return []
    if not manifest.get('specification'):raise ValueError('Automatic import needs a specification binding')
    if sum(s['output']==task['output'] for s in manifest['stages'])!=1:
        raise ValueError('Automatic import needs exactly one producer')
    return [command_template(acquisition,manifest['project'],task['output'],tool)
            for tool in validate_imports(task['output'],task['imports'])]

def auto_template(approved):
    # Same fixed command and executable/script/config pins; the checked output
    # gets its actual byte hash only after production.
    return {'tool':approved['tool'],'output':approved['output'],'argv':approved['argv'],
            'guards':[approved['guards'][0],*approved['guards'][2:]]}

def auto_authority(workflows,approved,roadmap,mixed):
    run=workflows.get(approved['workflow_id'])
    if not run or run['state']!='complete' or run['manifest_sha']!=approved['manifest_sha']:
        raise ValueError('Automatic import producer changed')
    manifest=json.loads(run['manifest'])
    if digest(manifest)!=run['manifest_sha'] or manifest['project']!=approved['project']:
        raise ValueError('Automatic import manifest changed')
    link=manifest.get('roadmap') or {}
    task=manifest.get('mixed_task') or {}
    binding=manifest.get('specification')
    if (not binding or binding!=approved['specification'] or not link or
        roadmap['state']!='active' or link['request_id']!=roadmap['request_id'] or
        link['manifest_sha256']!=roadmap['manifest_sha256'] or link['project']!=roadmap['project'] or
        not mixed or mixed['sha']!=roadmap.get('mixed_sha') or mixed['request_id']!=roadmap['request_id']
        or mixed['code_sha']!=roadmap['manifest_sha256'] or task not in mixed['tasks']
        or approved['tool'] not in task.get('imports',[]) or approved['output']!=task['output']
        or auto_template(approved) not in manifest.get('auto_imports',[])):
        raise ValueError('No current reviewed automatic import authority')
    from .workflow_design import current_source_file
    if not current_source_file(binding,workflows.janus.path.parent/'conversations.sqlite3'):
        raise ValueError('Automatic import specification superseded')
    return {'request_id':roadmap['request_id'],'code_sha':roadmap['manifest_sha256'],'mixed_sha':mixed['sha']}

def claim_auto_authority(janus,approved,authority):
    from .project_authority import load_policy
    from .roadmap_runs import RoadmapRuns
    from .mixed_roadmap import MixedRoadmaps
    from .tool_workflows import ToolWorkflows
    state=janus.path.parent
    if not load_policy(state/'project-work-policy.json')['enabled'] or janus.status().get('paused'):
        return False
    if not (state/'roadmap-runs.sqlite3').is_file() or not (state/'mixed-roadmaps.sqlite3').is_file():
        raise ValueError('Automatic import roadmap database missing')
    roadmap=RoadmapRuns(state/'roadmap-runs.sqlite3').get(authority['request_id'])
    if not roadmap or roadmap['state']!='active':return False
    mixed=MixedRoadmaps(state/'mixed-roadmaps.sqlite3').get(authority['request_id'],authority['code_sha'])
    return auto_authority(ToolWorkflows(janus),approved,roadmap,mixed)==authority

class AssetProbes:
    def __init__(self,workflows):
        self.workflows=workflows
        self.janus=workflows.janus
        with self.janus.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS asset_probe_runs(
                action_id INTEGER PRIMARY KEY, plan TEXT NOT NULL, plan_sha TEXT NOT NULL)''')
    def queue(self,approved,acquisition,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Approve exact application smoke test')
        return self._queue(approved,acquisition)
    def queue_required(self,approved,acquisition,roadmap,mixed,*,enabled=False):
        if enabled is not True:raise PermissionError('Unattended project work disabled')
        authority=auto_authority(self.workflows,approved,roadmap,mixed)
        if not claim_auto_authority(self.janus,approved,authority):
            raise ValueError('Automatic import authority is not active')
        pending=required_imports(self.workflows,self.workflows.get(approved['workflow_id']))
        if not any(p['tool']==approved['tool'] and p['ordinal']==approved['ordinal'] and p['status']=='needs_approval' for p in pending):
            return None  # failed/cancelled/interrupted tests need deliberate review
        return self._queue(approved,acquisition,authority=authority)
    def _queue(self,approved,acquisition,authority=None):
        if plan(self.workflows,acquisition,approved['workflow_id'],approved['ordinal'],approved['tool'])!=approved:
            raise ValueError('Asset or executable changed during approval')
        verify_guards(approved['guards'])
        stored=dict(approved)
        if authority:stored['automatic_authority']=authority
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM janus_actions WHERE status IN ('approved','running') LIMIT 1").fetchone():
                raise ValueError('Wait for existing approved processes')
            if authority:
                # Durable, one attempt for each exact requirement, even on restart.
                if db.execute("""SELECT 1 FROM asset_probe_runs WHERE json_extract(plan,'$.workflow_id')=?
                    AND json_extract(plan,'$.ordinal')=? AND json_extract(plan,'$.tool')=? LIMIT 1""",
                    (approved['workflow_id'],approved['ordinal'],approved['tool'])).fetchone():return None
            ident=db.execute("""INSERT INTO janus_actions(kind,label,cwd,argv_json,approved_at,approval_source,input_guards_json)
                VALUES('tool',?,?,?,?,'desktop-user-confirmation',?)""",
                ('Asset import smoke test: '+approved['tool'],approved['project'],json.dumps(approved['argv']),
                 utc_now(),json.dumps(approved['guards']))).lastrowid
            db.execute('INSERT INTO asset_probe_runs VALUES(?,?,?)',(ident,json.dumps(stored),digest(stored)))
        return ident
    def recent(self,project):
        with self.janus.connect() as db:
            rows=db.execute('SELECT action_id,plan FROM asset_probe_runs ORDER BY action_id DESC LIMIT 100').fetchall()
        return [(ident,json.loads(raw)) for ident,raw in rows if json.loads(raw)['project']==str(Path(project).resolve())]
    def for_requirement(self,workflow_id,ordinal,tool):
        with self.janus.connect() as db:
            rows=db.execute("""SELECT action_id,plan FROM asset_probe_runs
                WHERE json_extract(plan,'$.workflow_id')=? AND json_extract(plan,'$.ordinal')=?
                AND json_extract(plan,'$.tool')=? ORDER BY action_id DESC LIMIT 100""",
                (workflow_id,ordinal,tool)).fetchall()
        return [(ident,json.loads(raw)) for ident,raw in rows]
    def result(self,ident):
        with self.janus.connect() as db:
            row=db.execute('SELECT plan,plan_sha FROM asset_probe_runs WHERE action_id=?',(ident,)).fetchone()
        if not row:raise ValueError('Unknown asset probe')
        approved=json.loads(row[0])
        if digest(approved)!=row[1]:raise ValueError('Asset probe plan changed')
        action=self.janus.action(ident)
        if not action:raise ValueError('Asset probe action missing')
        if approved.get('specification'):
            from .workflow_design import current_source_file
            if not current_source_file(approved['specification'],self.janus.path.parent/'conversations.sqlite3'):
                raise ValueError('Import specification superseded')
        if action['status']!='succeeded':
            return {'status':action['status'],'detail':action['detail'],'import_verified':False}
        if json.loads(action['input_guards_json'])!=approved['guards']:raise ValueError('Asset test guards changed')
        verify_guards(approved['guards'])
        run=self.workflows.get(approved['workflow_id'])
        if not run or run['state']!='complete' or run['manifest_sha']!=approved['manifest_sha']:
            raise ValueError('Original workflow changed')
        manifest=json.loads(run['manifest'])
        if digest(manifest)!=run['manifest_sha']:raise ValueError('Original manifest changed')
        ordinal=approved['ordinal']
        receipt=self.workflows._check_receipt(run['project'],manifest['stages'][ordinal-1],
                                             self.workflows.stages(run['id'])[ordinal-1])
        if receipt['artifact']['sha256']!=approved['artifact_sha256']:raise ValueError('Tested artifact changed')
        log,sha,_=_approved_result(action,approved['argv'],approved['project'],kind='tool')
        lines=log.decode('utf-8',errors='replace').splitlines()
        matches=[line[len(MARKER):] for line in lines if line.startswith(MARKER)]
        if len(matches)!=1:raise ValueError('Application did not emit one import result')
        result=json.loads(matches[0])
        kind='image' if Path(approved['output']).suffix.casefold()=='.png' else 'mesh'
        expected={'kind','width','height'} if kind=='image' else {'kind','meshes','vertices'}
        if (not isinstance(result,dict) or set(result)!=expected or result['kind']!=kind or
            any(type(result[k]) is not int or result[k]<=0 for k in expected-{'kind'})):
            raise ValueError('Application did not report valid loaded content')
        if kind=='image':
            from .artifact_media_checks import unpack_at
            target=safe_target(approved['project'],approved['output'],must_exist=True)
            with target.open('rb') as stream:
                header=stream.read(24)
            if (result['width'],result['height'])!=unpack_at('>II',header,16):
                raise ValueError('Imported image dimensions differ from checked artifact')
            verify_guards(approved['guards'])
        if any('SCRIPT ERROR:' in l or l.startswith(('ERROR:','Error:','Traceback (most recent call last):')) for l in lines):
            raise ValueError('Application log contains errors despite zero exit')
        return {'status':'import_checked','import_verified':True,'observed':result,
                'artifact_sha256':approved['artifact_sha256'],'log_sha256':sha,
                'scope':'Application import smoke test only; not rendering or project integration'}
