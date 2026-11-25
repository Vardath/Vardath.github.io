"""Persist local-only coding-chat messages; no external inference endpoints."""
from __future__ import annotations
from contextlib import closing
import json
import os
from .triad_profiles import MODEL_ID,PROFILES
import re
import time
from .flight_recorder import record
import sqlite3
from contextlib import contextmanager
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


class LocalModelClient:
    def __init__(self, state_db: str | Path, base_url: str = 'http://127.0.0.1:8765', timeout: int = 7200, role: str | None = None):
        url = urlparse(base_url)
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password or url.query or url.fragment or url.path not in ('','/') or not url.port:
            raise ValueError('Only literal http://127.0.0.1:<port> is allowed')
        if not 1 <= timeout <= 7200: raise ValueError('timeout out of range')
        self.base_url=base_url.rstrip('/')
        self.role=role or ('janus' if url.port==8766 else 'implementation')
        if self.role not in PROFILES:raise ValueError('Unknown Triad role')
        self.timeout=timeout
        self.db=Path(state_db)
        self.db.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('user','assistant')),content TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('CREATE INDEX IF NOT EXISTS session_messages ON messages(session_id,id)')
    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.db,timeout=30)
        try:
            db.execute('PRAGMA journal_mode=WAL')
            with db:yield db
        finally:db.close()
    def history(self,session_id:str,max_messages:int=6):
        if not isinstance(session_id,str) or not 1 <= len(session_id) <= 128: raise ValueError('invalid session')
        if not 1 <= max_messages <= 10: raise ValueError('history size too large')
        with self._connect() as conn:
            rows=conn.execute('SELECT role,content FROM (SELECT id,role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT ?) ORDER BY id',(session_id,max_messages)).fetchall()
        return [{'role':r,'content':c} for r,c in rows]
    def display_history(self, session_id: str, max_messages: int = 250):
        # Legacy transcript with timestamps, ONLY for rendering the GUI timeline.
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 128:
            raise ValueError('invalid session')
        if not 1 <= max_messages <= 1000:
            raise ValueError('invalid display history limit')
        with self._connect() as conn:
            rows = conn.execute('SELECT id,role,content,created_at FROM '
                 '(SELECT id,role,content,created_at FROM messages WHERE session_id=? '
                 'ORDER BY id DESC LIMIT ?) ORDER BY id',
                 (session_id,max_messages)).fetchall()
        return [{'id':i,'role':role,'content':content,'created_at':stamp}
                for i,role,content,stamp in rows]

    def inference_context(self, session_id: str, max_messages: int = 6):
        # Local deterministic diagnostics belong in UI, never inside the LLM prompt.
        # Previously repeated diagnostic dumps consumed ~4K characters of prefill.
        data = self.display_history(session_id, max_messages=100)
        filtered = []
        i = 0
        while i < len(data):
            if (i + 1 < len(data) and data[i]['role'] == 'user'
                and data[i+1]['role'] == 'assistant'
                and data[i+1]['content'].startswith('LOCAL COMPUTER DIAGNOSTIC')):
                i += 2
                continue
            if (data[i]['role'] == 'assistant' and
                    data[i]['content'].startswith('LOCAL COMPUTER DIAGNOSTIC')):
                i += 1
                continue
            filtered.append({'role': data[i]['role'], 'content': data[i]['content']})
            i += 1
        return filtered[-max_messages:]

    def record_local_exchange(self, session_id: str, prompt: str, report: str) -> None:
        """Store an explicitly-labelled deterministic diagnostic as a chat interaction."""
        if not isinstance(prompt,str) or not prompt.strip() or not isinstance(report,str) or not report.startswith('LOCAL COMPUTER DIAGNOSTIC'):
            raise ValueError('only genuine, labelled local diagnostics may be stored this way')
        self.history(session_id)  # Validates thread ID; no network request.
        with self._connect() as conn:
            conn.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',
                              ((session_id,'user',prompt),(session_id,'assistant',report)))

    def completed_exchange(self, session_id: str, prompt: str) -> str | None:
        """Reuse an already completed *identical* model pass after interruption.

        Draft planning uses distinct session IDs per pass, and chat() writes both
        messages in one SQLite transaction only when a complete answer arrives.
        Comparing the exact saved input prevents carrying answers into changed
        specifications, references or model correction prompts. No new inference,
        approval, or source-file writes are triggered here.
        """
        self.history(session_id)  # Validate the session identifier.
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError('prompt required')
        with self._connect() as conn:
            rows = conn.execute(
                'SELECT role,content FROM messages WHERE session_id=? '
                'ORDER BY id DESC LIMIT 2', (session_id,)).fetchall()
        if (len(rows) == 2 and rows[0][0] == 'assistant' and rows[1] == ('user', prompt)
                and isinstance(rows[0][1], str) and rows[0][1].strip()):
            return rows[0][1]
        return None

    def historical_plan_exchange(self, prompt: str, *, project: str | Path,
                                 request: str, chat_id: str) -> str | None:
        """Reclaim pre-v46 answers from the owner's existing SQLite history.

        Historical logs contain no model text and are never interpreted as a
        plan. Reuse requires one saved complete prompt/answer pair plus a
        matching durable conversation (project, original user request, chat).
        An old partial JSON fragment still faces current path and X4 checks.
        """
        if not all(isinstance(x, str) and x for x in (prompt, request, chat_id)):
            return None
        conversation_db = self.db.parent / 'conversations.sqlite3'
        if not conversation_db.is_file():
            return None
        project_key = str(Path(project).resolve()).casefold()
        with closing(sqlite3.connect(conversation_db, timeout=20)) as conversations, conversations:
            eligible = {
                int(row[0]) for row in conversations.execute(
                    'SELECT id, project FROM conversation_requests '
                    'WHERE mode=? AND prompt=? AND chat_id=? AND attachments=?',
                    ('draft_plan', request, chat_id, '[]'))
                if str(Path(row[1]).resolve()).casefold() == project_key
            }
        if not eligible:
            return None
        with self._connect() as conn:
            # The adjacency of the two records is essential: never use the
            # assistant reply from an unrelated prompt in the same session.
            candidates = conn.execute("""SELECT u.session_id, a.content
                FROM messages AS u JOIN messages AS a
                ON a.id = u.id+1 AND a.session_id=u.session_id
                WHERE u.role='user' AND a.role='assistant' AND u.content=?
                AND u.session_id LIKE 'plan-%' ORDER BY u.id DESC LIMIT 300""",
                (prompt,)).fetchall()
        for session, answer in candidates:
            match = re.fullmatch(r'plan-(\d+)-(.+)', session)
            if not match or int(match.group(1)) not in eligible:
                continue
            suffix = match.group(2)
            # Both original one-session v15 plans and later per-pass sessions.
            if suffix != chat_id and not (suffix.startswith(chat_id + '-') and
                    suffix[len(chat_id)+1:].isdigit()):
                continue
            if isinstance(answer, str) and answer.strip():
                record(self.db.parent, 'model_client', 'historical_plan_exchange_restored',
                       old_request_id=int(match.group(1)),
                       prompt_sha256=__import__('hashlib').sha256(prompt.encode('utf-8')).hexdigest()[:16],
                       response_characters=len(answer))
                return answer
        return None

    def chat_as(self,role,session_id,prompt,max_tokens=96):
        return self.chat(session_id,prompt,max_tokens=max_tokens,triad_role=role)

    def chat(self,session_id:str,prompt:str,max_tokens:int=96,*,visible_prompt:str|None=None,triad_role:str|None=None):
        if not isinstance(prompt,str) or not prompt.strip(): raise ValueError('prompt required')
        if visible_prompt is not None and (not isinstance(visible_prompt,str) or not visible_prompt.strip()):
            raise ValueError('visible_prompt must be non-empty text')
        if not 1 <= max_tokens <= 768: raise ValueError('max_tokens must be 1..768')
        role=triad_role or self.role
        if role not in PROFILES:raise ValueError('Unknown Triad role')
        messages=[{'role':'system','content':'You are an offline coding assistant. Be concise, precise, and never claim unverified code execution.'}, *self.inference_context(session_id),{'role':'user','content':prompt}]
        # Prevent oversized prompts on limited-memory machines.
        while sum(len(m['content']) for m in messages)>14000 and len(messages)>2: messages.pop(1)
        payload=json.dumps({'model':MODEL_ID,'triad_role':role,'messages':messages,'max_tokens':max_tokens,'stream':False}).encode('utf8')
        req=urllib.request.Request(self.base_url+'/v1/chat/completions',data=payload,method='POST',headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ.get('DEEPTHORT_TRIAD_TOKEN','')})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        started=time.monotonic()
        record(self.db.parent,'model_client','request_started',session_id=session_id[:36],
               prompt_characters=len(prompt),context_characters=len(payload),max_tokens=max_tokens)
        try:
            with opener.open(req,timeout=self.timeout) as response:
                reply=json.load(response)
                if reply.get('model')!=MODEL_ID or reply.get('triad_role')!=role:
                    raise ValueError('Local broker returned an unexpected model or role')
                content=reply['choices'][0]['message']['content']
        except Exception as exc:
            record(self.db.parent,'model_client','request_failed',level='ERROR',
                   session_id=session_id[:36],seconds=round(time.monotonic()-started,2),
                   error_type=type(exc).__name__,error=str(exc)[:450])
            raise
        record(self.db.parent,'model_client','request_completed',session_id=session_id[:36],
               seconds=round(time.monotonic()-started,2),response_characters=len(content) if isinstance(content,str) else -1)
        if not isinstance(content,str) or not content.strip(): raise ValueError('model produced no response')
        with self._connect() as conn:
            conn.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',[(session_id,'user',visible_prompt if visible_prompt is not None else prompt),(session_id,'assistant',content)])
        return content
