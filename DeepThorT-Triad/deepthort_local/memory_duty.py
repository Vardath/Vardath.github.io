"""Independent memory duties and a scoped, durable advisory exchange.

Discovery runs on the Memory worker's thread. The existing approved job and
conversation stores remain authoritative; reports are observations, never
new jobs, permissions, or automatic proof of current source behaviour.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import time
from .memory_governor import canonical,evidence_eligible
from .reasoning_council import sha

STATES=('queued','running','waiting_verification','waiting_repair')
# A blocked approved job can still benefit from independent memory research.
# Keep the original live_scope default for unrelated callers.
DUTY_STATES=(*STATES,'needs_input')
SCAN_JOBS=4
LOOKAHEAD=2
MAX_BACKLOG=128
OFFER_DUTIES=8
REPORT_TTL=600
MAX_REPORTS=256

def reader(path,*,timeout=.4):
    db=sqlite3.connect(Path(path).resolve(strict=True).as_uri()+'?mode=ro',uri=True,timeout=timeout)
    db.row_factory=sqlite3.Row
    return db

def live_scope(job_db,job_id,request_id,*,states=STATES,timeout=.4):
    """Check the exact approved job/request pair independently of GUI selection."""
    with closing(reader(job_db,timeout=timeout)) as db:
        row=db.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()
        if not row or row['mode']!='build' or row['state'] not in states or not row['approval_key']:
            return None
        job=dict(row)
    with closing(reader(Path(job_db).parent/'conversations.sqlite3',timeout=timeout)) as db:
        req=db.execute("SELECT id,project,chat_id,prompt,state,mode FROM conversation_requests WHERE id=?",(request_id,)).fetchone()
        if not req or req['state']!='responded' or req['mode']!='draft_plan' or (req['project'],req['chat_id'])!=(job['project'],job['chat_id']):
            return None
        key=job['approval_key']
        if key.startswith('draft:'):
            draft=db.execute("SELECT request_id,queued_job_id,state,original_prompt FROM project_drafts WHERE id=?",(key[6:],)).fetchone()
            if not draft or (draft['request_id'],draft['queued_job_id'],draft['state'],draft['original_prompt'])!=(request_id,job_id,'approved',req['prompt']) or job['prompt']!=req['prompt']:
                return None
        elif key.startswith('milestone:'):
            parts=key.split(':')
            if len(parts)!=4 or parts[1]!=str(request_id) or parts[3]!=sha(req['prompt'])[:16]:return None
        else:return None
        if db.execute("""SELECT 1 FROM specification_amendments a JOIN conversation_requests c ON c.id=a.request_id
            WHERE c.chat_id=? AND c.project=? AND a.request_id>? LIMIT 1""",(job['chat_id'],job['project'],request_id)).fetchone():
            return None
    return {'job_id':job_id,'request_id':request_id,'project':job['project'],'chat_id':job['chat_id'],
            'original':req['prompt'],'spec_sha':sha(req['prompt']),'approval_key':key,
            'job_sha':sha(job['prompt'])}

def signature(scope):
    return {k:v for k,v in scope.items() if k!='original'}

class MemoryDuty:
    def __init__(self,job_db,resolve,*,clock=time.time):
        self.job_db=Path(job_db)
        self.path=self.job_db.parent/'memory-duty.sqlite3'
        self.resolve=resolve
        self.clock=clock
        self.cursor=0
        with closing(sqlite3.connect(self.path,timeout=2)) as db,db:
            db.executescript("""CREATE TABLE IF NOT EXISTS memory_duties_v47(
              work_id TEXT PRIMARY KEY,job_id INTEGER NOT NULL,request_id INTEGER NOT NULL,
              scope TEXT NOT NULL,focus TEXT NOT NULL,phase TEXT NOT NULL,
              outcome TEXT NOT NULL,findings TEXT NOT NULL,receipt_sha TEXT NOT NULL,
              completed REAL NOT NULL);
              CREATE INDEX IF NOT EXISTS memory_duty_job_v47 ON memory_duties_v47(job_id,completed);
              CREATE TABLE IF NOT EXISTS memory_pending_v54(
                work_id TEXT PRIMARY KEY,job_id INTEGER NOT NULL,request_id INTEGER NOT NULL,
                scope TEXT NOT NULL,step TEXT NOT NULL,watermark INTEGER NOT NULL,
                created REAL NOT NULL,last_offer INTEGER NOT NULL);
              CREATE INDEX IF NOT EXISTS memory_pending_offer_v54
                ON memory_pending_v54(last_offer,created);""")

    def _current(self,job):
        # Resolver calls master_for_job, including exact hierarchical scope
        # reconciliation. Read-only cross-process checks add amendment guard.
        req_id,original=self.resolve(job)
        current=live_scope(self.job_db,job['id'],req_id,states=DUTY_STATES)
        if not current or current['original']!=original or current['job_sha']!=sha(job['prompt']):
            return None
        return current

    def _still_current(self,bound):
        try:
            current=live_scope(self.job_db,bound['job_id'],bound['request_id'],states=DUTY_STATES)
            return bool(current and signature(current)==signature(bound))
        except (OSError,ValueError,sqlite3.Error):return False

    def _discover(self):
        """Read bounded upcoming work from the existing approved job store."""
        with closing(reader(self.job_db)) as db:
            marks=','.join('?' for _ in DUTY_STATES)
            rows=[dict(r) for r in db.execute(
                f"SELECT * FROM jobs WHERE id>? AND mode='build' AND approval_key IS NOT NULL AND state IN ({marks}) ORDER BY id LIMIT ?",
                (self.cursor,*DUTY_STATES,SCAN_JOBS))]
            if not rows:
                self.cursor=0
                rows=[dict(r) for r in db.execute(
                    f"SELECT * FROM jobs WHERE mode='build' AND approval_key IS NOT NULL AND state IN ({marks}) ORDER BY id LIMIT ?",
                    (*DUTY_STATES,SCAN_JOBS))]
            if rows:self.cursor=rows[-1]['id']
            result=[]
            for job in rows:
                try:bound=self._current(job)
                except (OSError,ValueError,KeyError,TypeError,sqlite3.Error):continue
                if not bound:continue
                steps=[dict(r) for r in db.execute("""SELECT id,path,description,state FROM job_steps
                    WHERE job_id=? AND state IN ('planned','proposed') ORDER BY sequence LIMIT ?""",(job['id'],LOOKAHEAD))]
                if not steps and job['state'] in ('waiting_verification','waiting_repair','needs_input'):
                    steps=[{'id':0,'path':'verification','description':'Check required tests and diagnose observed failures','state':job['state']}]
                watermark=db.execute("""SELECT COALESCE(MAX(n.id),0) FROM task_memory_notes n JOIN jobs j ON j.id=n.job_id
                    WHERE j.project=? AND j.chat_id=? AND n.spec_sha=?""",
                    (bound['project'],bound['chat_id'],bound['spec_sha'])).fetchone()[0]
                for step in steps:
                    scope=signature(bound)
                    work_id=sha(canonical([scope,step,watermark]))
                    result.append((work_id,bound['job_id'],bound['request_id'],canonical(scope),canonical(step),watermark))
        return result

    def _admit(self,discovered):
        """Persist admitted work before offering it to the bounded observer queue."""
        with closing(sqlite3.connect(self.path,timeout=2)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            db.execute("""DELETE FROM memory_pending_v54 WHERE work_id IN
                (SELECT work_id FROM memory_duties_v47)""")
            count,tail=db.execute("SELECT COUNT(*),COALESCE(MAX(last_offer),0) FROM memory_pending_v54").fetchone()
            for work in discovered:
                if count>=MAX_BACKLOG:break
                if db.execute("SELECT 1 FROM memory_duties_v47 WHERE work_id=?",(work[0],)).fetchone():continue
                # New work queues behind previously offered work; no silent eviction.
                count+=db.execute("INSERT OR IGNORE INTO memory_pending_v54 VALUES(?,?,?,?,?,?,?,?)",
                                  (*work,self.clock(),tail)).rowcount

    def _packet(self,row):
        """Return (packet,stale). A paused job keeps its admitted work."""
        scope=json.loads(row['scope']);step=json.loads(row['step'])
        if (scope['job_id']!=row['job_id'] or scope['request_id']!=row['request_id']
            or sha(canonical([scope,step,row['watermark']]))!=row['work_id']):
            return None,True
        bound=live_scope(self.job_db,row['job_id'],row['request_id'],states=(*DUTY_STATES,'paused'))
        if not bound or signature(bound)!=scope:return None,True
        with closing(reader(self.job_db)) as db:
            job=db.execute("SELECT state FROM jobs WHERE id=?",(row['job_id'],)).fetchone()
            if not job:return None,True
            if job['state']=='paused':return None,False
            if job['state'] not in DUTY_STATES:return None,True
            if step['id']:
                actual=db.execute("SELECT path,description FROM job_steps WHERE id=? AND job_id=?",
                                  (step['id'],row['job_id'])).fetchone()
                if not actual or (actual['path'],actual['description'])!=(step['path'],step['description']):
                    return None,True
        # A stage advancing from planned to saved does not invalidate late
        # research for an otherwise unchanged active project.
        return dict(project=bound['project'],chat_id=bound['chat_id'],original=bound['original'],
                    job_id=bound['job_id'],focus=(step['path']+': '+step['description'])[:500],
                    phase='anticipatory_recall',scope='duty:'+row['work_id'],
                    cancelled=lambda b=bound:not self._still_current(b)),False

    def scan(self):
        """Memory-thread only: bounded discovery, durable admission, fair replay.

        Offers rotate across admitted work, even if the in-memory observer
        queue is full or a recall is deferred. No inference or foreground wait.
        """
        self._admit(self._discover())
        with closing(reader(self.path)) as db:
            rows=[dict(r) for r in db.execute("""SELECT * FROM memory_pending_v54
                ORDER BY last_offer,created,rowid LIMIT ?""",(OFFER_DUTIES,))]
        packets=[];stale=[]
        for row in rows:
            try:packet,obsolete=self._packet(row)
            except (ValueError,TypeError,KeyError):packet,obsolete=None,True
            except (OSError,sqlite3.Error):packet,obsolete=None,False
            if obsolete:stale.append(row['work_id'])
            elif packet:packets.append(packet)
        # Do not hold a memory write transaction while inspecting other stores.
        # Rotate paused/transient offers too, so unrelated duties remain eligible.
        with closing(sqlite3.connect(self.path,timeout=2)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            db.executemany("DELETE FROM memory_pending_v54 WHERE work_id=?",[(x,) for x in stale])
            tail=db.execute("SELECT COALESCE(MAX(last_offer),0) FROM memory_pending_v54").fetchone()[0]
            for offset,row in enumerate(rows,1):
                db.execute("UPDATE memory_pending_v54 SET last_offer=? WHERE work_id=?",
                           (tail+offset,row['work_id']))
        return packets

    def complete(self,packet,selected):
        """Persist selection/no-match, not new knowledge claims or authorizations."""
        if packet.get('phase')!='anticipatory_recall' or not packet.get('scope','').startswith('duty:'):return
        work_id=packet['scope'][5:]
        if len(work_id)!=64:return
        with closing(reader(self.path)) as db:
            pending=db.execute("SELECT * FROM memory_pending_v54 WHERE work_id=?",(work_id,)).fetchone()
        if not pending:return
        expected,stale=self._packet(dict(pending))
        if stale or not expected or any(expected[k]!=packet.get(k) for k in
                ('project','chat_id','original','job_id','focus','phase','scope')):return
        bound=live_scope(self.job_db,pending['job_id'],pending['request_id'],states=DUTY_STATES)
        if not bound or signature(bound)!=json.loads(pending['scope']):return
        if len(selected)>3 or any(not evidence_eligible(x) for x in selected):raise ValueError('Invalid memory duty evidence')
        record={'work_id':work_id,'scope':signature(bound),'focus':packet['focus'],'phase':packet['phase'],
                'outcome':'findings' if selected else 'no_relevant_evidence','findings':selected}
        with closing(sqlite3.connect(self.path,timeout=2)) as db,db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute("SELECT 1 FROM memory_pending_v54 WHERE work_id=?",(work_id,)).fetchone():return
            db.execute("""INSERT OR IGNORE INTO memory_duties_v47 VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (work_id,bound['job_id'],bound['request_id'],canonical(signature(bound)),packet['focus'],
                 packet['phase'],record['outcome'],canonical(selected),sha(canonical(record)),self.clock()))
            db.execute("DELETE FROM memory_pending_v54 WHERE work_id=?",(work_id,))
            db.execute("""DELETE FROM memory_duties_v47 WHERE work_id IN
                (SELECT work_id FROM memory_duties_v47 ORDER BY completed DESC,work_id LIMIT -1 OFFSET ?)""",(MAX_REPORTS,))

    def has_reports(self,job_id):
        if not job_id:return False
        try:
            with closing(reader(self.path,timeout=.05)) as db:
                return bool(db.execute("SELECT 1 FROM memory_duties_v47 WHERE job_id=? AND completed>=? AND outcome='findings' LIMIT 1",
                                       (job_id,self.clock()-REPORT_TTL)).fetchone())
        except (OSError,sqlite3.Error):return False

    def advice_records(self,*,project,chat_id,original,job_id,current):
        if not job_id or not current:return []
        with closing(reader(self.path,timeout=.05)) as db:
            rows=[dict(r) for r in db.execute("""SELECT * FROM memory_duties_v47
                WHERE job_id=? AND completed>=? AND outcome='findings'
                ORDER BY completed DESC,work_id LIMIT 16""",(job_id,self.clock()-REPORT_TTL))]
        result=[];seen=set();scopes={}
        for row in rows:
            req=row['request_id']
            if req not in scopes:
                scopes[req]=live_scope(self.job_db,job_id,req,states=DUTY_STATES,timeout=.05)
            bound=scopes[req]
            if not bound or bound['original']!=original or (bound['project'],bound['chat_id'])!=(str(project),chat_id):continue
            findings=json.loads(row['findings'])
            record={'work_id':row['work_id'],'scope':signature(bound),'focus':row['focus'],'phase':row['phase'],
                    'outcome':row['outcome'],'findings':findings}
            if signature(bound)!=json.loads(row['scope']) or sha(canonical(record))!=row['receipt_sha']:continue
            for finding in findings:
                if finding['id'] not in seen and current.get(finding['id'])==finding and evidence_eligible(finding):
                    result.append(finding);seen.add(finding['id'])
                if len(result)>=3:return result
        return result

