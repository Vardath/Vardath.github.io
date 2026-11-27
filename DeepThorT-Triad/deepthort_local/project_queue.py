"""Persistent owner-directed project/task priorities and cooperative holds.
Task identity is the project and chat, so approved builds and later amendments
remain associated with the original task. No grant or job state is modified.
"""
from contextlib import closing
import sqlite3
from pathlib import Path

GENERAL='(general)'
LIMIT=512
class QueuePolicy:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as db,db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS project_priority(project TEXT PRIMARY KEY,position INTEGER NOT NULL,held INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS task_priority(project TEXT NOT NULL,chat_id TEXT NOT NULL,position INTEGER NOT NULL,held INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(project,chat_id));
            """)
            if "removed" not in {r[1] for r in db.execute("PRAGMA table_info(project_priority)")}:
                db.execute("ALTER TABLE project_priority ADD COLUMN removed INTEGER NOT NULL DEFAULT 0")
    def connect(self):
        db=sqlite3.connect(self.path,timeout=2);db.row_factory=sqlite3.Row;return db
    def sync(self,scopes):
        scopes=list(dict.fromkeys(scopes))
        if not scopes:return
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE')
            for project,chat in scopes:
                if not project or project==GENERAL or not chat:continue
                db.execute('INSERT OR IGNORE INTO project_priority(project,position) SELECT ?,COALESCE(MAX(position),0)+1 FROM project_priority',(project,))
                db.execute('INSERT OR IGNORE INTO task_priority(project,chat_id,position) SELECT ?,?,COALESCE(MAX(position),0)+1 FROM task_priority WHERE project=?',(project,chat,project))
    def snapshot(self):
        with closing(self.connect()) as db:
            return View({r['project']:(r['position'],bool(r['held'])) for r in db.execute('SELECT * FROM project_priority')},
                        {(r['project'],r['chat_id']):(r['position'],bool(r['held'])) for r in db.execute('SELECT * FROM task_priority')},
                        {r['project'] for r in db.execute('SELECT project FROM project_priority WHERE removed=1')})
    def remove(self,project):
        """Remove from scheduling and the visible queue, not from disk or history."""
        if not project or project==GENERAL:raise ValueError('Choose a named project')
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE')
            n=db.execute('UPDATE project_priority SET removed=1,held=1 WHERE project=? AND removed=0',(project,)).rowcount
            if not n:raise ValueError('Project is not in the active queue')
    def restore(self,project):
        """Explicitly restore at the tail, paused until a separate Resume."""
        if not project or project==GENERAL:raise ValueError('Choose a named project')
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE')
            n=db.execute('UPDATE project_priority SET removed=0,held=1,position=(SELECT COALESCE(MAX(position),0)+1 FROM project_priority) WHERE project=? AND removed=1',(project,)).rowcount
            if not n:raise ValueError('Project is not removed')
    def hold(self,project,chat_id=None,*,held):
        if type(held) is not bool or project==GENERAL:raise ValueError('Choose a named project or task')
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM project_priority WHERE project=? AND removed=0',(project,)).fetchone():
                raise ValueError('Restore the removed project before changing its pause state')
            if chat_id is None:
                n=db.execute('UPDATE project_priority SET held=? WHERE project=?',(int(held),project)).rowcount
            else:
                n=db.execute('UPDATE task_priority SET held=? WHERE project=? AND chat_id=?',(int(held),project,chat_id)).rowcount
            if not n:raise ValueError('Queue entry no longer exists')
    def move(self,project,chat_id=None,*,delta,visible):
        if delta not in (-1,1) or project==GENERAL:raise ValueError('Invalid queue move')
        with closing(self.connect()) as db,db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM project_priority WHERE project=? AND removed=0',(project,)).fetchone():
                raise ValueError('Removed project cannot be reordered')
            if chat_id is None:
                table='project_priority';key='project';scope=' WHERE removed=0';args=();chosen=project
            else:
                table='task_priority';key='chat_id';scope=' WHERE project=?';args=(project,);chosen=chat_id
            rows=[(r[0],r[1]) for r in db.execute(f'SELECT {key},position FROM {table}'+scope+' ORDER BY position',args) if r[0] in visible]
            keys=[r[0] for r in rows]
            if chosen not in keys:raise ValueError('Queue selection changed')
            i=keys.index(chosen);j=i+delta
            if not 0<=j<len(rows):return False
            for first,second in ((rows[i],rows[j]),(rows[j],rows[i])):
                sql=f'UPDATE {table} SET position=? WHERE {key}=?'
                params=(second[1],first[0])
                if chat_id is not None:sql+=' AND project=?';params+=(project,)
                db.execute(sql,params)
            return True

class View:
    def __init__(self,projects,tasks,removed=()):self.projects=projects;self.tasks=tasks;self.removed=frozenset(removed)
    def allowed(self,row):
        p=row['project'];c=row.get('chat_id') or ''
        return p not in self.removed and not (self.projects.get(p,(0,False))[1] or self.tasks.get((p,c),(0,False))[1])
    def key(self,row):
        p=row['project'];c=row.get('chat_id') or ''
        if p==GENERAL:return (-1,0,row.get('id',row.get('request_id',0)))
        return (self.projects.get(p,(10**12,False))[0],
                self.tasks.get((p,c),(10**12,False))[0],row.get('id',row.get('request_id',0)))
    def scope_key(self,row):return self.key(row)[:2]

def inventory(conversations,jobs,roadmaps=()):
    """Read bounded live metadata only; do not load full stored prompts."""
    rows=[]
    with closing(sqlite3.connect(conversations,timeout=2)) as db:
        db.row_factory=sqlite3.Row
        for r in db.execute("""SELECT c.id,c.project,c.chat_id,c.state,substr(c.prompt,1,160) AS preview,c.created_at
             FROM conversation_requests c WHERE c.project!='(general)' AND
             (c.state IN ('pending','running','waiting_sources') OR
               EXISTS(SELECT 1 FROM project_drafts d WHERE d.request_id=c.id AND d.state='draft'))
             ORDER BY c.id LIMIT ?""",(LIMIT,)):
            rows.append(dict(r,kind='prompt'))
    with closing(sqlite3.connect(jobs,timeout=2)) as db:
        db.row_factory=sqlite3.Row
        for r in db.execute("""SELECT id,project,chat_id,state,substr(prompt,1,160) AS preview,created_at
            FROM jobs WHERE project!='(general)' AND state NOT IN ('complete','failed','cancelled','responded')
            AND mode NOT IN ('chat','plan','edit') ORDER BY id LIMIT ?""",(LIMIT,)):
            rows.append(dict(r,kind='job'))
    for r in roadmaps:
        if r.get('project') and r.get('chat_id'):
            rows.append(dict(id=r['request_id'],project=r['project'],chat_id=r['chat_id'],state='active roadmap',
                preview='Approved roadmap',kind='roadmap',created_at=r.get('created_at','')))
    rows.sort(key=lambda r:(r['created_at'],r['kind'],r['id']))
    return rows

def grouped(rows,view):
    projects={}
    for p in sorted(view.projects,key=lambda p:view.projects[p][0]):
        if p not in view.removed:projects[p]={}
    for r in sorted(rows,key=view.key):
        if r['project'] not in view.removed:projects.setdefault(r['project'],{}).setdefault(r['chat_id'],[]).append(r)
    return projects
