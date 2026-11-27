"""Durable conversations and pre-approval project plans; NOT execution jobs.

A conversation request is never an implicit authorization to change files, run
programs, download software or add to the execution queue.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .flight_recorder import record
from .specification_library import MAX_STORED_REQUEST_CHARS

VALID_MODES = {'chat', 'draft_plan'}
VALID_STATES = {'pending', 'running', 'waiting_sources', 'responded', 'failed', 'cancelled'}

class ConversationStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS conversation_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL, project TEXT NOT NULL,
                    mode TEXT NOT NULL CHECK(mode IN ('chat','draft_plan')),
                    prompt TEXT NOT NULL, attachments TEXT NOT NULL DEFAULT '[]',
                    state TEXT NOT NULL DEFAULT 'pending',
                    response TEXT NOT NULL DEFAULT '',
                    detail TEXT NOT NULL DEFAULT 'Waiting for local model',
                    source_job_id INTEGER UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS conversation_dispatch
                    ON conversation_requests(state,id);
                CREATE INDEX IF NOT EXISTS conversation_thread
                    ON conversation_requests(chat_id,id);
                CREATE TABLE IF NOT EXISTS independent_prompt_queue (
                    request_id INTEGER PRIMARY KEY REFERENCES conversation_requests(id),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS queued_prompt_attempts (
                    request_id INTEGER NOT NULL REFERENCES independent_prompt_queue(request_id),
                    role TEXT NOT NULL, identity TEXT NOT NULL,
                    PRIMARY KEY(request_id,role,identity));
                CREATE TABLE IF NOT EXISTS queued_prompt_advice (
                    request_id INTEGER NOT NULL REFERENCES independent_prompt_queue(request_id),
                    role TEXT NOT NULL, identity TEXT NOT NULL, body TEXT NOT NULL,
                    receipt_sha TEXT NOT NULL, stamp REAL NOT NULL,
                    PRIMARY KEY(request_id,role));
                CREATE TABLE IF NOT EXISTS project_drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL UNIQUE,
                    chat_id TEXT NOT NULL, project TEXT NOT NULL,
                    original_prompt TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'draft'
                         CHECK(state IN ('draft','approved','discarded')),
                    queued_job_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS project_draft_thread ON project_drafts(chat_id,id);
                CREATE TABLE IF NOT EXISTS specification_amendments (
                    request_id INTEGER PRIMARY KEY, parent_request_id INTEGER NOT NULL,
                    root_request_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                    original_sha256 TEXT NOT NULL, amendment TEXT NOT NULL,
                    amendment_sha256 TEXT NOT NULL, effective_sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(root_request_id,ordinal));
            ''')
            from .planning_journal import ensure_schema
            ensure_schema(db)
            interrupted=[r[0] for r in db.execute("SELECT id FROM conversation_requests WHERE state IN ('running','waiting_sources') AND mode='draft_plan'")]
            # An interrupted model call must be visible and explicitly retryable.
            db.execute("UPDATE conversation_requests SET state='pending', detail='Recovered after app restart; waiting for local AI' WHERE state='running'")
            # Never silently repeat a previously approved extractor invocation.
            db.execute("UPDATE conversation_requests SET state='failed', detail='X4 source extraction was interrupted; please retry explicitly' WHERE state='waiting_sources'")
        for ident in interrupted:self.journal(ident)

    def journal(self,ident):
        try:
            from .planning_journal import render
            return render(self.path,ident)
        except (OSError,sqlite3.Error,ValueError,TypeError) as error:
            record(self.path.parent,'conversation','planning_journal_unavailable',level='WARNING',request_id=ident,error_type=type(error).__name__)
            return None

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def submit(self, chat_id, project, mode, prompt, attachments=(), source_job_id=None, *, independent=False):
        if mode not in VALID_MODES or not isinstance(prompt,str) or not prompt.strip() or not chat_id:
            raise ValueError('Invalid conversation request')
        if len(prompt) > MAX_STORED_REQUEST_CHARS: raise ValueError(f'Specification exceeds local storage safety ceiling ({MAX_STORED_REQUEST_CHARS:,} characters)')
        if len(attachments)>8: raise ValueError('Too many attachments')
        if type(independent) is not bool or (independent and (mode!='draft_plan' or not project or project=='(general)' or source_job_id is not None)):
            raise ValueError('Independent task requires a new project plan conversation')
        with self._db() as db:
            if independent:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT 1 FROM conversation_requests WHERE chat_id=? LIMIT 1',(chat_id,)).fetchone():
                    raise ValueError('Independent task requires an unused chat')
                count=db.execute("SELECT COUNT(*) FROM independent_prompt_queue q JOIN conversation_requests c ON c.id=q.request_id WHERE c.state IN ('pending','running','waiting_sources')").fetchone()[0]
                if count>=32:raise ValueError('Independent task queue is full (32 unfinished prompts)')
            if source_job_id is not None:
                old=db.execute('SELECT id FROM conversation_requests WHERE source_job_id=?', (source_job_id,)).fetchone()
                if old: return old['id']
            if mode=='draft_plan':
                # A requested revision revokes approval of an outdated draft even
                # when the new proposal is still waiting for the local model.
                db.execute("UPDATE project_drafts SET state='discarded',updated_at=CURRENT_TIMESTAMP "
                           "WHERE chat_id=? AND project=? AND state='draft'", (chat_id,project))
            n=db.execute('''INSERT INTO conversation_requests(chat_id,project,mode,prompt,attachments,source_job_id)
                            VALUES(?,?,?,?,?,?)''',
                            (chat_id,project,mode,prompt,json.dumps(list(attachments)),source_job_id)).lastrowid
            if independent:db.execute('INSERT INTO independent_prompt_queue(request_id) VALUES(?)',(n,))
        record(self.path.parent,'conversation','conversation_saved',request_id=n,mode=mode,
               prompt_characters=len(prompt),attachments=len(attachments),legacy_job=source_job_id)
        if mode=='draft_plan':self.journal(n)
        return n

    def latest_project_request(self,chat_id,project):
        with self._db() as db:
            row=db.execute("SELECT * FROM conversation_requests WHERE chat_id=? AND project=? "
                "AND mode='draft_plan' ORDER BY id DESC LIMIT 1",(chat_id,project)).fetchone()
            return dict(row) if row else None

    def historical_draft(self,request_id):
        """Return prior plan regardless of approval/discard state; evidence only."""
        with self._db() as db:
            row=db.execute('SELECT * FROM project_drafts WHERE request_id=? ORDER BY id DESC LIMIT 1',
                           (request_id,)).fetchone()
            if not row:return None
            result=dict(row);result['steps']=json.loads(result['steps_json']);return result

    def amend_project(self,chat_id,project,amendment,*,attachments=()):
        """Explicit user operation: atomically save revision and queue a new draft."""
        from .specification_amendments import render_revision,revision_matches,sha
        if not chat_id or not project or project=='(general)' or not isinstance(amendment,str) or not amendment.strip():
            raise ValueError('A selected project, chat and explicit amendment are required')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            parent=db.execute("SELECT * FROM conversation_requests WHERE chat_id=? AND project=? "
                "AND mode='draft_plan' ORDER BY id DESC LIMIT 1",(chat_id,project)).fetchone()
            if parent is None:raise ValueError('No original project specification in this chat; draft one first')
            prior=db.execute('SELECT * FROM specification_amendments WHERE request_id=?',(parent['id'],)).fetchone()
            root_id=prior['root_request_id'] if prior else parent['id']
            root=db.execute('SELECT * FROM conversation_requests WHERE id=?',(root_id,)).fetchone()
            if not root or root['chat_id']!=chat_id or root['project']!=project:
                raise ValueError('Original specification binding is invalid')
            history=db.execute('SELECT * FROM specification_amendments WHERE root_request_id=? ORDER BY ordinal',
                               (root_id,)).fetchall()
            original=root['prompt']
            for n,row in enumerate(history,1):
                if (row['ordinal']!=n or row['original_sha256']!=sha(original)
                    or row['amendment_sha256']!=sha(row['amendment'])):
                    raise ValueError('Prior amendment history is inconsistent')
            if prior and (not history or history[-1]['request_id']!=parent['id']
                    or sha(parent['prompt'])!=prior['effective_sha256']
                    or not revision_matches(parent['prompt'],original,[r['amendment'] for r in history])):
                raise ValueError('Prior effective specification no longer matches its history')
            if not prior and history:raise ValueError('Amendment chain is inconsistent')
            effective=render_revision(original,[r['amendment'] for r in history]+[amendment])
            combined=list(dict.fromkeys(json.loads(parent['attachments'])+list(attachments)))
            if len(combined)>8:raise ValueError('Amended plan exceeds eight retained attachments; review the attachments first')
            ident=db.execute("INSERT INTO conversation_requests(chat_id,project,mode,prompt,attachments,detail) "
                "VALUES(?,?,'draft_plan',?,?,?)",
                (chat_id,project,effective,json.dumps(combined),'Explicit user amendment; revised plan required')).lastrowid
            db.execute("INSERT INTO specification_amendments(request_id,parent_request_id,root_request_id,ordinal,"
                "original_sha256,amendment,amendment_sha256,effective_sha256) VALUES(?,?,?,?,?,?,?,?)",
                (ident,parent['id'],root_id,len(history)+1,sha(original),amendment,sha(amendment),sha(effective)))
            # Preserve all source and plan rows, but prevent approval of outdated drafts.
            db.execute("UPDATE project_drafts SET state='discarded',updated_at=CURRENT_TIMESTAMP "
                "WHERE chat_id=? AND project=? AND state='draft'",(chat_id,project))
            db.execute("UPDATE conversation_requests SET state='cancelled',detail='Superseded by explicit user amendment',"
                "updated_at=CURRENT_TIMESTAMP WHERE chat_id=? AND project=? AND mode='draft_plan' "
                "AND id<? AND state='pending'",(chat_id,project,ident))
        record(self.path.parent,'conversation','specification_amended',request_id=ident,
               parent_request_id=parent['id'],root_request_id=root_id,ordinal=len(history)+1,
               amendment_sha256=sha(amendment),approval_granted=False)
        self.journal(parent['id'])
        self.journal(ident)
        return ident

    def amendment_supersedes(self,request_id,chat_id,project):
        with self._db() as db:
            return bool(db.execute("SELECT 1 FROM specification_amendments a "
                "JOIN conversation_requests c ON c.id=a.request_id "
                "WHERE c.chat_id=? AND c.project=? AND a.request_id>? LIMIT 1",
                (chat_id,project,request_id)).fetchone())

    def amendment_history(self,request_id):
        with self._db() as db:
            row=db.execute('SELECT root_request_id FROM specification_amendments WHERE request_id=?',(request_id,)).fetchone()
            if not row:return []
            return [dict(x) for x in db.execute('SELECT * FROM specification_amendments '
                'WHERE root_request_id=? AND request_id<=? ORDER BY ordinal',(row[0],request_id))]

    def cancel_chat_requests(self, chat_id: str, reason: str = 'Stopped by user') -> list[int]:
        """Atomically revoke all unfinished replies in a chat, never requeue them.

        This does not delete messages, prompts, drafts or any approved jobs.
        Asynchronous/late worker results must check state before saving.
        """
        if not isinstance(chat_id, str) or not chat_id or not isinstance(reason, str) or not reason.strip():
            raise ValueError('Chat identifier and cancellation reason required')
        with self._db() as db:
            ids = [int(row[0]) for row in db.execute(
                "SELECT id FROM conversation_requests WHERE chat_id=? "
                "AND state IN ('pending','running','waiting_sources') ORDER BY id", (chat_id,))]
            if ids:
                db.execute("UPDATE conversation_requests SET state='cancelled',detail=?,"
                           "updated_at=CURRENT_TIMESTAMP WHERE chat_id=? "
                           "AND state IN ('pending','running','waiting_sources')", (reason,chat_id))
        for ident in ids:
            record(self.path.parent,'conversation','conversation_cancelled',request_id=ident,
                   reason=reason[:200])
        return ids

    def get(self, ident):
        with self._db() as db:
            row=db.execute('SELECT * FROM conversation_requests WHERE id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def thread(self, chat_id, limit=100):
        with self._db() as db:
            rows=db.execute('''SELECT * FROM (SELECT * FROM conversation_requests WHERE chat_id=?
                              ORDER BY id DESC LIMIT ?) ORDER BY id''',(chat_id,limit)).fetchall()
            return [dict(r) for r in rows]

    def restore_legacy_creation_times(self, job_lookup):
        """Recover the ORIGINAL timestamps of pre-v10.4 messages.

        Previously, migration gave old queued messages the migration timestamp,
        placing genuinely old requests below newer diagnostics in the transcript.
        This is idempotent and leaves normal conversations unchanged.
        """
        with self._db() as db:
            migrated = db.execute('SELECT id,source_job_id,created_at FROM '
                                  'conversation_requests WHERE source_job_id IS NOT NULL').fetchall()
            count=0
            for row in migrated:
                job=job_lookup(int(row['source_job_id']))
                original=job.get('created_at') if job else None
                if original and str(original)<str(row['created_at']):
                    db.execute('UPDATE conversation_requests SET created_at=? WHERE id=?',
                               (original,row['id']))
                    count+=1
        if count:
            record(self.path.parent,'conversation','legacy_timestamp_restored',count=count)
        return count

    def next_pending(self):
        with self._db() as db:
            row=db.execute("SELECT * FROM conversation_requests WHERE state='pending' ORDER BY id LIMIT 1").fetchone()
            return dict(row) if row else None

    def change(self, ident, state, detail, response=None, *, allowed=None):
        if state not in VALID_STATES: raise ValueError('Invalid conversation state')
        with self._db() as db:
            old=db.execute('SELECT state FROM conversation_requests WHERE id=?',(ident,)).fetchone()
            if old is None or (allowed and old['state'] not in allowed): return False
            if response is None:
                db.execute('''UPDATE conversation_requests SET state=?,detail=?,updated_at=CURRENT_TIMESTAMP
                              WHERE id=?''',(state,detail,ident))
            else:
                db.execute('''UPDATE conversation_requests SET state=?,detail=?,response=?,updated_at=CURRENT_TIMESTAMP
                              WHERE id=?''',(state,detail,response,ident))
        record(self.path.parent,'conversation','conversation_transition',request_id=ident,from_state=old['state'],
               to_state=state,detail=detail[:250],response_characters=len(response) if response else 0)
        self.journal(ident)
        return True

    def save_draft(self, request_id, steps):
        req=self.get(request_id)
        if not req or req['mode']!='draft_plan' or not steps:
            raise ValueError('Cannot save draft for non-plan conversation')
        with self._db() as db:
            old=db.execute('SELECT id FROM project_drafts WHERE request_id=?',(request_id,)).fetchone()
            if old: return old['id']
            # Never overwrite an earlier draft silently; keep old revisions inspectable.
            db.execute("UPDATE project_drafts SET state='discarded',updated_at=CURRENT_TIMESTAMP WHERE chat_id=? AND project=? AND state='draft'",
                      (req['chat_id'],req['project']))
            i=db.execute('''INSERT INTO project_drafts(request_id,chat_id,project,original_prompt,steps_json)
                            VALUES(?,?,?,?,?)''', (request_id,req['chat_id'],req['project'],req['prompt'],json.dumps(steps))).lastrowid
        record(self.path.parent,'conversation','draft_plan_saved',draft_id=i,request_id=request_id,steps=len(steps))
        self.journal(request_id)
        return i

    def invalidate_incompatible_drafts(self):
        """Fail closed on legacy drafts that violate domain-specific requirements.

        Preserve the full conversation and proposal as history; only revoke the
        ability to approve such a draft. No executable jobs are touched.
        """
        from .agent_plan import validate_project_plan, PlanError
        with self._db() as db:
            rows = db.execute("SELECT id,original_prompt,steps_json FROM project_drafts WHERE state='draft'").fetchall()
        count = 0
        for row in rows:
            try:
                validate_project_plan(json.loads(row['steps_json']),row['original_prompt'])
            except (PlanError, ValueError, KeyError, TypeError):
                if self.discard(row['id']):
                    count += 1
                    record(self.path.parent,'conversation','invalid_draft_revoked',draft_id=row['id'])
        return count

    def latest_draft(self, chat_id, project):
        with self._db() as db:
            r=db.execute("SELECT * FROM project_drafts WHERE chat_id=? AND project=? AND state='draft' ORDER BY id DESC LIMIT 1",(chat_id,project)).fetchone()
            if not r:return None
            d=dict(r);d['steps']=json.loads(d['steps_json']);return d

    def draft(self, ident):
        with self._db() as db:
            r=db.execute('SELECT * FROM project_drafts WHERE id=?',(ident,)).fetchone()
            if not r:return None
            d=dict(r);d['steps']=json.loads(d['steps_json']);return d

    def approve(self, draft_id, job_id):
        with self._db() as db:
            r=db.execute('SELECT state,queued_job_id FROM project_drafts WHERE id=?',(draft_id,)).fetchone()
            if not r:return False
            if r['state']=='approved':return r['queued_job_id']==job_id
            if r['state']!='draft':return False
            db.execute("UPDATE project_drafts SET state='approved',queued_job_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(job_id,draft_id))
        record(self.path.parent,'conversation','draft_plan_approved',draft_id=draft_id,job_id=job_id)
        return True

    def discard(self, draft_id):
        with self._db() as db:
            result=db.execute("UPDATE project_drafts SET state='discarded',updated_at=CURRENT_TIMESTAMP WHERE id=? AND state='draft'",(draft_id,))
            return result.rowcount==1