def observed_record(db,bound,item):
    """Read-only evidence check for journal and step records. Other receipts
    remain opaque references until the existing governed advice checkpoint."""
    ident=item['id']
    if len(ident)<2 or not ident[1:].isdigit():return None
    if ident.startswith('N'):
        row=db.execute("""SELECT n.* FROM task_memory_notes n JOIN jobs j ON j.id=n.job_id
            WHERE n.id=? AND j.project=? AND j.chat_id=? AND n.spec_sha=?""",
            (int(ident[1:]),bound['project'],bound['chat_id'],bound['spec_sha'])).fetchone()
        if not row:return None
        from .memory_consolidation import recall_group
        actual=recall_group(db,row,bound['project'],bound['chat_id'],bound['spec_sha']) or {
            'id':ident,'kind':'historical_'+row['role'],'focus':row['focus'][:100],
            'observation':row['note'][:220],'evidence':row['evidence_sha'][:64]}
    elif ident.startswith('S'):
        row=db.execute("SELECT id,path,description,state,outcome FROM job_steps WHERE id=? AND job_id=? AND state IN ('saved','verified','failed')",
                       (int(ident[1:]),bound['job_id'])).fetchone()
        if not row:return None
        actual={'id':ident,'kind':'historical_queue_state','focus':row['path'][:100],
                'observation':(row['state']+': '+row['outcome'])[:220],'evidence':sha(canonical(dict(row)))}
    elif ident.startswith(('T','M')):
        return {'id':ident,'evidence':item['evidence'],'scope':'Historical receipt reference; recheck at scoped review'}
    else:return None
    if actual!=item or not evidence_eligible(actual):return None
    return {'id':ident,'evidence':actual['evidence'],'observation':actual['observation']}

