"""Single, explicitly approved MCP calls with revalidated schema and durable receipts.

Not a sandbox: the external server can act outside the selected project.
No model-driven execution, inherited permissions, retries, or raw output injection.
"""
from __future__ import annotations
import json
import math
import time
import re
from pathlib import Path
from .local_mcp import Discovery,LocalMCP,endpoint,NAME,typed_tool
from .tool_workflows import digest
from .structured_source import strict_json

MAX_ARGS=8192
MAX_RECEIPTS=2000
SCALARS={'string','boolean','integer','number','null'}
ANNOTATIONS={'description','title','default','examples','$schema'}
def validate_args(schema,args):
    """Fail closed on unsupported JSON Schema features; bounded scalar subset."""
    if not isinstance(schema,dict) or schema.get('type')!='object' or not isinstance(args,dict):
        raise ValueError('Expected object schema and JSON object arguments')
    if set(schema)-({'type','properties','required','additionalProperties'}|ANNOTATIONS):
        raise ValueError('Unsupported object schema constraints')
    if 'additionalProperties' in schema and type(schema['additionalProperties']) is not bool:
        raise ValueError('Unsupported additionalProperties schema')
    props=schema.get('properties',{})
    typed_tool({'name':'validate','inputSchema':schema})
    if set(args)-set(props) or set(schema.get('required',[]))-set(args):
        raise ValueError('Missing required or unknown argument')
    if len(json.dumps(args,ensure_ascii=True,allow_nan=False))>MAX_ARGS:
        raise ValueError('Arguments exceed bound')
    for key,p in props.items():
        kind=p.get('type')
        if not isinstance(kind,str) or kind not in SCALARS:
            raise ValueError('Nested or union schemas not supported yet')
        supported={'type','enum','const'}|ANNOTATIONS
        if kind=='string':supported|={'minLength','maxLength'}
        if kind in ('integer','number'):supported|={'minimum','maximum','exclusiveMinimum','exclusiveMaximum'}
        if set(p)-supported:raise ValueError('Unsupported field schema constraints: '+key)
        if key not in args:continue
        v=args[key]
        valid=(type(v) is str if kind=='string' else type(v) is bool if kind=='boolean' else
               type(v) is int if kind=='integer' else type(v) in (int,float) if kind=='number' else v is None)
        if not valid:raise ValueError('Wrong type for '+key)
        if kind=='string':
            if len(v)>2048 or '\x00' in v:raise ValueError('String exceeds bound')
            for limit,compare in [('minLength',lambda n:len(v)>=n),('maxLength',lambda n:len(v)<=n)]:
                if limit in p and (type(p[limit]) is not int or p[limit]<0 or not compare(p[limit])):
                    raise ValueError('String length constraint failed: '+key)
        if kind in ('number','integer'):
            if abs(v)>10**15 or not math.isfinite(v):raise ValueError('Number exceeds bound')
            for limit,compare in [('minimum',lambda n:v>=n),('maximum',lambda n:v<=n),
                                  ('exclusiveMinimum',lambda n:v>n),('exclusiveMaximum',lambda n:v<n)]:
                if limit in p and (type(p[limit]) not in (int,float) or not math.isfinite(p[limit]) or not compare(p[limit])):
                    raise ValueError('Numeric constraint failed: '+key)
        def equal(x):
            if type(v) is bool or type(x) is bool:return type(x) is type(v) and x==v
            return x==v
        if 'enum' in p and (not isinstance(p['enum'],list) or not any(equal(x) for x in p['enum'])):
            raise ValueError('Enum constraint failed: '+key)
        if 'const' in p and not equal(p['const']):raise ValueError('Const constraint failed: '+key)
    return args

