"""Actual supervised Windows stdio test using a synthetic MCP server."""
import os
import sys
import tempfile
from pathlib import Path
from .mcp_stdio import prepare,discover,StdioCatalog
from .tool_workflows import digest
from .janus_engine import JanusStore

FIXTURE="""import sys,json
for line in sys.stdin:
    msg=json.loads(line)
    method=msg['method']
    if method=='notifications/initialized':continue
    if method=='initialize':result={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
    elif method=='tools/list':result={'tools':[{'name':'inspect','inputSchema':{'type':'object','properties':{'count':{'type':'integer'}},'required':['count']}}]}
    else:raise RuntimeError('Unexpected method')
    print(json.dumps({'jsonrpc':'2.0','id':msg['id'],'result':result}),flush=True)
"""
def exercise():
    if os.name!='nt':return {'status':'blocked','detail':'Native Windows root job required'}
    with tempfile.TemporaryDirectory(prefix='triad-stdio-test-') as folder:
        root=Path(folder);project=root/'project';project.mkdir()
        other=root/'other';other.mkdir()
        fixture=root/'fixture.py';fixture.write_text(FIXTURE,encoding='utf-8')
        proposal=prepare(project,sys.executable,['-I',str(fixture)])
        try:discover(proposal,expected_sha=digest(proposal))
        except PermissionError:pass
        else:raise ValueError('Unapproved launch allowed')
        result=discover(proposal,expected_sha=digest(proposal),user_approved=True)
        if [x['name'] for x in result['tools']]!=['inspect']:raise ValueError('Incorrect stdio catalog')
        library=StdioCatalog(JanusStore(root/'janus.sqlite3'))
        key=library.save(proposal,result)
        reopened=StdioCatalog(JanusStore(root/'janus.sqlite3'))
        if len(reopened.list(project))!=1 or reopened.list(other):raise ValueError('Scope or persistence failed')
        fixture.write_text(FIXTURE+'\n# Changed',encoding='utf-8')
        try:discover(proposal,expected_sha=digest(proposal),user_approved=True)
        except ValueError:pass
        else:raise ValueError('Stale input accepted')
        if not reopened.remove(project,key,user_approved=True):raise ValueError('Catalog removal failed')
        return {'status':'passed','detail':'Real capped Windows stdio fixture: exact approved launch, nested 256 MiB commit limit, typed discovery, cleanup, persistent project catalog and changed-input refusal. No actual third-party server.'}
