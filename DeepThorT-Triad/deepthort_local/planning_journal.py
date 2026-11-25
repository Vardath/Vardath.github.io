"""Planning journals, generated only from committed conversation state."""
import sqlite3
from contextlib import closing
from pathlib import Path
from .task_memory import sha,slug,_bounded,_LOCK,write_journal

def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS planning_journal_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER NOT NULL,
        stamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,state TEXT NOT NULL,detail TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS planning_journal_request ON planning_journal_events(request_id,id);
    CREATE TRIGGER IF NOT EXISTS planning_journal_insert AFTER INSERT ON conversation_requests
    WHEN NEW.mode='draft_plan' BEGIN
        INSERT INTO planning_journal_events(request_id,state,detail) VALUES(NEW.id,NEW.state,substr(NEW.detail,1,2000));
    END;
    CREATE TRIGGER IF NOT EXISTS planning_journal_update AFTER UPDATE OF state,detail ON conversation_requests
    WHEN NEW.mode='draft_plan' AND (NEW.state!=OLD.state OR NEW.detail!=OLD.detail) BEGIN
        INSERT INTO planning_journal_events(request_id,state,detail) VALUES(NEW.id,NEW.state,substr(NEW.detail,1,2000));
    END;
    """)

def render(path,ident):
    with _LOCK:
        with closing(sqlite3.connect(path,timeout=10)) as db:
            db.row_factory=sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            row=db.execute("SELECT * FROM conversation_requests WHERE id=? AND mode='draft_plan'",(ident,)).fetchone()
            if not row:return None
            events=db.execute('SELECT * FROM planning_journal_events WHERE request_id=? ORDER BY id DESC LIMIT 500',(ident,)).fetchall()
            draft=db.execute('SELECT id,state,queued_job_id,steps_json FROM project_drafts WHERE request_id=?',(ident,)).fetchone()
            amendment=db.execute('SELECT parent_request_id,ordinal,amendment,amendment_sha256 FROM specification_amendments WHERE request_id=?',(ident,)).fetchone()
        project=row['project']
        folder='project-'+slug(Path(project).name,32)+'-'+sha(project)[:12]
        dest=Path(path).parent/'task-journals'/folder/f"plan-{ident:06d}-{slug(row['prompt'][:100])}.md"
        lines=[f"# Planning request {ident}: {_bounded(row['prompt'].splitlines()[0],180)}",
            '',f"Project: {project}",f"State: {row['state']}",f"Specification SHA-256: {sha(row['prompt'])}",
            'Planning history only; this file cannot approve execution or change the original specification.',
            '', '## Request preview',_bounded(row['prompt'],4000)]
        if amendment:
            lines.extend(['','## Explicit amendment',f"Revision {amendment['ordinal']}; parent request {amendment['parent_request_id']}",
                          f"SHA-256: {amendment['amendment_sha256']}",_bounded(amendment['amendment'],2000)])
        lines.extend(['','## Planning events (latest 500; complete history in conversations.sqlite3)'])
        for e in reversed(events):lines.append(f"- {e['stamp']} UTC | {e['state']} | {e['detail']}")
        if draft:
            lines.extend(['','## Saved draft (not execution proof)',f"Draft {draft['id']}; state {draft['state']}; queued job {draft['queued_job_id']}",
                         _bounded(draft['steps_json'],5000)])
        if row['response']:
            lines.extend(['','## Last response preview (unverified model output)',f"SHA-256: {sha(row['response'])}",_bounded(row['response'],4000)])
        lines.append('\nFull request, response, amendments and plans remain in conversations.sqlite3.')
        return write_journal(dest,lines)
