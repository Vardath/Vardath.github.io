"""Read-only planning supervision and bounded automatic draft recovery.

Only previously requested draft plans may be resumed here. Neither the model
nor the recovery scheduler can approve a build or run a command.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

RECOVERABLE=(
    'Local model request failed: Indexed X4 roadmap paused',
    'Local model request failed: Indexed X4 roadmap remains incomplete',
    'Local model request failed: Large-document review paused',
    'Local model request failed: Large specification stored without truncation',
)
LATEST_DRAFT="""NOT EXISTS (SELECT 1 FROM conversation_requests newer
    WHERE newer.chat_id=c.chat_id AND newer.project=c.project
      AND newer.mode='draft_plan' AND newer.id>c.id)"""


def observe_planning(job_db):
    """Expose latest planning states without loading private prompt contents."""
    path=Path(job_db).parent/'conversations.sqlite3'
    if not path.is_file():return []
    try:
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute(
                "SELECT c.id,c.project,c.mode,c.state,c.detail,c.updated_at "
                "FROM conversation_requests c WHERE c.mode='draft_plan' AND "
                "c.state IN ('pending','running','waiting_sources','failed') AND "
                +LATEST_DRAFT+" ORDER BY c.id DESC LIMIT 80")]
    except sqlite3.Error:return []


def resume_stalled_draft(path,index,*,cooldown_seconds=90,max_attempts=2):
    """Requeue at most two retries per objective progress epoch, across restarts.

    A new reviewed section or newly closed validator check earns a fresh budget.
    Model activity alone, changes to error wording, and restarts do not.
    Superseded or cancelled requests and source/approval failures are excluded.
    """
    if not 0<=cooldown_seconds<=3600 or not 1<=max_attempts<=2:
        raise ValueError('Invalid bounded recovery settings')
    with closing(sqlite3.connect(path,timeout=10)) as db:
        db.row_factory=sqlite3.Row
        with db:
            db.execute('''CREATE TABLE IF NOT EXISTS planning_recovery_attempts (
                request_id INTEGER NOT NULL, progress_epoch TEXT NOT NULL,
                attempts INTEGER NOT NULL, PRIMARY KEY(request_id,progress_epoch))''')
        rows=db.execute(
            "SELECT c.id,c.updated_at FROM conversation_requests c WHERE "
            "c.mode='draft_plan' AND c.state='failed' AND "
            "((julianday('now')-julianday(c.updated_at))*86400)>=? AND ("
            +" OR ".join("c.detail LIKE ?" for _ in RECOVERABLE)+") AND "
            +LATEST_DRAFT+" ORDER BY c.id DESC LIMIT 32",
            (cooldown_seconds,*(p+'%' for p in RECOVERABLE))).fetchall()
        for row in rows:
            ident=row['id']
            req=db.execute('SELECT prompt,detail FROM conversation_requests WHERE id=?',
                           (ident,)).fetchone()
            if not req or not req['detail'].startswith(RECOVERABLE):continue
            original=req['prompt']
            try:
                status=index.status(ident,original)
                progress=index.roadmap_stall_status(ident,original)
            except (ValueError,OSError,sqlite3.Error):continue
            epoch=hashlib.sha256(json.dumps([
                status['sha256'],status['reviewed'],progress['checks_closed_total']],
                separators=(',',':')).encode()).hexdigest()
            with db:
                db.execute('BEGIN IMMEDIATE')
                # Recheck the latest request and its immutable source in the
                # same transaction that reserves this recovery attempt.
                current=db.execute("SELECT 1 FROM conversation_requests c WHERE "
                    "c.id=? AND c.state='failed' AND c.updated_at=? AND c.prompt=? "
                    "AND c.detail=? AND "+LATEST_DRAFT,
                    (ident,row['updated_at'],original,req['detail'])).fetchone()
                if not current:continue
                previous=db.execute('SELECT attempts FROM planning_recovery_attempts '
                    'WHERE request_id=? AND progress_epoch=?',(ident,epoch)).fetchone()
                count=previous[0] if previous else 0
                if count>=max_attempts:continue
                db.execute('INSERT INTO planning_recovery_attempts VALUES (?,?,1) '
                    'ON CONFLICT(request_id,progress_epoch) DO UPDATE SET attempts=attempts+1',
                    (ident,epoch))
                db.execute("UPDATE conversation_requests SET state='pending',detail=?,"
                    "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (f'JANUS recovery {count+1}/{max_attempts}: resume exact saved planning progress',ident))
                return {'request_id':ident,'attempt':count+1,'progress_epoch':epoch}
    return None
