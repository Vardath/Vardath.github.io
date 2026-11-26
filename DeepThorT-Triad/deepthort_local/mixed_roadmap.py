"""Model-authored artifact requirements interleaved with code milestones.

Each exact indexed specification section receives an independent assessment.
The approved artifact obligations are separate from executable commands.
Missing capabilities block their boundary, rather than silently disappearing.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .workspace import safe_target
from .tool_workflows import digest
from .structured_source import strict_json
from .roadmap_runs import manifest as code_manifest

MAX_TASKS=80

def parse_tasks(answer,roadmap,section):
    data=strict_json(answer.strip())
    if not isinstance(data,dict) or set(data)!={'artifacts'} or not isinstance(data['artifacts'],list) or len(data['artifacts'])>3:
        raise ValueError('Expected artifacts array with zero to three obligations')
    paths={s['path'].casefold() for m in roadmap['schedule'] for s in m['steps']}
    root=Path(roadmap['project']).resolve(strict=True)
    result=[]
    for task in data['artifacts']:
        if not isinstance(task,dict) or not {'after','goal','output'}<=set(task) or set(task)-{'after','goal','output','acceptance','imports','prepare_after'}:
            raise ValueError('Expected boundary, goal and output')
        after=task['after']
        if type(after) is not int or not 0<=after<=len(roadmap['schedule']):
            raise ValueError('Invalid artifact boundary')
        if not isinstance(task['goal'],str) or not 5<=len(task['goal'].strip())<=300:
            raise ValueError('Artifact goal must be specific and bounded')
        output=safe_target(root,task['output']).relative_to(root).as_posix()
        if output.casefold() in paths:raise ValueError('Artifact collides with text-source plan; reconcile the file plan')
        if safe_target(root,output).exists():raise ValueError('Artifact already exists; do not silently replace it')
        from .artifact_types import artifact_type
        entry={'after':after,'goal':task['goal'].strip(),'output':output,'section':section,'artifact_type':artifact_type(output)}
        if 'acceptance' in task:
            from .artifact_acceptance import validate
            entry['acceptance']=validate(output,task['acceptance'])
        if 'imports' in task:
            from .asset_import_probe import validate_imports
            entry['imports']=validate_imports(output,task['imports'])
        if 'prepare_after' in task:
            from .project_midi import supports
            if (type(task['prepare_after']) is not int or after<1 or task['prepare_after']!=after-1
                    or not supports(entry)):
                raise ValueError('Early preparation is only for independent native MIDI one milestone before publication')
            entry['prepare_after']=task['prepare_after']
        result.append(entry)
    return result


class MixedRoadmaps:
    def __init__(self,path):
        self.path=Path(path)
        with sqlite3.connect(self.path) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS mixed_sections(
              request_id INTEGER NOT NULL, code_sha TEXT NOT NULL, ordinal INTEGER NOT NULL,
              section_sha TEXT NOT NULL, tasks TEXT NOT NULL,
              PRIMARY KEY(request_id,code_sha,ordinal));
            CREATE TABLE IF NOT EXISTS mixed_plans(
              request_id INTEGER PRIMARY KEY, code_sha TEXT NOT NULL, body TEXT NOT NULL, sha TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS mixed_requests(
              task_id TEXT PRIMARY KEY, request_id INTEGER UNIQUE NOT NULL);
            """)
    def section(self,request_id,code_sha,ordinal,section_sha):
        with sqlite3.connect(self.path) as db:
            row=db.execute('SELECT section_sha,tasks FROM mixed_sections WHERE request_id=? AND code_sha=? AND ordinal=?',
                           (request_id,code_sha,ordinal)).fetchone()
        if not row:return None
        if row[0]!=section_sha:raise ValueError('Indexed section changed')
        return json.loads(row[1])
    def save_section(self,request_id,code_sha,ordinal,section_sha,tasks):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT OR IGNORE INTO mixed_sections VALUES(?,?,?,?,?)',
                       (request_id,code_sha,ordinal,section_sha,json.dumps(tasks,ensure_ascii=False)))
    def save(self,body):
        identity=digest(body)
        with sqlite3.connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT sha FROM mixed_plans WHERE request_id=?',(body['request_id'],)).fetchone()
            if row and row[0]!=identity:raise ValueError('Mixed roadmap changed; create a new specification revision')
            db.execute('INSERT OR IGNORE INTO mixed_plans VALUES(?,?,?,?)',
                       (body['request_id'],body['code_sha'],json.dumps(body,ensure_ascii=False),identity))
        return identity
    def get(self,request_id,code_sha):
        with sqlite3.connect(self.path) as db:
            row=db.execute('SELECT code_sha,body,sha FROM mixed_plans WHERE request_id=?',(request_id,)).fetchone()
        if not row:return None
        body=json.loads(row[1])
        if row[0]!=code_sha or digest(body)!=row[2]:raise ValueError('Mixed roadmap is stale')
        return {**body,'sha':row[2]}
    def request_for(self,task_id):
        with sqlite3.connect(self.path) as db:
            row=db.execute('SELECT request_id FROM mixed_requests WHERE task_id=?',(task_id,)).fetchone()
            return row[0] if row else None
    def bind_request(self,task_id,request_id):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT INTO mixed_requests VALUES(?,?)',(task_id,request_id))