class MCPCalls:
    def __init__(self,janus):
        self.janus=janus
        self.catalog=LocalMCP(janus)
        with janus.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS local_mcp_calls(
                id INTEGER PRIMARY KEY,project TEXT NOT NULL,endpoint TEXT NOT NULL,
                tool TEXT NOT NULL,schema_sha TEXT NOT NULL,args_sha TEXT NOT NULL,
                state TEXT NOT NULL,result_sha TEXT,created REAL NOT NULL,finished REAL)""")
            db.execute('BEGIN IMMEDIATE')
            cols={row[1] for row in db.execute('PRAGMA table_info(local_mcp_calls)')}
            for name,typ in (('task_id','INTEGER'),('task_spec_sha','TEXT'),('task_chat','TEXT'),
                             ('task_nonce','TEXT'),('task_review_sha','TEXT')):
                if name not in cols:db.execute('ALTER TABLE local_mcp_calls ADD COLUMN '+name+' '+typ)
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS mcp_task_once ON local_mcp_calls(task_nonce) WHERE task_nonce IS NOT NULL')
    def prepare(self,project,url,name,args):
        root=str(Path(project).resolve(strict=True))
        endpoint(url)
        if not isinstance(name,str) or not NAME.fullmatch(name):raise ValueError('Invalid tool name')
        record=next((x for x in self.catalog.list(root) if x['endpoint']==url),None)
        if not record:raise ValueError('Discover this endpoint in the selected project first')
        tool=next((x for x in record['tools'] if x['name']==name),None)
        if not tool:raise ValueError('Tool is not in the project catalog')
        if not isinstance(args,dict) or len(json.dumps(args,ensure_ascii=True,allow_nan=False))>MAX_ARGS:
            raise ValueError('Arguments must be a bounded JSON object')
        return {'project':root,'endpoint':url,'tool':name,'schema_sha':tool['schema_sha'],
                'catalog_sha':record['fingerprint'],'arguments':args}
    def call(self,proposal,*,expected_sha,user_approved=False,cancelled=None,task=None,task_current=None):
        if user_approved is not True:raise PermissionError('Exact tool call approval required')
        # Copy via JSON and bind all fields to the reviewed proposal.
        proposal=strict_json(json.dumps(proposal,ensure_ascii=True,allow_nan=False))
        if task is not None:
            task=strict_json(json.dumps(task,ensure_ascii=True,allow_nan=False))
            if (not isinstance(task,dict) or set(task)!={'job_id','spec_sha','chat_id','nonce','review_sha'}
                or type(task['job_id']) is not int or task['job_id']<1
                or not isinstance(task['chat_id'],str)
                or any(not isinstance(task[k],str) or not re.fullmatch(r'[a-f0-9]{64}',task[k])
                       for k in ('spec_sha','nonce','review_sha')) or not callable(task_current)):
                raise ValueError('Invalid MCP task binding')
        approved=proposal if task is None else {'call':proposal,'task':task}
        if digest(approved)!=expected_sha:raise ValueError('Approved tool call changed')
        if task is not None and not task_current(task,proposal):
            raise ValueError('Task or specification changed')
        current=self.prepare(proposal['project'],proposal['endpoint'],proposal['tool'],proposal['arguments'])
        if current!=proposal:raise ValueError('Project discovery changed; review again')
        client=Discovery(proposal['endpoint'],cancelled)
        fresh=client.discover()
        if digest(fresh)!=proposal['catalog_sha']:raise ValueError('Server tool inventory changed; rediscover and review')
        schema=client.schemas[proposal['tool']]
        if digest(schema)!=proposal['schema_sha']:raise ValueError('Tool schema changed')
        validate_args(schema,proposal['arguments'])
        if self.prepare(proposal['project'],proposal['endpoint'],proposal['tool'],proposal['arguments'])!=proposal:
            raise ValueError('Catalog changed during verification')
        client.remaining()
        if task is not None and not task_current(task,proposal):
            raise ValueError('Task or specification changed during verification')
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM local_mcp_calls WHERE project=?',(proposal['project'],)).fetchone()[0]>=MAX_RECEIPTS:
                raise ValueError('MCP receipt quota reached')
            if task is not None and db.execute('SELECT 1 FROM local_mcp_calls WHERE task_nonce=?',(task['nonce'],)).fetchone():
                raise ValueError('This reviewed MCP operation has already been dispatched; inspect receipt')
            binding=(None,)*5 if task is None else (task['job_id'],task['spec_sha'],task['chat_id'],task['nonce'],task['review_sha'])
            ident=db.execute("""INSERT INTO local_mcp_calls(project,endpoint,tool,schema_sha,args_sha,state,created,
                task_id,task_spec_sha,task_chat,task_nonce,task_review_sha)
                VALUES(?,?,?,?,?,'dispatching',?,?,?,?,?,?)""",(proposal['project'],proposal['endpoint'],proposal['tool'],
                    proposal['schema_sha'],digest(proposal['arguments']),time.time(),*binding)).lastrowid
        state='outcome_unknown';result_sha=None
        try:
            # The discovery API still refuses calls; this one guarded path
            # performs exactly one request. No retry even on timeout.
            if task is not None and not task_current(task,proposal):
                state='not_dispatched'
                raise ValueError('Task changed before dispatch')
            result=client._exchange('tools/call',{'name':proposal['tool'],'arguments':proposal['arguments']})
            if not isinstance(result.get('content'),list) or type(result.get('isError',False)) is not bool:
                raise ValueError('Malformed MCP call result')
            result_sha=digest(result)
            state='server_reported_error' if result.get('isError',False) else 'response_received'
            return {'id':ident,'state':state,'result':result,'result_sha':result_sha}
        finally:
            with self.janus.connect() as db:
                db.execute('UPDATE local_mcp_calls SET state=?,result_sha=?,finished=? WHERE id=?',
                           (state,result_sha,time.time(),ident))
    def history(self,project):
        root=str(Path(project).resolve(strict=True))
        with self.janus.connect() as db:
            db.row_factory=__import__('sqlite3').Row
            return [dict(x) for x in db.execute('SELECT * FROM local_mcp_calls WHERE project=? ORDER BY id DESC LIMIT 30',(root,))]
