"""Persistent explicit authorization of an exact, ordered roadmap.

A successor needs fresh predecessor verification and its own job grant.
No new paths, revised specifications or arbitrary commands are authorized.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .agent_plan import PlanError
from .reasoning_council import sha
from .project_authority import _safe_auto_path
from .semantic_reconciliation import verified_sources_current


def manifest(hierarchies,index,request):
    root,rows,milestones,steps=hierarchies._checked(index,request['id'],request['prompt'])
    project=Path(root['project']).resolve(strict=True)
    if root['chat_id']!=request['chat_id'] or str(project)!=str(Path(request['project']).resolve()):
        raise PlanError('Roadmap owner changed')
    if len(steps)>10000:raise PlanError('Roadmap exceeds approval bound')
    schedule=[]
    for m in milestones:
        files=json.loads(m['steps_json'])
        for s in files:_safe_auto_path(project,s['path'])
        schedule.append({'ordinal':m['ordinal'],'title':m['title'],'scope_sha256':m['scope_sha256'],
                         'source_sections':json.loads(m['section_ordinals_json']),'steps':files})
    body={'request_id':request['id'],'project':str(project),'chat_id':root['chat_id'],
          'spec_sha256':sha(request['prompt']),'schedule':schedule}
    return {**body,'manifest_sha256':sha(json.dumps(body,sort_keys=True,ensure_ascii=False))}


class RoadmapRuns:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS roadmap_runs(
                  request_id INTEGER PRIMARY KEY, project TEXT NOT NULL, chat_id TEXT NOT NULL,
                  manifest_sha256 TEXT NOT NULL, state TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS roadmap_dispatch(
                  approval_key TEXT PRIMARY KEY, request_id INTEGER NOT NULL,
                  ordinal INTEGER NOT NULL, job_id INTEGER,
                  state TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            ''')
            if 'mixed_sha' not in {r[1] for r in db.execute('PRAGMA table_info(roadmap_runs)')}:
                db.execute('ALTER TABLE roadmap_runs ADD COLUMN mixed_sha TEXT')
            if 'creative_midi' not in {r[1] for r in db.execute('PRAGMA table_info(roadmap_runs)')}:
                db.execute('ALTER TABLE roadmap_runs ADD COLUMN creative_midi INTEGER NOT NULL DEFAULT 0')

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=15)
        db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()

    def get(self,ident):
        with self.db() as db:
            row=db.execute('SELECT * FROM roadmap_runs WHERE request_id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def active(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM roadmap_runs WHERE state='active' ORDER BY request_id LIMIT 40")]

    def approve(self,reviewed):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT * FROM roadmap_runs WHERE request_id=?',(reviewed['request_id'],)).fetchone()
            if old and old['manifest_sha256']!=reviewed['manifest_sha256']:
                raise PlanError('Roadmap changed; create a new revision rather than replace consent')
            if old and old['state']=='complete':raise PlanError('Roadmap already completed')
            if old and old['mixed_sha']!=reviewed.get('mixed_sha'):raise PlanError('Artifact obligations changed; create a new revision')
            db.execute('''INSERT INTO roadmap_runs(request_id,project,chat_id,manifest_sha256,state,detail)
                VALUES(?,?,?,?,'active','User approved complete ordered roadmap')
                ON CONFLICT(request_id) DO UPDATE SET state='active',detail='User renewed roadmap consent',
                updated_at=CURRENT_TIMESTAMP''',
                (reviewed['request_id'],reviewed['project'],reviewed['chat_id'],reviewed['manifest_sha256']))
            db.execute('UPDATE roadmap_runs SET mixed_sha=?,creative_midi=? WHERE request_id=?',
                       (reviewed.get('mixed_sha'),int(reviewed.get('creative_midi') is True),reviewed['request_id']))

    def change(self,ident,state,detail):
        if state not in ('paused','blocked','complete','superseded'):raise ValueError('Invalid roadmap state')
        with self.db() as db:
            return bool(db.execute("UPDATE roadmap_runs SET state=?,detail=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE request_id=? AND state='active'",(state,detail[:600],ident)).rowcount)

    def reserve(self,ident,ordinal,key,manifest_sha):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            run=db.execute('SELECT * FROM roadmap_runs WHERE request_id=?',(ident,)).fetchone()
            if not run or run['state']!='active' or run['manifest_sha256']!=manifest_sha:return False
            return bool(db.execute("INSERT OR IGNORE INTO roadmap_dispatch(approval_key,request_id,ordinal,state) "
                "VALUES(?,?,?,'reserved')",(key,ident,ordinal)).rowcount)

    def finish(self,key,job_id,ready):
        with self.db() as db:
            return bool(db.execute("UPDATE roadmap_dispatch SET state=?,job_id=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE approval_key=? AND state='reserved'",
                ('ready' if ready else 'blocked',job_id,key)).rowcount)

    def dispatch_allowed(self,job):
        with self.db() as db:
            row=db.execute('SELECT state,job_id FROM roadmap_dispatch WHERE approval_key=?',
                           (job.get('approval_key'),)).fetchone()
            return row is None or (row['state']=='ready' and row['job_id']==job['id'])


def eligible_successor(run,request,conversations,hierarchies,index,jobs):
    if not request or request['mode']!='draft_plan' or request['state']!='responded':
        raise PlanError('Roadmap source request is not reviewable')
    latest=conversations.latest_project_request(request['chat_id'],request['project'])
    if not latest or latest['id']!=request['id'] or conversations.amendment_supersedes(
            request['id'],request['chat_id'],request['project']):
        raise PlanError('Roadmap superseded by a new user specification')
    current=manifest(hierarchies,index,request)
    if any(current[k]!=run[k] for k in ('project','chat_id','manifest_sha256')):
        raise PlanError('Approved roadmap manifest changed')
    state=hierarchies.reconcile_jobs(index,request['id'],request['prompt'],jobs)
    ordinal=state['next_approvable']
    if ordinal is None and not state['complete']:return None
    verified_prefix(current,request,hierarchies,index,jobs,ordinal or len(current['schedule'])+1)
    if state['complete']:return {'complete':True,'manifest_sha256':current['manifest_sha256']}
    item=hierarchies.milestone(index,request['id'],request['prompt'],ordinal)
    if item['state']!='planned' or item['job_id'] is not None:
        raise PlanError('Successor already has a job or is no longer planned')
    return {'complete':False,'manifest_sha256':current['manifest_sha256'],'milestone':item}


def verified_prefix(current,request,hierarchies,index,jobs,before):
    """Shared existing predecessor evidence gate; no inference or dispatch."""
    for n in range(1,before):
        prior=hierarchies.milestone(index,request['id'],request['prompt'],n)
        job=jobs.get(prior['job_id']) if prior['job_id'] else None
        if (prior['state']!='verified' or not job or job['state']!='complete' or
                job['approval_key']!=prior['approval_key'] or job['prompt']!=prior['scope_prompt']):
            raise PlanError('Predecessor is not verified under exact approved scope')
        try:snapshot=json.loads(job.get('result') or '')
        except (ValueError,TypeError):raise PlanError('Predecessor lacks verified source snapshot')
        if not verified_sources_current(current['project'],prior['steps'],snapshot):
            raise PlanError('Predecessor verification is stale; regression verification required')
        evidence=snapshot.get('verification')
        if not isinstance(evidence,dict) or evidence.get('assurance') in (None,'process_exit_only'):
            raise PlanError('Predecessor has only process-exit evidence; stronger verification required')
