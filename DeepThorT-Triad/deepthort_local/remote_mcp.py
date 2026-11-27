"""Explicit remote public HTTPS MCP discovery. No tools/call or credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import socket
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.local_mcp import Discovery,MAX_REPLY
from deepthort_local.website_monitor import checked_url,resolve_public,PinnedHTTPS
from deepthort_local.structured_source import strict_json
SCHEMA='janus-remote-mcp-discovery-v1'

def checked(s):
    if not isinstance(s,dict) or set(s)!={'url'}:raise ValueError('Expected one reviewed HTTPS MCP endpoint')
    host,path=checked_url(s['url'])
    if not re.fullmatch(r'/[A-Za-z0-9_./~-]{0,250}',path) or path.startswith('//') or any(p in ('.','..') for p in path.split('/')):
        raise ValueError('Use an explicit endpoint path without traversal or encoded segments')
    return s

class RemoteDiscovery(Discovery):
    def __init__(self,url,cancelled=None,*,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
        checked({'url':url});self.host,self.path=checked_url(url)
        self.cancelled=cancelled;self.deadline=time.monotonic()+30
        self.version=None;self.session=None;self.ident=0;self.connection=connection
        self.remaining();self.ip=resolve_public(self.host,resolver);self.remaining()
    def _exchange(self,method,params=None,*,notification=False):
        if method not in ('initialize','notifications/initialized','tools/list') or notification!=(method=='notifications/initialized'):
            raise ValueError('Only remote discovery methods allowed')
        body={'jsonrpc':'2.0','method':method}
        if params is not None:body['params']=params
        if not notification:self.ident+=1;body['id']=self.ident
        headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream',
                 'Accept-Encoding':'identity','Connection':'close','User-Agent':'JANUS-remote-mcp/1'}
        if self.version:headers['MCP-Protocol-Version']=self.version
        if self.session:headers['Mcp-Session-Id']=self.session
        self.remaining();conn=self.connection(self.host,self.ip)
        try:
            conn.request('POST',self.path,body=json.dumps(body,ensure_ascii=True).encode('ascii'),headers=headers)
            response=conn.getresponse();self.remaining()
            expected=202 if notification else 200
            if response.status!=expected:raise ValueError('Unexpected MCP status; redirects and authentication not supported')
            session=response.getheader('Mcp-Session-Id')
            if session is not None:
                if not re.fullmatch(r'[!-~]{1,200}',session) or self.session and session!=self.session:
                    raise ValueError('Invalid or changed remote MCP session')
                self.session=session
            if notification:return None
            if response.getheader('Content-Type','').split(';')[0].strip().lower()!='application/json' or response.getheader('Content-Encoding','identity').lower()!='identity':
                raise ValueError('Only uncompressed JSON responses supported')
            length=response.getheader('Content-Length')
            if length is not None and (not length.isdecimal() or not 0<int(length)<=MAX_REPLY):raise ValueError('Remote reply exceeds bound')
            data=bytearray()
            while True:
                self.remaining();chunk=response.read1(min(8192,MAX_REPLY-len(data)+1));self.remaining()
                if not chunk:break
                data.extend(chunk)
                if len(data)>MAX_REPLY:raise ValueError('Remote reply exceeds bound')
            if length is not None and len(data)!=int(length):raise ValueError('Incomplete remote MCP response')
            msg=strict_json(data.decode('utf-8'))
            if not isinstance(msg,dict) or msg.get('jsonrpc')!='2.0' or type(msg.get('id')) is not int or msg['id']!=self.ident or 'error' in msg or not isinstance(msg.get('result'),dict):
                raise ValueError('Remote MCP response did not match request')
            return msg['result']
        finally:conn.close()
def discover(s,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit remote MCP discovery approval required')
    checked(s);result=RemoteDiscovery(s['url'],cancelled,resolver=resolver,connection=connection).discover()
    return {'schema':'janus-remote-mcp-evidence-v1','endpoint':s['url'],**result,'tools_called':False,
            'scope':'Public HTTPS JSON discovery only, tool names, typed field summaries and schema hashes. No credentials, server instructions, SSE, resources, prompts or execution authority.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    return plan,dict(s,scope='Send MCP initialize, initialized notification and up to four tools/list POSTs to exact public HTTPS endpoint; no project data, credentials or tool calls.')
def execute(root,plan):
    s,dst,_=validate(root,plan);r=discover(s,approved=True)
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'remote_mcp_discovered','output':plan['output'],'sha256':digest,'tools':len(r['tools']),'tools_called':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Remote MCP discovery unavailable; inspect reviewed endpoint and JSON support'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
