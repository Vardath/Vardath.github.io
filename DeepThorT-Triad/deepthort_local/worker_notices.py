"""Nonblocking, scoped production findings in existing assignment stores.

A notice accompanies model output. It is not a review, verified result, new
task, specification amendment or execution authority.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import time
from .agent_contract import canonical_sha
from .memory_duty import reader,live_scope
from .task_graph import same_workspace
from .reasoning_council import sha
from .structured_source import strict_json

PREFIX='DEEPTHORT_WORKER_NOTICE:'
KINDS=frozenset(('discovery','integration_hint','upcoming_dependency','quality_concern'))
GUIDANCE=('\nIf you have a genuinely useful NONBLOCKING finding, you may prepend one line '
          'DEEPTHORT_WORKER_NOTICE: followed by JSON {"kind":"discovery","need":"specific finding",'
          '"reason":"why it matters"} (kind also integration_hint, upcoming_dependency or quality_concern), '
          'then a newline and the complete requested output in its original format. '
          'Do not add a notice for routine work. A real blocker still uses the report alternative.')
TTL=900
MAX_PER_ATTEMPT=4
MAX_STORED=512
JOB_STATES=('queued','running','waiting_verification','waiting_repair','needs_input')

def validate_notice(obj):
    if not isinstance(obj,dict) or set(obj)!={'kind','need','reason'} or not isinstance(obj['kind'],str) or obj['kind'] not in KINDS:
        raise ValueError('Invalid worker notice schema')
    result=dict(obj)
    for key,limit in (('need',180),('reason',240)):
        value=obj[key]
        if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
            raise ValueError('Invalid bounded worker notice')
        result[key]=value.strip()
    return result

def split_notice(answer):
    if not isinstance(answer,str) or not answer.lstrip().startswith(PREFIX):return None,answer
    header,sep,body=answer.lstrip().partition('\n')
    if not sep or len(header)>1000 or not body.strip():
        raise ValueError('A notice must accompany complete production output')
    if body.lstrip().startswith((PREFIX,'DEEPTHORT_WORKER_REPORT:')):
        raise ValueError('Notice cannot accompany a blocker or another notice')
    return validate_notice(strict_json(header[len(PREFIX):].strip())),body

def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS worker_notices_v53(
        receipt_sha TEXT PRIMARY KEY,attempt TEXT NOT NULL,request_id INTEGER NOT NULL,
        notice_sha TEXT NOT NULL,notice TEXT NOT NULL,output_sha TEXT NOT NULL,
        created REAL NOT NULL,UNIQUE(attempt,notice_sha))""")

def envelope(attempt,request_id,contract,notice,output_sha,sender,created):
    if not isinstance(output_sha,str) or len(output_sha)!=64 or any(c not in '0123456789abcdef' for c in output_sha):
        raise ValueError('Notice requires exact output hash')
    item={'attempt':attempt,'request_id':request_id,'contract_sha':canonical_sha(contract),
          'sender':sender,'recipients':['janus','sentinel'],'report':validate_notice(notice),
          'output_sha':output_sha,'created':created,'nonblocking':True,'authority':False,'verified':False}
    if sender=='implementation':
        item.update(job_id=contract['job_id'],step_id=contract['step_id'],spec_sha=contract['original_sha256'])
    elif sender=='multimedia':
        item.update(task_id=contract['task']['id'],spec_sha=contract['original_sha'])
    else:raise ValueError('Unknown notice sender')
    return item

def record(db,attempt,request_id,contract,notice,output_sha,sender,*,clock=time.time):
    """Caller validates active assignment in the same transaction."""
    item=envelope(attempt,request_id,contract,notice,output_sha,sender,clock())
    digest=canonical_sha(item)
    if db.execute("SELECT COUNT(*) FROM worker_notices_v53 WHERE attempt=?",(attempt,)).fetchone()[0]>=MAX_PER_ATTEMPT:return False
    added=db.execute("INSERT OR IGNORE INTO worker_notices_v53 VALUES(?,?,?,?,?,?,?)",
        (digest,attempt,request_id,canonical_sha(item['report']),json.dumps(item['report'],sort_keys=True),output_sha,item['created'])).rowcount
    if added:
        db.execute("""DELETE FROM worker_notices_v53 WHERE receipt_sha IN
          (SELECT receipt_sha FROM worker_notices_v53 ORDER BY created DESC,receipt_sha LIMIT -1 OFFSET ?)""",(MAX_STORED,))
    return bool(added)

