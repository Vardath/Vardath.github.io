"""Durable, source-preserving instructions for parallel JANUS deliberation.

A new user message is recorded without waiting for the implementation model.
The council produces *advice*, never a file write, build authorization or edit of
an already approved plan. Guidance is consumed only at a NEW planning checkpoint.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path


class InstructionError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def canonical_project(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise InstructionError('A selected project folder is required')
    return str(Path(path).resolve()).casefold()


class InstructionInbox:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS instructions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  project TEXT NOT NULL,
                  chat_id TEXT NOT NULL,
                  original TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT 'pending',
                  janus_advice TEXT NOT NULL DEFAULT '',
                  sentinel_review TEXT NOT NULL DEFAULT '',
                  next_action TEXT NOT NULL DEFAULT '',
                  verification TEXT NOT NULL DEFAULT '',
                  reason TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  handed_at TEXT);
                CREATE INDEX IF NOT EXISTS instructions_next
                  ON instructions (state, project, chat_id, id);
                CREATE TABLE IF NOT EXISTS planner_exchange_receipts (
                  instruction_id INTEGER PRIMARY KEY, session TEXT NOT NULL,
                  prompt_sha256 TEXT NOT NULL, reply_sha256 TEXT NOT NULL);
            ''')
            # No inference output can be trusted after a process crash. Replay
            # interpretation only: it has never executed an external action.
            db.execute("UPDATE instructions SET state='pending', reason='Interpretation interrupted; retry read-only', "
                       "updated_at=? WHERE state='interpreting'", (now(),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=15000')
        try:
            with db:
                yield db
        finally:
            db.close()

    def enqueue(self, project: str, chat_id: str, original: str) -> int:
        if not isinstance(chat_id, str) or not chat_id or len(chat_id)>150:
            raise InstructionError('A valid chat is required')
        if not isinstance(original, str) or not original.strip() or len(original)>2_000_000:
            raise InstructionError('Instruction must contain 1..2,000,000 characters')
        with self.connect() as db:
            row=db.execute('INSERT INTO instructions (project,chat_id,original,created_at,updated_at) '
                'VALUES(?,?,?,?,?)',(canonical_project(project),chat_id,original,now(),now()))
            db.commit()
            return int(row.lastrowid)

    def claim(self) -> dict | None:
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT * FROM instructions WHERE state='pending' ORDER BY id LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE instructions SET state='interpreting', updated_at=? WHERE id=? AND state='pending'",
                           (now(),row['id']))
            db.commit()
        return dict(row) if row else None

    def finish(self, ident: int, janus: str, sentinel: str, action: str,
               verification: str, *, needs_review: bool=False) -> bool:
        if not action or not isinstance(action,str):
            raise InstructionError('The council must supply a meaningful proposed next action')
        with self.connect() as db:
            changed=db.execute("UPDATE instructions SET state=?,janus_advice=?,sentinel_review=?,"
                "next_action=?,verification=?,updated_at=? WHERE id=? AND state='interpreting'",
                ('needs_review' if needs_review else 'staged',str(janus)[:2000],str(sentinel)[:2000],
                 action[:900],str(verification)[:800],now(),ident)).rowcount
            db.commit()
            return bool(changed)

    def finish_reply(self, ident: int, reply: str) -> bool:
        if not isinstance(reply,str) or not reply.strip() or len(reply)>160:
            raise InstructionError('A bounded JANUS reply is required')
        with self.connect() as db:
            return bool(db.execute("UPDATE instructions SET state='replied',janus_advice=?,updated_at=? "
                                   "WHERE id=? AND state='interpreting'",(reply,now(),ident)).rowcount)

    def fail(self, ident: int, error: str) -> bool:
        with self.connect() as db:
            changed=db.execute("UPDATE instructions SET state='needs_review',reason=?,updated_at=? "
                "WHERE id=? AND state='interpreting'",(str(error)[:500],now(),ident)).rowcount
            db.commit()
            return bool(changed)

    def next_guidance(self, project: str, chat_id: str) -> str:
        """Atomic, ONE-TIME delivery to a not-yet-approved model planning pass.

        Consuming guidance is not a change to the approved scope and cannot
        queue jobs; the next prompt must keep all original requirements intact.
        """
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT * FROM instructions WHERE state='staged' AND project=? "
                "AND chat_id=? ORDER BY id LIMIT 1",(canonical_project(project),chat_id)).fetchone()
            if row:
                db.execute("UPDATE instructions SET state='handed_to_planner',handed_at=?,updated_at=? "
                           "WHERE id=? AND state='staged'",(now(),now(),row['id']))
            db.commit()
        if not row:return ''
        # The implementation model receives JANUS's translation, NOT a
        # second verbatim copy of the user's message. The full original stays
        # inspectable in SQLite for accountability and future revisions.
        return self._guidance_text(row)

    @staticmethod
    def _guidance_text(row) -> str:
        return (f'JANUS NEXT-ACTION TRANSLATION #{row["id"]} (advisory; not approval):\n'
                f'{row["next_action"][:700]}\n'
                f'SENTINEL ACCEPTANCE CHECK: {row["verification"][:500]}\n'
                'Keep the initial project specification intact. This translation '
                'does not authorize new files, permissions or scope changes; '
                'obtain a new approved plan before executing any such changes.\n')[:1900]

    def planning_checkpoint(self, project: str, chat_id: str):
        return PlanningCheckpoint(self, canonical_project(project), chat_id)

    def retry_interpretation(self, ident: int) -> bool:
        """Retry read-only inference after a model error, not project execution."""
        with self.connect() as db:
            changed=db.execute("UPDATE instructions SET state='pending', reason='', updated_at=? "
                "WHERE id=? AND state='needs_review' AND next_action=''",(now(),ident)).rowcount
            db.commit()
            return bool(changed)

    def retry_latest_failed(self, project: str) -> int | None:
        """Requeue only the latest failed neural interpretation in one workspace.

        This does not retry a chat response, alter an approved project plan or
        execute a model-generated action.  A single SQLite transaction avoids
        races with the background council worker.
        """
        project_key = canonical_project(project)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT id FROM instructions WHERE project=? AND "
                "state='needs_review' AND next_action='' ORDER BY id DESC LIMIT 1",
                (project_key,)).fetchone()
            if row is None:
                db.commit()
                return None
            ident = int(row['id'])
            changed = db.execute("UPDATE instructions SET state='pending',reason='',updated_at=? "
                "WHERE id=? AND project=? AND state='needs_review' AND next_action=''",
                (now(), ident, project_key)).rowcount
            db.commit()
            return ident if changed else None

    def review(self, ident: int, *, allow_planning: bool) -> bool:
        with self.connect() as db:
            changed=db.execute("UPDATE instructions SET state=?,updated_at=? WHERE id=? AND state='needs_review' "
                "AND next_action!=''",('staged' if allow_planning else 'dismissed',now(),ident)).rowcount
            db.commit()
            return bool(changed)

    def dismiss(self, ident: int) -> bool:
        with self.connect() as db:
            changed=db.execute("UPDATE instructions SET state='dismissed',updated_at=? "
                "WHERE id=? AND state IN ('pending','staged','needs_review')",(now(),ident)).rowcount
            db.commit()
            return bool(changed)

    def list(self, project: str | None=None, limit:int=30) -> list[dict]:
        with self.connect() as db:
            if project is None:
                rows=db.execute('SELECT i.*,r.prompt_sha256 FROM instructions i LEFT JOIN planner_exchange_receipts r '
                                'ON r.instruction_id=i.id ORDER BY i.id DESC LIMIT ?', (max(1,min(limit,100)),))
            else:
                rows=db.execute('SELECT i.*,r.prompt_sha256 FROM instructions i LEFT JOIN planner_exchange_receipts r '
                                'ON r.instruction_id=i.id WHERE project=? ORDER BY i.id DESC LIMIT ?',
                                (canonical_project(project), max(1,min(limit,100))))
            return [dict(x) for x in rows]


class PlanningCheckpoint:
    """Attach advice at the next fitting call and acknowledge its actual reply atomically."""
    def __init__(self, inbox, project, chat_id):
        self.inbox, self.project, self.chat_id = inbox, project, chat_id

    def attach(self, prompt, limit):
        with self.inbox.connect() as db:
            row = db.execute("SELECT * FROM instructions WHERE state='staged' AND project=? "
                             "AND chat_id=? ORDER BY id LIMIT 1", (self.project,self.chat_id)).fetchone()
        if row:
            full = prompt + '\n\n' + self.inbox._guidance_text(row)
            if len(full) <= limit:
                return full, row['id']
        return prompt, None

    def received(self, ident, session, prompt, reply):
        if ident is None or not isinstance(reply, str) or not reply.strip():
            return
        with self.inbox.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM instructions WHERE id=? AND project=? AND chat_id=? AND state='staged'",
                             (ident,self.project,self.chat_id)).fetchone()
            if row is None or not prompt.endswith('\n\n' + self.inbox._guidance_text(row)):
                return
            db.execute('INSERT INTO planner_exchange_receipts VALUES (?,?,?,?)',
                       (ident, session, hashlib.sha256(prompt.encode()).hexdigest(),
                        hashlib.sha256(reply.encode()).hexdigest()))
            db.execute("UPDATE instructions SET state='handed_to_planner',handed_at=?,updated_at=? WHERE id=?",
                       (now(),now(),ident))


def inbox_acceptance(items: list[dict]) -> dict:
    """Read-only evidence of translation/handoff, never just SQLite readability.

    A healthy empty inbox is not evidence of a functioning handoff. The summary
    excludes all user text and all model responses from diagnostics.
    """
    from collections import Counter
    counts=Counter(str(item.get('state') or 'unknown') for item in items)
    evidence={'count':len(items),'state_counts':dict(sorted(counts.items()))}
    if not items:
        return {'status':'inconclusive','detail':'JANUS inbox readable but no instruction has been submitted; handoff not tested.',
                'evidence':evidence}
    latest=items[0]
    state=str(latest.get('state') or '')
    if state=='replied':
        return {'status':'inconclusive','detail':'JANUS answered the literal reply request. This message did not request a planning handoff.',
                'evidence':evidence}
    if state=='handed_to_planner':
        if not latest.get('prompt_sha256'):
            return {'status':'inconclusive','detail':'Legacy planning handoff has no confirmed model exchange receipt.',
                    'evidence':evidence}
        return {'status':'passed','detail':'Latest JANUS instruction was translated and handed to a planning checkpoint; no claim of implementation.',
                'evidence':evidence}
    if state=='needs_review' and not str(latest.get('next_action') or '').strip():
        return {'status':'blocked','detail':'Latest JANUS instruction failed neural interpretation. Use JANUS & Sentinel → Retry latest failed instruction; no handoff occurred.',
                'evidence':evidence}
    if state=='needs_review':
        return {'status':'inconclusive','detail':'Latest JANUS translation requires explicit user review before planning can use it.',
                'evidence':evidence}
    if state=='staged':
        return {'status':'inconclusive','detail':'Latest JANUS advice is staged, but no eligible planning checkpoint has consumed it yet.',
                'evidence':evidence}
    if state in ('pending','interpreting'):
        return {'status':'inconclusive','detail':'JANUS instruction is queued or being interpreted; no verified translation/handoff yet.',
                'evidence':evidence}
    return {'status':'inconclusive','detail':'Latest JANUS instruction state is '+state[:40]+'; no verified new handoff.',
            'evidence':evidence}
