"""Durable per-project local work queue.

The queue is a state machine, not a claim of autonomous task completion.
Only a verified GUI action can approve file writes. Lost running jobs become
PAUSED after restart, never falsely COMPLETE.
"""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
import uuid
import json
from pathlib import Path
from .flight_recorder import record
from .specification_library import MAX_STORED_REQUEST_CHARS

STATES = {'queued', 'running', 'responded', 'waiting_approval', 'needs_input', 'complete', 'failed', 'cancelled', 'paused', 'waiting_verification', 'waiting_repair'}
TERMINAL = {'complete', 'failed', 'cancelled', 'responded'}

class JobStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project TEXT NOT NULL, chat_id TEXT NOT NULL,
                    mode TEXT NOT NULL CHECK(mode IN ('chat','edit','plan','build','vision','image')),
                    target TEXT, prompt TEXT NOT NULL, attachments_json TEXT NOT NULL DEFAULT '[]',
                    state TEXT NOT NULL DEFAULT 'queued',
                    detail TEXT NOT NULL DEFAULT 'Waiting for model',
                    result TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS jobs_project ON jobs(project,id);
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL,
                    stamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    note TEXT NOT NULL);
            ''')
            ddl = db.execute("SELECT sql FROM sqlite_master WHERE name='jobs'").fetchone()[0]
            if "'build'" not in ddl:
                # Migrating older v6 queue: preserve actual tasks and IDs.
                db.execute('ALTER TABLE jobs RENAME TO old_jobs')
                db.executescript('''CREATE TABLE jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project TEXT NOT NULL,
                    chat_id TEXT NOT NULL, mode TEXT NOT NULL
                    CHECK(mode IN ('chat','edit','plan','build','vision','image')),
                    target TEXT, prompt TEXT NOT NULL,
                    attachments_json TEXT NOT NULL DEFAULT '[]',
                    state TEXT NOT NULL DEFAULT 'queued',
                    detail TEXT NOT NULL DEFAULT 'Waiting for model',
                    result TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                    CREATE INDEX IF NOT EXISTS jobs_project_v7 ON jobs(project,id);''')
                old_cols=[r[1] for r in db.execute('PRAGMA table_info(old_jobs)')]
                keep=[x for x in ('id','project','chat_id','mode','target','prompt','state','detail','result','created_at','updated_at') if x in old_cols]
                db.execute(f"INSERT INTO jobs ({','.join(keep)}) SELECT {','.join(keep)} FROM old_jobs")
                db.execute('DROP TABLE old_jobs')
                db.execute('DROP INDEX IF EXISTS jobs_project_v7')
                db.execute('CREATE INDEX IF NOT EXISTS jobs_project ON jobs(project,id)')
            cols={r[1] for r in db.execute('PRAGMA table_info(jobs)')}
            if 'attachments_json' not in cols:
                db.execute("ALTER TABLE jobs ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]'")
            db.execute('''CREATE TABLE IF NOT EXISTS job_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL,
                sequence INTEGER NOT NULL, path TEXT NOT NULL,
                description TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'planned',
                outcome TEXT NOT NULL DEFAULT '', UNIQUE(job_id,sequence))''')
            if 'approval_key' not in {r[1] for r in db.execute('PRAGMA table_info(jobs)')}:
                db.execute('ALTER TABLE jobs ADD COLUMN approval_key TEXT')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS jobs_approval_key ON jobs(approval_key)')
            # Processes killed or the application closed mid-generation are not complete.
            from .task_memory import ensure_schema
            ensure_schema(db)
            from .corrective_coordination import ensure_schema as ensure_coordination
            ensure_coordination(db)
            interrupted=[row[0] for row in db.execute("SELECT id FROM jobs WHERE state='running'")]
            db.execute("UPDATE jobs SET state='paused', detail='Interrupted by previous shutdown; resume or cancel' WHERE state='running'")
            for ident in interrupted:
                db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',(ident,'Interrupted by previous shutdown; no completion inferred'))
        for ident in interrupted:self._journal(ident)

    def _journal(self,ident):
        # The queue transaction is authoritative. A failed projection never
        # falsifies or rolls back its committed state.
        try:
            from .task_memory import render
            return render(self.path,ident)
        except (OSError,sqlite3.Error,ValueError) as error:
            record(self.path.parent,'queue','task_journal_unavailable',level='WARNING',
                   job_id=ident,error_type=type(error).__name__)
            return None

    def journal(self,ident):
        return self._journal(ident)

    def remember(self,ident,role,focus,spec_sha,evidence_sha,note):
        from .task_memory import append_note
        try:
            with self._conn() as db:
                changed=append_note(db,ident,role,focus,spec_sha,evidence_sha,note)
            if changed:self._journal(ident)
            return changed
        except (OSError,sqlite3.Error,ValueError) as error:
            record(self.path.parent,'queue','task_memory_unavailable',level='WARNING',
                   job_id=ident,error_type=type(error).__name__)
            return False

    def memory_context(self,job,original,focus,budget=800):
        from .task_memory import context
        try:
            return context(self.path,job['id'],job['project'],job['chat_id'],original,focus,budget=budget)
        except (OSError,sqlite3.Error,ValueError):
            return ''
    @contextmanager
    def _conn(self):
        db=sqlite3.connect(self.path,timeout=20)
        try:
            db.execute('PRAGMA busy_timeout=20000')
            with db:
                yield db
        finally:db.close()
    def submit(self, project: str, chat_id: str, mode: str, prompt: str,
               target: str | None = None, attachments: list[str] | tuple[str,...] = ()) -> int:
        if mode not in ('chat','edit','plan','build','vision','image') or not prompt.strip() or not chat_id:
            raise ValueError('Invalid job data')
        if len(prompt)>MAX_STORED_REQUEST_CHARS: raise ValueError(f'Prompt exceeds local storage safety ceiling ({MAX_STORED_REQUEST_CHARS:,} characters)')
        if len(attachments)>8: raise ValueError('At most eight attachments per job')
        from .media_tools import validate_attachment
        attachments=[str(validate_attachment(p)) for p in attachments]
        with self._conn() as db:
            i = db.execute('INSERT INTO jobs(project,chat_id,mode,target,prompt,attachments_json) VALUES(?,?,?,?,?,?)',
                           (project,chat_id,mode,target,prompt,json.dumps(attachments))).lastrowid
            db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',(i,'Queued by user'))
            record(self.path.parent,'queue','job_submitted',job_id=i,mode=mode,
                   project_name=Path(project).name,prompt_characters=len(prompt),attachments=len(attachments))
        self._journal(i)
        return i
    def submit_approved_build(self, project: str, chat_id: str, prompt: str,
                              steps: list[dict], approval_key: str) -> int:
        """Original single-draft approval boundary, unchanged in meaning."""
        if not approval_key.startswith('draft:') or not approval_key[6:].isdigit():
            raise ValueError('Approved build requires a durable draft identifier')
        if not isinstance(steps,list) or not 1<=len(steps)<=24:
            raise ValueError('Approved plan requires 1..24 file stages')
        from .agent_plan import validate_project_plan
        validate_project_plan(steps,prompt)
        return self._record_approved_build(project,chat_id,prompt,steps,approval_key)

    def submit_approved_milestone_build(self, project: str, chat_id: str,
                                        scoped_prompt: str, steps: list[dict],
                                        approval_key: str, *, master_prompt: str,
                                        master_steps: list[dict]) -> int:
        """One explicitly approved milestone, checked against full master plan.

        This never silently downgrades full-project validation to a subset.
        The hierarchy caller must also validate exact section hashes and
        dependency/verification status before this operation.
        """
        import re
        from .agent_plan import validate_project_plan
        if not re.fullmatch(r'milestone:[1-9][0-9]*:[1-9][0-9]*:[0-9a-f]{16}',approval_key or ''):
            raise ValueError('Hierarchical job needs a durable milestone approval identifier')
        if not isinstance(steps,list) or not 1<=len(steps)<=24 or len(scoped_prompt)>6500:
            raise ValueError('Milestone needs 1..24 bounded file stages and a scoped prompt')
        validate_project_plan(master_steps,master_prompt)
        indexed={str(s['path']).casefold():s for s in master_steps}
        if (len(indexed)!=len(master_steps) or
            any(indexed.get(str(s.get('path','')).casefold())!=s for s in steps)):
            raise ValueError('Milestone step does not belong to the validated master plan')
        if not scoped_prompt.startswith('HIERARCHICAL MILESTONE '):
            raise ValueError('Missing traceable milestone scope')
        return self._record_approved_build(project,chat_id,scoped_prompt,steps,approval_key)

    def _record_approved_build(self, project: str, chat_id: str, prompt: str,
                               steps: list[dict], approval_key: str) -> int:
        if not project or project == '(general)' or not chat_id or not prompt.strip():
            raise ValueError('An approved build requires a project and prompt')
        if not isinstance(steps,list) or not 1<=len(steps)<=24:
            raise ValueError('Approved plan requires 1..24 file stages')
        from .workspace import safe_target
        validated=[]
        seen=set()
        for step in steps:
            target=safe_target(Path(project),step['path'])
            rel=target.relative_to(Path(project).resolve()).as_posix()
            if not isinstance(step['description'],str) or not 3<=len(step['description'])<=1000:
                raise ValueError('Invalid file stage')
            if rel.casefold() in seen:
                raise ValueError('Repeated file in approved plan')
            seen.add(rel.casefold())
            validated.append((rel,step['description']))
        with self._conn() as db:
            previous=db.execute('SELECT id FROM jobs WHERE approval_key=?',(approval_key,)).fetchone()
            if previous:
                existing=db.execute('SELECT project,chat_id,prompt FROM jobs WHERE id=?',(previous[0],)).fetchone()
                saved=db.execute('SELECT path,description FROM job_steps WHERE job_id=? ORDER BY sequence',(previous[0],)).fetchall()
                if existing!=(project,chat_id,prompt) or list(saved)!=validated:
                    raise ValueError('Existing approval key is bound to a different milestone')
                return int(previous[0])
            ident=db.execute(
                "INSERT INTO jobs(project,chat_id,mode,prompt,approval_key,detail) "
                "VALUES(?,?,'build',?,?,'User-approved plan; ready to execute')",
                (project,chat_id,prompt,approval_key)).lastrowid
            for n,(path,description) in enumerate(validated):
                db.execute('INSERT INTO job_steps(job_id,sequence,path,description) VALUES(?,?,?,?)',
                           (ident,n,path,description))
            db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',
                       (ident,f'Explicit approval of {approval_key}; {len(steps)} validated file stages'))
        record(self.path.parent,'queue','approved_plan_submitted',job_id=ident,
               approval_key=approval_key,stages=len(validated))
        self._journal(ident)
        return ident

    def by_approval_key(self,key):
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT * FROM jobs WHERE approval_key=?',(key,)).fetchone()
            return dict(row) if row else None

    def get(self, ident: int):
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT * FROM jobs WHERE id=?',(ident,)).fetchone()
            return dict(row) if row else None
    def items(self, project: str, limit: int = 200):
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM jobs WHERE project=? ORDER BY id DESC LIMIT ?', (project,limit))]
    def next_queued(self, project: str, skip_modes: tuple[str,...]=()):
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            sql="SELECT * FROM jobs WHERE project=? AND state='queued'"
            params=[project]
            if skip_modes:
                sql+=' AND mode NOT IN ('+','.join('?' for _ in skip_modes)+')'
                params.extend(skip_modes)
            row=db.execute(sql+' ORDER BY id LIMIT 1',params).fetchone()
            return dict(row) if row else None
    def interrupted_builds(self,limit=40):
        from .interrupted_build import INTERRUPTED
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute(
                "SELECT * FROM jobs WHERE mode='build' AND state='paused' AND detail=? ORDER BY id LIMIT ?",
                (INTERRUPTED,limit))]

    def requeue_interrupted_build(self,ident):
        from .interrupted_build import INTERRUPTED
        detail='Restart recovery: approved source, grant and task graph agree; resume inference'
        with self._conn() as db:
            changed=db.execute("UPDATE jobs SET state='queued',detail=?,updated_at=CURRENT_TIMESTAMP "
                "WHERE id=? AND mode='build' AND state='paused' AND detail=?",
                (detail,ident,INTERRUPTED)).rowcount
            if changed:
                db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',(ident,detail))
        if changed:self._journal(ident)
        return bool(changed)

    def freeze_unapproved_legacy_builds(self):
        """Prevent pre-approval v10.3 builds from auto-executing after upgrade."""
        with self._conn() as db:
            entries=db.execute("SELECT id FROM jobs WHERE mode='build' AND state='queued' "
                               "AND approval_key IS NULL AND NOT EXISTS "
                               "(SELECT 1 FROM job_steps WHERE job_steps.job_id=jobs.id)").fetchall()
        for (ident,) in entries:
            self.change(ident,'needs_input',
                'Legacy unapproved build: discuss a plan in Chats and explicitly approve it',allowed=('queued',))
        return len(entries)

    def pending_verifications(self, limit: int = 40) -> list[dict]:
        """Find approved builds awaiting real tests across all project workspaces.

        This is a durable query; the GUI separately checks an explicit active
        project-scoped grant, exact source fingerprints and process/game gates.
        """
        if not 1 <= limit <= 100:
            raise ValueError('Verification query limit must be 1..100')
        with self._conn() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(
                "SELECT * FROM jobs WHERE mode='build' AND state='waiting_verification' "
                "ORDER BY id LIMIT ?", (limit,))]

    def pending_conversation_jobs(self):
        """Legacy pre-approval messages for lossless, idempotent v10.4 migration."""
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute(
                "SELECT * FROM jobs WHERE mode IN ('chat','plan','edit') "
                "AND state IN ('queued','paused','needs_input','failed') ORDER BY id")]

    def next_any_queued(self, skip_modes: tuple[str,...]=(), *, exclude_project=None):
        """Oldest eligible job; a busy workspace must not block unrelated work.

        Inspect only ID and workspace while skipping, not large stored prompts.
        The caller still owns all actual dispatch authority and grant checks.
        """
        from .task_graph import independent_workspaces
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            sql="SELECT id,project FROM jobs WHERE state='queued'"
            params=[]
            if skip_modes:
                sql+=' AND mode NOT IN ('+','.join('?' for _ in skip_modes)+')'
                params.extend(skip_modes)
            for row in db.execute(sql+' ORDER BY id',params):
                if exclude_project is not None and not independent_workspaces(row['project'],exclude_project):
                    continue
                current=db.execute("SELECT * FROM jobs WHERE id=? AND state='queued'",(row['id'],)).fetchone()
                if current:return dict(current)
            return None

    def change(self, ident: int, state: str, detail: str, result: str | None = None, allowed: tuple[str,...] | None = None) -> bool:
        if state not in STATES: raise ValueError('Unknown status')
        with self._conn() as db:
            row=db.execute('SELECT state FROM jobs WHERE id=?',(ident,)).fetchone()
            if row is None or (allowed is not None and row[0] not in allowed): return False
            if result is None:
                db.execute('UPDATE jobs SET state=?,detail=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(state,detail,ident))
            else:
                db.execute('UPDATE jobs SET state=?,detail=?,result=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',(state,detail,result,ident))
            db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',(ident,detail[:4000]))
            record(self.path.parent,'queue','job_transition',job_id=ident,from_state=row[0],to_state=state,
                   detail=detail[:500],result_characters=len(result) if result else 0)
        self._journal(ident)
        return True
    def cancel(self, ident: int) -> bool:
        return self.change(ident,'cancelled','Cancelled by user',allowed=('queued','running','paused','needs_input','waiting_approval','waiting_verification','waiting_repair'))
    def resume(self, ident: int) -> bool:
        return self.change(ident,'queued','Requeued by user',allowed=('paused','failed','needs_input','waiting_verification'))
    def events(self, ident: int, limit: int = 40):
        with self._conn() as db:
            return list(reversed(db.execute('SELECT stamp,note FROM job_events WHERE job_id=? ORDER BY id DESC LIMIT ?',(ident,limit)).fetchall()))
    def add_plan(self, ident: int, steps: list[dict]):
        if not steps or len(steps)>24: raise ValueError('Plan must contain 1..24 concrete file steps')
        with self._conn() as db:
            if db.execute('SELECT 1 FROM job_steps WHERE job_id=?',(ident,)).fetchone():
                raise ValueError('A plan already exists for this job')
            for n,step in enumerate(steps):
                db.execute('INSERT INTO job_steps(job_id,sequence,path,description) VALUES(?,?,?,?)',
                           (ident,n,step['path'],step['description']))
            db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',
                       (ident,f'Validated plan with {len(steps)} bounded file steps'))
        self._journal(ident)
    def steps(self, ident: int):
        with self._conn() as db:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute('SELECT * FROM job_steps WHERE job_id=? ORDER BY sequence',(ident,))]
    def next_step(self, ident: int):
        return next((s for s in self.steps(ident) if s['state']=='planned'),None)
    def set_step(self, step_id: int, state: str, outcome: str=''):
        if state not in ('planned','proposed','saved','verified','failed','skipped'):
            raise ValueError('Invalid step state')
        with self._conn() as db:
            row=db.execute('SELECT job_id,path FROM job_steps WHERE id=?',(step_id,)).fetchone()
            db.execute('UPDATE job_steps SET state=?,outcome=? WHERE id=?',(state,outcome,step_id))
            if row:
                db.execute('INSERT INTO job_events(job_id,note) VALUES(?,?)',
                    (row[0],f'File {row[1]}: {state}; {outcome[:500]}'))
        if row:self._journal(row[0])

    def count(self, project: str):
        with self._conn() as db:
            return dict(db.execute('SELECT state,COUNT(*) FROM jobs WHERE project=? GROUP BY state',(project,)).fetchall())

class ChatRegistry:
    def __init__(self, path: str | Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._conn() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS chat_threads (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            if 'closed' not in {col[1] for col in db.execute('PRAGMA table_info(chat_threads)')}:
                db.execute('ALTER TABLE chat_threads ADD COLUMN closed INTEGER NOT NULL DEFAULT 0')
    @contextmanager
    def _conn(self):
        db=sqlite3.connect(self.path,timeout=20)
        try:
            with db:yield db
        finally:db.close()
    def create(self, project: str, title: str='New chat') -> str:
        ident='chat-'+uuid.uuid4().hex
        with self._conn() as db:
            db.execute('INSERT INTO chat_threads(id,project,title) VALUES(?,?,?)',(ident,project,title[:70]))
        return ident
    def list(self, project: str):
        with self._conn() as db:
            return db.execute('SELECT id,title FROM chat_threads WHERE project=? AND closed=0 ORDER BY rowid',(project,)).fetchall()
    def closed(self, project: str):
        with self._conn() as db:
            return db.execute('SELECT id,title FROM chat_threads WHERE project=? AND closed=1 ORDER BY rowid',(project,)).fetchall()
    def close(self, ident: str, project: str) -> bool:
        """Hide the tab, not its durable messages, drafts or approved work."""
        with self._conn() as db:
            return bool(db.execute('UPDATE chat_threads SET closed=1 WHERE id=? AND project=? AND closed=0',
                                   (ident,project)).rowcount)
    def reopen(self, ident: str, project: str) -> bool:
        with self._conn() as db:
            return bool(db.execute('UPDATE chat_threads SET closed=0 WHERE id=? AND project=? AND closed=1',
                                   (ident,project)).rowcount)
    def rename(self, ident: str, title: str):
        if not title.strip(): raise ValueError('Title required')
        with self._conn() as db:
            db.execute('UPDATE chat_threads SET title=? WHERE id=?',(title[:70],ident))
    def delete(self, ident: str, project: str):
        with self._conn() as db:
            db.execute('DELETE FROM chat_threads WHERE id=? AND project=?',(ident,project))
