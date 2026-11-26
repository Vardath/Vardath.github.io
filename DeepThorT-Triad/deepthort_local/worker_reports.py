"""Typed production-worker advisory messages. No execution or approval authority.

A report is an alternative to source bytes for an explicitly enabled, existing
Granite assignment. It records a model claim, not an established missing
dependency. Both societies independently check its current identity.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .agent_contract import canonical_sha
from .task_graph import same_workspace
from .memory_duty import reader,live_scope

PREFIX='DEEPTHORT_WORKER_REPORT:'
KINDS=frozenset(('missing_dependency','interface_conflict','tool_requirement','evidence_gap'))
GUIDANCE=("\nIf a genuine unresolved dependency makes producing the required output unsafe, "
          "return ONLY DEEPTHORT_WORKER_REPORT: followed by JSON with keys kind, need, reason. "
          "kind must be missing_dependency, interface_conflict, tool_requirement or evidence_gap. "
          "Name the exact need and why the supplied evidence is insufficient; never request execution permission "
          "or report a blocker merely because the task is difficult. Otherwise return the requested source.")

class WorkerReport(RuntimeError):
    def __init__(self,report):
        self.report=report
        super().__init__('Granite reported '+report['kind']+': '+report['need'])

def parse_report(answer):
    if not isinstance(answer,str) or not answer.lstrip().startswith(PREFIX):return None
    text=answer.strip()[len(PREFIX):].strip()
    if len(text)>1800:raise ValueError('Oversized worker report')
    from .structured_source import strict_json
    obj=strict_json(text)
    if not isinstance(obj,dict) or set(obj)!={'kind','need','reason'} or not isinstance(obj['kind'],str) or obj['kind'] not in KINDS:
        raise ValueError('Invalid worker report schema')
    for key,limit in (('need',240),('reason',400)):
        v=obj[key]
        if not isinstance(v,str) or not v.strip() or len(v)>limit or any(ord(c)<32 for c in v):
            raise ValueError('Invalid bounded worker report field')
        obj[key]=v.strip()
    return obj

def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS worker_reports_v48(
      attempt TEXT PRIMARY KEY,request_id INTEGER NOT NULL,report TEXT NOT NULL,
      receipt_sha TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")

def envelope(attempt,request_id,contract,report):
    return {'attempt':attempt,'request_id':request_id,'job_id':contract['job_id'],
            'step_id':contract['step_id'],'contract_sha':canonical_sha(contract),
            'spec_sha':contract['original_sha256'],'sender':'implementation',
            'recipients':['janus','sentinel'],'report':report,
            'authority':False,'verified':False}

def observe_worker_reports(job_db):
    """Read-only projection; never accept stale attempts or a changed original."""
    empty={'available':False,'reports':[]}
    try:
        path=Path(job_db).parent/'task-graph.sqlite3'
        with closing(reader(path)) as db:
            rows=[dict(r) for r in db.execute("""SELECT w.*,a.contract,a.contract_sha,a.job_id,a.step_id
                FROM worker_reports_v48 w JOIN project_assignments_v43 a ON a.attempt=w.attempt
                WHERE a.state='abandoned' AND NOT EXISTS(
                  SELECT 1 FROM project_assignments_v43 n WHERE n.job_id=a.job_id
                    AND n.step_id=a.step_id AND n.rowid>a.rowid)
                ORDER BY w.rowid DESC LIMIT 24""")]
        result=[]
        for row in rows:
            c=json.loads(row['contract'])
            if canonical_sha(c)!=row['contract_sha'] or c['job_id']!=row['job_id'] or c['step_id']!=row['step_id'] or c['assignee']!='implementation':continue
            bound=live_scope(job_db,row['job_id'],row['request_id'],states=('running','needs_input','failed'))
            if not bound or bound['spec_sha']!=c['original_sha256'] or bound['chat_id']!=c['chat_id'] or bound['approval_key']!=c['approval_key'] or not same_workspace(bound['project'],c['project']):continue
            with closing(reader(job_db)) as db:
                step=db.execute("SELECT path,description,state FROM job_steps WHERE id=? AND job_id=?",
                    (row['step_id'],row['job_id'])).fetchone()
            if not step or step['state']!='planned' or step['path']!=c['path']:continue
            from .reasoning_council import sha
            if sha(step['description'])!=c['description_sha256']:continue
            report=parse_report(PREFIX+row['report'])
            item=envelope(row['attempt'],row['request_id'],c,report)
            if canonical_sha(item)!=row['receipt_sha']:continue
            item['receipt_sha']=row['receipt_sha']
            item['focus']=(step['path']+': '+step['description'])[:300]
            result.append(item)
            if len(result)>=8:break
        return {'available':True,'reports':result}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return empty

def still_current(job_db,receipt_sha):
    return any(r['receipt_sha']==receipt_sha for r in observe_worker_reports(job_db)['reports'])

def counsel_fields(item):
    """Bounded untrusted claim, tied to exact file obligation, for neural advice."""
    report=item['report']
    return ('Granite '+report['kind']+' for '+item['focus'],
            'Unverified worker claim. Need: '+report['need']+'; reason: '+report['reason']+
            '; original specification SHA: '+item['spec_sha'])
