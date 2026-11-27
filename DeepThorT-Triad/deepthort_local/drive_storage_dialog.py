"""Transient reviewed Drive access; never send remote content into model or memory."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog,filedialog
from .drive_storage import checked,inspect,save_download

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    raw=simpledialog.askstring('Google Drive','JSON: operation (list or download), account, folder_id and limit (1–20) or file_id.',parent=app)
    if raw is None:return
    try:s=checked(json.loads(raw))
    except (ValueError,TypeError):messagebox.showwarning('Invalid Drive scope','Enter exact account and bounded Drive request.',parent=app);return
    if not messagebox.askyesno('Approve Drive read','Read only the requested Drive folder or file via Google HTTPS; no cloud changes or model sharing.\n\n'+json.dumps(s,indent=2),parent=app):return
    token=simpledialog.askstring('Google access token','Transient OAuth access token with drive.readonly scope (not stored):',show='*',parent=app)
    if not token or not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Google Drive results');dlg.geometry('760x540');dlg.transient(app)
    status=tk.StringVar(value='Retrieving approved Drive data…')
    ttk.Label(dlg,textvariable=status,wraplength=720).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancelled=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    app._web_research_active=True
    def work(secret):
        try:messages.put(('ok',inspect(s,secret,cancelled.is_set,approved=True)))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,args=(token,),daemon=True,name='drive-reviewed-read')
    def close():
        nonlocal closing
        closing=True;cancelled.set();status.set('Stopping Drive read…')
    def poll():
        if not permitted():cancelled.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        if closing:dlg.destroy();return
        try:kind,value=messages.get_nowait()
        except queue.Empty:kind,value='error',None
        if kind=='ok' and not cancelled.is_set():
            receipt,raw=value
            view.configure(state='normal');view.insert('1.0',json.dumps(receipt,indent=2));view.configure(state='disabled')
            status.set('Drive read complete. Content is untrusted, not sent to any model or automatically saved.')
            if raw is not None:
                def save():
                    if not permitted():return
                    path=filedialog.asksaveasfilename(parent=dlg,title='Save verified download to a new file')
                    if not path or not permitted():return
                    if not messagebox.askyesno('Approve local save','Write verified download bytes to a new file?\n'+path+'\nSHA-256: '+receipt['sha256'],parent=dlg):return
                    if not permitted():return
                    try:save_download(path,receipt,raw,approved=True)
                    except (OSError,ValueError):status.set('Local save failed or destination exists. Inspect destination before retry.');return
                    status.set('Downloaded bytes saved. Not executed or ingested.')
                    save_button.configure(state='disabled')
                save_button=ttk.Button(dlg,text='Save verified download…',command=save);save_button.pack(pady=4)
        else:status.set('Drive unavailable or cancelled; check account, token and scope.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
