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
    def __init__(self,report,sender='implementation'):
        if sender not in ('implementation','multimedia'):raise ValueError('Unknown reporting worker')
        self.report=report
        self.sender=sender
        super().__init__(('Gemma' if sender=='multimedia' else 'Granite')+' reported '+report['kind']+': '+report['need'])

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

def observe_granite_reports(job_db):
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

def creative_request(job_db,contract,*,states=('active','blocked')):
    """Recheck current approved roadmap and exact original request."""
    from .reasoning_council import sha
    with closing(reader(Path(job_db).parent/'roadmap-runs.sqlite3')) as db:
        run=db.execute("SELECT * FROM roadmap_runs WHERE request_id=?",(contract['request_id'],)).fetchone()
        if (not run or run['state'] not in states or run['creative_midi']!=1
                or run['manifest_sha256']!=contract['code_sha'] or run['mixed_sha']!=contract['plan_sha']
                or run['chat_id']!=contract['chat_id'] or not same_workspace(run['project'],contract['project'])):
            return None
    with closing(reader(Path(job_db).parent/'conversations.sqlite3')) as db:
        req=db.execute("SELECT * FROM conversation_requests WHERE id=?",(contract['request_id'],)).fetchone()
        if (not req or req['state']!='responded' or req['mode']!='draft_plan' or req['chat_id']!=contract['chat_id']
                or not same_workspace(req['project'],contract['project']) or sha(req['prompt'])!=contract['original_sha']):
            return None
        if db.execute("""SELECT 1 FROM specification_amendments a JOIN conversation_requests c ON c.id=a.request_id
                WHERE c.chat_id=? AND c.project=? AND a.request_id>? LIMIT 1""",
                (req['chat_id'],req['project'],req['id'])).fetchone():return None
        return dict(req)

def creative_envelope(lease,contract,report):
    return {'attempt':lease,'request_id':contract['request_id'],'task_id':contract['task']['id'],
            'contract_sha':canonical_sha(contract),'spec_sha':contract['original_sha'],
            'sender':'multimedia','recipients':['janus','sentinel'],'report':report,
            'authority':False,'verified':False}

def observe_gemma_reports(job_db):
    empty={'available':False,'reports':[]}
    try:
        with closing(reader(Path(job_db).parent/'roadmap-runs.sqlite3')) as db:
            rows=[dict(r) for r in db.execute("""SELECT w.*,m.contract,m.contract_sha,m.state,m.task_id
                FROM creative_reports_v49 w JOIN project_midi_v45 m ON m.lease=w.lease
                WHERE m.state='blocked' ORDER BY w.rowid DESC LIMIT 16""")]
        result=[]
        for row in rows:
            contract=json.loads(row['contract'])
            if canonical_sha(contract)!=row['contract_sha'] or contract['task']['id']!=row['task_id']:continue
            if not creative_request(job_db,contract):continue
            report=parse_report(PREFIX+row['report'])
            item=creative_envelope(row['lease'],contract,report)
            if canonical_sha(item)!=row['receipt_sha']:continue
            item['receipt_sha']=row['receipt_sha']
            item['focus']=(contract['task']['output']+': '+contract['task']['goal'])[:300]
            result.append(item)
            if len(result)>=4:break
        return {'available':True,'reports':result}
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return empty

def observe_worker_reports(job_db):
    granite=observe_granite_reports(job_db);gemma=observe_gemma_reports(job_db)
    from .worker_notices import observe_notices
    return {'available':granite['available'] or gemma['available'],
            'reports':granite['reports'][:4]+gemma['reports'][:4],
            'notices':observe_notices(job_db)}

def still_current(job_db,receipt_sha):
    from .worker_notices import observe_notices
    return (any(r['receipt_sha']==receipt_sha for r in observe_worker_reports(job_db)['reports'])
            or bool(observe_notices(job_db,receipt_sha=receipt_sha)))

