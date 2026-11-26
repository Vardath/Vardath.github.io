"""Durable, bounded corrective assignments for already-approved source work.

JANUS proposes guidance; Sentinel reviews the exact proposal. The desktop may
schedule ONE fresh inference per approved file. No new file, dependency edge,
tool invocation, grant, specification revision or test acceptance is implied.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
from .agent_contract import canonical_sha
from .structured_source import strict_json
from .worker_reports import observe_granite_reports,saved_dependency_catalog
from .reasoning_council import sha

KINDS=('missing_dependency','interface_conflict','evidence_gap')
WAIT='Worker dependency awaiting coordination: '
READY='Reviewed corrective inference: '

def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS corrective_assignments_v50(
        report_id TEXT PRIMARY KEY, job_id INTEGER NOT NULL, step_id INTEGER NOT NULL,
        contract_sha TEXT NOT NULL, proposal TEXT NOT NULL, proposal_sha TEXT NOT NULL,
        verdict TEXT, verdict_sha TEXT, state TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

def parse(answer,*,review=False):
    if not isinstance(answer,str) or len(answer)>1800:raise ValueError('Invalid coordination response')
    obj=strict_json(answer.strip())
    fields={'decision','reason'} if review else {'decision','guidance','reason'}
    decisions=('accept','reject') if review else ('retry','hold')
    if not isinstance(obj,dict) or obj.get('decision') not in decisions:
        raise ValueError('Invalid corrective decision schema')
    keys=set(obj)
    if keys!=fields:
        if review or obj['decision']!='retry' or keys!=fields|{'evidence_path'}:
            raise ValueError('Invalid corrective decision schema')
        from .inspection_exclusions import normalized_relative
        path=obj['evidence_path']
        if not isinstance(path,str) or len(path)>240 or any(ord(c)<32 for c in path):
            raise ValueError('Invalid corrective evidence path')
        normalized_relative(path)
        if path!=path.strip() or '\\' in path:
            raise ValueError('Require exact project-relative evidence path')
    for k in fields-{'decision'}:
        v=obj[k]
        if not isinstance(v,str) or len(v)>(360 if k=='guidance' else 300) or any(ord(c)<32 for c in v):
            raise ValueError('Invalid bounded corrective decision')
        obj[k]=v.strip()
    if not obj['reason'] or (not review and bool(obj['guidance'])!=(obj['decision']=='retry')):
        raise ValueError('Incomplete corrective decision')
    return obj

def read(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=.5)
    db.row_factory=sqlite3.Row
    return db

def write(path):
    db=sqlite3.connect(path,timeout=2)
    db.row_factory=sqlite3.Row
    return db

def current(path,report_id):
    return next((r for r in observe_granite_reports(path,receipt_sha=report_id)['reports'] if r['receipt_sha']==report_id),None)

def eligible(path,item):
    if not item or item['sender']!='implementation' or item['report']['kind'] not in KINDS:return False
    try:
        with closing(read(path)) as db:
            from .branch_holds import coordination_open
            if not coordination_open(db,item['job_id'],item['receipt_sha']):return False
            return not db.execute("""SELECT 1 FROM corrective_assignments_v50 WHERE report_id=?
                OR (job_id=? AND step_id=? AND state IN ('queued','consumed'))""",
                (item['receipt_sha'],item['job_id'],item['step_id'])).fetchone()
    except (sqlite3.Error,OSError):return False

def binding(item,decision):
    return {'report_id':item['receipt_sha'],'contract_sha':item['contract_sha'],
            'job_id':item['job_id'],'step_id':item['step_id'],'decision':decision,
            'requester':'janus','reviewer':'sentinel','assignee':'implementation',
            'authority':False,'verified':False}

def propose(path,item,answer):
    decision=parse(answer)
    fresh=current(path,item['receipt_sha'])
    if fresh!=item or not eligible(path,item):return False
    evidence_path=decision.get('evidence_path')
    if evidence_path and not any(r['path']==evidence_path for r in saved_dependency_catalog(path,item)):
        return False
    proposal=binding(item,decision)
    with closing(write(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        from .branch_holds import coordination_open
        if not coordination_open(db,item['job_id'],item['receipt_sha']):return False
        if db.execute("""SELECT 1 FROM corrective_assignments_v50 WHERE report_id=?
                OR (job_id=? AND step_id=? AND state IN ('queued','consumed'))""",
                (item['receipt_sha'],item['job_id'],item['step_id'])).fetchone():return False
        db.execute("""INSERT INTO corrective_assignments_v50(report_id,job_id,step_id,contract_sha,proposal,proposal_sha,state)
                VALUES(?,?,?,?,?,?,?)""",(item['receipt_sha'],item['job_id'],item['step_id'],item['contract_sha'],
                json.dumps(proposal,sort_keys=True),canonical_sha(proposal),'proposed' if decision['decision']=='retry' else 'held'))
        return True

def checked(row):
    p=json.loads(row['proposal'])
    if canonical_sha(p)!=row['proposal_sha'] or any(p[k]!=row[k] for k in ('report_id','job_id','step_id','contract_sha')):
        raise ValueError('Corrective proposal identity changed')
    if binding({'receipt_sha':p['report_id'],'contract_sha':p['contract_sha'],'job_id':p['job_id'],'step_id':p['step_id']},
               parse(json.dumps(p['decision'])))!=p:raise ValueError('Invalid corrective proposal')
    if p['decision']['decision']!='retry':raise ValueError('Not a retry proposal')
    return p

def checked_review(row):
    p=checked(row)
    v=json.loads(row['verdict'])
    if v!={'proposal_sha':row['proposal_sha'],'reviewer':'sentinel',
           'decision':parse(json.dumps(v['decision']),review=True)} or canonical_sha(v)!=row['verdict_sha'] or v['decision']['decision']!='accept':
        raise ValueError('No exact independently accepted corrective proposal')
    return p

def pending_review(path):
    try:
        with closing(read(path)) as db:
            from .branch_holds import coordination_open
            rows=[dict(r) for r in db.execute("""SELECT c.* FROM corrective_assignments_v50 c JOIN jobs j ON j.id=c.job_id
                WHERE c.state='proposed' AND j.state IN ('needs_input','queued','running') ORDER BY c.rowid LIMIT 64""")
                  if coordination_open(db,r['job_id'],r['report_id'])][:8]
        for row in rows:
            item=current(path,row['report_id'])
            if not item:continue
            if checked(row)['contract_sha']!=item['contract_sha']:continue
            return item,row
    except (sqlite3.Error,OSError,ValueError,KeyError,TypeError):pass
    return None

def review(path,item,row,answer):
    decision=parse(answer,review=True)
    if current(path,item['receipt_sha'])!=item:return False
    p=checked(row)
    if p['report_id']!=item['receipt_sha'] or p['contract_sha']!=item['contract_sha']:return False
    verdict={'proposal_sha':row['proposal_sha'],'reviewer':'sentinel','decision':decision}
    with closing(write(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        from .branch_holds import coordination_open
        if not coordination_open(db,row['job_id'],row['report_id']):return False
        return bool(db.execute("""UPDATE corrective_assignments_v50 SET verdict=?,verdict_sha=?,state=?
                WHERE report_id=? AND proposal_sha=? AND proposal=? AND state='proposed'""",
                (json.dumps(verdict,sort_keys=True),canonical_sha(verdict),'approved' if decision['decision']=='accept' else 'rejected',
                row['report_id'],row['proposal_sha'],row['proposal'])).rowcount)

def invalidate_review(path,row):
    """A malformed response cannot count as acceptance or a model rejection."""
    with closing(write(path)) as db,db:
        db.execute("UPDATE corrective_assignments_v50 SET state='invalid' WHERE report_id=? AND proposal_sha=? AND state='proposed'",
                   (row['report_id'],row['proposal_sha']))

def approved(path):
    try:
        with closing(read(path)) as db:
            from .branch_holds import coordination_open
            return [dict(r) for r in db.execute("""SELECT c.* FROM corrective_assignments_v50 c JOIN jobs j ON j.id=c.job_id
                WHERE c.state='approved' AND j.state IN ('queued','needs_input') ORDER BY c.rowid LIMIT 64""")
                if coordination_open(db,r['job_id'],r['report_id'],dispatch=True)][:8]
    except (sqlite3.Error,OSError):return []

def requeue(jobs,row,*,validate,validate_evidence=None):
    """Atomically reserve the single retry with the original blocked job state."""
    p=checked_review(row);item=current(jobs.path,row['report_id'])
    if not item or item['contract_sha']!=p['contract_sha'] or not validate(item):return False
    evidence_path=p['decision'].get('evidence_path')
    if evidence_path:
        if not any(r['path']==evidence_path for r in saved_dependency_catalog(jobs.path,item)):
            return False
        if validate_evidence is None or not validate_evidence(item,evidence_path):return False
    # The explicit graph host validates the exact ready node, rather than
    # interpreting the first planned stage as the only possible target.
    explicit=False
    try:
        from .task_graph import TaskGraphStore
        graph=TaskGraphStore(jobs.path.parent/'task-graph.sqlite3')
        if graph.explicit(p['job_id']):
            explicit=True
            current_job=jobs.get(p['job_id'])
            if not graph.ready_step(current_job,jobs.steps(p['job_id']),preferred=p['step_id']):return False
    except (OSError,ValueError,sqlite3.Error):return False
    with jobs._conn() as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        fresh=db.execute("SELECT * FROM corrective_assignments_v50 WHERE report_id=?",(row['report_id'],)).fetchone()
        if not fresh or dict(fresh)!=row or fresh['state']!='approved':return False
        if db.execute("""SELECT 1 FROM corrective_assignments_v50 WHERE job_id=? AND step_id=?
                         AND state IN ('queued','consumed')""",(p['job_id'],p['step_id'])).fetchone():return False
        step=(db.execute("SELECT id FROM job_steps WHERE job_id=? AND id=? AND state='planned'",(p['job_id'],p['step_id'])).fetchone()
              if explicit else db.execute("SELECT id FROM job_steps WHERE job_id=? AND state='planned' ORDER BY sequence LIMIT 1",(p['job_id'],)).fetchone())
        if not step or step[0]!=p['step_id']:return False
        from .branch_holds import coordination_open
        if not coordination_open(db,p['job_id'],p['report_id'],dispatch=True):return False
        if not db.execute("""UPDATE jobs SET state='queued',detail=?,updated_at=CURRENT_TIMESTAMP WHERE id=?
                 AND state IN ('queued','needs_input')""",(READY+row['report_id'],p['job_id'])).rowcount:return False
        db.execute("UPDATE corrective_assignments_v50 SET state='queued' WHERE report_id=?",(row['report_id'],))
        db.execute("INSERT INTO job_events(job_id,note) VALUES(?,?)",(p['job_id'],'JANUS proposed and Sentinel reviewed one corrective inference; no new authority.'))
    jobs.journal(p['job_id'])
    return True

def queued_target(jobs,queued_job):
    """Read the exact reviewed retry target before assigning a ready node."""
    detail=queued_job['detail']
    if not detail.startswith(READY):return None
    with closing(read(jobs.path)) as db:
        row=db.execute("SELECT * FROM corrective_assignments_v50 WHERE report_id=? AND state='queued'",(detail[len(READY):],)).fetchone()
    if not row:raise ValueError('Missing queued corrective assignment')
    packet=checked_review(row)
    if packet['job_id']!=queued_job['id']:raise ValueError('Corrective job identity changed')
    return packet['step_id']


def consume(jobs,queued_job,contract,*,resolve_evidence=None):
    """After the normal new assignment checks, bind and consume the exact packet."""
    detail=queued_job['detail']
    if not detail.startswith(READY):return ''
    ident=detail[len(READY):]
    def current_packet(db):
        row=db.execute("SELECT * FROM corrective_assignments_v50 WHERE report_id=? AND state='queued'",(ident,)).fetchone()
        if not row:raise ValueError('Missing corrective assignment')
        p=checked_review(row)
        if p['job_id']!=queued_job['id'] or p['contract_sha']!=canonical_sha(contract) or p['step_id']!=contract['step_id']:
            raise ValueError('Corrective assignment scope changed')
        job=db.execute("SELECT state FROM jobs WHERE id=?",(p['job_id'],)).fetchone()
        if not job or job[0]!='running':raise ValueError('Corrective job no longer running')
        return dict(row),p
    # Resolve evidence without a job-store write lock. The resolver may read
    # grants, the job store, and the graph ledger or record an evidence receipt.
    # A stale receipt alone never authorizes dispatch or publication.
    with closing(read(jobs.path)) as db:
        expected,p=current_packet(db)
    evidence=''
    if p['decision'].get('evidence_path'):
        if resolve_evidence is None:
            raise ValueError('Corrective inference requires actual dependency evidence')
        evidence=resolve_evidence(p['decision']['evidence_path'])
        if not isinstance(evidence,str) or not evidence or len(evidence)>2100:
            raise ValueError('Requested corrective dependency is unavailable or too large')
    with jobs._conn() as db:
        db.row_factory=sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        fresh,p=current_packet(db)
        if fresh!=expected:raise ValueError('Corrective proposal changed during evidence acquisition')
        db.execute("UPDATE corrective_assignments_v50 SET state='consumed' WHERE report_id=?",(ident,))
    return ('\n\nINDEPENDENTLY REVIEWED CORRECTIVE GUIDANCE (advisory, not a specification change; '
            'do not invent missing inputs or tools): '+p['decision']['guidance']+
            '\nPreserve the original approved file task and all requirements.'+evidence)

def observe(path):
    """Bounded read-only status evidence for both independent societies."""
    try:
        with closing(read(path)) as db:
            rows=db.execute("""SELECT c.report_id,c.job_id,c.step_id,c.state,c.proposal_sha,c.verdict_sha,
                       j.state AS job_state,j.detail AS job_detail
                FROM corrective_assignments_v50 c JOIN jobs j ON j.id=c.job_id
                ORDER BY c.rowid DESC LIMIT 12""").fetchall()
        result=[]
        for row in rows:
            active=(row['state'] in ('proposed','approved') and row['job_state']=='needs_input'
                    and row['job_detail']==WAIT+row['report_id']) or (
                    row['state']=='queued' and row['job_state']=='queued'
                    and row['job_detail']==READY+row['report_id'])
            result.append({'report_id':row['report_id'],'job_id':row['job_id'],'step_id':row['step_id'],
                'state':row['state'],'job_state':row['job_state'],'active':active,
                'proposal_sha':row['proposal_sha'],'verdict_sha':row['verdict_sha'],
                'authority':False,'verified':False})
        return {'available':True,'recent':result}
    except (OSError,sqlite3.Error):return {'available':False,'recent':[]}
