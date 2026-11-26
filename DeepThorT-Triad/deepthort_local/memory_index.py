"""Derived persistent term index for historical notes.

Original SQLite notes and job scope are authoritative. No embedding model,
network dependency, or SQLite optional extension. Triggers invalidate terms
even for writes made by older releases or direct SQL. Lazy scoped backfill is
transactional. The index never grants relevance or execution authority.
"""
import re
import sqlite3
import time
from pathlib import Path

STOP={'the','and','for','with','from','this','that','into','your','are','was','have','has','not','task','build','file','create','implement','approved','project','operation','memory','current'}
MAX_NOTE_SHORTLIST=64

def terms(value):
    return {x for x in re.findall(r'[a-z0-9]{3,}',str(value).casefold()) if x not in STOP}

def connect(path,*,read_only=False):
    if read_only:
        # Foreground advisory delivery must never initialize or rebuild the
        # term index, acquire a write lock, or wait for a background writer.
        db=sqlite3.connect(Path(path).resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=.05)
    else:
        db=sqlite3.connect(path,timeout=20)
    db.row_factory=sqlite3.Row
    try:
        if read_only:
            deadline=time.monotonic()+.15
            db.set_progress_handler(lambda:int(time.monotonic()>=deadline),1000)
            db.execute('BEGIN')
        else:
            db.execute('BEGIN IMMEDIATE')
            ensure(db)
        return db
    except BaseException:
        db.close()
        raise

def ensure(db):
    existing=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_term_index_v23'").fetchone()
    db.execute("""CREATE TABLE IF NOT EXISTS memory_term_index_v23(
        note_id INTEGER NOT NULL,term TEXT NOT NULL,
        title_hit INTEGER NOT NULL,body_hit INTEGER NOT NULL,
        PRIMARY KEY(note_id,term)) WITHOUT ROWID""")
    db.execute('CREATE INDEX IF NOT EXISTS memory_term_lookup_v23 ON memory_term_index_v23(term,note_id)')
    db.execute('CREATE TABLE IF NOT EXISTS memory_term_dirty_v23(note_id INTEGER PRIMARY KEY)')
    db.execute('CREATE INDEX IF NOT EXISTS memory_jobs_scope_v23 ON jobs(project,chat_id,id)')
    db.execute("""CREATE TRIGGER IF NOT EXISTS memory_note_insert_v23 AFTER INSERT ON task_memory_notes
        BEGIN INSERT OR IGNORE INTO memory_term_dirty_v23 VALUES(NEW.id); END""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS memory_note_update_v23 AFTER UPDATE ON task_memory_notes
        BEGIN
        DELETE FROM memory_term_index_v23 WHERE note_id=OLD.id;
        DELETE FROM memory_term_dirty_v23 WHERE note_id=OLD.id;
        INSERT OR IGNORE INTO memory_term_dirty_v23 VALUES(NEW.id);
        END""")
    db.execute("""CREATE TRIGGER IF NOT EXISTS memory_note_delete_v23 AFTER DELETE ON task_memory_notes
        BEGIN
        DELETE FROM memory_term_index_v23 WHERE note_id=OLD.id;
        DELETE FROM memory_term_dirty_v23 WHERE note_id=OLD.id;
        END""")
    if not existing:
        db.execute('INSERT OR IGNORE INTO memory_term_dirty_v23 SELECT id FROM task_memory_notes')

def refresh(db,project,chat_id,spec_sha):
    # Process only dirty records in this exact scope. Other scopes remain
    # pending and are not read into Python. Batch to bound working memory.
    while True:
        rows=db.execute("""SELECT n.id,n.focus,n.note
            FROM memory_term_dirty_v23 d JOIN task_memory_notes n ON n.id=d.note_id
            JOIN jobs j ON j.id=n.job_id
            WHERE j.project=? AND j.chat_id=? AND n.spec_sha=?
            ORDER BY n.id LIMIT 256""",(project,chat_id,spec_sha)).fetchall()
        if not rows:return
        for row in rows:
            ident=row['id']
            title=terms(row['focus']);body=terms(row['note'])
            db.execute('DELETE FROM memory_term_index_v23 WHERE note_id=?',(ident,))
            db.executemany('INSERT INTO memory_term_index_v23 VALUES(?,?,?,?)',
                ((ident,t,int(t in title),int(t in body)) for t in sorted(title|body)))
            db.execute('DELETE FROM memory_term_dirty_v23 WHERE note_id=?',(ident,))

def ranked_notes(db,project,chat_id,spec_sha,words,job_id,*,refresh_index=True):
    if not words:return
    if refresh_index:
        refresh(db,project,chat_id,spec_sha)
    elif not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_term_index_v23'").fetchone():
        return
    slots=','.join('?' for _ in words)
    # Scope is checked against current authoritative rows, never copied scope
    # metadata. Indexed matches are ranked across the entire scoped history.
    sql="""SELECT n.id,n.job_id,n.role,n.focus,n.note,n.evidence_sha,
        SUM(5*t.title_hit+2*t.body_hit)
        + CASE WHEN n.job_id=? AND ?>0 THEN 2 ELSE 0 END
        + CASE WHEN n.role='verification' OR substr(n.note,1,8)='Rejected' THEN 2 ELSE 0 END AS score,
        CASE WHEN n.role='verification' OR
             (n.role='sentinel' AND substr(n.note,1,10)='Rejected: ') THEN 1 ELSE 0 END AS eligible
        FROM memory_term_index_v23 t
        JOIN task_memory_notes n ON n.id=t.note_id JOIN jobs j ON j.id=n.job_id
        WHERE t.term IN ("""+slots+""") AND j.project=? AND j.chat_id=? AND n.spec_sha=?
        GROUP BY n.id
        ORDER BY eligible DESC,score DESC,CAST(n.id AS TEXT) ASC"""
    yield from db.execute(sql,(job_id,job_id,*sorted(words),project,chat_id,spec_sha))
