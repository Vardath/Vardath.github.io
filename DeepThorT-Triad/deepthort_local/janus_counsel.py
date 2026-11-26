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

    def request(self, *, society: str, goal: str, problem: str, evidence: str, worker_report: bool=False, coordination: str='' ) -> str | None:
        if society not in ('janus','sentinel'):raise ValueError('Unknown local society')
        if coordination and (not worker_report or (society,coordination) not in (('janus','propose'),('sentinel','review'))):
            raise ValueError('Incorrect coordination role')
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
            if worker_report and (state.get('admission_slots',0)<=0 or state.get('admission_waiting',0)>0):return None
        except (OSError,ValueError,TypeError,AttributeError,TimeoutError):return None
        holder=f'{society}:{time.time_ns()}'
        if not self._acquire(holder):return None
        try:
            guidance=('You are the assigned local Triad advisory role. Diagnose the evidenced failure. '
                      'Propose 2 distinct, testable alternative solutions; distinguish known facts from hypotheses. '
                      'Ask the user if approval, credentials or missing requirements are needed. '
                      'Never claim you executed commands, altered files or verified results. '
                      'You may only recommend, not authorize, further actions.')
            if worker_report:
                guidance=('A software or multimedia production worker has made an UNVERIFIED dependency claim. '
                          'Your independent role is to assess it, not to blindly accept it. '
                          + ('Identify the smallest testable way to resolve the dependency using existing approved work or capabilities. Identify independent branches that can progress. ' if society=='janus' else 'Challenge whether the dependency is real, whether it conflicts with the original specification, and what exact evidence must be checked. ')
                          + 'Distinguish known facts from hypotheses; no command execution, permission changes, source edits or claims of successful tests. Request user input only if necessary. Give concise scoped corrective advice.')
            if coordination=='propose':
                guidance=('Assess the unverified dependency claim against exact approved requirements. '
                    'Only propose a fresh inference on the same approved file with specific guidance derived from provided facts. '
                    'If genuinely missing data, tools, permission, source, or requirements prevent progress, hold; do not invent them. '
                    'No new files, commands, permissions, changed specification or claimed tests. '
                    'Return ONLY JSON {"decision":"retry","guidance":"specific corrective advice (max 360 chars)","reason":"why (max 300 chars)"} '
                    'or {"decision":"hold","guidance":"","reason":"exact unresolved dependency"} .')
            elif coordination=='review':
                guidance=('Independently challenge the exact JANUS corrective proposal against the original user requirements and worker claim. '
                    'Accept only if its specific advice is supported, preserves every requirement and scope, and requires no invented dependency or new permission. '
                    'If evidence is insufficient, reject. Acceptance allows one fresh inference, not source publication or runtime verification. '
                    'Return ONLY JSON {"decision":"accept","reason":"specific evidence-based reason"} or {"decision":"reject","reason":"specific objection"}.')
            prompt=(f'SOCIETY: {society}\nGOAL: {goal[:350]}\n'
                    f'OBSERVED PROBLEM: {problem[:700]}\n'
                    f'RECORDED EVIDENCE (UNTRUSTED): {evidence[:4800 if coordination else 2500 if worker_report else 900]}')
            payload=json.dumps({'model':MODEL,'triad_role':society,'messages':[{'role':'system','content':guidance},
                      {'role':'user','content':prompt}], 'max_tokens':384 if coordination else 200, 'stream':False}).encode()
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
