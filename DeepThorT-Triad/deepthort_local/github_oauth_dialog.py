"""User-directed GitHub device authorization, session held only in process memory."""
from __future__ import annotations
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .github_oauth import connect,client_id,VERIFY
def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return not app._quitting and app._project_key()==project and app.current_chat==chat and not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused')
    if not permitted():return
    old=getattr(app,'_github_oauth_session',None)
    if old:
        try:old.token()
        except ValueError:app._github_oauth_session=None
        else:
            if messagebox.askyesno('Connected GitHub account','Connected as '+old.login+'. Disconnect local session? This does not revoke provider authorization.',parent=app):
                old.disconnect();app._github_oauth_session=None
            return
    client=simpledialog.askstring('Registered GitHub OAuth client','Enter your own registered public GitHub OAuth application client ID with device flow enabled. No client secret.',parent=app)
    if not client:return
    try:client_id(client)
    except ValueError as e:messagebox.showwarning('Invalid OAuth client',str(e),parent=app);return
    if not messagebox.askyesno('Approve GitHub device authorization','Request read:user access via GitHub device flow, verify identity and keep token in local process memory for up to 15 minutes? No repository write access is requested. Approve only your own trusted OAuth application.',parent=app):return
    if not permitted():return
    dialog=tk.Toplevel(app);dialog.title('GitHub device authorization');dialog.geometry('640x250');dialog.transient(app)
    state=tk.StringVar(value='Requesting device code…')
    ttk.Label(dialog,textvariable=state,wraplength=600).pack(fill='x',padx=12,pady=12)
    ttk.Label(dialog,text='Open '+VERIFY+' in your own browser. Enter only the displayed code and check application identity before authorizing.',wraplength=600).pack(fill='x',padx=12,pady=8)
    cancel=threading.Event();messages=queue.Queue();closing=False;app._web_research_active=True
    def worker():
        try:
            session=connect(client,lambda code:messages.put(('code',code)),cancel.is_set,approved=True,wait=cancel.wait)
            messages.put(('session',session))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=worker,daemon=True,name='github-device-auth');thread.start()
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping device authorization…')
    def poll():
        if not permitted():cancel.set()
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='code' and not cancel.is_set():state.set('Device code: '+value+' — waiting for authorization.')
                elif kind=='session':
                    if cancel.is_set():value.disconnect()
                    else:app._github_oauth_session=value;state.set('Connected as '+value.login+'. Read-only session retained in memory for up to 15 minutes.')
                elif kind=='error':state.set('Authorization unsuccessful or cancelled; no session retained.')
        except queue.Empty:pass
        if not thread.is_alive():
            app._web_research_active=False
            if closing:dialog.destroy();return
            button.configure(text='Close',command=dialog.destroy);dialog.protocol('WM_DELETE_WINDOW',dialog.destroy)
        else:dialog.after(150,poll)
    button=ttk.Button(dialog,text='Cancel',command=close);button.pack(pady=10)
    dialog.protocol('WM_DELETE_WINDOW',close);dialog.after(150,poll);dialog.grab_set();app.wait_window(dialog)
