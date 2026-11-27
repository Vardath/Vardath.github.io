"""Explicit local developer API session, separate from the internal broker token."""
import os
import queue
import secrets
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from .openai_gateway import serve,broker
from .developer_status import status
from .task_submission import Inbox

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not permitted():return
    if not messagebox.askyesno('Approve local developer API','Enable an authenticated loopback-only developer endpoint for up to 120 seconds of admission and two Granite text-completion attempts? No tools, project access, persistent conversation or remote binding. An admitted broker inference may continue after session cancellation; use Stop AI if necessary.',parent=app):return
    if not permitted():return
    read_status=None
    if chat and messagebox.askyesno('Optional current-chat status','Also expose read-only job and conversation IDs, modes and states for this exact selected project/chat? No paths, prompts, results, files or new actions.',parent=app):
        if not permitted():return
        jobs_path,requests_path=app.jobs.path,app.conversations.path
        read_status=lambda:status(jobs_path,requests_path,project,chat,approved=True)
    if not permitted():return
    inbox=None
    if chat and messagebox.askyesno('Optional external task inbox','Accept up to two external prompts into a temporary review inbox for this exact project/chat? Each prompt requires your separate review before creating an ordinary conversation. No automatic execution or new permission.',parent=app):
        if not permitted():return
        inbox=Inbox(project,chat,approved=True)
    if not permitted():return
    key=secrets.token_urlsafe(32);internal=os.environ.get('DEEPTHORT_TRIAD_TOKEN','')
    dlg=tk.Toplevel(app);dlg.title('Local developer API');dlg.geometry('780x520');dlg.transient(app)
    state=tk.StringVar(value='Opening local developer endpoint…')
    ttk.Label(dlg,textvariable=state,wraplength=740).pack(fill='x',padx=8,pady=8)
    ttk.Label(dlg,text='Temporary API key (local clients only; not the internal broker key):').pack(anchor='w',padx=8)
    entry=ttk.Entry(dlg,width=65);entry.insert(0,key);entry.configure(state='readonly');entry.pack(fill='x',padx=8,pady=8)
    ttk.Label(dlg,text='Supports GET /v1/models and non-streaming POST /v1/chat/completions. Use the displayed base URL. No tool calls or usage counts. Cancel stops further admissions; an admitted inference may finish later.',wraplength=740).pack(fill='x',padx=8,pady=8)
    if read_status is not None:ttk.Label(dlg,text='Current-chat metadata enabled: GET /janus/v1/status (same host and key).').pack(anchor='w',padx=8)
    cancel=threading.Event();messages=queue.Queue();closing=False;app._web_research_active=True
    if inbox is not None:
        ttk.Label(dlg,text='Task inbox enabled: POST /janus/v1/tasks. Exact incoming prompts require review.').pack(anchor='w',padx=8)
        inbox_view=tk.Text(dlg,height=7,wrap='word',state='disabled');inbox_view.pack(fill='both',expand=True,padx=8,pady=4)
        def refresh_inbox():
            rows=inbox.pending()
            inbox_view.configure(state='normal');inbox_view.delete('1.0','end')
            if rows:inbox_view.insert('1.0',rows[0][1])
            inbox_view.configure(state='disabled')
            review_button.configure(state='normal' if rows and permitted() and not cancel.is_set() else 'disabled')
        def review_first():
            if not permitted() or cancel.is_set():return
            rows=inbox.pending()
            if not rows:return
            ident,prompt=rows[0]
            if not messagebox.askyesno('Approve exact incoming conversation',prompt+'\n\nCreate this ordinary conversation request? No build or tool execution is approved.',parent=dlg):return
            if not permitted() or cancel.is_set():return
            try:
                request=inbox.review(ident,prompt,app._project_key(),app.current_chat,app.conversations.submit,approved=True)
                app._reload_chat();state.set('Conversation request #'+str(request)+' saved; no execution approved.')
            except Exception:state.set('Admission unconfirmed; inspect conversation before any new submission.')
            refresh_inbox()
        review_button=ttk.Button(dlg,text='Review and admit first prompt…',command=review_first,state='disabled');review_button.pack(pady=4)
    def work(external):
        try:messages.put(('done',serve(external,lambda p:broker(p,internal),lambda port:messages.put(('port',port)),cancel.is_set,approved=True,status_reader=read_status,task_receiver=inbox.receive if inbox is not None else None)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,args=(key,),daemon=True,name='local-developer-api');key=None
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if inbox is not None:inbox.discard()
        state.set('Stopping admissions; unreviewed prompts discarded.')
    def poll():
        if not permitted():
            cancel.set()
            if inbox is not None:inbox.discard()
        if inbox is not None:refresh_inbox()
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
        if inbox is not None:
            def finish():
                inbox.discard();dlg.destroy()
        else:finish=dlg.destroy
        button.configure(text='Close',command=finish);dlg.protocol('WM_DELETE_WINDOW',finish)
        if inbox is not None:
            def poll_review():
                if not permitted():cancel.set();inbox.discard()
                refresh_inbox();dlg.after(300,poll_review)
            dlg.after(300,poll_review)
    button=ttk.Button(dlg,text='Cancel admissions',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll)
    # Non-modal so the owner's existing Stop AI control remains accessible.
