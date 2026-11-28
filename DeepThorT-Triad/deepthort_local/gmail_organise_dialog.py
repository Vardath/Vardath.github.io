"""Two-stage inbox organisation: approved read, then exact reviewed mutations."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .gmail_organise import checked,preview,apply

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    raw=simpledialog.askstring('Organise Gmail','JSON: account, query, limit (1–5), add (label IDs), remove (label IDs). Archive uses remove INBOX. No deletion.',parent=app)
    if raw is None:return
    try:s=checked(json.loads(raw))
    except (ValueError,TypeError) as e:messagebox.showwarning('Invalid inbox rule',str(e),parent=app);return
    if not messagebox.askyesno('Approve read-only preview','Search and inspect these bounded messages? No writes yet.\n\n'+json.dumps(s,indent=2),parent=app):return
    token=simpledialog.askstring('Google access token','Transient OAuth token with gmail.modify scope (not stored):',show='*',parent=app)
    if not token or not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Review inbox organisation');fit_dialog(dlg,800,650);dlg.transient(app)
    status=tk.StringVar(value='Retrieving read-only preview…')
    ttk.Label(dlg,textvariable=status,wraplength=760).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    worker=None;plan=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def launch(fn):
        nonlocal worker
        cancel.clear();app._web_research_active=True
        def work():
            try:messages.put(('ok',fn()))
            except Exception:messages.put(('error',None))
        worker=threading.Thread(target=work,daemon=True,name='gmail-reviewed-organise');worker.start()
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dlg.destroy()
        else:status.set('Stopping. A transmitted change may have succeeded; inspect Gmail before retry.')
    def commit():
        if worker is not None or plan is None or not permitted():return
        if not messagebox.askyesno('Approve exact inbox changes','Apply label changes to the '+str(len(plan['rows']))+' exact message IDs displayed? No delete or retry. Partial completion is possible.',parent=dlg):return
        button.configure(state='disabled');status.set('Applying reviewed changes once…')
        launch(lambda:apply(plan,token,cancel.is_set,approved=True))
    def poll():
        nonlocal worker,plan
        if worker is not None:
            if not permitted():cancel.set()
            if not worker.is_alive():
                worker=None;app._web_research_active=False
                if closing:dlg.destroy();return
                try:kind,value=messages.get_nowait()
                except queue.Empty:kind,value='error',None
                if kind=='ok' and not cancel.is_set():
                    view.configure(state='normal');view.delete('1.0','end');view.insert('1.0',json.dumps(value,indent=2));view.configure(state='disabled')
                    if 'rows' in value:
                        plan=value
                        if plan['rows']:button.configure(state='normal');status.set('Review exact IDs and before/after labels. Preview expires after five minutes.')
                        else:status.set('No changes needed in this bounded preview.')
                    else:status.set('Operation complete or stopped. Inspect the receipt; no automatic retry.')
                else:status.set('Unavailable, cancelled or uncertain. Inspect Gmail before retrying.')
        dlg.after(150,poll)
    row=ttk.Frame(dlg);row.pack(fill='x',padx=8,pady=8)
    button=ttk.Button(row,text='Approve displayed changes…',command=commit,state='disabled');button.pack(side='left')
    ttk.Button(row,text='Close',command=close).pack(side='right')
    dlg.protocol('WM_DELETE_WINDOW',close);launch(lambda:preview(s,token,cancel.is_set,approved=True));dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
