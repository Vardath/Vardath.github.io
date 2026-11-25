"""Supervised, discovery-only stdio MCP sessions.
A trusted wrapper and its server descendants share the existing Windows
root CPU/commit cap and a small nested commit cap. No shell, server install,
tool calls or persistent process. Closing the nested job kills descendants.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
import tempfile
import queue
import threading
import subprocess
from pathlib import Path
from .local_mcp import typed_tool,VERSIONS,MAX_REPLY,MAX_PAGES,MAX_TOOLS
from .structured_source import strict_json
from .tool_workflows import digest
from .action_guards import snapshot_file,verify_guards

MEMORY_LIMIT=256*1024**2
MAX_ARGS=16
MAX_SECONDS=30
BLOCKED={'cmd.exe','powershell.exe','pwsh.exe','wscript.exe','cscript.exe','mshta.exe','rundll32.exe','regsvr32.exe','bash.exe','sh.exe','wsl.exe'}
def prepare(project,executable,args):
    root=Path(project).resolve(strict=True)
    exe=Path(executable)
    if not root.is_dir() or not exe.is_absolute() or exe.is_symlink() or not exe.is_file():
        raise ValueError('Select an existing absolute executable and project folder')
    exe=exe.resolve(strict=True)
    if exe.suffix.casefold()!='.exe' or exe.name.casefold() in BLOCKED:
        raise ValueError('Choose an installed native server executable; shell launchers are not accepted')
    if not isinstance(args,list) or len(args)>MAX_ARGS or any(
        not isinstance(x,str) or not x or len(x)>500 or any(c in x for c in ('\x00','\r','\n'))
        for x in args):raise ValueError('Enter a bounded JSON argument array')
    # No credentials or network values are needed by this discovery-only
    # transport. The user still sees the exact arguments and must trust code.
    if any(re.search(r'(?i)://|password|secret|token|api[-_]?key|credential|authorization',x) for x in args):
        raise ValueError('Credential/network arguments not supported')
    guards=[snapshot_file(exe,kind='stat')]
    # Pin explicit existing file arguments; reject missing absolute paths.
    for arg in args:
        p=Path(arg)
        if p.is_absolute():
            if p.is_symlink() or not p.is_file():raise ValueError('Absolute argument must be a real existing file')
            guard=snapshot_file(p.resolve())
            if guard['path'] not in [g['path'] for g in guards]:guards.append(guard)
    if len(guards)>10:raise ValueError('Too many pinned executable inputs')
    return {'project':str(root),'argv':[str(exe),*args],'guards':guards}

def stdio_discover(argv,cwd):
    """Runs only inside the supervised wrapper in production. One server."""
    env={k:v for k,v in os.environ.items() if k.upper() in {
        'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT','TEMP','TMP','USERPROFILE',
        'LOCALAPPDATA','APPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
    # Wrapper and descendants are already in the nested Windows job;
    # no CREATE_BREAKAWAY_FROM_JOB, no shell.
    process=subprocess.Popen(argv,cwd=cwd,env=env,stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                             shell=False,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    incoming=queue.Queue(maxsize=2)
    done=threading.Event()
    def read():
        try:
            while not done.is_set():
                line=process.stdout.readline(MAX_REPLY+1)
                if not line or len(line)>MAX_REPLY:
                    incoming.put(None,timeout=.5);return
                incoming.put(line,timeout=.5)
        except (OSError,ValueError,queue.Full):pass
    thread=threading.Thread(target=read,daemon=True);thread.start()
    deadline=time.monotonic()+20
    ident=0
    def send(method,params=None,notification=False):
        nonlocal ident
        body={'jsonrpc':'2.0','method':method}
        if params is not None:body['params']=params
        if not notification:
            ident+=1;body['id']=ident
        process.stdin.write(json.dumps(body,separators=(',',':')).encode()+b'\n')
        process.stdin.flush()
        if notification:return None
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('Stdio MCP deadline exceeded')
        try:line=incoming.get(timeout=min(5,remaining))
        except queue.Empty as error:raise TimeoutError('No bounded MCP reply') from error
        if not line:raise ValueError('Stdio MCP response absent or oversized')
        msg=strict_json(line.decode('utf-8'))
        if (not isinstance(msg,dict) or msg.get('jsonrpc')!='2.0' or
            type(msg.get('id')) is not int or msg['id']!=ident or 'error' in msg
            or not isinstance(msg.get('result'),dict)):
            raise ValueError('Unexpected stdio MCP reply; server requests/notifications unsupported')
        return msg['result']
    try:
        first=send('initialize',{'protocolVersion':VERSIONS[0],'capabilities':{},
                    'clientInfo':{'name':'DeepThorT-Triad','version':'20'}})
        version=first.get('protocolVersion');capabilities=first.get('capabilities')
        if version not in VERSIONS or not isinstance(capabilities,dict) or not isinstance(capabilities.get('tools'),dict):
            raise ValueError('Unsupported protocol or missing tool capability')
        send('notifications/initialized',notification=True)
        tools=[];names=set();cursor=None;seen=set()
        for _ in range(MAX_PAGES):
            page=send('tools/list',{'cursor':cursor} if cursor is not None else {})
            if not isinstance(page.get('tools'),list):raise ValueError('Invalid tool list')
            for raw in page['tools']:
                tool=typed_tool(raw)
                if tool['name'] in names:raise ValueError('Duplicate tool')
                names.add(tool['name']);tools.append(tool)
                if len(tools)>MAX_TOOLS:raise ValueError('Too many tools')
            cursor=page.get('nextCursor')
            if cursor is None:break
            if not isinstance(cursor,str) or not 1<=len(cursor)<=512 or cursor in seen:
                raise ValueError('Invalid pagination')
            seen.add(cursor)
        else:raise ValueError('Too many pages')
        return {'protocol':version,'tools':sorted(tools,key=lambda x:x['name'])}
    finally:
        done.set()
        # Root wrapper cleanup job also kills descendants, including any
        # grandchildren after the direct server process exits.
        if process.poll() is None:process.kill()
        process.wait(timeout=3)

def discover(proposal,*,expected_sha,user_approved=False,cancelled=None):
    if user_approved is not True:raise PermissionError('Exact server launch approval required')
    proposal=strict_json(json.dumps(proposal,ensure_ascii=True,allow_nan=False))
    if digest(proposal)!=expected_sha:raise ValueError('Server proposal changed')
    current=prepare(proposal['project'],proposal['argv'][0],proposal['argv'][1:])
    if current!=proposal:raise ValueError('Server executable or input changed')
    if cancelled and cancelled():raise ValueError('Discovery cancelled')
    from .triad_job import child_server,verify_root_cap
    cap,available,total=verify_root_cap()
    if available<total//10+MEMORY_LIMIT:
        raise RuntimeError('Insufficient foreground memory reserve for supervised server')
    with tempfile.TemporaryDirectory(prefix='triad-mcp-supervised-') as folder:
        root=Path(folder);config=root/'request.json';result=root/'result.json'
        config.write_text(json.dumps(proposal,ensure_ascii=True),encoding='utf-8')
        wrapper=Path(__file__).resolve().parents[1]/'mcp_stdio_worker.py'
        # Use the current interpreter, a fixed bundled wrapper, and no shell.
        with child_server([sys.executable,str(wrapper),str(config),str(result)],
                          root,root/'wrapper.log',memory_limit=MEMORY_LIMIT) as (pid,alive):
            deadline=time.monotonic()+MAX_SECONDS
            while alive():
                if (cancelled and cancelled()) or time.monotonic()>=deadline:
                    raise TimeoutError('Supervised discovery stopped; cleanup job closed')
                time.sleep(.1)
            if alive.code()!=0:
                raise ValueError('Supervised server discovery failed (wrapper exit '+str(alive.code())+')')
        if not result.is_file() or result.stat().st_size>MAX_REPLY:raise ValueError('Missing bounded discovery result')
        data=strict_json(result.read_text('utf-8'))
        if not isinstance(data,dict) or set(data)!={'protocol','tools'}:raise ValueError('Invalid wrapper result')
        return data

class StdioCatalog:
    def __init__(self,janus):
        self.janus=janus
        with janus.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS mcp_stdio_catalog(
                project TEXT NOT NULL, profile_sha TEXT NOT NULL, payload TEXT NOT NULL,
                observed REAL NOT NULL, PRIMARY KEY(project,profile_sha))""")
    def save(self,proposal,result):
        root=proposal['project'];key=digest(proposal)
        payload=json.dumps(result,ensure_ascii=True)
        if len(payload)>MAX_REPLY:raise ValueError('Inventory exceeds bound')
        with self.janus.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM mcp_stdio_catalog WHERE project=?',(root,)).fetchone()[0]>=12 and not db.execute(
                'SELECT 1 FROM mcp_stdio_catalog WHERE project=? AND profile_sha=?',(root,key)).fetchone():
                raise ValueError('Stdio catalog full')
            db.execute('INSERT OR REPLACE INTO mcp_stdio_catalog VALUES(?,?,?,?)',(root,key,payload,time.time()))
        return key
    def list(self,project):
        with self.janus.connect() as db:
            rows=db.execute('SELECT profile_sha,payload,observed FROM mcp_stdio_catalog WHERE project=? ORDER BY observed DESC LIMIT 12',
                            (str(Path(project).resolve()),)).fetchall()
        return [{'profile_sha':key,'tools':json.loads(payload)['tools'],'observed':stamp} for key,payload,stamp in rows]
    def remove(self,project,key,*,user_approved=False):
        if user_approved is not True:raise PermissionError('Explicit removal required')
        with self.janus.connect() as db:
            return bool(db.execute('DELETE FROM mcp_stdio_catalog WHERE project=? AND profile_sha=?',
                (str(Path(project).resolve()),key)).rowcount)
