"""Reviewed local Chromium DevTools probe with a disposable profile; no arbitrary CDP."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import http.client
import importlib.metadata
import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import snapshot_file,verify_guards
from deepthort_local.android_emulator import real_file
from deepthort_local.disk_gate import require_storage
from deepthort_local.structured_source import strict_json

SCHEMA='janus-browser-devtools-v1'
MAX_MESSAGE=128*1024
MAX_LOG=1024*1024
PATH_RE=re.compile(r'/devtools/browser/[0-9a-fA-F-]{36}')
METHODS={'Browser.getVersion','Target.getTargets'}

def checked(s):
    if not isinstance(s,dict) or set(s)!={'browser'} or s['browser'] not in ('chrome','edge'):
        raise ValueError('Choose installed Chrome or Edge')
    return s

def runtime(root,s,env=None):
    checked(s);env=os.environ if env is None else env
    if s['browser']=='chrome':suffix=Path('Google/Chrome/Application/chrome.exe')
    else:suffix=Path('Microsoft/Edge/Application/msedge.exe')
    for key in ('ProgramFiles','ProgramFiles(x86)','LOCALAPPDATA'):
        base=env.get(key)
        if not base or not Path(base).is_absolute():continue
        candidate=Path(base)/suffix
        if not candidate.is_file():continue
        exe=real_file(candidate)
        if exe.is_relative_to(Path(root).resolve()):raise ValueError('Project-local browser refused')
        return snapshot_file(exe,kind='stat')
    raise ValueError('Separately installed Chrome or Edge required')

def command(exe,profile):
    return [exe,'--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
            '--disable-background-networking','--disable-sync','--disable-component-update','--disable-extensions',
            '--disable-default-apps','--disable-breakpad','--disable-domain-reliability',
            '--proxy-server=http://127.0.0.1:9','--proxy-bypass-list=<-loopback>',
            '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost',
            '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0',
            '--user-data-dir='+str(profile),'about:blank']

def parse_port(raw):
    if not isinstance(raw,bytes) or not 1<=len(raw)<=256:raise ValueError('Invalid DevTools endpoint file')
    lines=raw.decode('ascii').splitlines()
    if len(lines)!=2 or not lines[0].isdecimal() or not 1024<=int(lines[0])<=65535 or not PATH_RE.fullmatch(lines[1]):
        raise ValueError('Invalid ephemeral DevTools endpoint')
    return int(lines[0]),lines[1]

def local_version(port,path):
    if type(port) is not int or not 1024<=port<=65535 or not PATH_RE.fullmatch(path):
        raise ValueError('Invalid local endpoint')
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
    try:
        conn.request('GET','/json/version',headers={'Connection':'close'})
        resp=conn.getresponse()
        if resp.status!=200:raise ValueError('DevTools version unavailable')
        raw=resp.read(MAX_MESSAGE+1)
        if not raw or len(raw)>MAX_MESSAGE:raise ValueError('Version response exceeds bound')
        result=strict_json(raw.decode('utf-8'))
        if result.get('webSocketDebuggerUrl')!=f'ws://127.0.0.1:{port}{path}':
            raise ValueError('DevTools endpoint does not match disposable profile')
        return result
    finally:conn.close()

def call(ws,method,ident):
    if method not in METHODS or type(ident) is not int or not 1<=ident<=20:raise ValueError('Unapproved DevTools command')
    ws.send(json.dumps({'id':ident,'method':method},separators=(',',':')))
    for _ in range(20):
        raw=ws.recv()
        if not isinstance(raw,str) or not 1<=len(raw)<=MAX_MESSAGE:raise ValueError('Invalid DevTools response')
        message=strict_json(raw)
        if not isinstance(message,dict):raise ValueError('Invalid DevTools message')
        if message.get('id')==ident:
            if 'error' in message or not isinstance(message.get('result'),dict):raise ValueError('DevTools command failed')
            return message['result']
        if 'id' in message:raise ValueError('Unexpected DevTools response ID')
    raise ValueError('No matching DevTools response')

def inspect(ws):
    version=call(ws,'Browser.getVersion',1);targets=call(ws,'Target.getTargets',2)
    fields={}
    for name in ('protocolVersion','product','revision','jsVersion'):
        value=version.get(name)
        if not isinstance(value,str) or not 1<=len(value)<=160 or any(ord(c)<32 for c in value):
            raise ValueError('Invalid DevTools version field')
        fields[name]=value
    rows=targets.get('targetInfos')
    if not isinstance(rows,list) or not 1<=len(rows)<=20:raise ValueError('Invalid DevTools target inventory')
    if any(not isinstance(row,dict) for row in rows):raise ValueError('Invalid target')
    pages=[row for row in rows if row.get('type')=='page']
    if len(pages)!=1 or pages[0].get('url')!='about:blank':raise ValueError('Expected only disposable blank page')
    return {'version':fields,'page_targets':1,'blank_page_verified':True,'cdp_commands':['Browser.getVersion','Target.getTargets']}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:
        raise ValueError('Missing reviewed browser runtime guard')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=runtime(root,s):raise ValueError('Reviewed browser changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(runtime(root,s))
    return plan,dict(s,command=command(plan['guards'][1]['path'],'<private disposable profile>'),
        scope='Launch installed browser with a new headless disposable profile, ephemeral loopback DevTools port and fixed blank page. Fixed read-only CDP commands, no personal profile, websites, arbitrary code or remote debugging attachment. Network-reducing flags are not an OS sandbox. Requires separately installed websocket-client; no automatic install.')

@contextmanager
def native_connection(plan,directory):
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    verify_root_cap()
    importlib.metadata.version('websocket-client')
    import websocket
    sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(directory,install=True)
    with tempfile.TemporaryDirectory(prefix='.janus-cdp-',dir=directory) as tmp:
        stage=Path(tmp);profile=stage/'profile';profile.mkdir();log=stage/'browser.log'
        verify_guards(plan['guards'])
        with child_server(command(plan['guards'][1]['path'],profile),stage,log) as (pid,alive):
            if not alive.member(pid):raise ValueError('Browser outside cleanup job')
            deadline=time.monotonic()+30;endpoint=profile/'DevToolsActivePort'
            while not endpoint.is_file():
                if not alive() or time.monotonic()>=deadline:raise ValueError('Browser DevTools did not start')
                cpu,ram=sampler.read()
                if ram is None or ram<10 or (cpu is not None and cpu>=90) or log.stat().st_size>MAX_LOG:
                    raise ValueError('Browser resource bound exceeded')
                time.sleep(.25)
            port,path=parse_port(guard.read_bound(endpoint,256))
            local_version(port,path)
            sock=socket.create_connection(('127.0.0.1',port),timeout=3)
            try:
                ws=websocket.create_connection(f'ws://127.0.0.1:{port}{path}',timeout=3,socket=sock,suppress_origin=True)
                try:yield ws
                finally:ws.close(timeout=1)
            finally:sock.close()
            if not alive() or log.stat().st_size>MAX_LOG:raise ValueError('Browser stopped or log bound exceeded')

def execute(root,plan):
    s,dst=validate(root,plan)
    with native_connection(plan,dst.parent) as ws:result=inspect(ws)
    result.update(schema=SCHEMA,browser=s['browser'],disposable_profile=True,personal_profile_used=False,
                  shared_root_cap_verified=True,cleanup_scope_closed=True,external_site_tested=False,host_sandbox=False)
    digest=guard.publish(json.dumps(result,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'devtools_connection_observed','output':plan['output'],'sha256':digest,
            'blank_page_verified':True,'external_site_tested':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Review installed browser, optional websocket-client and shared resource admission'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
