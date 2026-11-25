"""Isolated task MCP integration using real stores/HTTP, scripted model answers."""
import json
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .janus_engine import JanusStore
from .job_queue import JobStore
from .conversation_workflow import ConversationStore
from .mcp_calls import MCPCalls
from .task_mcp import plan,execute
from .reasoning_council import ReasoningCouncil
from .tool_workflows import digest

class ScriptedCouncilClient:
    def __init__(self,verdict='ACCEPT'):
        self.roles=[];self.verdict=verdict
    def chat_as(self,role,session_id,prompt,max_tokens=240):
        self.roles.append(role)
        if role=='janus':return '{"choice":1,"arguments":{"count":2},"reason":"Inspect the sector list"}'
        return json.dumps({'verdict':self.verdict,'reason':'Sector count inspection is relevant to the approved task.'})

def exercise():
    calls=[]
    schema={'type':'object','properties':{'count':{'type':'integer','minimum':1,'maximum':3}},'required':['count']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            msg=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method=msg['method']
            if method=='initialize':result={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
            elif method=='notifications/initialized':self.send_response(202);self.end_headers();return
            elif method=='tools/list':result={'tools':[{'name':'inspect_sectors','inputSchema':schema}]}
            elif method=='tools/call':
                calls.append(msg['params']);result={'content':[{'type':'text','text':'fixture sectors'}]}
            else:self.send_error(405);return
            data=json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':result}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='triad-task-mcp-') as folder:
            root=Path(folder);project=root/'project';project.mkdir();project=str(project)
            jobs=JobStore(root/'jobs.sqlite3');conversations=ConversationStore(root/'conversations.sqlite3')
            original='Create a space sector catalogue in JSON.'
            rid=conversations.submit('chat',project,'draft_plan',original)
            steps=[{'path':'sectors.json','description':'Create sector catalogue'}]
            draft=conversations.save_draft(rid,steps)
            job=jobs.submit_approved_build(project,'chat',original,steps,'draft:'+str(draft))
            conversations.approve(draft,job);jobs.change(job,'paused','Await inspection')
            service=MCPCalls(JanusStore(root/'janus.sqlite3'))
            service.catalog.discover(project,f'http://127.0.0.1:{server.server_port}/mcp',user_approved=True)
            client=ScriptedCouncilClient()
            council=ReasoningCouncil(root/'council.db')
            envelope=plan(service,council,client,jobs,conversations,None,None,job_id=job,goal='Inspect sectors')
            if client.roles!=['janus','sentinel'] or calls:raise ValueError('Planning must review both roles without dispatch')
            try:execute(service,jobs,conversations,None,None,envelope,expected_sha=digest(envelope))
            except PermissionError:pass
            else:raise ValueError('Unapproved task MCP call accepted')
            result=execute(service,jobs,conversations,None,None,envelope,expected_sha=digest(envelope),user_approved=True)
            if result['state']!='response_received' or len(calls)!=1:raise ValueError('Task call failed')
            try:execute(service,jobs,conversations,None,None,envelope,expected_sha=digest(envelope),user_approved=True)
            except ValueError:pass
            else:raise ValueError('Replay accepted')
            if len(calls)!=1:raise ValueError('Call repeated')
            history=service.history(project)
            if history[0]['task_id']!=job:raise ValueError('Receipt not task bound')
            journal=jobs.journal(job).read_text('utf-8')
            if 'Task MCP receipts' not in journal or 'response_received' not in journal:raise ValueError('Task memory receipt missing')
            recall=jobs.memory_context(jobs.get(job),original,'Inspect sectors',800)
            if 'mcp_receipt' not in recall or 'fixture sectors' in recall:raise ValueError('Bounded receipt recall failed')
            second=plan(service,council,client,jobs,conversations,None,None,job_id=job,goal='Inspect sectors again')
            conversations.amend_project('chat',project,'Do not inspect sectors; use an offline catalogue.')
            try:execute(service,jobs,conversations,None,None,second,expected_sha=digest(second),user_approved=True)
            except ValueError:pass
            else:raise ValueError('Superseded task executed')
            if len(calls)!=1:raise ValueError('Stale call dispatched')
            return {'status':'passed','detail':'Scripted JANUS/Sentinel turns, real scoped job/store and loopback invocation: exact approval, task receipt/journal recall, replay refusal and amendment blocking passed. No live model inference.'}
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
