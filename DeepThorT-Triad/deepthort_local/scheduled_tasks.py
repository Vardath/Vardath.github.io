"""Durable one-shot scheduled conversations, not preapproved executable jobs."""
from __future__ import annotations
from datetime import datetime,timezone
import time
from .flight_recorder import record

MAX_ACTIVE=128
MAX_PER_CHAT=24
MAX_PROMPT=8000
MAX_DELAY=365*86400

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
            db.execute("""CREATE INDEX IF NOT EXISTS scheduled_conversations_due_v1
                ON scheduled_conversations_v1(project,state,due_utc,id)""")

    def create(self,project,chat_id,prompt,due_utc,*,now=None,user_approved=False):
        now=clock(now)
        if user_approved is not True:raise ValueError('Explicit user approval is required')
        if not isinstance(project,str) or not project or not isinstance(chat_id,str) or not chat_id:
            raise ValueError('Existing chat and project binding required')
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>MAX_PROMPT or '\0' in prompt:
            raise ValueError('Enter a nonempty prompt of at most 8000 characters')
        if type(due_utc) is not int or not now<due_utc<=now+MAX_DELAY:
            raise ValueError('Choose a future time within 365 days')
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT count(*) FROM scheduled_conversations_v1 WHERE state='scheduled'").fetchone()[0]>=MAX_ACTIVE:
                raise ValueError('Active schedule limit reached')
            if db.execute("SELECT count(*) FROM scheduled_conversations_v1 WHERE state='scheduled' AND chat_id=? AND project=?",(chat_id,project)).fetchone()[0]>=MAX_PER_CHAT:
                raise ValueError('Chat schedule limit reached')
            n=db.execute("""INSERT INTO scheduled_conversations_v1(project,chat_id,prompt,due_utc,created_utc,updated_utc)
                VALUES(?,?,?,?,?,?)""",(project,chat_id,prompt,due_utc,now,now)).lastrowid
        return n

    def rows(self,project,chat_id):
        with self.conversations._db() as db:
            return [dict(x) for x in db.execute("""SELECT * FROM scheduled_conversations_v1
                WHERE project=? AND chat_id=? ORDER BY CASE WHEN state='scheduled' THEN 0 ELSE 1 END,
                due_utc DESC,id DESC LIMIT 100""",(project,chat_id))]

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
            row=next((r for r in rows if r['chat_id'] in allowed),None)
            if row is None:return None
            n=db.execute("""INSERT INTO conversation_requests(chat_id,project,mode,prompt,attachments,detail)
                VALUES(?,?,'chat',?,'[]',?)""",
                (row['chat_id'],project,row['prompt'],'Released from user-approved schedule #'+str(row['id']))).lastrowid
            changed=db.execute("""UPDATE scheduled_conversations_v1 SET state='released',request_id=?,updated_utc=?
                WHERE id=? AND state='scheduled'""",(n,now,row['id'])).rowcount
            if changed!=1:raise RuntimeError('Schedule admission transaction changed')
            receipt={'schedule_id':row['id'],'request_id':n,'chat_id':row['chat_id'],'due_utc':row['due_utc']}
        record(self.conversations.path.parent,'conversation','scheduled_conversation_released',
               schedule_id=receipt['schedule_id'],request_id=n)
        return receipt
