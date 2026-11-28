"""Explicitly approved account inventory, using only the existing transient OAuth session."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .github_account import inspect,MAX_PAGE

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    session=getattr(app,'_github_oauth_session',None)
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused') and getattr(app,'_github_oauth_session',None) is session)
    if not permitted():return
    if session is None:
        messagebox.showwarning('GitHub account unavailable','Connect your GitHub account first.',parent=app);return
    try:session.token()
    except ValueError:
        messagebox.showwarning('Session expired','Reconnect your GitHub account.',parent=app);return
    page=simpledialog.askinteger('Public repositories','Page of up to 30 public repositories owned by '+session.login+' (1–10):',minvalue=1,maxvalue=MAX_PAGE,parent=app)
    if page is None:return
    if not messagebox.askyesno('Approve account inventory','Use the connected read-only session to verify account identity and retrieve public repository page '+str(page)+'? Three HTTPS GET requests; no changes or private repository access.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('GitHub account inventory');fit_dialog(dlg,760,540);dlg.transient(app)
    state=tk.StringVar(value='Retrieving approved public repository page…')
    ttk.Label(dlg,textvariable=state,wraplength=720).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancelled=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    app._web_research_active=True
    def work():
        try:messages.put(('ok',inspect(session,page,cancelled.is_set,approved=True)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,daemon=True,name='github-account-inventory')
    def close():
        nonlocal closing
        closing=True;cancelled.set();state.set('Stopping account inventory…')
    def poll():
        if not permitted():cancelled.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        if closing:dlg.destroy();return
        try:kind,value=messages.get_nowait()
        except queue.Empty:kind,value='error',None
        if kind=='ok' and not cancelled.is_set():
            view.configure(state='normal');view.insert('1.0',json.dumps(value,indent=2));view.configure(state='disabled')
            state.set('Public page retrieved. Inventory is bounded; no repository was cloned or changed.')
        else:state.set('Account inventory unavailable or cancelled.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
