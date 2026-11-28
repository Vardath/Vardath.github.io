"""Transient explicitly approved GitHub mutation dialog; no persisted token."""
from __future__ import annotations
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .web_search import token_checked
from . import credential_vault as vault
from .github_pull_request import checked as pr_checked,create as pr_create
from .github_release import checked as release_checked,create as release_create
from .github_pr_review import checked as review_checked,inspect as review_inspect

def show(app,mode='pull_request'):
    if mode not in ('pull_request','release','review'):raise ValueError('Unknown GitHub operation')
    release=mode=='release';review=mode=='review'
    checked,create=(review_checked,review_inspect) if review else (release_checked,release_create) if release else (pr_checked,pr_create)
    noun='pull request evidence' if review else 'draft release' if release else 'draft pull request'
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat
                and not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming()
                and not app.janus.status().get('paused'))
    if not permitted():
        messagebox.showwarning('GitHub paused','Resume work and stop gaming before a network request.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title(('Inspect GitHub ' if review else 'Create GitHub ')+noun);fit_dialog(dialog,800,620);dialog.transient(app)
    ttk.Label(dialog,text=('Enter exact PR number and head/base SHAs. Three read-only requests, up to 30 changed files, no review posting or merge. Token requires pull-request read permission.' if review else 'Enter existing lightweight tag and exact commit SHA, title and notes. Token requires contents write permission. No publication or asset upload.' if release else 'Enter exact existing remote branches, title and body. No push, merge or local file upload. A GitHub token with pull-request write permission is required.'),wraplength=760).pack(anchor='w',padx=8,pady=6)
    variables={}
    for key,label in ([('repository','Owner/repository'),('number','PR number'),('head_sha','Head SHA'),('base_sha','Base SHA')] if review else [('repository','Owner/repository'),('tag','Existing tag'),('commit','Commit SHA'),('title','Title')] if release else [('repository','Owner/repository'),('head','Head branch'),('base','Base branch'),('title','Title')]):
        row=ttk.Frame(dialog);row.pack(fill='x',padx=8,pady=3);ttk.Label(row,text=label,width=20).pack(side='left')
        variables[key]=tk.StringVar(value='main' if key=='base' else '')
        ttk.Entry(row,textvariable=variables[key]).pack(side='left',fill='x',expand=True)
    body=None
    if not review:
        ttk.Label(dialog,text='Release notes' if release else 'Pull request body').pack(anchor='w',padx=8)
        body=tk.Text(dialog,height=9,wrap='word');body.pack(fill='both',expand=True,padx=8,pady=4)
    status=tk.StringVar(value='No remote action performed.')
    ttk.Label(dialog,textvariable=status,wraplength=760).pack(anchor='w',padx=8,pady=4)
    result=tk.Text(dialog,height=6,wrap='word',state='disabled');result.pack(fill='both' if review else 'x',expand=review,padx=8,pady=4)
    worker=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dialog.destroy()
        else:status.set('Stopping; a transmitted remote request may still have succeeded.')
    def begin():
        nonlocal worker
        if worker is not None or not permitted():return
        try:
            fields={k:v.get() for k,v in variables.items()}
            if review:fields['number']=int(fields['number'])
            else:fields['body']=body.get('1.0','end-1c')
            s=checked(fields)
        except ValueError as exc:messagebox.showwarning('Invalid draft',str(exc),parent=dialog);return
        if not messagebox.askyesno('Approve GitHub remote creation',('Retrieve remote PR evidence with these exact commit identities?' if review else 'Check the existing tag, then create one remote draft release with these exact fields?' if release else 'Create one remote draft pull request with these exact fields?')+'\n\n'+json.dumps(s,ensure_ascii=True,indent=2)+'\n\nThese fields and token go to GitHub. No automatic retries.',parent=dialog):return
        key=None
        session=getattr(app,'_github_oauth_session',None) if review else None
        if session is not None:
            try:
                if messagebox.askyesno('Use connected account','Use the transient read-only OAuth session for '+session.login+'?',parent=dialog):key=session.token()
            except ValueError:app._github_oauth_session=None
        if key is None and vault.available() and permitted():
            if messagebox.askyesno('Use stored token','Retrieve a JANUS-owned Windows credential for '+s['repository']+' / '+mode+' for this approved request only?',parent=dialog):
                if not permitted():return
                try:key=vault.retrieve(s['repository'],mode,approved=True)
                except (OSError,ValueError):messagebox.showwarning('Credential unavailable','Stored credential unavailable; enter a token manually.',parent=dialog)
        if key is None:
            key=simpledialog.askstring('GitHub token','Token for this request (not saved unless separately approved):',show='*',parent=dialog)
            if key is not None and vault.available() and permitted():
                try:token_checked(key)
                except ValueError:pass
                else:
                    if messagebox.askyesno('Save or replace stored token','Store this token for '+s['repository']+' / '+mode+' in your Windows Credential Manager? Other processes running as your Windows user may access it. Future requests still require approval.',parent=dialog):
                        if not permitted():return
                        try:vault.save(s['repository'],mode,key,approved=True)
                        except (OSError,ValueError):messagebox.showwarning('Credential not saved','Windows credential storage failed. The token remains transient.',parent=dialog)
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
                    status.set('Read-only evidence retrieved; review patches and independently test. No review posted.' if review else 'GitHub confirmed draft creation. Close this dialog to submit a separate request.')
                else:status.set('Evidence unavailable or identity changed; no review posted.' if review else 'Outcome unconfirmed. Inspect GitHub before any retry; a transmitted request may have succeeded.')
        dialog.after(150,poll)
    def forget():
        if worker is not None or not permitted():return
        repo=variables['repository'].get()
        try:name=vault.target(repo,mode)
        except ValueError:messagebox.showwarning('Invalid repository','Enter the exact owner/repository.',parent=dialog);return
        if not messagebox.askyesno('Forget saved credential','Delete only this JANUS Windows credential?\n'+name+'\nThis does not revoke the token at GitHub.',parent=dialog):return
        if not permitted():return
        try:removed=vault.forget(repo,mode,approved=True)
        except (OSError,ValueError):messagebox.showwarning('Credential not removed','Windows credential removal failed.',parent=dialog);return
        status.set('Stored credential removed.' if removed else 'No stored credential for this purpose.')
    row=ttk.Frame(dialog);row.pack(fill='x',padx=8,pady=6)
    start=ttk.Button(row,text='Review and retrieve evidence…' if review else 'Review and create draft…',command=begin);start.pack(side='left')
    if vault.available():ttk.Button(row,text='Forget saved token…',command=forget).pack(side='left',padx=6)
    ttk.Button(row,text='Close',command=close).pack(side='right')
    dialog.protocol('WM_DELETE_WINDOW',close);dialog.after(150,poll);dialog.grab_set();app.wait_window(dialog)
