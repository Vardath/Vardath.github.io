"""Small local Python language server; LSP stdio, no project imports or execution."""
from __future__ import annotations
import ast
import json
import sys
MAX_MESSAGE=1024*1024
URI='file:///janus-reviewed.py'

def frame(value):
    raw=json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')
    if len(raw)>MAX_MESSAGE:raise ValueError('LSP message exceeds bound')
    return b'Content-Length: '+str(len(raw)).encode('ascii')+b'\r\n\r\n'+raw

def read(stream):
    first=stream.readline(128)
    if not first:return None
    if not first.startswith(b'Content-Length: ') or not first.endswith(b'\r\n') or stream.readline(128)!=b'\r\n':
        raise ValueError('Invalid LSP header')
    n=int(first[16:-2])
    if not 1<=n<=MAX_MESSAGE:raise ValueError('Invalid LSP body length')
    raw=stream.read(n)
    if len(raw)!=n:raise ValueError('Incomplete LSP message')
    value=json.loads(raw)
    if not isinstance(value,dict) or value.get('jsonrpc')!='2.0':raise ValueError('Invalid JSON-RPC')
    return value

def position(lines,line,bytecol):
    text=lines[line-1].encode('utf-8')[:bytecol].decode('utf-8')
    return {'line':line-1,'character':len(text.encode('utf-16-le'))//2}
def inspect(text):
    if not isinstance(text,str) or len(text)>120000:raise ValueError('Source exceeds LSP bound')
    lines=text.split('\n')
    try:tree=ast.parse(text)
    except SyntaxError as e:
        line=max(1,min(e.lineno or 1,len(lines)))
        col=max(0,min((e.offset or 1)-1,len(lines[line-1])))
        point={'line':line-1,'character':len(lines[line-1][:col].encode('utf-16-le'))//2}
        return [{'range':{'start':point,'end':point},'severity':1,'source':'janus-python-ast','message':str(e.msg)[:300]}],[]
    symbols=[]
    def visit(nodes,depth):
        if depth>16:raise ValueError('Symbol nesting exceeds bound')
        result=[]
        for n in nodes:
            if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                if len(symbols)>=512:raise ValueError('Symbol count exceeds bound')
                kind=5 if isinstance(n,ast.ClassDef) else 12
                a=position(lines,n.lineno,n.col_offset)
                b=position(lines,n.end_lineno,n.end_col_offset)
                item={'name':n.name,'kind':kind,'range':{'start':a,'end':b},
                      'selectionRange':{'start':a,'end':a}}
                symbols.append(item);children=visit(n.body,depth+1)
                if children:item['children']=children
                result.append(item)
        return result
    return [],visit(tree.body,0)

def response(i,result):return {'jsonrpc':'2.0','id':i,'result':result}
def serve(src,dst):
    state=0;symbols=[]
    for _ in range(8):
        m=read(src)
        if m is None:raise ValueError('LSP ended before exit')
        method=m.get('method');p=m.get('params',{})
        reply=None
        if state==0 and method=='initialize':
            reply=response(m['id'],{'capabilities':{'textDocumentSync':1,'documentSymbolProvider':True,'positionEncoding':'utf-16'},
                                    'serverInfo':{'name':'JANUS Python AST','version':'1'}});state=1
        elif state==1 and method=='initialized':state=2
        elif state==2 and method=='textDocument/didOpen':
            doc=p['textDocument']
            if doc['uri']!=URI or doc['languageId']!='python':raise ValueError('Invalid reviewed document')
            diagnostics,symbols=inspect(doc['text'])
            reply={'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':URI,'version':doc['version'],'diagnostics':diagnostics}}
            state=3
        elif state==3 and method=='textDocument/documentSymbol' and p['textDocument']['uri']==URI:
            reply=response(m['id'],symbols);state=4
        elif state==4 and method=='shutdown':reply=response(m['id'],None);state=5
        elif state==5 and method=='exit':return
        else:raise ValueError('Unsupported LSP lifecycle or method')
        if reply is not None:dst.write(frame(reply));dst.flush()
    raise ValueError('Incomplete LSP session')

def main():
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(5,5))
        serve(sys.stdin.buffer,sys.stdout.buffer);return 0
    except Exception:return 2
if __name__=='__main__':sys.exit(main())