def observe_memory_duties(job_db,*,clock=time.time):
    """Both societies independently read exact, current, advisory report receipts.

    Journal findings are read-only revalidated and presented as scoped historical
    observations. Tool references stay opaque until the existing governed advice
    checkpoint. No index maintenance or inference occurs in either society.
    """
    empty={'available':False,'reports':[]}
    try:
        path=Path(job_db).parent/'memory-duty.sqlite3'
        with closing(reader(path)) as db:
            rows=[dict(r) for r in db.execute("""SELECT * FROM memory_duties_v47
                WHERE completed>=? AND outcome='findings' ORDER BY completed DESC,work_id LIMIT 16""",(clock()-REPORT_TTL,))]
        result=[]
        for row in rows:
            bound=live_scope(job_db,row['job_id'],row['request_id'],states=DUTY_STATES)
            if not bound or signature(bound)!=json.loads(row['scope']):continue
            findings=json.loads(row['findings'])
            record={'work_id':row['work_id'],'scope':signature(bound),'focus':row['focus'],'phase':row['phase'],
                    'outcome':row['outcome'],'findings':findings}
            if sha(canonical(record))!=row['receipt_sha'] or not 1<=len(findings)<=3:continue
            with closing(reader(job_db)) as source:
                checked=[observed_record(source,bound,v) for v in findings]
            if any(v is None for v in checked):continue
            result.append({'job_id':row['job_id'],'request_id':row['request_id'],
                'scope_sha':sha(canonical(signature(bound))),'receipt_sha':row['receipt_sha'],
                'records':checked,
                'sender':'memory','recipients':['janus','sentinel'],'authority':False})
            if len(result)>=4:break
        return {'available':True,'reports':result}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return empty


