"""Single explicitly reviewed Mastodon text publishing dialog."""
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .social_publish import checked,publish

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and
                not app.janus.status().get('paused'))
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Publish reviewed Mastodon post');dlg.geometry('720x510');dlg.transient(app)
    ttk.Label(dlg,text='mastodon.social username (without @)').pack(anchor='w',padx=8,pady=4)
    account=tk.StringVar();ttk.Entry(dlg,textvariable=account).pack(fill='x',padx=8)
    visibility=tk.StringVar(value='unlisted')
    ttk.Label(dlg,text='Visibility').pack(anchor='w',padx=8,pady=4)
    ttk.Combobox(dlg,textvariable=visibility,values=('unlisted','public'),state='readonly').pack(anchor='w',padx=8)
    ttk.Label(dlg,text='Post text (up to 400 characters)').pack(anchor='w',padx=8,pady=4)
    body=tk.Text(dlg,wrap='word',height=8);body.pack(fill='both',expand=True,padx=8)
    status=tk.StringVar(value='Not published. One post only; no automatic retry.')
    ttk.Label(dlg,textvariable=status,wraplength=680).pack(fill='x',padx=8,pady=6)
    worker=None;cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False
    def close():
        nonlocal closing
        closing=True;cancel.set()
        if worker is None:dlg.destroy()
        else:status.set('Stopping observation; post may already exist. Inspect account before retry.')
    def begin():
        nonlocal worker
        if worker is not None or not permitted():return
        try:s=checked({'account':account.get(),'visibility':visibility.get(),'text':body.get('1.0','end-1c')})
        except ValueError as e:messagebox.showwarning('Invalid post',str(e),parent=dlg);return
        if not messagebox.askyesno('Approve publishing exactly this text','Publish one '+s['visibility']+' post as @'+s['account']+'@mastodon.social?\n\n'+s['text']+'\n\nThis is a remote publication. No automatic retry.',parent=dlg):return
        token=simpledialog.askstring('Mastodon access token','Transient token with read:accounts and write:statuses scopes (not stored):',show='*',parent=dlg)
        if not token or not permitted():return
        start.configure(state='disabled');body.configure(state='disabled');app._web_research_active=True
        status.set('Submitting approved post once…')
        def work(secret):
            try:messages.put(('ok',publish(s,secret,cancel.is_set,approved=True)))
            except Exception:messages.put(('uncertain',None))
        worker=threading.Thread(target=work,args=(token,),daemon=True,name='mastodon-reviewed-post');worker.start()
    def poll():
        nonlocal worker
        if worker is not None:
            if not permitted():cancel.set()
            if not worker.is_alive():
                app._web_research_active=False;worker=None
                if closing:dlg.destroy();return
                try:kind,value=messages.get_nowait()
                except queue.Empty:kind,value='uncertain',None
                if kind=='ok':status.set('Provider accepted post '+value['post_id']+'. Rendered text and reach not verified.')
                else:status.set('Publication outcome unconfirmed. Inspect account before any retry.')
        dlg.after(150,poll)
    row=ttk.Frame(dlg);row.pack(fill='x',padx=8,pady=8)
    start=ttk.Button(row,text='Review and publish…',command=begin);start.pack(side='left')
    ttk.Button(row,text='Close',command=close).pack(side='right')
    dlg.protocol('WM_DELETE_WINDOW',close);dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