def _read(job_db,now,sender,receipt_sha=None):
    granite=sender=='implementation'
    path=Path(job_db).parent/('task-graph.sqlite3' if granite else 'roadmap-runs.sqlite3')
    sql=("""SELECT w.*,a.contract,a.contract_sha,a.job_id,a.step_id,g.plan_sha256,g.state AS graph_state
        FROM worker_notices_v53 w JOIN project_assignments_v43 a ON a.attempt=w.attempt
        JOIN graphs g ON g.job_id=a.job_id
        WHERE w.created>=? AND a.state IN ('assigned','reviewed','committing','saved')
        AND NOT EXISTS(SELECT 1 FROM project_assignments_v43 n WHERE n.job_id=a.job_id
          AND n.step_id=a.step_id AND n.rowid>a.rowid)""" if granite else
        """SELECT w.*,m.contract,m.contract_sha,m.task_id,m.request_id AS current_request
        FROM worker_notices_v53 w JOIN project_midi_v45 m ON m.lease=w.attempt
        WHERE w.created>=? AND m.state IN ('assigned','prepared','reviewed','publishing','checked')""")
    args=(now-TTL,)
    if receipt_sha:
        sql+=' AND w.receipt_sha=?';args+=(receipt_sha,)
    sql+=' ORDER BY w.created DESC,w.receipt_sha LIMIT 32'
    try:
        with closing(reader(path)) as db:rows=[dict(r) for r in db.execute(sql,args)]
    except (OSError,ValueError,sqlite3.Error):return []
    result=[]
    for row in rows:
        try:
            c=json.loads(row['contract'])
            if row['created']>now or canonical_sha(c)!=row['contract_sha']:continue
            if granite:
                if (c['job_id']!=row['job_id'] or c['step_id']!=row['step_id'] or c['assignee']!='implementation'
                    or c['graph_sha256']!=row['plan_sha256'] or row['graph_state']!='active'):continue
                bound=live_scope(job_db,c['job_id'],row['request_id'],states=JOB_STATES)
                if (not bound or bound['spec_sha']!=c['original_sha256'] or bound['chat_id']!=c['chat_id']
                    or bound['approval_key']!=c['approval_key'] or not same_workspace(bound['project'],c['project'])):continue
                with closing(reader(job_db)) as db:
                    step=db.execute("SELECT path,description,state FROM job_steps WHERE id=? AND job_id=?",(c['step_id'],c['job_id'])).fetchone()
                if (not step or step['state'] not in ('planned','proposed','saved','verified') or step['path']!=c['path']
                    or sha(step['description'])!=c['description_sha256']):continue
                focus=step['path']+': '+step['description']
            else:
                from .worker_reports import creative_request
                if (c['task']['id']!=row['task_id'] or c['request_id']!=row['request_id']
                    or row['current_request']!=row['request_id'] or not creative_request(job_db,c)):continue
                focus=c['task']['output']+': '+c['task']['goal']
            notice=validate_notice(json.loads(row['notice']))
            item=envelope(row['attempt'],row['request_id'],c,notice,row['output_sha'],sender,row['created'])
            if canonical_sha(item)!=row['receipt_sha'] or canonical_sha(notice)!=row['notice_sha']:continue
            item.update(receipt_sha=row['receipt_sha'],focus=focus[:300])
            result.append(item)
            if len(result)>=8:break
        except (ValueError,TypeError,KeyError,OSError,sqlite3.Error):continue
    return result

def observe_notices(job_db,*,clock=time.time,receipt_sha=None):
    now=clock()
    return _read(job_db,now,'implementation',receipt_sha)+_read(job_db,now,'multimedia',receipt_sha)
