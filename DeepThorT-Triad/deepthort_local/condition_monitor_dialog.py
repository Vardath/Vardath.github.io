"""Reviewed project condition watch UI and cooperative polling."""
from __future__ import annotations
import json
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .condition_monitor import checked,observe,MIN_INTERVAL,MAX_INTERVAL,MAX_CHECKS
from .scheduled_tasks import utc_stamp

class ConditionController:
    def __init__(self,app,store):
        self.app=app;self.store=store;self.thread=None;self.cancel=None
        self.results=queue.Queue(maxsize=1);self.snapshot=None;self.exclude=None;self.last=-60
    def tick(self):
        app=self.app;project=app._project_key()
        enabled=(project!='(general)' and not app._quitting and not app.queue_paused and
                 not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
        if self.thread is not None:
            if (not enabled or self.snapshot['project']!=project or self.snapshot['chat_id'] not in {i for i,_ in app.chats.list(project)}
                    or self.exclude!=app.inspection_exclusions.paths(project)):
                self.cancel.set()
            if self.thread.is_alive():return
            try:result=self.results.get_nowait()
            except queue.Empty:result=None
            snapshot=self.snapshot;cancelled=self.cancel.is_set()
            self.thread=self.cancel=self.snapshot=self.exclude=None
            if not cancelled and enabled:
                receipt=self.store.finish(snapshot,result)
                if receipt and receipt['status'] in ('became_true','became_false'):
                    app._log(f"Condition watch #{receipt['watch_id']}: {receipt['status']}. See Condition watches.")
            return
        now=time.monotonic()
        if not enabled or now-self.last<5:return
        self.last=now
        snapshot=self.store.due(project,[i for i,_ in app.chats.list(project)])
        if snapshot is None:return
        exclude=set(app.inspection_exclusions.paths(project));self.exclude=exclude
        self.snapshot=snapshot;self.cancel=threading.Event();cancel=self.cancel;results=self.results
        def work():
            try:result=observe(project,json.loads(snapshot['spec']),exclude,cancel.is_set)
            except Exception:result=None
            results.put_nowait(result)
        self.thread=threading.Thread(target=work,daemon=True,name='condition-watch')
        self.thread.start()

def show(app):
    project=app._project_key();chat=app.current_chat;store=app.condition_watches
    if project=='(general)' or not chat or chat not in {i for i,_ in app.chats.list(project)}:
        messagebox.showwarning('Condition monitoring unavailable','Open a project chat first.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title('Condition watches');fit_dialog(dialog,820,440);dialog.transient(app)
    ttk.Label(dialog,text='Monitor exact local project files with fixed read-only predicates. No arbitrary scripts, page reads or new execution grants.',wraplength=790).pack(anchor='w',padx=8,pady=6)
    tree=ttk.Treeview(dialog,columns=('state','due','status','remaining','condition'),show='headings',selectmode='browse')
    for key,label,width in (('state','State',75),('due','Next UTC',165),('status','Last observation',135),('remaining','Remaining',80),('condition','Condition',350)):
        tree.heading(key,text=label);tree.column(key,width=width,stretch=key=='condition')
    tree.pack(fill='both',expand=True,padx=8,pady=6)
    detail=tk.Text(dialog,height=7,wrap='word',state='disabled');detail.pack(fill='x',padx=8,pady=4)
    def refresh():
        tree.delete(*tree.get_children())
        for r in store.rows(project,chat):
            s=json.loads(r['spec'])
            tree.insert('','end',iid=str(r['id']),values=(r['state'],utc_stamp(r['due_utc']) if r['state']=='active' else '',
                r['last_status'],r['remaining'],s['kind']+' | '+s['path']))
    def select(_=None):
        sel=tree.selection();detail.configure(state='normal');detail.delete('1.0','end')
        if sel:
            row=next((r for r in store.rows(project,chat) if str(r['id'])==sel[0]),None)
            if row:detail.insert('end',row['spec']+'\n')
            for r in store.history(int(sel[0]),project,chat):
                detail.insert('end',f"{utc_stamp(r['checked_utc'])}: {r['status']} | {r['observation'] or 'no observation'}\n")
        detail.configure(state='disabled')
    def add():
        if app._project_key()!=project or chat not in {i for i,_ in app.chats.list(project)}:return
        p=simpledialog.askstring('File condition','Exact workspace-relative file path (use / separators):',parent=dialog)
        if not p:return
        kind=simpledialog.askstring('Predicate','Choose exists, missing, size_at_least or sha256_equals:',initialvalue='exists',parent=dialog)
        if not kind:return
        s={'path':p,'kind':kind}
        if kind=='size_at_least':
            v=simpledialog.askinteger('Byte threshold','Minimum file size in bytes:',minvalue=1,maxvalue=2**40,parent=dialog)
            if v is None:return
            s['value']=v
        elif kind=='sha256_equals':
            v=simpledialog.askstring('Expected hash','Exact lowercase SHA-256:',parent=dialog)
            if v is None:return
            s['value']=v
        try:checked(s)
        except ValueError as exc:messagebox.showwarning('Invalid predicate',str(exc),parent=dialog);return
        interval=simpledialog.askinteger('Check interval','Minutes between checks (1–10080):',minvalue=MIN_INTERVAL//60,maxvalue=MAX_INTERVAL//60,parent=dialog)
        if interval is None:return
        count=simpledialog.askinteger('Attempt limit','Maximum checks, including errors (2–1000):',minvalue=2,maxvalue=MAX_CHECKS,parent=dialog)
        if count is None:return
        if not messagebox.askyesno('Approve finite condition watch',
            f'Check {json.dumps(s,ensure_ascii=True)} every {interval} minutes for up to {count} attempts? Only metadata and optional bounded file hash are recorded.',parent=dialog):return
        try:store.create(project,chat,s,interval*60,count,approved=True,exclude=app.inspection_exclusions.paths(project));refresh()
        except (OSError,ValueError) as exc:messagebox.showwarning('Watch not saved',str(exc),parent=dialog)
    def cancel():
        sel=tree.selection()
        if sel and messagebox.askyesno('Cancel condition watch','Stop future checks?',parent=dialog):
            store.cancel(int(sel[0]),project,chat);refresh()
    tree.bind('<<TreeviewSelect>>',select)
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8)
    for label,action in (('New condition…',add),('Cancel selected',cancel),('Refresh',refresh),('Close',dialog.destroy)):
        ttk.Button(bar,text=label,command=action).pack(side='left',padx=3)
    refresh();dialog.grab_set();app.wait_window(dialog)
