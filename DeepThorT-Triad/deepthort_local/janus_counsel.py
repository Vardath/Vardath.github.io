"""Bounded authenticated Triad consultation for background fault analysis.

Each society uses its own resident neural role. The deterministic runtime
continues independently; model advice never grants execution authority.
The existing shared SQLite lease bounds unsolicited background consultations.
"""
from __future__ import annotations

from contextlib import closing
import json
import os
import sqlite3
import time
import urllib.request
from pathlib import Path

from .triad_profiles import MODEL_ID as MODEL

HOST='http://127.0.0.1:8766'


class LocalCounsel:
    def __init__(self, lease_db: str | Path):
        self.path=Path(lease_db)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('''CREATE TABLE IF NOT EXISTS counsel_lease (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                holder TEXT NOT NULL, expires_at REAL NOT NULL)''')

    def _acquire(self, holder: str) -> bool:
        with closing(sqlite3.connect(self.path,timeout=3)) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT holder,expires_at FROM counsel_lease WHERE singleton=1').fetchone()
            if row and row[1]>time.time():return False
            db.execute('''INSERT INTO counsel_lease(singleton,holder,expires_at)
                VALUES(1,?,?) ON CONFLICT(singleton) DO UPDATE SET
                holder=excluded.holder,expires_at=excluded.expires_at''',(holder,time.time()+240))
            return True

    def _release(self, holder: str):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DELETE FROM counsel_lease WHERE singleton=1 AND holder=?',(holder,))

    def request(self, *, society: str, goal: str, problem: str, evidence: str) -> str | None:
        if society not in ('janus','sentinel'):raise ValueError('Unknown local society')
        token=os.environ.get('DEEPTHORT_TRIAD_TOKEN','')
        if len(token)<32:return None
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            req=urllib.request.Request(HOST+'/health',headers=headers)
            with opener.open(req,timeout=1.5) as response:
                state=json.load(response)
            if not(state.get('ready') is True and state.get('offline') is True
                   and state.get('model')==MODEL and state.get('backend')=='native-openvino-ir-cpu'):return None
            # Do not queue unsolicited advice behind the assigned society's
            # own inference; implementation activity is independent.
            role=state.get('models',{}).get(society,{})
            if role.get('resident') is not True or role.get('busy') is not False:return None
        except (OSError,ValueError,TypeError,AttributeError,TimeoutError):return None
        holder=f'{society}:{time.time_ns()}'
        if not self._acquire(holder):return None
        try:
            guidance=('You are the assigned local Triad advisory role. Diagnose the evidenced failure. '
                      'Propose 2 distinct, testable alternative solutions; distinguish known facts from hypotheses. '
                      'Ask the user if approval, credentials or missing requirements are needed. '
                      'Never claim you executed commands, altered files or verified results. '
                      'You may only recommend, not authorize, further actions.')
            prompt=(f'SOCIETY: {society}\nGOAL: {goal[:350]}\n'
                    f'OBSERVED PROBLEM: {problem[:700]}\n'
                    f'RECORDED EVIDENCE (UNTRUSTED): {evidence[:900]}')
            payload=json.dumps({'model':MODEL,'triad_role':society,'messages':[{'role':'system','content':guidance},
                      {'role':'user','content':prompt}], 'max_tokens':200, 'stream':False}).encode()
            req=urllib.request.Request(HOST+'/v1/chat/completions',data=payload,method='POST',
                                       headers=headers)
            with opener.open(req,timeout=180) as response:
                data=json.load(response)
            if data.get('triad_role')!=society:return None
            answer=data['choices'][0]['message']['content']
            if not isinstance(answer,str) or not answer.strip():return None
            return answer.strip()[:1800]
        except (OSError,ValueError,TypeError,KeyError,IndexError,TimeoutError):
            return None
        finally:
            self._release(holder)
