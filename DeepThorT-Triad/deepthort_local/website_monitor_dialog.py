"""Bounded website-monitor GUI and nonblocking desktop polling controller."""
from __future__ import annotations
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .website_monitor import checked_url,fetch,MIN_INTERVAL,MAX_INTERVAL,MAX_CHECKS
from .scheduled_tasks import utc_stamp

class MonitorController:
    def __init__(self,app,store):
        self.app=app;self.store=store
        self.thread=None;self.cancel=None;self.results=queue.Queue(maxsize=1)
        self.snapshot=None;self.last=-60
    def tick(self):
        app=self.app
        enabled=(not app._quitting and not app.queue_paused and not app._explicit_model_stop
                 and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
        project=app._project_key()
        if self.thread is not None:
            open_chats={i for i,_ in app.chats.list(project)}
            if not enabled or self.snapshot['project']!=project or self.snapshot['chat_id'] not in open_chats:
                self.cancel.set()
            if self.thread.is_alive():return
            try:
                result=self.results.get_nowait()
            except queue.Empty:result=None
            snapshot=self.snapshot;cancelled=self.cancel.is_set()
            self.thread=self.cancel=self.snapshot=None
            if not cancelled and enabled:
                receipt=self.store.finish(snapshot,result)
                if receipt and receipt['status']=='changed':
                    app._log(f"Website monitor #{receipt['monitor_id']}: content bytes changed. See Website monitors for evidence.")
            return
        now=time.monotonic()
        if not enabled or now-self.last<10:return
        self.last=now
        snapshot=self.store.due(project,[i for i,_ in app.chats.list(project)])
        if snapshot is None:return
        self.snapshot=snapshot;self.cancel=threading.Event();cancel=self.cancel;results=self.results
        def work():
            try:result=fetch(snapshot['url'],cancel.is_set)
            except Exception:result=None
            results.put_nowait(result)
        self.thread=threading.Thread(target=work,daemon=True,name='website-monitor')
        self.thread.start()

def show(app):
    project=app._project_key();chat=app.current_chat;store=app.website_monitors
    if not chat or chat not in {i for i,_ in app.chats.list(project)}:
        messagebox.showwarning('Monitoring unavailable','Open a chat first.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title('Website monitors');dialog.geometry('800x440');dialog.transient(app)
    ttk.Label(dialog,text='Read-only public HTTPS checks. Hashes only; page text is not saved or sent to a model. Changes may include dynamic page markup.',wraplength=770).pack(anchor='w',padx=8,pady=6)
    tree=ttk.Treeview(dialog,columns=('state','due','status','remaining','url'),show='headings',selectmode='browse')
    for key,label,width in (('state','State',75),('due','Next UTC',170),('status','Last check',110),('remaining','Remaining',80),('url','URL',330)):
        tree.heading(key,text=label);tree.column(key,width=width,stretch=key=='url')
    tree.pack(fill='both',expand=True,padx=8,pady=6)
    detail=tk.Text(dialog,height=7,wrap='word',state='disabled');detail.pack(fill='x',padx=8,pady=4)
    def refresh():
        tree.delete(*tree.get_children())
        for r in store.rows(project,chat):
            tree.insert('','end',iid=str(r['id']),values=(r['state'],utc_stamp(r['due_utc']) if r['state']=='active' else '',
                r['last_status'],r['remaining'],r['url']))
    def select(_=None):
        sel=tree.selection();detail.configure(state='normal');detail.delete('1.0','end')
        if sel:
            row=next((r for r in store.rows(project,chat) if str(r['id'])==sel[0]),None)
            if row:detail.insert('end',row['url']+'\n')
            for r in store.history(int(sel[0]),project,chat):
                detail.insert('end',f"{utc_stamp(r['checked_utc'])}: {r['status']} | {r['bytes']} bytes | {r['sha256'] or 'no observation'}\n")
        detail.configure(state='disabled')
    def add():
        if app._project_key()!=project or chat not in {i for i,_ in app.chats.list(project)}:return
        url=simpledialog.askstring('Watch public website','Exact HTTPS page URL (no query or credentials):',parent=dialog)
        if not url:return
        try:checked_url(url)
        except ValueError as exc:messagebox.showwarning('Unsupported URL',str(exc),parent=dialog);return
        interval=simpledialog.askinteger('Check interval','Minutes between checks (15–10080):',minvalue=MIN_INTERVAL//60,maxvalue=MAX_INTERVAL//60,parent=dialog)
        if interval is None:return
        count=simpledialog.askinteger('Check limit','Maximum attempts, including errors (2–1000):',minvalue=2,maxvalue=MAX_CHECKS,parent=dialog)
        if count is None:return
        if not messagebox.askyesno('Approve recurring network access',
                f'Check {url} every {interval} minutes, up to {count} attempts? The server receives the normal HTTPS request and your IP address. No cookies, credentials, redirects, page execution or model inputs.',parent=dialog):return
        try:store.create(project,chat,url,interval*60,count,approved=True);refresh()
        except ValueError as exc:messagebox.showwarning('Monitor not saved',str(exc),parent=dialog)
    def cancel():
        sel=tree.selection()
        if sel and messagebox.askyesno('Cancel monitor','Stop future checks?',parent=dialog):
            store.cancel(int(sel[0]),project,chat);refresh()
    tree.bind('<<TreeviewSelect>>',select)
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8)
    for label,action in (('New monitor…',add),('Cancel selected',cancel),('Refresh',refresh),('Close',dialog.destroy)):
        ttk.Button(bar,text=label,command=action).pack(side='left',padx=3)
    refresh();dialog.grab_set();app.wait_window(dialog)
