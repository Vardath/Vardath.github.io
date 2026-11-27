"""Explicit local developer API session, separate from the internal broker token."""
import os
import queue
import secrets
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from .openai_gateway import serve,broker

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not permitted():return
    if not messagebox.askyesno('Approve local developer API','Enable an authenticated loopback-only developer endpoint for up to 120 seconds of admission and two Granite text-completion attempts? No tools, project access, persistent conversation or remote binding. An admitted broker inference may continue after session cancellation; use Stop AI if necessary.',parent=app):return
    if not permitted():return
    key=secrets.token_urlsafe(32);internal=os.environ.get('DEEPTHORT_TRIAD_TOKEN','')
    dlg=tk.Toplevel(app);dlg.title('Local developer API');dlg.geometry('780x300');dlg.transient(app)
    state=tk.StringVar(value='Opening local developer endpoint…')
    ttk.Label(dlg,textvariable=state,wraplength=740).pack(fill='x',padx=8,pady=8)
    ttk.Label(dlg,text='Temporary API key (local clients only; not the internal broker key):').pack(anchor='w',padx=8)
    entry=ttk.Entry(dlg,width=65);entry.insert(0,key);entry.configure(state='readonly');entry.pack(fill='x',padx=8,pady=8)
    ttk.Label(dlg,text='Supports GET /v1/models and non-streaming POST /v1/chat/completions. Use the displayed base URL. No tool calls or usage counts. Cancel stops further admissions; an admitted inference may finish later.',wraplength=740).pack(fill='x',padx=8,pady=8)
    cancel=threading.Event();messages=queue.Queue();closing=False;app._web_research_active=True
    def work(external):
        try:messages.put(('done',serve(external,lambda p:broker(p,internal),lambda port:messages.put(('port',port)),cancel.is_set,approved=True)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,args=(key,),daemon=True,name='local-developer-api');key=None
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping admissions; an admitted inference may still be running.')
    def poll():
        if not permitted():cancel.set()
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='port' and not cancel.is_set():state.set('Base URL: http://127.0.0.1:'+str(value)+'/v1')
                elif kind=='done':state.set('Session ended. Completion attempts: '+str(value['completion_attempts']))
                elif kind=='error':state.set('Local developer API closed.')
        except queue.Empty:pass
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        entry.configure(state='normal');entry.delete(0,'end');entry.configure(state='readonly')
        if closing:dlg.destroy();return
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel admissions',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll)
    # Non-modal so the owner's existing Stop AI control remains accessible.
