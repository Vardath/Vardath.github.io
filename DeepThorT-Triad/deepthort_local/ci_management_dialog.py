"""Transient reviewed GitHub Actions evidence; no remote mutation or token storage."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .ci_management import checked,inspect

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    raw=simpledialog.askstring('Inspect GitHub CI','JSON: repository, run_id, commit, required_jobs (list of exact names).',parent=app)
    if raw is None:return
    try:s=checked(json.loads(raw))
    except (ValueError,TypeError):messagebox.showwarning('Invalid CI scope','Enter exact run and required job identities.',parent=app);return
    if not messagebox.askyesno('Approve CI observation','Read exact GitHub workflow attempt and jobs (three GET requests); no merge, rerun or deployment.\n\n'+json.dumps(s,indent=2),parent=app):return
    token=simpledialog.askstring('GitHub token','Transient Actions-read token (not stored):',show='*',parent=app)
    if not token or not permitted():return
    dlg=tk.Toplevel(app);dlg.title('GitHub Actions evidence');dlg.geometry('760x540');dlg.transient(app)
    status=tk.StringVar(value='Retrieving reviewed CI evidence…')
    ttk.Label(dlg,textvariable=status,wraplength=720).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancelled=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    app._web_research_active=True
    def work(secret):
        try:messages.put(('ok',inspect(s,secret,cancelled.is_set,approved=True)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,args=(token,),daemon=True,name='github-ci-observation')
    def close():
        nonlocal closing
        closing=True;cancelled.set();status.set('Stopping CI observation…')
    def poll():
        if not permitted():cancelled.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        if closing:dlg.destroy();return
        try:kind,value=messages.get_nowait()
        except queue.Empty:kind,value='error',None
        if kind=='ok' and not cancelled.is_set():
            view.configure(state='normal');view.insert('1.0',json.dumps(value,indent=2));view.configure(state='disabled')
            status.set('Required jobs observed green; no authority granted.' if value['required_jobs_green'] else 'CI is not verified green.')
        else:status.set('CI evidence unavailable or cancelled.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