def assess(store,hierarchies,index,request,council,client,review,*,cancelled=None,stage=None):
    roadmap=code_manifest(hierarchies,index,request)
    ident=request['id'];code_sha=roadmap['manifest_sha256']
    existing=store.get(ident,code_sha)
    if existing:return existing
    _,rows,_,_=hierarchies._checked(index,ident,request['prompt'])
    tasks={}
    for ordinal,start,end,section_sha,_,plan_json in rows:
        if cancelled and cancelled():raise ValueError('Mixed roadmap assessment cancelled')
        prior=store.section(ident,code_sha,ordinal,section_sha)
        if prior is None:
            exact=request['prompt'][start:end]
            scoped=json.loads(plan_json)
            schedule=[{'ordinal':m['ordinal'],'paths':[s['path'] for s in m['steps'] if s['path'] in {x['path'] for x in scoped}]}
                      for m in roadmap['schedule']]
            schedule=[m for m in schedule if m['paths']]
            prompt=('JANUS: assess this exact specification section for required external-tool artifact work NOT '
                    'already represented by the code-file plan. Examples include mesh conversion, raster textures, '
                    'rendering, packaging. Do not invent requirements or treat ordinary code as an external artifact. '
                    'Return ONLY JSON {"artifacts":[{"after":0,"goal":"specific required operation","output":"relative/file"}]}. '
                    'Optional acceptance object ONLY for explicitly requested measurable properties: PNG/DDS width,height; '
                    'PNG min_visible_pixels,min_distinct_visible_colors (8-bit noninterlaced, max 1048576 pixels, distinct count capped at 256); '
                    'OBJ min_vertices,min_faces and min_extent_x,max_extent_x (also y,z; raw Cartesian units, no scene transforms); '
                    'WAV channels,sample_rate,min_frames; short monophonic MIDI bpm,notes (4–48 notes); ZIP/APK/AAB/JAR required_members (array of exact filenames). '
                    'Do not invent numeric targets. Omit acceptance when no supported criterion is explicit. '
                    'Optional imports array: Blender for OBJ/GLB/PNG; Godot for GLB/PNG. Include only when '
                    'the artifact is intended for that application in the user specification. This requires a real '
                    'headless import smoke check before later milestones, not a rendering or gameplay test. '
                    'Use an empty array if no separate artifact is required. after=N means after verified milestone N '
                    'and before N+1; 0 means before code. Maximum three artifacts. '
                    'Only for a native MIDI whose entire brief is independent of milestone N code outputs, '
                    'you may include prepare_after:N-1 for private preparation during N; publication still waits for N verified. '
                    'Omit if any dependency is uncertain. '
                    f'Total milestones: {len(roadmap["schedule"])}. '
                    f'Related code milestones and paths: {json.dumps(schedule,ensure_ascii=False)}\n'
                    f'EXACT USER SECTION {ordinal+1}:\n{exact}')
            if len(prompt)>7000:raise ValueError('Artifact assessment context exceeds model bound')
            feedback=''
            for attempt in range(2):
                if cancelled and cancelled():raise ValueError('Mixed roadmap assessment cancelled')
                query=prompt+('\nCorrect rejected assessment: '+feedback[:300] if feedback else '')
                try:
                    answer=council._run(client,role=f'JANUS_ARTIFACTS_{attempt}',session=f'mixed-{ident}',
                        evidence_sha=digest([code_sha,section_sha,query]),prompt=query,stage=stage)
                    proposed=parse_tasks(answer,roadmap,ordinal+1)
                    review(exact,proposed,ordinal+1)
                    if cancelled and cancelled():raise ValueError('Mixed roadmap assessment cancelled')
                    store.save_section(ident,code_sha,ordinal,section_sha,proposed)
                    prior=proposed
                    break
                except ValueError as exc:feedback=str(exc)
            if prior is None:raise ValueError('Artifact assessment needs correction: '+feedback[:350])
        for task in prior:
            key=task['output'].casefold()
            if key in tasks:
                old=tasks[key]
                if any(old.get(k)!=task.get(k) for k in ('after','goal','output','acceptance','imports','prepare_after')):
                    raise ValueError('Conflicting artifact requirements; reconcile the roadmap')
                old['sections'].append(task['section'])
            else:tasks[key]={k:v for k,v in task.items() if k!='section'}|{'sections':[task['section']]}
            if len(tasks)>MAX_TASKS:raise ValueError('Artifact obligation count exceeds bound')
    ordered=sorted(tasks.values(),key=lambda x:(x['after'],x['output']))
    for task in ordered:task['id']=digest([ident,code_sha,task])
    body={'request_id':ident,'code_sha':code_sha,'tasks':ordered}
    store.save(body)
    return store.get(ident,code_sha)


