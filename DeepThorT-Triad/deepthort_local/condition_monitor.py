"""Bounded, read-only project file predicates; no arbitrary expressions or commands."""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from .source_security import excluded,exclusions,linked,identity
from .reference_learning import BLOCKED_NAMES
from .website_monitor import epoch

MAX_BYTES=16*1024*1024
MIN_INTERVAL=60
MAX_INTERVAL=7*86400
MAX_ACTIVE=32
MAX_CHECKS=1000

def checked(s):
    if not isinstance(s,dict) or not isinstance(s.get('path'),str) or not isinstance(s.get('kind'),str):
        raise ValueError('Expected exact file path and predicate')
    p=s['path'];parts=p.split('/')
    if (not 1<=len(p)<=300 or any(not x or x in ('.','..') or x.endswith(('.', ' ')) or
            any(ord(c)<32 or c in '\\:*?"<>|' for c in x) or BLOCKED_NAMES.search(x) for x in parts)
            or excluded(p,set()) or any(re.fullmatch(r'(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',x,re.I) for x in parts)):
        raise ValueError('Unsafe or protected project-relative file path')
    kind=s['kind']
    if kind in ('exists','missing'):
        if set(s)!={'path','kind'}:raise ValueError('Unexpected predicate value')
    elif kind=='size_at_least':
        if set(s)!={'path','kind','value'} or type(s['value']) is not int or not 1<=s['value']<=2**40:
            raise ValueError('Expected positive byte threshold up to 1 TiB')
    elif kind=='sha256_equals':
        if set(s)!={'path','kind','value'} or not isinstance(s['value'],str) or not re.fullmatch(r'[0-9a-f]{64}',s['value']):
            raise ValueError('Expected exact lowercase SHA-256')
    else:raise ValueError('Unsupported file predicate')
    return s

def inspect_path(root,relative,exclude):
    root=Path(root).resolve(strict=True)
    if not root.is_dir() or excluded(relative,set(exclusions(exclude))):
        raise ValueError('File inspection excluded')
    current=root;parts=relative.split('/')
    for i,part in enumerate(parts):
        current=current/part
        try:st=current.lstat()
        except FileNotFoundError:return current,None
        if linked(current):raise ValueError('Linked file path refused')
        if i<len(parts)-1:
            if not stat.S_ISDIR(st.st_mode):raise ValueError('Non-directory parent')
        elif not stat.S_ISREG(st.st_mode):raise ValueError('Expected a regular file, not directory or device')
    return current,st

def observe(root,s,exclude=(),cancelled=None):
    checked(s);root=Path(root).resolve(strict=True)
    def stop():
        if cancelled and cancelled():raise ValueError('Condition check cancelled')
    stop()
    path,st=inspect_path(root,s['path'],exclude)
    kind=s['kind'];exists=st is not None;size=st.st_size if exists else None;digest=None
    if kind=='sha256_equals' and exists:
        if size>MAX_BYTES:raise ValueError('Hash input exceeds 16 MiB')
        h=sha256();total=0
        flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
        fd=os.open(path,flags)
        with os.fdopen(fd,'rb') as f:
            if identity(os.fstat(f.fileno()))!=identity(st):raise ValueError('File identity changed')
            while True:
                stop();block=f.read(65536)
                if not block:break
                total+=len(block)
                if total>MAX_BYTES:raise ValueError('Hash input exceeds 16 MiB')
                h.update(block)
            if total!=size or identity(os.fstat(f.fileno()))!=identity(st):
                raise ValueError('File changed during hash')
        digest=h.hexdigest()
    again,after=inspect_path(root,s['path'],exclude)
    if again!=path or (after is None)!= (st is None) or (st is not None and identity(after)!=identity(st)):
        raise ValueError('File changed during observation')
    stop()
    matched=(exists if kind=='exists' else not exists if kind=='missing' else
             exists and size>=s['value'] if kind=='size_at_least' else exists and digest==s['value'])
    return {'matched':matched,'exists':exists,'bytes':size,'sha256':digest}