def saved_dependency_catalog(job_db,item):
    """Read-only graph receipts, not proof that bytes are still available.

    Only exact direct saved predecessors of the report's bound assignment
    are candidates. The desktop independently checks grant, exclusions and
    actual bytes before dispatch and again before inference.
    """
    if item.get('sender')!='implementation':return []
    try:
        with closing(reader(Path(job_db).parent/'task-graph.sqlite3')) as db:
            row=db.execute("SELECT contract,contract_sha FROM project_assignments_v43 WHERE attempt=? AND state='abandoned'",(item['attempt'],)).fetchone()
            if not row:return []
            contract=json.loads(row['contract'])
            if (canonical_sha(contract)!=row['contract_sha'] or row['contract_sha']!=item['contract_sha']
                or contract['job_id']!=item['job_id'] or contract['step_id']!=item['step_id']):return []
            rows=db.execute("""SELECT n.title,n.evidence_sha256 FROM edges e
              JOIN nodes n ON n.job_id=e.job_id AND n.node=e.depends_on
              WHERE e.job_id=? AND e.node=? AND n.kind='artifact' AND n.state='saved'
              ORDER BY n.title LIMIT 12""",(item['job_id'],f"file:{item['step_id']}")).fetchall()
            return [{'path':r[0],'sha256':r[1]} for r in rows
                    if isinstance(r[0],str) and 0<len(r[0])<=240
                    and isinstance(r[1],str) and len(r[1])==64
                    and all(c in '0123456789abcdef' for c in r[1])]
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return []


def counsel_fields(item,job_db):
    """Provide exact, bounded current requirements, never just a hash."""
    report=item['report']
    notice=item.get('nonblocking') is True
    if notice and not still_current(job_db,item['receipt_sha']):raise ValueError('Stale worker notice')
    if item['sender']=='multimedia':
        states=('assigned','prepared','reviewed','publishing','checked') if notice else ('blocked',)
        with closing(reader(Path(job_db).parent/'roadmap-runs.sqlite3')) as db:
            row=db.execute("SELECT contract,contract_sha FROM project_midi_v45 WHERE lease=? AND state IN ("+
                ','.join('?' for _ in states)+")",(item['attempt'],*states)).fetchone()
        if not row:raise ValueError('Missing creative assignment')
        contract=json.loads(row['contract'])
        if canonical_sha(contract)!=row['contract_sha'] or row['contract_sha']!=item['contract_sha']:raise ValueError('Changed creative assignment')
        req=creative_request(job_db,contract)
        if not req:raise ValueError('Stale creative request')
        original=req['prompt']
    else:
        from .worker_notices import JOB_STATES
        bound=live_scope(job_db,item['job_id'],item['request_id'],states=JOB_STATES if notice else ('running','needs_input','failed'))
        if not bound or bound['spec_sha']!=item['spec_sha']:
            raise ValueError('Worker report no longer has its original specification')
        original=bound['original']
    if len(original)<=1200:source='COMPLETE ORIGINAL: '+original
    else:
        from .recovery_council import select_source_section
        source=('ORIGINAL BEGINNING (verbatim): '+original[:400]+'\nRELEVANT REQUIREMENT (verbatim): '+
                select_source_section(original,item['focus'],600))
        if original.startswith('USER SPECIFICATION REVISION:'):
            source+='\nREVISION TAIL (verbatim): '+original[-400:]
    return (('Gemma' if item['sender']=='multimedia' else 'Granite')+' '+report['kind']+' for '+item['focus'],
            ('Unverified NONBLOCKING observation, not a dependency hold. Output SHA: '+item['output_sha']+'; ' if notice else 'Unverified worker claim. ')+
            'Need: '+report['need']+'; reason: '+report['reason']+
            '; original specification SHA: '+item['spec_sha']+'\n'+source+
            ('\nDirect saved predecessor receipt candidates (not current byte verification): '+
             json.dumps([r['path'] for r in saved_dependency_catalog(job_db,item)],ensure_ascii=False)[:900]
             if item['sender']=='implementation' else ''))
