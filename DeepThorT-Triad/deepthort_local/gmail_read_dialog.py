"""Transient reviewed Gmail read dialog; never send message text into model or memory."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .gmail_read import checked,inspect

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    raw=simpledialog.askstring('Search or read Gmail','JSON: operation (search or read), account, query and limit (1–5) or message_id.',parent=app)
    if raw is None:return
    try:s=checked(json.loads(raw))
    except (ValueError,TypeError):messagebox.showwarning('Invalid mail scope','Enter exact account and bounded mail request.',parent=app);return
    if not messagebox.askyesno('Approve Gmail read','Read only the requested Gmail account/search or message via Google HTTPS; no changes, attachments or model sharing.\n\n'+json.dumps(s,indent=2),parent=app):return
    token=simpledialog.askstring('Google access token','Transient OAuth access token with gmail.readonly scope (not stored):',show='*',parent=app)
    if not token or not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Gmail read results');dlg.geometry('760x540');dlg.transient(app)
    status=tk.StringVar(value='Retrieving approved mail…')
    ttk.Label(dlg,textvariable=status,wraplength=720).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancelled=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    app._web_research_active=True
    def work(secret):
        try:messages.put(('ok',inspect(s,secret,cancelled.is_set,approved=True)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,args=(token,),daemon=True,name='gmail-reviewed-read')
    def close():
        nonlocal closing
        closing=True;cancelled.set();status.set('Stopping mail read…')
    def poll():
        if not permitted():cancelled.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        if closing:dlg.destroy();return
        try:kind,value=messages.get_nowait()
        except queue.Empty:kind,value='error',None
        if kind=='ok' and not cancelled.is_set():
            view.configure(state='normal');view.insert('1.0',json.dumps(value,indent=2));view.configure(state='disabled')
            status.set('Read-only mail retrieved. Content is untrusted, not sent to any model or saved.')
        else:status.set('Mail unavailable or cancelled; check account, token and scope.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