def pending_task(plan,workflows,before,*,creative=None):
    """All earlier required outputs must have current checked workflow receipts."""
    from .roadmap_tool_bridge import check_complete
    runs=workflows.roadmap_members(plan['request_id'])
    for task in plan['tasks']:
        if task['after']>=before:continue
        if creative is not None:
            status=creative.checked(plan,task)
            if status is True:continue
            if status is False:return task
        matches=[]
        for run in runs:
            manifest=json.loads(run['manifest'])
            if manifest.get('mixed_task')!=task:continue
            if run['state']=='complete':
                check_complete(workflows,run)
                outputs={s['output'] for s in manifest['stages']}
                if task['output'] in outputs:
                    from .artifact_types import require_checked_receipt
                    rows=workflows.stages(run['id'])
                    for step,row in zip(manifest['stages'],rows):
                        if step['output']==task['output']:
                            require_checked_receipt(task,json.loads(row['receipt'])['artifact'])
                            break
                    else:raise ValueError('Required artifact receipt missing')
                    from .asset_import_probe import required_imports
                    if required_imports(workflows,run):return task
                    break
            matches.append(run)
        else:return task
    return None


def require_output(task,manifest):
    info=task.get('artifact_type')
    if info and info['verification']!='structural':
        raise ValueError('Required artifact lacks a supported format verifier; learn or add one before approval')
    if 'acceptance' in task:
        from .artifact_acceptance import validate
        validate(task['output'],task['acceptance'])
    if 'imports' in task:
        from .asset_import_probe import validate_imports
        validate_imports(task['output'],task['imports'])
    if task['output'] not in {s['output'] for s in manifest['stages']}:
        raise ValueError('Workflow does not produce the exact required roadmap artifact')
    return True
