"""Branch-local dependency holds in the authoritative existing job store.

Only a current typed abandoned Granite assignment can park its exact node.
An independent node remains available; a parked node needs the existing
JANUS/Sentinel corrective decision, not a generic job resume. No new grant.
"""
from contextlib import closing
import sqlite3
from .memory_duty import reader

BRANCH_WAIT='Independent branches exhausted; outstanding worker dependencies: '
BRANCH_QUEUED='Independent branch available; worker dependency parked: '

def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS branch_holds_v61(
        job_id INTEGER NOT NULL,step_id INTEGER NOT NULL,report_id TEXT NOT NULL UNIQUE,
        contract_sha TEXT NOT NULL,PRIMARY KEY(job_id,step_id))""")

def blocked_steps(path,job_id):
    # Do not turn an unreadable hold ledger into permission to retry.
    with closing(reader(path)) as db:
        return {r[0] for r in db.execute("""SELECT h.step_id FROM branch_holds_v61 h
            JOIN job_steps s ON s.job_id=h.job_id AND s.id=h.step_id
            WHERE h.job_id=? AND s.state='planned'""",(job_id,))}

def parked(db,job_id,report_id,step_id=None,contract_sha=None):
    sql="""SELECT h.step_id,h.contract_sha FROM branch_holds_v61 h
           JOIN job_steps s ON s.id=h.step_id AND s.job_id=h.job_id
           WHERE h.job_id=? AND h.report_id=? AND s.state='planned'"""
    try:row=db.execute(sql,(job_id,report_id)).fetchone()
    except sqlite3.OperationalError as exc:
        if 'no such table' in str(exc):return False
        raise
    return bool(row and (step_id is None or row[0]==step_id)
                and (contract_sha is None or row[1]==contract_sha))

def coordination_open(db,job_id,report_id,*,dispatch=False):
    from .corrective_coordination import WAIT,READY
    row=db.execute("SELECT state,detail FROM jobs WHERE id=?",(job_id,)).fetchone()
    if not row:return False
    state,detail=row
    if state=='needs_input' and detail==WAIT+report_id:return True
    if not parked(db,job_id,report_id):return False
    if state=='needs_input':return detail.startswith(BRANCH_WAIT)
    if state=='queued':return not detail.startswith(READY)
    return state=='running' and not dispatch

def park(jobs,graphs,job,report_id):
    """Called on receipt of a finished inference-only worker report."""
    from .worker_reports import observe_granite_reports
    from .corrective_coordination import WAIT
    if not graphs.explicit(job['id']) or job['state']!='running':return False
    item=next((r for r in observe_granite_reports(jobs.path,receipt_sha=report_id)['reports']
               if r['receipt_sha']==report_id and r['job_id']==job['id']),None)
    if not item:return False
    steps=jobs.steps(job['id'])
    blocked=blocked_steps(jobs.path,job['id'])|{item['step_id']}
    ready=graphs.ready_step(job,steps,exclude=blocked)
    state='queued' if ready else 'needs_input'
    detail=(BRANCH_QUEUED if ready else BRANCH_WAIT)+report_id
    with jobs._conn() as db:
        db.execute('BEGIN IMMEDIATE')
        fresh=db.execute("SELECT state,approval_key,prompt FROM jobs WHERE id=?",(job['id'],)).fetchone()
        if not fresh or tuple(fresh)!=('running',job['approval_key'],job['prompt']):return False
        step=db.execute("SELECT state FROM job_steps WHERE id=? AND job_id=?",
                        (item['step_id'],job['id'])).fetchone()
        if not step or step[0]!='planned':return False
        db.execute("""INSERT INTO branch_holds_v61 VALUES(?,?,?,?)
            ON CONFLICT(job_id,step_id) DO UPDATE SET report_id=excluded.report_id,
            contract_sha=excluded.contract_sha""",
            (job['id'],item['step_id'],report_id,item['contract_sha']))
        db.execute("UPDATE jobs SET state=?,detail=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                   (state,detail,job['id']))
        db.execute("INSERT INTO job_events(job_id,note) VALUES(?,?)",
                   (job['id'],'Exact worker dependency parked; '+('independent work ready.' if ready else 'no independent stage currently ready.')))
    jobs.journal(job['id'])
    return True

def wait(jobs,job_id):
    """No ready work must not be interpreted as completion or generic retry."""
    held=blocked_steps(jobs.path,job_id)
    if not held:return False
    return jobs.change(job_id,'needs_input',BRANCH_WAIT+','.join(map(str,sorted(held))),allowed=('running',))