def validated_result(s,r):
    if (not isinstance(r,dict) or set(r)!={'matched','exists','bytes','sha256'}
            or type(r['matched']) is not bool or type(r['exists']) is not bool
            or (r['exists'] and (type(r['bytes']) is not int or r['bytes']<0))
            or (not r['exists'] and (r['bytes'] is not None or r['sha256'] is not None))):
        raise ValueError('Invalid condition observation')
    kind=s['kind']
    if kind=='sha256_equals' and r['exists']:
        if not isinstance(r['sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',r['sha256']) or r['bytes']>MAX_BYTES:
            raise ValueError('Invalid observed digest')
    elif r['sha256'] is not None:raise ValueError('Unexpected observed digest')
    matched=(r['exists'] if kind=='exists' else not r['exists'] if kind=='missing' else
             r['exists'] and r['bytes']>=s['value'] if kind=='size_at_least' else r['exists'] and r['sha256']==s['value'])
    if matched!=r['matched']:raise ValueError('Predicate receipt mismatch')
    return r

class ConditionWatches:
    def __init__(self,conversations):
        self.conversations=conversations
        with conversations._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS condition_watches_v1 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,project TEXT NOT NULL,chat_id TEXT NOT NULL,
                    spec TEXT NOT NULL,interval_seconds INTEGER NOT NULL,remaining INTEGER NOT NULL,
                    due_utc INTEGER NOT NULL,state TEXT NOT NULL DEFAULT 'active',
                    last_matched INTEGER,last_status TEXT NOT NULL DEFAULT 'awaiting baseline',
                    last_checked_utc INTEGER);
                CREATE TABLE IF NOT EXISTS condition_checks_v1 (
                    watch_id INTEGER NOT NULL,due_utc INTEGER NOT NULL,checked_utc INTEGER NOT NULL,
                    status TEXT NOT NULL,observation TEXT,PRIMARY KEY(watch_id,due_utc));
            """)
    def create(self,project,chat,spec,interval,checks,*,approved=False,now=None,exclude=()):
        now=epoch(now);checked(spec)
        if approved is not True or not isinstance(project,str) or not project or project=='(general)' or not isinstance(chat,str) or not chat:
            raise ValueError('Explicit approval, workspace and chat required')
        inspect_path(project,spec['path'],exclude)
        if type(interval) is not int or not MIN_INTERVAL<=interval<=MAX_INTERVAL or type(checks) is not int or not 2<=checks<=MAX_CHECKS:
            raise ValueError('Choose 1 minute–7 days and 2–1000 attempts')
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT count(*) FROM condition_watches_v1 WHERE state='active'").fetchone()[0]>=MAX_ACTIVE:
                raise ValueError('Active condition watch limit reached')
            return db.execute("""INSERT INTO condition_watches_v1(project,chat_id,spec,interval_seconds,remaining,due_utc)
                VALUES(?,?,?,?,?,?)""",(project,chat,json.dumps(spec,sort_keys=True),interval,checks,now)).lastrowid
    def rows(self,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT * FROM condition_watches_v1 WHERE project=? AND chat_id=?
                ORDER BY CASE WHEN state='active' THEN 0 ELSE 1 END,id DESC LIMIT 100""",(project,chat))]
    def due(self,project,open_chats,*,now=None):
        now=epoch(now);allowed=set(open_chats)
        with self.conversations._db() as db:
            rows=db.execute("""SELECT * FROM condition_watches_v1 WHERE state='active' AND project=? AND due_utc<=?
                ORDER BY due_utc,id LIMIT ?""",(project,now,MAX_ACTIVE)).fetchall()
            return next((dict(r) for r in rows if r['chat_id'] in allowed),None)
    def cancel(self,ident,project,chat):
        with self.conversations._db() as db:
            return bool(db.execute("UPDATE condition_watches_v1 SET state='cancelled' WHERE id=? AND project=? AND chat_id=? AND state='active'",(ident,project,chat)).rowcount)
    def cancel_chat(self,project,chat):
        with self.conversations._db() as db:
            return db.execute("UPDATE condition_watches_v1 SET state='cancelled' WHERE project=? AND chat_id=? AND state='active'",(project,chat)).rowcount
    def history(self,ident,project,chat):
        with self.conversations._db() as db:
            return [dict(r) for r in db.execute("""SELECT c.* FROM condition_checks_v1 c JOIN condition_watches_v1 w ON w.id=c.watch_id
                WHERE w.id=? AND w.project=? AND w.chat_id=? ORDER BY c.due_utc DESC LIMIT 30""",(ident,project,chat))]
    def finish(self,snapshot,result=None,*,now=None):
        now=epoch(now)
        spec=checked(json.loads(snapshot['spec']))
        if result is not None:validated_result(spec,result)
        with self.conversations._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT * FROM condition_watches_v1 WHERE id=?",(snapshot['id'],)).fetchone()
            if row is None or dict(row)!=snapshot or row['state']!='active' or now<row['due_utc']:return None
            due=row['due_utc'];remaining=row['remaining']-1;interval=row['interval_seconds']
            prior=row['last_matched'];current=int(result['matched']) if result is not None else None
            status=('error' if current is None else
                    ('baseline_true' if current else 'baseline_false') if prior is None else
                    ('became_true' if current else 'became_false') if prior!=current else
                    ('unchanged_true' if current else 'unchanged_false'))
            next_due=due+((now-due)//interval+1)*interval
            db.execute("INSERT INTO condition_checks_v1 VALUES(?,?,?,?,?)",
                       (row['id'],due,now,status,json.dumps(result,sort_keys=True) if result is not None else None))
            db.execute("""UPDATE condition_watches_v1 SET remaining=?,due_utc=?,state=?,last_matched=?,
                last_status=?,last_checked_utc=? WHERE id=?""",
                (remaining,next_due,'active' if remaining else 'finished',prior if current is None else current,status,now,row['id']))
            return {'watch_id':row['id'],'status':status,'checked_utc':now,'due_utc':due,'matched':current,
                    'remaining':remaining,'project':row['project'],'chat_id':row['chat_id']}