def inspection_records(path,project,limit=80):
    """Bounded historical receipt metadata for the selected workspace only.

    Does not rerank, refresh the index, expose unrelated text, or claim that
    the receipt is still eligible for delivery. Relevance remains advisory.
    """
    if not project or project=='(general)':return []
    limit=max(1,min(100,int(limit)))
    result=[]
    with closing(reader(path,timeout=.15)) as db:
        rows=db.execute("""SELECT work_id,job_id,request_id,scope,focus,phase,outcome,findings,
                         receipt_sha,completed FROM memory_duties_v47
                         ORDER BY completed DESC,work_id LIMIT ?""",(MAX_REPORTS,))
        for row in rows:
            try:
                scope=json.loads(row['scope'])
                if scope.get('project')!=str(project):continue
                findings=json.loads(row['findings'])
                record={'work_id':row['work_id'],'scope':scope,'focus':row['focus'],'phase':row['phase'],
                        'outcome':row['outcome'],'findings':findings}
                if not isinstance(findings,list) or sha(canonical(record))!=row['receipt_sha']:continue
                result.append({'work_id':row['work_id'],'job_id':row['job_id'],
                    'request_id':row['request_id'],'focus':row['focus'],'phase':row['phase'],
                    'outcome':row['outcome'],'finding_count':len(findings),'receipt_sha':row['receipt_sha'],
                    'completed':row['completed'],'findings':findings})
                if len(result)>=limit:break
            except (ValueError,TypeError,AttributeError):continue
    return result
