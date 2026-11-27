"""Independent prompt queue readout and bounded advisory preparation.
The existing conversation scheduler remains the sole dispatcher. No writes,
tools, job approvals or speculative file work are authorized by advice.
"""
import hashlib
import json
import sqlite3
import time
from contextlib import closing
from .agent_contract import canonical_sha
from .structured_source import strict_json

ROLES=('janus','sentinel','implementation')
MAX_PROMPT=2400
TTL=1800
def identity(row):
    return canonical_sha({'id':row['id'],'project':row['project'],'chat_id':row['chat_id'],
                          'mode':row['mode'],'prompt':row['prompt'],'attachments':row['attachments']})
def checked(body):
    if not isinstance(body,dict) or set(body)!={'kind','finding','guidance'} or body['kind'] not in ('advice','none'):
        raise ValueError('Invalid advisory schema')
    for name,n in (('finding',220),('guidance',320)):
        val=body[name]
        if not isinstance(val,str) or len(val)>n or any(ord(c)<32 for c in val):raise ValueError('Invalid advisory text')
        if body['kind']=='advice' and not val.strip():raise ValueError('Empty finding')
        if body['kind']=='none' and val:raise ValueError('Unexpected finding')
    return body
def connect(path):
    db=sqlite3.connect(path,timeout=.05);db.row_factory=sqlite3.Row;return db
def rows(path,project=None,limit=100):
    with closing(connect(path)) as db:
        where="WHERE c.project=?" if project is not None else ""
        args=(project,limit) if project is not None else (limit,)
        result=db.execute("SELECT c.*,(SELECT COUNT(*) FROM queued_prompt_advice a WHERE a.request_id=c.id AND a.stamp>=strftime('%s','now')-1800) AS prepared "
            "FROM independent_prompt_queue q JOIN conversation_requests c ON c.id=q.request_id "+where+
            " ORDER BY CASE WHEN c.state IN ('pending','running','waiting_sources') THEN 0 ELSE 1 END,c.id LIMIT ?",args)
        return [dict(r) for r in result]
def current(db,ident):
    r=db.execute('SELECT c.* FROM independent_prompt_queue q JOIN conversation_requests c ON c.id=q.request_id WHERE c.id=?',(ident,)).fetchone()
    return dict(r) if r else None
def candidate(path,roles,exclude=(),priority=None):
    allowed=[r for r in ROLES if r in roles]
    if not allowed:return None
    with closing(connect(path)) as db:
        pending=db.execute("SELECT c.* FROM independent_prompt_queue q JOIN conversation_requests c ON c.id=q.request_id WHERE c.state='pending' ORDER BY c.id LIMIT 32").fetchall()
        if priority is not None:pending=sorted((dict(r) for r in pending if priority.allowed(dict(r))),key=priority.key)
        for raw in pending:
            row=dict(raw)
            if row['id'] in exclude or len(row['prompt'])>MAX_PROMPT or json.loads(row['attachments']):continue
            # Each scope is considered once by each role; expired advice is not retried indefinitely.
            done={x[0] for x in db.execute('SELECT role FROM queued_prompt_attempts WHERE request_id=? AND identity=? UNION SELECT role FROM queued_prompt_advice WHERE request_id=? AND identity=?',(row['id'],identity(row),row['id'],identity(row)))}
            for role in allowed:
                if role not in done:return row,role
    return None
def available_roles(health,pid):
    if not isinstance(health,dict) or health.get('pid')!=pid or health.get('ready') is not True or health.get('serial_memory_mode') is not False or health.get('admission_waiting')!=0:return ()
    models=health.get('models');memory=health.get('memory_model')
    if not isinstance(models,dict) or not isinstance(memory,dict):return ()
    slots=health.get('admission_slots')
    if type(slots) is not int or slots<2:return ()
    workers=list(models.values())+[memory]
    if any(not isinstance(w,dict) or type(w.get('generating')) is not bool for w in workers):return ()
    if sum(w['generating'] for w in workers)>=slots:return ()
    return tuple(role for role in ROLES if isinstance(models.get(role),dict) and models[role].get('resident') is True
                 and models[role].get('busy') is False and models[role].get('generating') is False)
def run_once(path,client,roles,stopped,*,exclude=(),priority=None):
    if stopped():return None
    item=candidate(path,roles,exclude,priority)
    if not item:return None
    row,role=item;key=identity(row)
    focus={'janus':'Identify useful dependencies, decomposition or planning questions.',
           'sentinel':'Identify requirement ambiguity, risk and acceptance criteria.',
           'implementation':'Identify useful implementation interfaces, prerequisites or tests.'}[role]
    prompt=('Prepare advisory notes for a waiting independent user task. '+focus+
            ' No tools, execution, file changes, approvals, or claims of verification. Do not invent evidence. '
            'Keep the original request authoritative. Return ONLY JSON {"kind":"advice","finding":"max 220 chars","guidance":"max 320 chars"} '
            'or {"kind":"none","finding":"","guidance":""}. Exact queued user prompt:\n'+row['prompt'])
    if stopped():return None
    # Reserve one exact advisory attempt atomically. A malformed reply or interrupted
    # inference cannot monopolize the queue through automatic infinite retries.
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        fresh=current(db,row['id'])
        if not fresh or fresh['state']!='pending' or identity(fresh)!=key:return None
        if not db.execute('INSERT OR IGNORE INTO queued_prompt_attempts VALUES(?,?,?)',(row['id'],role,key)).rowcount:return None
    if stopped():return None
    body=checked(strict_json(client.chat_as(role,'queued-prep-'+key[:24]+'-'+role,prompt,max_tokens=256)))
    if stopped():return None
    receipt={'role':role,'identity':key,'body':body,'authority':False,'verified':False}
    with closing(connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        fresh=current(db,row['id'])
        if not fresh or fresh['state']!='pending' or identity(fresh)!=key or stopped():return None
        if not db.execute('INSERT OR IGNORE INTO queued_prompt_advice VALUES(?,?,?,?,?,?)',
            (row['id'],role,key,json.dumps(receipt,sort_keys=True),canonical_sha(receipt),time.time())).rowcount:return None
    return receipt
def advice(path,request,budget=600):
    if budget<100:return ''
    try:
        with closing(connect(path)) as db:
            fresh=current(db,request['id'])
            if not fresh or fresh['state']!='running' or identity(fresh)!=identity(request):return ''
            records=db.execute('SELECT * FROM queued_prompt_advice WHERE request_id=? ORDER BY role',(request['id'],)).fetchall()
        result=''
        for r in records:
            if r['role'] not in ROLES or r['identity']!=identity(request) or not 0<=time.time()-r['stamp']<=TTL:continue
            receipt=json.loads(r['body'])
            if canonical_sha(receipt)!=r['receipt_sha'] or receipt['identity']!=r['identity'] or receipt['role']!=r['role'] or receipt['authority'] is not False or receipt['verified'] is not False:continue
            body=checked(receipt['body'])
            if body['kind']!='advice':continue
            line='\nQueued '+r['role']+' preparation (unverified advisory only): '+body['finding']+'; '+body['guidance']
            if len(result)+len(line)<=budget:result+=line
        return result
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):return ''
