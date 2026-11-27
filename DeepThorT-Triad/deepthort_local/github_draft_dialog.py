"""Transient explicitly approved GitHub mutation dialog; no persisted token."""
from __future__ import annotations
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .web_search import token_checked
from .github_pull_request import checked as pr_checked,create as pr_create
from .github_release import checked as release_checked,create as release_create

def show(app,mode='pull_request'):
    if mode not in ('pull_request','release'):raise ValueError('Unknown GitHub operation')
    release=mode=='release'
    checked,create=(release_checked,release_create) if release else (pr_checked,pr_create)
    noun='draft release' if release else 'draft pull request'
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat
                and not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming()
                and not app.janus.status().get('paused'))
    if not permitted():
        messagebox.showwarning('GitHub paused','Resume work and stop gaming before a network request.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title('Create GitHub '+noun);dialog.geometry('800x620');dialog.transient(app)
    ttk.Label(dialog,text=('Enter existing lightweight tag and exact commit SHA, title and notes. Token requires contents write permission. No publication or asset upload.' if release else 'Enter exact existing remote branches, title and body. No push, merge or local file upload. A GitHub token with pull-request write permission is required.'),wraplength=760).pack(anchor='w',padx=8,pady=6)
    variables={}
    for key,label in ([('repository','Owner/repository'),('tag','Existing tag'),('commit','Commit SHA'),('title','Title')] if release else [('repository','Owner/repository'),('head','Head branch'),('base','Base branch'),('title','Title')]):
        row=ttk.Frame(dialog);row.pack(fill='x',padx=8,pady=3);ttk.Label(row,text=label,width=20).pack(side='left')
        variables[key]=tk.StringVar(value='main' if key=='base' else '')
        ttk.Entry(row,textvariable=variables[key]).pack(side='left',fill='x',expand=True)
    ttk.Label(dialog,text='Release notes' if release else 'Pull request body').pack(anchor='w',padx=8)
    body=tk.Text(dialog,height=9,wrap='word');body.pack(fill='both',expand=True,padx=8,pady=4)
    status=tk.StringVar(value='No remote action performed.')
    ttk.Label(dialog,textvariable=status,wraplength=760).pack(anchor='w',padx=8,pady=4)
    result=tk.Text(dialog,height=6,wrap='word',state='disabled');result.pack(fill='x',padx=8,pady=4)
    worker=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dialog.destroy()
        else:status.set('Stopping; a transmitted remote request may still have succeeded.')
    def begin():
        nonlocal worker
        if worker is not None or not permitted():return
        try:s=checked({k:v.get() for k,v in variables.items()}|{'body':body.get('1.0','end-1c')})
        except ValueError as exc:messagebox.showwarning('Invalid draft',str(exc),parent=dialog);return
        if not messagebox.askyesno('Approve GitHub remote creation',('Check the existing tag, then create one remote draft release with these exact fields?' if release else 'Create one remote draft pull request with these exact fields?')+'\n\n'+json.dumps(s,ensure_ascii=True,indent=2)+'\n\nThese fields and token go to GitHub. No automatic retries.',parent=dialog):return
        key=simpledialog.askstring('GitHub token','Token for this request only (not saved):',show='*',parent=dialog)
        if key is None:return
        try:token_checked(key)
        except ValueError:messagebox.showwarning('Invalid token','Invalid token format.',parent=dialog);return
        if not permitted():return
        cancel.clear();app._web_research_active=True;start.state(['disabled'])
        status.set('Submitting approved draft once…')
        def work(secret):
            try:messages.put_nowait(('ok',create(s,secret,cancel.is_set,approved=True)))
            except Exception:messages.put_nowait(('uncertain',None))
        worker=threading.Thread(target=work,args=(key,),daemon=True,name='reviewed-github-draft');worker.start()
    def poll():
        nonlocal worker
        if worker is not None:
            if not permitted():cancel.set()
            if not worker.is_alive():
                try:kind,value=messages.get_nowait()
                except queue.Empty:kind,value='uncertain',None
                worker=None;app._web_research_active=False
                if closing:dialog.destroy();return
                if kind=='ok':
                    result.configure(state='normal');result.delete('1.0','end');result.insert('1.0',json.dumps(value,indent=2));result.configure(state='disabled')
                    status.set('GitHub confirmed draft creation. Close this dialog to submit a separate request.')
                else:status.set('Outcome unconfirmed. Inspect GitHub before any retry; a transmitted request may have succeeded.')
        dialog.after(150,poll)
    row=ttk.Frame(dialog);row.pack(fill='x',padx=8,pady=6)
    start=ttk.Button(row,text='Review and create draft…',command=begin);start.pack(side='left')
    ttk.Button(row,text='Close',command=close).pack(side='right')
    dialog.protocol('WM_DELETE_WINDOW',close);dialog.after(150,poll);dialog.grab_set();app.wait_window(dialog)
