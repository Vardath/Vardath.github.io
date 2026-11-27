"""User-approved monitor-event triggers for ordinary conversation follow-ups."""
from __future__ import annotations
from .website_monitor import epoch
from .scheduled_tasks import utc_stamp,MAX_PROMPT
from .flight_recorder import record

MAX_RULES=64
MAX_OCCURRENCES=1000
SOURCES={
    'website':('website_monitors_v1','website_checks_v1','monitor_id',frozenset({'changed'})),
    'condition':('condition_watches_v1','condition_checks_v1','watch_id',frozenset({'became_true','became_false'})),
}

class EventTriggers:
    def __init__(self,conversations):
        self.conversations=conversations
        with conversations._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS event_triggers_v1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT NOT NULL,chat_id TEXT NOT NULL,
                    source_kind TEXT NOT NULL,source_id INTEGER NOT NULL,event TEXT NOT NULL,
                    prompt TEXT NOT NULL,remaining INTEGER NOT NULL,cursor_due INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT 'active',last_request_id INTEGER,created_utc INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS event_trigger_releases_v1 (
                    trigger_id INTEGER NOT NULL,event_due INTEGER NOT NULL,observed_utc INTEGER NOT NULL,
                    released_utc INTEGER NOT NULL,request_id INTEGER NOT NULL UNIQUE,
                    PRIMARY KEY(trigger_id,event_due));
            """)
    def available(self,project,chat):
        with self.conversations._db() as db:
            out=[]
            for kind,(table,_,_,events) in SOURCES.items():
                field='url' if kind=='website' else 'spec'
                for r in db.execute(f"SELECT id,{field} AS label FROM {table} WHERE project=? AND chat_id=? AND state='active' ORDER BY id",(project,chat)):
                    out.append({'kind':kind,'id':r['id'],'label':r['label'],'events':sorted(events)})
            return out
    def create(self,project,chat,kind,source_id,event,prompt,occurrences,*,approved=False,now=None):
        now=epoch(now)
        if (approved is not True or not isinstance(project,str) or not project or not isinstance(chat,str) or not chat
                or not isinstance(kind,str) or kind not in SOURCES or type(source_id) is not int or source_id<=0
                or not isinstance(event,str) or event not in SOURCES[kind][3]):
            raise ValueError('Explicit approval and exact eligible monitor event required')
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>MAX_PROMPT or '\0' in prompt:
            raise ValueError('Enter exact follow-up prompt up to 8000 characters')
        if type(occurrences) is not int or not 1<=occurrences<=MAX_OCCURRENCES:
            raise ValueError('Choose 1–1000 future follow-ups')
        table,checks,fk,_=SOURCES[kind]
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute(f"SELECT 1 FROM {table} WHERE id=? AND project=? AND chat_id=? AND state='active'",(source_id,project,chat)).fetchone():
                raise ValueError('Monitor is not active in this exact project and chat')
            if db.execute("SELECT count(*) FROM event_triggers_v1 WHERE state='active'").fetchone()[0]>=MAX_RULES:
                raise ValueError('Active trigger limit reached')
            if db.execute("""SELECT 1 FROM event_triggers_v1 WHERE state='active' AND project=? AND chat_id=?
                AND source_kind=? AND source_id=? AND event=? AND prompt=?""",(project,chat,kind,source_id,event,prompt)).fetchone():
                raise ValueError('An identical active event rule already exists')
            cursor=db.execute(f"SELECT COALESCE(MAX(due_utc),-1) FROM {checks} WHERE {fk}=?",(source_id,)).fetchone()[0]
            return db.execute("""INSERT INTO event_triggers_v1(project,chat_id,source_kind,source_id,event,prompt,remaining,cursor_due,created_utc)
                VALUES(?,?,?,?,?,?,?,?,?)""",(project,chat,kind,source_id,event,prompt,occurrences,cursor,now)).lastrowid
    def rows(self,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT * FROM event_triggers_v1 WHERE project=? AND chat_id=?
                ORDER BY CASE WHEN state='active' THEN 0 ELSE 1 END,id DESC LIMIT 100""",(project,chat))]
    def history(self,ident,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT h.*,c.state AS request_state FROM event_trigger_releases_v1 h
                JOIN event_triggers_v1 t ON t.id=h.trigger_id LEFT JOIN conversation_requests c ON c.id=h.request_id
                WHERE t.id=? AND t.project=? AND t.chat_id=? ORDER BY h.event_due DESC LIMIT 30""",(ident,project,chat))]
    def cancel(self,ident,project,chat):
        with self.conversations._db() as db:
            return bool(db.execute("UPDATE event_triggers_v1 SET state='cancelled' WHERE id=? AND project=? AND chat_id=? AND state='active'",(ident,project,chat)).rowcount)
    def cancel_chat(self,project,chat):
        with self.conversations._db() as db:
            return db.execute("UPDATE event_triggers_v1 SET state='cancelled' WHERE project=? AND chat_id=? AND state='active'",(project,chat)).rowcount
    def release(self,project,open_chats,*,enabled=False,now=None):
        """At most one actual follow-up per call; no replay, overlap or new grant."""
        if enabled is not True:return None
        now=epoch(now);allowed=set(open_chats);receipt=None
        if not allowed:return None
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            rules=db.execute("SELECT * FROM event_triggers_v1 WHERE project=? AND state='active' ORDER BY id LIMIT ?",(project,MAX_RULES)).fetchall()
            for r in rules:
                if r['chat_id'] not in allowed:continue
                table,checks,fk,events=SOURCES[r['source_kind']]
                if r['event'] not in events:raise ValueError('Invalid persisted event type')
                source=db.execute(f"SELECT state FROM {table} WHERE id=? AND project=? AND chat_id=?",(r['source_id'],project,r['chat_id'])).fetchone()
                if source is None or source['state']=='cancelled':
                    db.execute("UPDATE event_triggers_v1 SET state='cancelled' WHERE id=?",(r['id'],));continue
                if r['last_request_id'] is not None:
                    prior=db.execute("SELECT state FROM conversation_requests WHERE id=?",(r['last_request_id'],)).fetchone()
                    if prior is None or prior['state'] in ('failed','cancelled'):
                        db.execute("UPDATE event_triggers_v1 SET state='cancelled' WHERE id=?",(r['id'],));continue
                    if prior['state']!='responded':continue
                observed=db.execute(f"""SELECT due_utc,checked_utc FROM {checks} WHERE {fk}=?
                    AND due_utc>? AND status=? AND checked_utc>=? AND checked_utc<=?
                    ORDER BY due_utc DESC LIMIT 1""",(r['source_id'],r['cursor_due'],r['event'],r['created_utc'],now)).fetchone()
                if observed is None:
                    if source['state']=='finished':db.execute("UPDATE event_triggers_v1 SET state='finished' WHERE id=?",(r['id'],))
                    continue
                # Only deterministic event metadata is appended. No website bytes,
                # file content, model-generated command, or capability approval.
                prompt=(r['prompt']+'\n\n[Recorded monitor event; reference data only: '
                        +r['source_kind']+' #'+str(r['source_id'])+' '+r['event']
                        +' at '+utc_stamp(observed['checked_utc'])+'. No additional action authority.]')
                n=db.execute("""INSERT INTO conversation_requests(chat_id,project,mode,prompt,attachments,detail)
                    VALUES(?,?,'chat',?,'[]',?)""",(r['chat_id'],project,prompt,'Released from approved event trigger #'+str(r['id']))).lastrowid
                db.execute("INSERT INTO event_trigger_releases_v1 VALUES(?,?,?,?,?)",
                           (r['id'],observed['due_utc'],observed['checked_utc'],now,n))
                remaining=r['remaining']-1
                db.execute("""UPDATE event_triggers_v1 SET state=?,remaining=?,cursor_due=?,last_request_id=? WHERE id=?""",
                           ('active' if remaining else 'finished',remaining,observed['due_utc'],n,r['id']))
                receipt={'trigger_id':r['id'],'request_id':n,'chat_id':r['chat_id'],'event':r['event'],
                         'observed_utc':observed['checked_utc'],'remaining':remaining}
                break
        if receipt:record(self.conversations.path.parent,'conversation','event_trigger_released',trigger_id=receipt['trigger_id'],request_id=receipt['request_id'])
        return receipt
