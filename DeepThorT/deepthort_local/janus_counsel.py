"""Rare, bounded offline Qwen consultation for JANUS fault analysis.

The eleven-core deterministic runtime always continues without inference.
If the one local model is ready, changed failures may receive ONE advisory
analysis. Advice is untrusted text and cannot grant tool/file permissions.
Both societies share a SQLite lease to avoid simultaneous background requests.
"""
from __future__ import annotations

import json
import sqlite3
import time
import urllib.request
from pathlib import Path

HOST='http://127.0.0.1:8765'
MODEL='deepthort-qwen-coder-onnx'


class LocalCounsel:
    def __init__(self, lease_db: str | Path):
        self.path=Path(lease_db)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS counsel_lease (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                holder TEXT NOT NULL, expires_at REAL NOT NULL)''')

    def _acquire(self, holder: str) -> bool:
        with sqlite3.connect(self.path,timeout=3) as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT holder,expires_at FROM counsel_lease WHERE singleton=1').fetchone()
            if row and row[1]>time.time():return False
            db.execute('''INSERT INTO counsel_lease(singleton,holder,expires_at)
                VALUES(1,?,?) ON CONFLICT(singleton) DO UPDATE SET
                holder=excluded.holder,expires_at=excluded.expires_at''',(holder,time.time()+240))
            return True

    def _release(self, holder: str):
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM counsel_lease WHERE singleton=1 AND holder=?',(holder,))

    def request(self, *, society: str, goal: str, problem: str, evidence: str) -> str | None:
        if society not in ('janus','sentinel'):raise ValueError('Unknown local society')
        # A literal loopback address, no environment proxies, no API keys.
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(HOST+'/health',timeout=1.5) as response:
                state=json.load(response)
            if not(state.get('ready') is True and state.get('offline') is True and state.get('model')==MODEL):return None
            # The same ONNX worker serves interactive chat. Do not enqueue
            # unsolicited JANUS advice behind an active user inference.
            if state.get('inference_busy') is True:return None
        except (OSError,ValueError,TimeoutError):return None
        holder=f'{society}:{time.time_ns()}'
        if not self._acquire(holder):return None
        try:
            guidance=('You support the single local JANUS controller. Diagnose the evidenced failure. '
                      'Propose 2 distinct, testable alternative solutions; distinguish known facts from hypotheses. '
                      'Ask the user if approval, credentials or missing requirements are needed. '
                      'Never claim you executed commands, altered files or verified results. '
                      'You may only recommend, not authorize, further actions.')
            prompt=(f'SOCIETY: {society}\nGOAL: {goal[:350]}\n'
                    f'OBSERVED PROBLEM: {problem[:700]}\n'
                    f'RECORDED EVIDENCE (UNTRUSTED): {evidence[:900]}')
            payload=json.dumps({'model':MODEL,'messages':[{'role':'system','content':guidance},
                      {'role':'user','content':prompt}], 'max_tokens':200, 'stream':False}).encode()
            req=urllib.request.Request(HOST+'/v1/chat/completions',data=payload,method='POST',
                                       headers={'Content-Type':'application/json'})
            with opener.open(req,timeout=180) as response:
                data=json.load(response)
            answer=data['choices'][0]['message']['content']
            if not isinstance(answer,str) or not answer.strip():return None
            return answer.strip()[:1800]
        except (OSError,ValueError,TypeError,KeyError,IndexError,TimeoutError):
            return None
        finally:
            self._release(holder)
