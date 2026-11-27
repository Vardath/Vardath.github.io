"""User-controlled transient network research; secrets never enter prompts or disk."""
from __future__ import annotations
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .web_search import query_checked,token_checked,search

def show(app):
    if getattr(app,'_web_research_active',False):
        messagebox.showinfo('Research busy','Finish the previous network request first.',parent=app);return
    if app._quitting or app.queue_paused or app._explicit_model_stop or app.disk_gate.gaming() or app.janus.status().get('paused'):
        messagebox.showwarning('Research paused','Resume work and stop gaming before a network request.',parent=app);return
    project=app._project_key();chat=app.current_chat
    dialog=tk.Toplevel(app);dialog.title('General internet search');dialog.geometry('820x500');dialog.transient(app)
    ttk.Label(dialog,text='Brave Search API. A user-supplied key and active provider account are required. Only the entered query is sent. Snippets are not verified page contents.',wraplength=790).pack(anchor='w',padx=8,pady=6)
    output=tk.Text(dialog,wrap='word',state='disabled');output.pack(fill='both',expand=True,padx=8,pady=6)
    status=tk.StringVar(value='No network request performed.')
    ttk.Label(dialog,textvariable=status,wraplength=790).pack(anchor='w',padx=8)
    result=None;worker=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat
                and not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming()
                and not app.janus.status().get('paused'))
    def finish_close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dialog.destroy()
        else:status.set('Cancelling; waiting for the bounded network worker to exit.')
    def begin():
        nonlocal worker,result
        if worker is not None or not permitted():return
        query=simpledialog.askstring('Exact web query','Enter only the public search terms to send to Brave:',parent=dialog)
        if not query:return
        count=simpledialog.askinteger('Search result limit','Maximum results (1–20):',minvalue=1,maxvalue=20,initialvalue=10,parent=dialog)
        if count is None:return
        try:query_checked(query,count)
        except ValueError as exc:messagebox.showwarning('Invalid search',str(exc),parent=dialog);return
        if not messagebox.askyesno('Approve one network search',
            f'Send this exact query to Brave Search API?\n\n{query}\n\nUp to {count} results. Your IP, query and API token go to Brave; provider charges and terms may apply. No local project files or conversation history are sent.',parent=dialog):return
        token=simpledialog.askstring('Brave Search API key','Key for this request only (not saved):',show='*',parent=dialog)
        if token is None:return
        try:token_checked(token)
        except ValueError:messagebox.showwarning('Invalid key','Enter a valid provider token.',parent=dialog);return
        if not permitted():return
        result=None;cancel.clear();app._web_research_active=True
        start.state(['disabled']);copy.state(['disabled']);status.set('Searching approved provider…')
        output.configure(state='normal');output.delete('1.0','end');output.configure(state='disabled')
        def work(key):
            try:messages.put_nowait(('ok',search(query,count,key,cancel.is_set,approved=True)))
            except Exception:messages.put_nowait(('error',None))
        worker=threading.Thread(target=work,args=(token,),daemon=True,name='reviewed-web-search');worker.start()
    def poll():
        nonlocal worker,result
        if worker is not None:
            if not permitted():cancel.set()
            if not worker.is_alive():
                try:kind,value=messages.get_nowait()
                except queue.Empty:kind,value='error',None
                worker=None;app._web_research_active=False
                if closing:dialog.destroy();return
                start.state(['!disabled'])
                if cancel.is_set():status.set('Request stopped; late results discarded.')
                elif kind=='ok':
                    result=value;output.configure(state='normal');output.delete('1.0','end')
                    output.insert('1.0',json.dumps(result,ensure_ascii=True,indent=2))
                    output.configure(state='disabled');copy.state(['!disabled'])
                    status.set('Search completed. No sources opened; evidence remains unverified.')
                else:status.set('Search failed: check network, provider key, quota or response format. No result claimed.')
        dialog.after(150,poll)
    def copy_results():
        if result is None:return
        if not messagebox.askyesno('Copy provider results','Copy these unverified search rows as JSON? Retain or reuse only if your provider plan permits.',parent=dialog):return
        dialog.clipboard_clear();dialog.clipboard_append(json.dumps(result['supplied_results'],ensure_ascii=True,indent=2))
        status.set('Copied supplied-result JSON. Use Interpret search results for reviewed project publication.')
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8)
    start=ttk.Button(bar,text='Search…',command=begin);start.pack(side='left',padx=3)
    copy=ttk.Button(bar,text='Copy supplied results',command=copy_results,state='disabled');copy.pack(side='left',padx=3)
    ttk.Button(bar,text='Cancel request',command=cancel.set).pack(side='left',padx=3)
    ttk.Button(bar,text='Close',command=finish_close).pack(side='right',padx=3)
    dialog.protocol('WM_DELETE_WINDOW',finish_close);dialog.after(150,poll);dialog.grab_set();app.wait_window(dialog)
