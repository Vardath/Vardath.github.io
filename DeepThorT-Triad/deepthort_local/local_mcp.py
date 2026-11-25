"""Explicit project-scoped local MCP discovery, not execution authority.

Limited Streamable HTTP JSON client for the 2025-11-25 handshake revision
(and negotiated 2025-06-18). No remote hosts, redirects, proxy, credentials,
server launch, resource reads, prompts, sampling, or tools/call.
"""
from __future__ import annotations
import http.client
import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from .tool_workflows import digest
from .structured_source import strict_json

VERSIONS=('2025-11-25','2025-06-18')
MAX_REPLY=128_000
MAX_TOOLS=64
MAX_PAGES=4
NAME=re.compile(r'[A-Za-z0-9_.-]{1,100}')
TYPES={'object','array','string','integer','number','boolean','null'}

def endpoint(value):
    if not isinstance(value,str) or len(value)>240:raise ValueError('Invalid local MCP endpoint')
    try:
        p=urlsplit(value)
        port=p.port
    except ValueError as error:raise ValueError('Invalid local MCP endpoint') from error
    if (p.scheme!='http' or p.hostname!='127.0.0.1' or not port or p.netloc!=f'127.0.0.1:{port}'
        or not re.fullmatch(r'/[A-Za-z0-9_./-]{0,150}',p.path) or '..' in p.path.split('/')
        or p.query or p.fragment):
        raise ValueError('Use an explicit http://127.0.0.1:PORT/path endpoint without credentials or query')
    return port,p.path

def typed_tool(tool):
    if not isinstance(tool,dict) or not isinstance(tool.get('name'),str) or not NAME.fullmatch(tool['name']):
        raise ValueError('Invalid MCP tool name')
    schema=tool.get('inputSchema')
    if not isinstance(schema,dict) or schema.get('type')!='object':raise ValueError('MCP tool needs object input schema')
    props=schema.get('properties',{})
    required=schema.get('required',[])
    if (not isinstance(props,dict) or len(props)>32 or not isinstance(required,list)
        or any(not isinstance(x,str) or x not in props for x in required) or len(set(required))!=len(required)):
        raise ValueError('Unsupported MCP input schema')
    fields=[]
    for key,value in sorted(props.items()):
        if not NAME.fullmatch(key) or not isinstance(value,dict):raise ValueError('Unsupported MCP field')
        kind=value.get('type')
        fields.append({'name':key,'type':kind if isinstance(kind,str) and kind in TYPES else 'complex',
                       'required':key in required})
    # Only the structural digest and bounded type summary survive discovery.
    # Server descriptions, defaults, example values and instructions are not
    # persisted or inserted into prompts.
    if len(json.dumps(schema,ensure_ascii=True))>16000:raise ValueError('MCP schema too large')
    return {'name':tool['name'],'fields':fields,'schema_sha':digest(schema)}

