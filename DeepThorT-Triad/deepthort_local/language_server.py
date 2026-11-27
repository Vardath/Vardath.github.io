"""Reviewed local LSP session against bundled Python syntax/symbol provider."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.python_language_server import frame,read,URI,MAX_MESSAGE
SCHEMA='janus-language-server-v1'
EXTRA=('document','.py')
MAX_SOURCE=120000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'document'} or not isinstance(s['document'],str):
        raise ValueError('Expected a project-relative Python document')
    return s
def analyze(raw):
    if len(raw)>MAX_SOURCE:raise ValueError('Python source exceeds limit')
    text=raw.decode('utf-8-sig')
    def request(method,params=None,i=None):
        m={'jsonrpc':'2.0','method':method}
        if params is not None:m['params']=params
        if i is not None:m['id']=i
        return frame(m)
    packet=b''.join([request('initialize',{'processId':None,'rootUri':None,'capabilities':{}},1),
        request('initialized',{}),request('textDocument/didOpen',{'textDocument':{'uri':URI,'languageId':'python','version':1,'text':text}}),
        request('textDocument/documentSymbol',{'textDocument':{'uri':URI}},2),request('shutdown',None,3),request('exit')])
    worker=Path(__file__).with_name('python_language_server.py').resolve(strict=True)
    run=subprocess.run([sys.executable,'-I','-B',str(worker)],input=packet,capture_output=True,timeout=10,check=True)
    if len(run.stdout)>3*MAX_MESSAGE:raise ValueError('Language server response exceeds bound')
    stream=io.BytesIO(run.stdout);init,diag,symbols,shutdown=[read(stream) for _ in range(4)]
    if read(stream) is not None or init.get('id')!=1 or init['result']['capabilities']['positionEncoding']!='utf-16' or diag.get('method')!='textDocument/publishDiagnostics' or diag['params']['uri']!=URI or symbols.get('id')!=2 or shutdown.get('id')!=3 or shutdown.get('result') is not None:
        raise ValueError('Invalid language server response')
    return {'schema':'janus-language-server-result-v1','source_sha256':hashlib.sha256(raw).hexdigest(),
            'server':init['result']['serverInfo'],'position_encoding':'utf-16',
            'diagnostics':diag['params']['diagnostics'],'symbols':symbols['result'],
            'scope':'Real bounded LSP stdio session for Python AST syntax diagnostics and direct class/function symbols only. No type checking, project import, references or arbitrary server execution.'}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    if doc.stat().st_size>MAX_SOURCE:raise ValueError('Python source exceeds limit')
    return plan,dict(s,scope='Run bundled Python language server on exact reviewed source bytes, never import or execute document.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);r=analyze(guard.exact(doc,plan['guards'][1],MAX_SOURCE))
    digest=guard.publish(json.dumps(r,ensure_ascii=True,allow_nan=False,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'status':'language_server_session_completed','output':plan['output'],'sha256':digest,
            'diagnostics':len(r['diagnostics']),'top_level_symbols':len(r['symbols']),'source_executed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Language server inspection unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
