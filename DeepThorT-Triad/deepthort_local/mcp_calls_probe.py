"""Actual loopback invocation against an isolated synthetic server."""
import json
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .janus_engine import JanusStore
from .mcp_calls import MCPCalls
from .tool_workflows import digest

def exercise():
    calls=[];schema={'type':'object','properties':{'count':{'type':'integer','minimum':1,'maximum':3}},'required':['count']}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            msg=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method=msg['method']
            if method=='initialize':
                result={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
            elif method=='notifications/initialized':
                self.send_response(202);self.end_headers();return
            elif method=='tools/list':result={'tools':[{'name':'inspect','inputSchema':schema}]}
            elif method=='tools/call':
                calls.append(msg['params'])
                result={'content':[{'type':'text','text':'synthetic result'}],'isError':False}
            else:self.send_error(405);return
            data=json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':result}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='triad-mcp-call-') as folder:
            root=Path(folder);project=root/'project';project.mkdir();other=root/'other';other.mkdir()
            url=f'http://127.0.0.1:{server.server_port}/mcp'
            service=MCPCalls(JanusStore(root/'janus.db'))
            service.catalog.discover(project,url,user_approved=True)
            proposal=service.prepare(project,url,'inspect',{'count':2})
            try:service.call(proposal,expected_sha=digest(proposal))
            except PermissionError:pass
            else:raise ValueError('Unapproved call accepted')
            wrong=service.prepare(project,url,'inspect',{'count':True})
            try:service.call(wrong,expected_sha=digest(wrong),user_approved=True)
            except ValueError:pass
            else:raise ValueError('Invalid type accepted')
            result=service.call(proposal,expected_sha=digest(proposal),user_approved=True)
            if calls!=[{'name':'inspect','arguments':{'count':2}}] or result['state']!='response_received':
                raise ValueError('Unexpected invocation')
            reopened=MCPCalls(JanusStore(root/'janus.db'))
            history=reopened.history(project)
            if len(history)!=1 or history[0]['result_sha']!=result['result_sha'] or reopened.history(other):
                raise ValueError('Receipt persistence or project scope failed')
            schema['properties']['count']['maximum']=4
            try:service.call(proposal,expected_sha=digest(proposal),user_approved=True)
            except ValueError:pass
            else:raise ValueError('Changed schema accepted')
            if len(calls)!=1:raise ValueError('Unexpected repeated call')
            return {'status':'passed','detail':'Real loopback tools/call: exact approval, scalar schema validation, fresh schema check, one dispatch, durable scoped hash receipt and stale-schema rejection passed; synthetic server.'}
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