class Discovery:
    def __init__(self,url,cancelled=None):
        self.port,self.path=endpoint(url)
        self.cancelled=cancelled
        self.deadline=time.monotonic()+24
        self.version=None;self.session=None;self.ident=0

    def remaining(self):
        if self.cancelled and self.cancelled():raise ValueError('MCP discovery cancelled')
        remaining=self.deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('MCP discovery deadline exceeded')
        return min(3,remaining)

    def post(self,method,params=None,*,notification=False):
        if method not in ('initialize','notifications/initialized','tools/list'):
            raise ValueError('MCP discovery does not permit this method')
        if notification!=(method=='notifications/initialized'):raise ValueError('Invalid discovery request')
        body={'jsonrpc':'2.0','method':method}
        if params is not None:body['params']=params
        if not notification:
            self.ident+=1;body['id']=self.ident
        headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
        if self.version:headers['MCP-Protocol-Version']=self.version
        if self.session:headers['Mcp-Session-Id']=self.session
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=self.remaining())
        try:
            conn.request('POST',self.path,json.dumps(body).encode('utf-8'),headers)
            response=conn.getresponse()
            session=response.getheader('Mcp-Session-Id')
            if session is not None:
                if not re.fullmatch(r'[!-~]{1,200}',session):raise ValueError('Invalid MCP session ID')
                if self.session and self.session!=session:raise ValueError('MCP session changed')
                self.session=session
            if notification:
                if response.status!=202:raise ValueError('MCP initialized notification not accepted')
                return None
            if response.status!=200:raise ValueError('MCP discovery HTTP status '+str(response.status))
            if response.getheader('Content-Type','').split(';')[0].strip().lower()!='application/json':
                raise ValueError('Only JSON responses supported in this MCP pass; streaming not yet supported')
            data=bytearray()
            while True:
                self.remaining()
                chunk=response.read1(min(8192,MAX_REPLY-len(data)+1))
                if not chunk:break
                data.extend(chunk)
                if len(data)>MAX_REPLY:raise ValueError('MCP response exceeds bound')
            msg=strict_json(data.decode('utf-8'))
            if (not isinstance(msg,dict) or msg.get('jsonrpc')!='2.0'
                or type(msg.get('id')) is not int or msg['id']!=self.ident or 'error' in msg
                or not isinstance(msg.get('result'),dict)):
                raise ValueError('MCP response did not match request')
            return msg['result']
        finally:conn.close()

    def discover(self):
        result=self.post('initialize',{'protocolVersion':VERSIONS[0],'capabilities':{},
                        'clientInfo':{'name':'DeepThorT-Triad','version':'17'}})
        self.version=result.get('protocolVersion')
        if self.version not in VERSIONS:raise ValueError('Unsupported MCP protocol revision')
        capabilities=result.get('capabilities')
        if not isinstance(capabilities,dict) or not isinstance(capabilities.get('tools'),dict):
            raise ValueError('Server did not advertise tools')
        self.post('notifications/initialized',notification=True)
        tools=[];names=set();cursor=None;seen=set()
        for _ in range(MAX_PAGES):
            page=self.post('tools/list',{'cursor':cursor} if cursor is not None else {})
            if not isinstance(page.get('tools'),list):raise ValueError('Invalid MCP tool list')
            for item in page['tools']:
                tool=typed_tool(item)
                if tool['name'] in names:raise ValueError('Duplicate MCP tool name')
                names.add(tool['name']);tools.append(tool)
                if len(tools)>MAX_TOOLS:raise ValueError('MCP tool count exceeds bound')
            cursor=page.get('nextCursor')
            if cursor is None:break
            if not isinstance(cursor,str) or not 1<=len(cursor)<=512 or cursor in seen:raise ValueError('Invalid MCP pagination')
            seen.add(cursor)
        else:raise ValueError('MCP page count exceeds bound')
        return {'protocol':self.version,'tools':sorted(tools,key=lambda x:x['name'])}

class LocalMCP:
    def __init__(self,janus):
        self.janus=janus
        with janus.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS local_mcp_catalog(
                project TEXT NOT NULL, endpoint TEXT NOT NULL, payload TEXT NOT NULL,
                fingerprint TEXT NOT NULL, observed REAL NOT NULL,
                PRIMARY KEY(project,endpoint))""")
    def discover(self,project,url,*,user_approved=False,cancelled=None):
        if user_approved is not True:raise PermissionError('Explicit local MCP discovery approval required')
        root=str(Path(project).resolve(strict=True))
        if not Path(root).is_dir():raise ValueError('Select a project directory')
        endpoint(url)
        # No project paths, files, secrets, or user prompts sent to server.
        result=Discovery(url,cancelled).discover()
        if cancelled and cancelled():raise ValueError('MCP discovery cancelled')
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT count(*) FROM local_mcp_catalog WHERE project=?',(root,)).fetchone()[0]
            existing=db.execute('SELECT 1 FROM local_mcp_catalog WHERE project=? AND endpoint=?',(root,url)).fetchone()
            if count>=12 and not existing:raise ValueError('Project MCP catalog full')
            db.execute("""INSERT INTO local_mcp_catalog VALUES(?,?,?,?,?)
                ON CONFLICT(project,endpoint) DO UPDATE SET payload=excluded.payload,
                fingerprint=excluded.fingerprint,observed=excluded.observed""",
                (root,url,json.dumps(result,sort_keys=True),digest(result),time.time()))
        return result
    def list(self,project):
        root=str(Path(project).resolve(strict=True))
        with self.janus.connect() as db:
            rows=db.execute('SELECT endpoint,payload,fingerprint,observed FROM local_mcp_catalog WHERE project=? ORDER BY endpoint LIMIT 12',(root,)).fetchall()
        found=[]
        for url,payload,fingerprint,observed in rows:
            try:
                endpoint(url)
                if len(payload)>MAX_REPLY:continue
                result=json.loads(payload)
                if digest(result)!=fingerprint:continue
                if result.get('protocol') not in VERSIONS or not isinstance(result.get('tools'),list):continue
                # UI exposes names and field types only; catalog remains historical.
                found.append({'endpoint':url,'protocol':result['protocol'],'tools':result['tools'],
                              'fingerprint':fingerprint,'observed':observed})
            except (ValueError,TypeError,KeyError):continue
        return found
    def remove(self,project,url,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit removal required')
        root=str(Path(project).resolve(strict=True))
        with self.janus.connect() as db:
            return bool(db.execute('DELETE FROM local_mcp_catalog WHERE project=? AND endpoint=?',(root,url)).rowcount)
