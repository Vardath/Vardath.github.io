"""Persistent per-project task board. Execution remains user directed."""
from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class TaskBoard:
    def __init__(self, db: str | Path):
        self.path = Path(db)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as con:
            con.execute('''CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            con.execute('''CREATE TABLE IF NOT EXISTS task_job_links (
                task_id INTEGER PRIMARY KEY, project TEXT NOT NULL,
                job_id INTEGER NOT NULL)''')
    @contextmanager
    def _conn(self):
        db=sqlite3.connect(self.path,timeout=20)
        try:
            with db:yield db
        finally:db.close()
    def add(self, project: str, title: str) -> int:
        if not project or not title.strip() or len(title) > 4000:
            raise ValueError('Select a project and enter a task')
        with self._conn() as con:
            return con.execute('INSERT INTO tasks(project,title) VALUES(?,?)',(project,title.strip())).lastrowid
    def items(self, project: str):
        with self._conn() as con:
            return con.execute('SELECT id,title,done FROM tasks WHERE project=? ORDER BY done,id',(project,)).fetchall()
    def mark(self, project: str, task_id: int, done: bool):
        with self._conn() as con:
            con.execute('UPDATE tasks SET done=? WHERE project=? AND id=?',(int(done),project,task_id))

    def links(self, project: str):
        with self._conn() as con:
            return dict(con.execute('''SELECT l.task_id,l.job_id FROM task_job_links l
                JOIN tasks t ON t.id=l.task_id AND t.project=l.project
                WHERE l.project=?''',(project,)))

    def link(self, project: str, task_id: int, job_id: int | None):
        """Explicit user association only, not job approval or task completion."""
        if job_id is not None and (type(job_id) is not int or job_id<1):
            raise ValueError('Invalid job identity')
        with self._conn() as con:
            if not con.execute('SELECT 1 FROM tasks WHERE project=? AND id=?',(project,task_id)).fetchone():
                raise ValueError('Task is outside the selected workspace')
            if job_id is None:
                con.execute('DELETE FROM task_job_links WHERE project=? AND task_id=?',(project,task_id))
            else:
                con.execute('''INSERT INTO task_job_links(task_id,project,job_id) VALUES(?,?,?)
                    ON CONFLICT(task_id) DO UPDATE SET project=excluded.project,job_id=excluded.job_id''',
                    (task_id,project,job_id))
