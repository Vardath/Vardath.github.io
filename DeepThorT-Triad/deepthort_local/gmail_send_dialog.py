"""Explicit final send confirmation; no saved credentials or automatic retry."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .gmail_send import checked,send

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Compose reviewed Gmail');fit_dialog(dlg,760,650);dlg.transient(app)
    fields={}
    for key,label in [('account','Sending account'),('to','Recipient'),('subject','Subject')]:
        row=ttk.Frame(dlg);row.pack(fill='x',padx=8,pady=3);ttk.Label(row,text=label,width=18).pack(side='left')
        fields[key]=tk.StringVar();ttk.Entry(row,textvariable=fields[key]).pack(side='left',fill='x',expand=True)
    ttk.Label(dlg,text='Plain-text message').pack(anchor='w',padx=8)
    body=tk.Text(dlg,wrap='word',height=14);body.pack(fill='both',expand=True,padx=8,pady=6)
    status=tk.StringVar(value='Not sent. One recipient; no attachments or automatic retry.')
    ttk.Label(dlg,textvariable=status,wraplength=720).pack(fill='x',padx=8,pady=6)
    worker=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dlg.destroy()
        else:status.set('Stopping observation; mail may already have been accepted. Inspect Sent before retry.')
    def begin():
        nonlocal worker
        if worker is not None or not permitted():return
        try:s=checked(dict({k:v.get() for k,v in fields.items()},body=body.get('1.0','end-1c')))
        except ValueError as e:messagebox.showwarning('Invalid message',str(e),parent=dlg);return
        if not messagebox.askyesno('Approve sending exactly this message','Send one email via Gmail to this recipient?\n\nFrom: '+s['account']+'\nTo: '+s['to']+'\nSubject: '+s['subject']+'\n\n'+s['body']+'\n\nNo automatic retry. Provider acceptance does not prove delivery.',parent=dlg):return
        token=simpledialog.askstring('Google access token','Transient OAuth access token with Gmail read-only and send scopes (not stored):',show='*',parent=dlg)
        if not token or not permitted():return
        start.configure(state='disabled');body.configure(state='disabled');app._web_research_active=True
        status.set('Submitting approved mail once…')
        def work(secret):
            try:messages.put(('ok',send(s,secret,cancel.is_set,approved=True)))
            except Exception:messages.put(('uncertain',None))
        worker=threading.Thread(target=work,args=(token,),daemon=True,name='gmail-reviewed-send');worker.start()
    def poll():
        nonlocal worker
        if worker is not None:
            if not permitted():cancel.set()
            if not worker.is_alive():
                app._web_research_active=False;worker=None
                if closing:dlg.destroy();return
                try:kind,value=messages.get_nowait()
                except queue.Empty:kind,value='uncertain',None
                if kind=='ok':status.set('Gmail accepted message '+value['message_id']+'. Delivery not verified.')
                else:status.set('Send outcome unconfirmed. Inspect Gmail Sent before any retry.')
        dlg.after(150,poll)
    row=ttk.Frame(dlg);row.pack(fill='x',padx=8,pady=8)
    start=ttk.Button(row,text='Review and send…',command=begin);start.pack(side='left')
    ttk.Button(row,text='Close',command=close).pack(side='right')
    dlg.protocol('WM_DELETE_WINDOW',close);dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
