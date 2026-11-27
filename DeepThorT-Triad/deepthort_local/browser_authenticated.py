"""Reviewed user-authenticated disposable browser session; no credential automation."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import http.client
import importlib.metadata
import json
from pathlib import Path
import socket
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.action_guards import verify_guards
from deepthort_local.browser_devtools import runtime,parse_port,local_version,call,MAX_LOG
from deepthort_local.browser_automation import exchange,identifier
from deepthort_local.website_monitor import checked_url
from deepthort_local.website_crawling import safe_path
SCHEMA='janus-user-authenticated-browser-v1'
MAX_SECONDS=180
MARKER="Array.from(document.querySelectorAll('h1,h2,h3'), e => e.innerText.trim()).slice(0,100)"

def checked(s):
    if not isinstance(s,dict) or set(s)!={'browser','url','expected_heading','seconds'} or s['browser'] not in ('chrome','edge'):
        raise ValueError('Choose browser, exact destination, expected heading and session duration')
    _,path=checked_url(s['url']);safe_path(path)
    h=s['expected_heading']
    if not isinstance(h,str) or not 1<=len(h)<=160 or h!=h.strip() or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in h):
        raise ValueError('Choose a literal visible heading')
    if type(s['seconds']) is not int or not 30<=s['seconds']<=MAX_SECONDS:raise ValueError('Choose 30–180 seconds')
    return s

def command(exe,profile,url):
    checked_url(url)
    return [exe,'--no-first-run','--no-default-browser-check','--disable-sync','--disable-extensions',
            '--disable-background-networking','--disable-component-update','--disable-default-apps',
            '--remote-debugging-address=127.0.0.1','--remote-debugging-port=0',
            '--user-data-dir='+str(profile),'--new-window',url]

def exact_page(ws,url):
    result=call(ws,'Target.getTargets',1)
    rows=result.get('targetInfos')
    if not isinstance(rows,list) or len(rows)>30 or any(not isinstance(x,dict) for x in rows):
        raise ValueError('Unexpected browser target inventory')
    pages=[x for x in rows if x.get('type')=='page' and x.get('url')==url]
    if len(pages)!=1:raise ValueError('Open exactly one tab at the reviewed page URL')
    return identifier(pages[0].get('targetId'))

def observe(ws,s):
    checked(s)
    target=exact_page(ws,s['url'])
    session=identifier(exchange(ws,4,'Target.attachToTarget',{'targetId':target,'flatten':True}).get('sessionId'))
    def check_frame(ident):
        frame=exchange(ws,ident,'Page.getFrameTree',session=session)['frameTree']['frame']
        if frame.get('url')!=s['url']:raise ValueError('Page changed from approved URL')
    check_frame(5)
    # Host-owned code only. No cookie, storage, password, form value or profile inspection.
    result=exchange(ws,6,'Runtime.evaluate',{'expression':MARKER,'returnByValue':True},session)
    values=result.get('result',{}).get('value')
    if result.get('exceptionDetails') or not isinstance(values,list) or len(values)>100 or any(not isinstance(v,str) or len(v)>2000 for v in values):
        raise ValueError('Heading observation unavailable')
    check_frame(7)
    if s['expected_heading'] not in values:raise ValueError('Expected heading not observed')
    return {'page_url':s['url'],'expected_heading_observed':True,'user_confirmed_login':True,
            'authentication_independently_verified':False,'credentials_read':False,'cookies_exported':False}

def validate(root,plan):
    if not isinstance(plan,dict) or not isinstance(plan.get('guards'),list) or len(plan['guards'])!=2:
        raise ValueError('Missing reviewed runtime')
    s,dst,_=guard.validate(root,dict(plan,guards=plan['guards'][:1]),schema=SCHEMA,checked=checked,output_suffix='.json')
    if plan['guards'][1]!=runtime(root,{'browser':s['browser']}):raise ValueError('Reviewed browser changed')
    return s,dst

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json')
    plan['guards'].append(runtime(root,{'browser':s['browser']}))
    return plan,dict(s,scope='Open a visible disposable browser with normal website networking. You manually sign in, navigate to the exact approved page, and confirm in a separate local dialog. JANUS then checks only the exact page and expected heading. No password entry, cookie export, personal profile attachment, automatic navigation or submission. Site login and redirects are user-operated and may affect remote state. Temporary profile contains browser data until cleanup; this is not an OS sandbox.')

def confirmation(s,alive,deadline,sampler,log,*,research=False):
    import tkinter as tk
    from tkinter import ttk
    window=tk.Tk();window.title('JANUS — confirm manual browser sign-in')
    window.geometry('640x250');accepted=[False]
    ttk.Label(window,text='Sign in yourself in the separate browser, then return to this dialog.\\nDo not enter your password here.',wraplength=600).pack(padx=12,pady=12)
    ttk.Label(window,text='Approved page: '+s['url'],wraplength=600).pack(padx=12,pady=4)
    ttk.Label(window,text=('Collect visible text from section: '+s['expected_heading']+'; private text will be saved locally.' if research else 'Confirm only after the reviewed page is open.'),wraplength=600).pack(padx=12,pady=8)
    def confirm():
        accepted[0]=True;window.destroy()
    ttk.Button(window,text='I signed in; collect approved section locally' if research else 'I signed in; inspect this page',command=confirm).pack(pady=5)
    ttk.Button(window,text='Cancel',command=window.destroy).pack(pady=5)
    def monitor():
        try:
            cpu,ram=sampler.read()
            if not alive() or time.monotonic()>=deadline or ram is None or ram<10 or (cpu is not None and cpu>=90) or log.stat().st_size>MAX_LOG:
                window.destroy();return
            window.after(500,monitor)
        except Exception:window.destroy()
    window.after(500,monitor);window.mainloop()
    if not accepted[0] or not alive() or time.monotonic()>=deadline:
        raise ValueError('Manual sign-in cancelled or timed out')

@contextmanager
def user_session(plan,s,*,research=False):
    from deepthort_local.triad_job import verify_root_cap,child_server
    from deepthort_local.quiet_playtest import WindowsPressureSampler
    from deepthort_local.disk_gate import require_storage
    verify_root_cap();importlib.metadata.version('websocket-client')
    import websocket
    sampler=WindowsPressureSampler();_,ram=sampler.read()
    if ram is None or ram<15:raise ValueError('Insufficient RAM reserve')
    require_storage(Path(tempfile.gettempdir()),install=True)
    # Never store the browser's temporary profile in the project or attach to an existing one.
    with tempfile.TemporaryDirectory(prefix='janus-user-browser-') as tmp:
        stage=Path(tmp);profile=stage/'profile';profile.mkdir();log=stage/'browser.log'
        verify_guards(plan['guards'])
        with child_server(command(plan['guards'][-1]['path'],profile,s['url']),stage,log) as (pid,alive):
            if not alive.member(pid):raise ValueError('Browser outside cleanup job')
            deadline=time.monotonic()+s['seconds'];endpoint=profile/'DevToolsActivePort'
            while not endpoint.is_file():
                if not alive() or time.monotonic()>=deadline:raise ValueError('Browser did not start')
                time.sleep(.25)
            port,path=parse_port(guard.read_bound(endpoint,256))
            confirmation(s,alive,deadline,sampler,log,research=research)
            verify_guards(plan['guards'])
            local_version(port,path)
            sock=socket.create_connection(('127.0.0.1',port),timeout=3)
            try:
                ws=websocket.create_connection(f'ws://127.0.0.1:{port}{path}',timeout=3,socket=sock,suppress_origin=True)
                try:yield ws
                finally:ws.close(timeout=1)
            finally:sock.close()

def execute(root,plan):
    s,dst=validate(root,plan)
    with user_session(plan,s) as ws:r=observe(ws,s)
    r.update(schema=SCHEMA,disposable_profile=True,personal_profile_used=False,profile_cleanup_completed=True,
             shared_root_cap_verified=True,host_sandbox=False)
    sha=guard.publish(json.dumps(r,sort_keys=True,indent=2).encode(),dst,lambda:validate(root,plan))
    return {'schema':SCHEMA,'status':'user_confirmed_page_observed','output':plan['output'],'sha256':sha,
            'authentication_independently_verified':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Manual sign-in or reviewed page observation unavailable; inspect site state before retrying'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
