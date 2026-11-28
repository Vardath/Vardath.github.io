"""User-reviewed finite local webhook receiver; secret only in memory."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .webhook_receiver import listen,checked

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not permitted():return
    event=simpledialog.askstring('Webhook event','Exact event name, for example push:',parent=app)
    if not event:return
    secret=simpledialog.askstring('Local test secret','Enter a dedicated local webhook test secret (16–128 printable ASCII characters); not stored:',show='*',parent=app)
    if not secret:return
    try:checked(event,secret,60)
    except ValueError as e:messagebox.showwarning('Invalid webhook session',str(e),parent=app);return
    if not messagebox.askyesno('Approve local webhook receiver','Listen for one HMAC-signed '+event+' delivery for up to 60 seconds on 127.0.0.1 only? No public listener, payload retention or task execution.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Local signed webhook receiver');fit_dialog(dlg,740,360);dlg.transient(app)
    state=tk.StringVar(value='Starting local listener…')
    ttk.Label(dlg,textvariable=state,wraplength=700).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancel=threading.Event();messages=queue.Queue();closing=False
    app._web_research_active=True
    def worker(key):
        try:messages.put(('receipt',listen(event,key,60,lambda port:messages.put(('port',port)),cancel.is_set,approved=True)))
        except Exception:messages.put(('ended',None))
    thread=threading.Thread(target=worker,args=(secret,),daemon=True,name='local-webhook-receiver');secret=None
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping local listener…')
    def poll():
        if not permitted():cancel.set()
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='port' and not cancel.is_set():state.set('Local sender endpoint: http://127.0.0.1:'+str(value)+'/webhook — one signed '+event+' delivery.')
                elif kind=='receipt' and not cancel.is_set():
                    view.configure(state='normal');view.insert('1.0',json.dumps(value,indent=2));view.configure(state='disabled')
                    state.set('Signed local delivery received; listener closed. No task submitted.')
                elif kind=='ended':state.set('Listener closed without a retained delivery.')
        except queue.Empty:pass
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        if closing:dlg.destroy();return
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
