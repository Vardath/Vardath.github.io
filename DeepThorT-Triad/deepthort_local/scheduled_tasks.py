"""Durable one-shot scheduled conversations, not preapproved executable jobs."""
from __future__ import annotations
from datetime import datetime,timezone
import time
from .flight_recorder import record

MAX_ACTIVE=128
MAX_PER_CHAT=24
MAX_PROMPT=8000
MAX_DELAY=365*86400
MIN_INTERVAL=15*60
MAX_OCCURRENCES=1000

def utc_stamp(epoch):
    return datetime.fromtimestamp(epoch,timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

def clock(now):
    if now is None:return int(time.time())
    if type(now) is not int or now<0:raise ValueError('Invalid schedule clock')
    return now

class ScheduledTasks:
    def __init__(self,conversations):
        self.conversations=conversations
        with conversations._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS scheduled_conversations_v1 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL, chat_id TEXT NOT NULL,
                prompt TEXT NOT NULL, due_utc INTEGER NOT NULL,
                state TEXT NOT NULL DEFAULT 'scheduled' CHECK(state IN ('scheduled','released','cancelled')),
                request_id INTEGER UNIQUE,
                created_utc INTEGER NOT NULL, updated_utc INTEGER NOT NULL)""")
            cols={r[1] for r in db.execute('PRAGMA table_info(scheduled_conversations_v1)')}
            for col,definition in (('interval_seconds','INTEGER'),('remaining_runs','INTEGER NOT NULL DEFAULT 1'),
                                   ('released_count','INTEGER NOT NULL DEFAULT 0')):
                if col not in cols:db.execute('ALTER TABLE scheduled_conversations_v1 ADD COLUMN '+col+' '+definition)
            db.execute("UPDATE scheduled_conversations_v1 SET remaining_runs=0,released_count=1 WHERE state='released' AND interval_seconds IS NULL AND released_count=0")
            db.execute("""CREATE TABLE IF NOT EXISTS scheduled_occurrences_v1 (
                schedule_id INTEGER NOT NULL, due_utc INTEGER NOT NULL, request_id INTEGER NOT NULL UNIQUE,
                released_utc INTEGER NOT NULL, PRIMARY KEY(schedule_id,due_utc))""")
            db.execute("""INSERT OR IGNORE INTO scheduled_occurrences_v1(schedule_id,due_utc,request_id,released_utc)
                SELECT id,due_utc,request_id,updated_utc FROM scheduled_conversations_v1
                WHERE state='released' AND interval_seconds IS NULL AND request_id IS NOT NULL""")
            db.execute("""CREATE INDEX IF NOT EXISTS scheduled_conversations_due_v1
                ON scheduled_conversations_v1(project,state,due_utc,id)""")

    def create(self,project,chat_id,prompt,due_utc,*,now=None,user_approved=False,interval_seconds=None,occurrences=1):
        now=clock(now)
        if user_approved is not True:raise ValueError('Explicit user approval is required')
        if not isinstance(project,str) or not project or not isinstance(chat_id,str) or not chat_id:
            raise ValueError('Existing chat and project binding required')
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>MAX_PROMPT or '\0' in prompt:
            raise ValueError('Enter a nonempty prompt of at most 8000 characters')
        if type(due_utc) is not int or not now<due_utc<=now+MAX_DELAY:
            raise ValueError('Choose a future time within 365 days')
        if interval_seconds is None:
            if type(occurrences) is not int or occurrences!=1:raise ValueError('One-time schedule must have exactly one occurrence')
        elif (type(interval_seconds) is not int or not MIN_INTERVAL<=interval_seconds<=MAX_DELAY
                or type(occurrences) is not int or not 2<=occurrences<=MAX_OCCURRENCES):
            raise ValueError('Recurring schedules require 15 minutes to 365 days and 2–1000 occurrences')
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT count(*) FROM scheduled_conversations_v1 WHERE state='scheduled'").fetchone()[0]>=MAX_ACTIVE:
                raise ValueError('Active schedule limit reached')
            if db.execute("SELECT count(*) FROM scheduled_conversations_v1 WHERE state='scheduled' AND chat_id=? AND project=?",(chat_id,project)).fetchone()[0]>=MAX_PER_CHAT:
                raise ValueError('Chat schedule limit reached')
            n=db.execute("""INSERT INTO scheduled_conversations_v1(project,chat_id,prompt,due_utc,created_utc,updated_utc,interval_seconds,remaining_runs)
                VALUES(?,?,?,?,?,?,?,?)""",(project,chat_id,prompt,due_utc,now,now,interval_seconds,occurrences)).lastrowid
        return n

    def rows(self,project,chat_id):
        with self.conversations._db() as db:
            return [dict(x) for x in db.execute("""SELECT * FROM scheduled_conversations_v1
                WHERE project=? AND chat_id=? ORDER BY CASE WHEN state='scheduled' THEN 0 ELSE 1 END,
                due_utc DESC,id DESC LIMIT 100""",(project,chat_id))]

    def occurrences(self,ident,project,chat_id):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT o.*,c.state AS request_state FROM scheduled_occurrences_v1 o
                JOIN scheduled_conversations_v1 s ON s.id=o.schedule_id
                LEFT JOIN conversation_requests c ON c.id=o.request_id
                WHERE s.id=? AND s.project=? AND s.chat_id=? ORDER BY o.due_utc DESC LIMIT 100""",
                (ident,project,chat_id))]

    def cancel(self,ident,project,chat_id,*,now=None):
        now=clock(now)
        with self.conversations._db() as db:
            return bool(db.execute("""UPDATE scheduled_conversations_v1 SET state='cancelled',updated_utc=?
                WHERE id=? AND project=? AND chat_id=? AND state='scheduled'""",
                (now,ident,project,chat_id)).rowcount)

    def cancel_chat(self,project,chat_id,*,now=None):
        now=clock(now)
        with self.conversations._db() as db:
            return db.execute("""UPDATE scheduled_conversations_v1 SET state='cancelled',updated_utc=?
                WHERE project=? AND chat_id=? AND state='scheduled'""",(now,project,chat_id)).rowcount

    def release_due(self,project,open_chat_ids,*,now=None,enabled=False):
        """Atomically admit at most one due request. No duplicate after restart."""
        if enabled is not True:return None
        now=clock(now);allowed=set(open_chat_ids)
        if not allowed:return None
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("""SELECT * FROM scheduled_conversations_v1
                WHERE project=? AND state='scheduled' AND due_utc<=?
                ORDER BY due_utc,id LIMIT ?""",(project,now,MAX_ACTIVE)).fetchall()
            row=None
            for candidate in rows:
                if candidate['chat_id'] not in allowed:continue
                if candidate['request_id'] is not None:
                    prior=db.execute('SELECT state FROM conversation_requests WHERE id=?',(candidate['request_id'],)).fetchone()
                    if not prior or prior['state'] in ('failed','cancelled'):
                        # Stop the recurrence rather than repeat a failed or explicitly stopped request.
                        db.execute("UPDATE scheduled_conversations_v1 SET state='cancelled',updated_utc=? WHERE id=?",(now,candidate['id']))
                        continue
                    if prior['state']!='responded':continue
                row=candidate;break
            if row is None:return None
            due=row['due_utc'];remaining=row['remaining_runs']-1;interval=row['interval_seconds']
            if remaining<0 or (interval is None and remaining!=0):
                raise RuntimeError('Invalid persisted recurrence state')
            # Keep the original cadence. Never enqueue a burst for missed intervals.
            next_due=due+((now-due)//interval+1)*interval if interval and remaining else due
            n=db.execute("""INSERT INTO conversation_requests(chat_id,project,mode,prompt,attachments,detail)
                VALUES(?,?,'chat',?,'[]',?)""",
                (row['chat_id'],project,row['prompt'],'Released from user-approved schedule #'+str(row['id']))).lastrowid
            db.execute("""INSERT INTO scheduled_occurrences_v1(schedule_id,due_utc,request_id,released_utc)
                VALUES(?,?,?,?)""",(row['id'],due,n,now))
            changed=db.execute("""UPDATE scheduled_conversations_v1 SET state=?,request_id=?,updated_utc=?,due_utc=?,
                remaining_runs=?,released_count=released_count+1 WHERE id=? AND state='scheduled'""",
                ('scheduled' if remaining else 'released',n,now,next_due,remaining,row['id'])).rowcount
            if changed!=1:raise RuntimeError('Schedule admission transaction changed')
            receipt={'schedule_id':row['id'],'request_id':n,'chat_id':row['chat_id'],'due_utc':due,
                     'remaining_runs':remaining,'next_due_utc':next_due if remaining else None}
        record(self.conversations.path.parent,'conversation','scheduled_conversation_released',
               schedule_id=receipt['schedule_id'],request_id=n)
        return receipt
