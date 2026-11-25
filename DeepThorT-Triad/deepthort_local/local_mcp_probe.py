"""Real loopback HTTP exchange with an isolated synthetic MCP server."""
import json
import tempfile
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .janus_engine import JanusStore
from .local_mcp import LocalMCP,Discovery,endpoint

def exercise():
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            msg=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method=msg['method'];requests.append(method)
            if method=='initialize':
                result={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
            elif self.headers.get('Mcp-Session-Id')!='fixture-session' or self.headers.get('MCP-Protocol-Version')!='2025-11-25':
                self.send_error(400);return
            elif method=='notifications/initialized':
                self.send_response(202);self.end_headers();return
            elif method=='tools/list':
                if msg['params'].get('cursor')=='page2':
                    result={'tools':[{'name':'inspect_mesh','inputSchema':{'type':'object','properties':{'path':{'type':'string'}},'required':['path']}}]}
                else:
                    result={'tools':[{'name':'inspect_scene','description':'UNTRUSTED_FIXTURE_INSTRUCTION','inputSchema':{'type':'object','properties':{'detail':{'type':'boolean','default':True}}}}],'nextCursor':'page2'}
            else:self.send_error(405);return
            data=json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':result}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)))
            if method=='initialize':self.send_header('Mcp-Session-Id','fixture-session')
            self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix='triad-mcp-test-') as folder:
            root=Path(folder);project=root/'project';project.mkdir();other=root/'other';other.mkdir()
            url=f'http://127.0.0.1:{server.server_port}/mcp'
            catalog=LocalMCP(JanusStore(root/'janus.db'))
            try:catalog.discover(project,url)
            except PermissionError:pass
            else:return {'status':'failed','detail':'Unapproved discovery permitted'}
            result=catalog.discover(project,url,user_approved=True)
            if requests!=['initialize','notifications/initialized','tools/list','tools/list']:
                return {'status':'failed','detail':'Unexpected MCP method sequence'}
            if [x['name'] for x in result['tools']]!=['inspect_mesh','inspect_scene'] or 'UNTRUSTED_FIXTURE_INSTRUCTION' in str(result):
                return {'status':'failed','detail':'Typed tool inventory invalid'}
            reopened=LocalMCP(JanusStore(root/'janus.db'))
            if len(reopened.list(project))!=1 or reopened.list(other):
                return {'status':'failed','detail':'MCP catalog persistence or scope failed'}
            try:Discovery(url).post('tools/call')
            except ValueError:pass
            else:return {'status':'failed','detail':'Discovery client allowed execution'}
            if not reopened.remove(project,url,user_approved=True) or reopened.list(project):
                return {'status':'failed','detail':'MCP catalog removal failed'}
            return {'status':'passed','detail':'Actual loopback JSON-RPC handshake and paginated tool discovery passed; typed metadata, consent, persistence, scope, removal and call refusal verified. Synthetic server only.'}
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
