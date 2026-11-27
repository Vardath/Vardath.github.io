"""Durable role tasks attached to the authoritative conversation database.

Only the currently supported, explicitly requested staged MIDI adapter is
registered. No model can issue arbitrary commands or publish project files.
The host claims dependency-ready stages transactionally. A lost lease is
interrupted, never automatically replayed. This shares the existing conversation
DB so cancellation and final handoff cannot race a separate state store.
"""
import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from .agent_contract import canonical_sha,validate_creative_assignment
from .creative_core import is_midi_request,request_packet
from .team_plan import is_team_request,TEAM_STAGES

MAX_PENDING=32
STAGES=(('compose','multimedia',()),('verify','host',('compose',)))
def eligible(row):
    if not row or row['mode']!='chat' or not (is_midi_request(row['prompt']) or is_team_request(row['prompt'])):
        return False
    try:return len(row['prompt'])<=1400 and json.loads(row['attachments'])==[]
    except (ValueError,TypeError,KeyError):return False

def binding(row):
    return canonical_sha({k:row[k] for k in ('id','project','chat_id','mode','prompt','attachments')})

def scope(row,attempt):
    return 'conversation:'+str(row['id'])+':attempt:'+str(attempt)+':'+binding(row)

class DelegationError(ValueError):pass

class DelegationStore:
    def __init__(self,path,artifact_root):
        self.path=Path(path)
        self.artifact_root=Path(artifact_root).resolve()
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS agent_batches_v39(
                    request_id INTEGER PRIMARY KEY,binding TEXT NOT NULL,
                    attempt INTEGER NOT NULL,state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS agent_stages_v39(
                    request_id INTEGER NOT NULL,attempt INTEGER NOT NULL,
                    stage TEXT NOT NULL,role TEXT NOT NULL,state TEXT NOT NULL,
                    lease TEXT,receipt TEXT,PRIMARY KEY(request_id,attempt,stage));
                CREATE TABLE IF NOT EXISTS agent_edges_v39(
                    request_id INTEGER NOT NULL,attempt INTEGER NOT NULL,
                    stage TEXT NOT NULL,dependency TEXT NOT NULL,
                    PRIMARY KEY(request_id,attempt,stage,dependency));
                CREATE TABLE IF NOT EXISTS agent_events_v39(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,request_id INTEGER NOT NULL,
                    attempt INTEGER NOT NULL,stage TEXT NOT NULL,event TEXT NOT NULL,
                    stamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            """)
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=3)
        db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()
    @staticmethod
    def _request(db,ident):
        return db.execute('SELECT * FROM conversation_requests WHERE id=?',(ident,)).fetchone()
    @staticmethod
    def _superseded(db,row):
        return bool(db.execute("""SELECT 1 FROM specification_amendments a
            JOIN conversation_requests c ON c.id=a.request_id
            WHERE c.chat_id=? AND c.project=? AND a.request_id>? LIMIT 1""",
            (row['chat_id'],row['project'],row['id'])).fetchone())
    @staticmethod
    def _event(db,ident,attempt,stage,event):
        db.execute('INSERT INTO agent_events_v39(request_id,attempt,stage,event) VALUES(?,?,?,?)',
                   (ident,attempt,stage,event))
    def recover(self):
        """After application restart, never replay a possibly completed native action."""
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT * FROM agent_batches_v39 WHERE state='running'").fetchall()
            for b in rows:
                ident,attempt=b['request_id'],b['attempt']
                db.execute("UPDATE agent_batches_v39 SET state='interrupted' WHERE request_id=?",(ident,))
                db.execute("""UPDATE agent_stages_v39 SET state='interrupted'
                    WHERE request_id=? AND attempt=? AND state IN ('queued','running')""",(ident,attempt))
                db.execute("""UPDATE conversation_requests SET state='failed',
                    detail='Creative task interrupted; inspect staged artifacts before explicit Retry'
                    WHERE id=? AND state IN ('pending','running')""",(ident,))
                self._event(db,ident,attempt,'batch','interrupted')
            return len(rows)
    def next_candidate(self,*,exclude_chat=None,priority=None):
        with self.db() as db:
            # Respect chat ordering; do not overtake a preceding unresolved
            # conversation in the same thread. Other threads are independent.
            rows=db.execute("""SELECT c.* FROM conversation_requests c
                WHERE c.state='pending' AND NOT EXISTS(
                    SELECT 1 FROM conversation_requests old
                    WHERE old.chat_id=c.chat_id AND old.project=c.project
                    AND old.id<c.id AND old.state IN ('pending','running','waiting_sources'))
                ORDER BY c.id LIMIT ?""",(512 if priority is not None else MAX_PENDING,)).fetchall()
            if priority is not None:rows=sorted((dict(r) for r in rows if priority.allowed(dict(r))),key=priority.key)
            for row in rows:
                if row['chat_id']!=exclude_chat and eligible(row):return dict(row)
            return None
    def next_foreground(self,*,priority=None):
        """First noncreative pending thread head; don't overtake a creative reply."""
        with self.db() as db:
            rows=db.execute("""SELECT c.* FROM conversation_requests c
                WHERE c.state='pending' AND NOT EXISTS(
                    SELECT 1 FROM conversation_requests old
                    WHERE old.chat_id=c.chat_id AND old.project=c.project
                    AND old.id<c.id AND old.state IN ('pending','running','waiting_sources'))
                ORDER BY c.id LIMIT ?""",(512 if priority is not None else MAX_PENDING,)).fetchall()
            if priority is not None:rows=sorted((dict(r) for r in rows if priority.allowed(dict(r))),key=priority.key)
            for row in rows:
                if not eligible(row):return dict(row)
            return None
    def start(self,ident):
        """Claim an explicit user request, not a model-authored permission."""
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=self._request(db,ident)
            if not row or row['state']!='pending' or not eligible(row):return False
            if self._superseded(db,row):
                db.execute("UPDATE conversation_requests SET state='failed',detail='Superseded creative request' WHERE id=?",(ident,))
                return False
            if db.execute("SELECT 1 FROM agent_batches_v39 WHERE state='running' LIMIT 1").fetchone():return False
            if db.execute("""SELECT 1 FROM conversation_requests WHERE chat_id=? AND project=? AND id<?
                AND state IN ('pending','running','waiting_sources') LIMIT 1""",
                (row['chat_id'],row['project'],ident)).fetchone():return False
            digest=binding(row)
            prior=db.execute('SELECT * FROM agent_batches_v39 WHERE request_id=?',(ident,)).fetchone()
            if prior:
                if prior['binding']!=digest:raise DelegationError('Creative request identity changed')
                # Existing Retry action is the only supported re-run of a lost
                # or failed attempt. New requests use fresh conversation IDs.
                if prior['state'] not in ('failed','interrupted') or row['detail']!='Retry requested by user':
                    db.execute("UPDATE conversation_requests SET state='failed',detail='Prior creative attempt exists; explicit Retry required' WHERE id=?",(ident,))
                    return False
                attempt=prior['attempt']+1
                db.execute("UPDATE agent_batches_v39 SET attempt=?,state='running' WHERE request_id=?",(attempt,ident))
            else:
                attempt=1
                db.execute("INSERT INTO agent_batches_v39 VALUES(?,?,?,'running')",(ident,digest,attempt))
            for stage,role,deps in (TEAM_STAGES if is_team_request(row['prompt']) else STAGES):
                db.execute("INSERT INTO agent_stages_v39 VALUES(?,?,?,?,'queued',NULL,NULL)",(ident,attempt,stage,role))
                db.executemany('INSERT INTO agent_edges_v39 VALUES(?,?,?,?)',[(ident,attempt,stage,d) for d in deps])
            db.execute("UPDATE conversation_requests SET state='running',detail='Independent creative assignment queued',updated_at=CURRENT_TIMESTAMP WHERE id=?",(ident,))
            self._event(db,ident,attempt,'batch','started')
            return True
    def _live(self,db,ident):
        row=self._request(db,ident)
        batch=db.execute('SELECT * FROM agent_batches_v39 WHERE request_id=?',(ident,)).fetchone()
        if not row or not batch or batch['state']!='running' or row['state']!='running' or binding(row)!=batch['binding'] or self._superseded(db,row):
            raise DelegationError('Assignment cancelled, superseded or no longer current')
        return row,batch
    def current(self,ident):
        try:
            with self.db() as db:self._live(db,ident)
            return True
        except (DelegationError,sqlite3.Error):return False
    def claim(self,ident,role):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,b=self._live(db,ident);attempt=b['attempt']
            if db.execute("SELECT 1 FROM agent_stages_v39 WHERE role=? AND state='running' LIMIT 1",(role,)).fetchone():return None
            stage=db.execute("""SELECT s.* FROM agent_stages_v39 s
                WHERE s.request_id=? AND s.attempt=? AND s.role=? AND s.state='queued'
                AND NOT EXISTS(SELECT 1 FROM agent_edges_v39 e
                    LEFT JOIN agent_stages_v39 d ON d.request_id=e.request_id
                    AND d.attempt=e.attempt AND d.stage=e.dependency
                    WHERE e.request_id=s.request_id AND e.attempt=s.attempt AND e.stage=s.stage
                    AND (d.state IS NULL OR d.state!='complete'))
                ORDER BY s.stage LIMIT 1""",(ident,attempt,role)).fetchone()
            if not stage:return None
            lease=uuid.uuid4().hex
            db.execute("UPDATE agent_stages_v39 SET state='running',lease=? WHERE request_id=? AND attempt=? AND stage=?",
                       (lease,ident,attempt,stage['stage']))
            self._event(db,ident,attempt,stage['stage'],'claimed')
            return {'request_id':ident,'attempt':attempt,'stage':stage['stage'],'role':role,'lease':lease,
                    'scope':scope(row,attempt),'brief':row['prompt']}
    def _leased(self,db,task):
        row,b=self._live(db,task['request_id'])
        s=db.execute("""SELECT * FROM agent_stages_v39 WHERE request_id=? AND attempt=?
            AND stage=? AND role=? AND lease=? AND state='running'""",
            (task['request_id'],task['attempt'],task['stage'],task['role'],task['lease'])).fetchone()
        if not s or task['attempt']!=b['attempt'] or task['scope']!=scope(row,b['attempt']) or task['brief']!=row['prompt']:
            raise DelegationError('Missing or stale exact task lease')
        return row,b,s
    def _artifact(self,folder,receipt,task):
        folder=Path(folder)
        if (folder.is_symlink() or folder.resolve().parent!=self.artifact_root
                or folder.parent.resolve()!=self.artifact_root):raise DelegationError('Artifact outside private staging')
        for name in ('score.mid','receipt.json','request.json'):
            p=folder/name
            if p.is_symlink() or not p.is_file() or p.stat().st_size>65536:raise DelegationError('Invalid staged artifact file')
        packet=json.loads((folder/'request.json').read_text('utf-8'))
        requester=task.get('requester','user')
        expected=request_packet(requester,task['scope'],task['brief'])
        if canonical_sha(packet)!=canonical_sha(expected):raise DelegationError('Artifact assignment mismatch')
        stored=json.loads((folder/'receipt.json').read_text('utf-8'))
        if canonical_sha(stored)!=canonical_sha(receipt):raise DelegationError('Stored artifact receipt mismatch')
        raw=(folder/'score.mid').read_bytes()
        if (receipt.get('status')!='artifact_created' or receipt.get('artifact')!='score.mid'
                or receipt.get('assigned_role')!='multimedia' or receipt.get('requester')!=requester
                or receipt.get('scope')!=task['scope'] or receipt.get('project_publication_authorized') is not False
                or receipt.get('native_inference_verified') is not True
                or receipt.get('assignment_sha256')!=validate_creative_assignment(expected)
                or hashlib.sha256(raw).hexdigest()!=receipt.get('sha256') or not raw.startswith(b'MThd')):
            raise DelegationError('Staged artifact or native receipt invalid')
        return {'folder':str(folder.resolve()),'receipt':receipt}
    def composed(self,task,folder,receipt):
        if task['stage']!='compose' or task['role']!='multimedia':raise DelegationError('Wrong stage')
        data=self._artifact(folder,receipt,task)
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._leased(db,task)
            db.execute("UPDATE agent_stages_v39 SET state='complete',receipt=? WHERE request_id=? AND attempt=? AND stage='compose'",
                       (json.dumps(data),task['request_id'],task['attempt']))
            self._event(db,task['request_id'],task['attempt'],'compose','complete')
    def verify_and_deliver(self,task):
        if task['stage']!='verify' or task['role']!='host':raise DelegationError('Wrong stage')
        with self.db() as db:
            self._leased(db,task)
            data=json.loads(db.execute("""SELECT receipt FROM agent_stages_v39
                WHERE request_id=? AND attempt=? AND stage='compose' AND state='complete'""",
                (task['request_id'],task['attempt'])).fetchone()[0])
        verified=self._artifact(data['folder'],data['receipt'],task)
        receipt=verified['receipt']
        answer=(f"Fourth intelligent AI created a MIDI draft: {Path(verified['folder'])/'score.mid'}\n"
                f"{receipt['notes']} notes, {receipt['bpm']} BPM.\n"
                "Native generation and structural checks passed; musical quality and project publication remain unapproved.")
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._leased(db,task)
            db.execute("UPDATE agent_stages_v39 SET state='complete',receipt=? WHERE request_id=? AND attempt=? AND stage='verify'",
                       (json.dumps({'artifact_sha256':receipt['sha256']}),task['request_id'],task['attempt']))
            db.execute("UPDATE agent_batches_v39 SET state='complete' WHERE request_id=?",(task['request_id'],))
            db.execute("""UPDATE conversation_requests SET state='responded',response=?,detail='Independent creative task completed',
                updated_at=CURRENT_TIMESTAMP WHERE id=? AND state='running'""",(answer,task['request_id']))
            self._event(db,task['request_id'],task['attempt'],'verify','delivered')
        return answer
    def fail(self,ident,reason,*,interrupted=False):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            b=db.execute("SELECT * FROM agent_batches_v39 WHERE request_id=? AND state='running'",(ident,)).fetchone()
            if not b:return False
            state='interrupted' if interrupted else 'failed'
            db.execute('UPDATE agent_batches_v39 SET state=? WHERE request_id=?',(state,ident))
            db.execute("UPDATE agent_stages_v39 SET state=? WHERE request_id=? AND attempt=? AND state IN ('queued','running')",
                       (state,ident,b['attempt']))
            db.execute("UPDATE conversation_requests SET state='failed',detail=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND state='running'",
                       (str(reason)[:400],ident))
            self._event(db,ident,b['attempt'],'batch',state)
            return True
    def summary(self,ident):
        with self.db() as db:
            b=db.execute('SELECT * FROM agent_batches_v39 WHERE request_id=?',(ident,)).fetchone()
            if not b:return None
            return {'state':b['state'],'attempt':b['attempt'],'stages':[dict(r) for r in db.execute(
                'SELECT stage,role,state FROM agent_stages_v39 WHERE request_id=? AND attempt=? ORDER BY stage',(ident,b['attempt']))]}
