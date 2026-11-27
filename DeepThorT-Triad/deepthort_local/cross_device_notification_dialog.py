"""Owner-approved one-shot status notification; no automatic external disclosure."""
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .cross_device_notification import destination,selected_state,watch,TERMINAL,message

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app._project_key();chat=app.current_chat
    def permitted():
        return (not app._quitting and app._project_key()==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not chat or not permitted():return
    kind=simpledialog.askstring('Status source','Enter job or conversation:',parent=app)
    if kind not in TERMINAL:return
    ident=simpledialog.askinteger('Exact local record','Enter the numeric ID in the selected project/chat:',minvalue=1,maxvalue=2147483647,parent=app)
    if ident is None:return
    path=app.jobs.path if kind=='job' else app.conversations.path
    def read():return selected_state(path,kind,ident,project,chat)
    try:initial=read()
    except Exception:messagebox.showwarning('Status unavailable','No matching record in the selected project/chat.',parent=app);return
    topic=simpledialog.askstring('ntfy protected topic','Enter your dedicated ntfy.sh topic. Configure private read/write access and subscribe on the receiving device yourself.',parent=app)
    if not topic:return
    key=simpledialog.askstring('ntfy access token','Dedicated ntfy access token, used once and not saved:',show='*',parent=app)
    if not key:return
    try:destination(topic,key)
    except ValueError as e:messagebox.showwarning('Invalid notification destination',str(e),parent=app);return
    texts='\n'.join(message(kind,s) for s in sorted(TERMINAL[kind]))
    if not messagebox.askyesno('Approve one cross-device notification','Watch local '+kind+' #'+str(ident)+' (currently '+initial+') for up to five minutes. On terminal state, send one matching generic message to https://ntfy.sh/ on topic '+topic+'.\n\n'+texts+'\n\nNo ID, project name, path, prompt or answer is transmitted. ntfy may cache messages. Topic privacy and receiving-device subscription are your responsibility. Provider acceptance does not prove device delivery.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Cross-device notification watch');dlg.geometry('680x210');dlg.transient(app)
    state=tk.StringVar(value='Watching selected status for up to five minutes…')
    ttk.Label(dlg,textvariable=state,wraplength=640).pack(fill='x',padx=12,pady=12)
    cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False;app._web_research_active=True
    def work(secret):
        try:messages.put(watch(read,kind,topic,secret,cancel.is_set,approved=True,wait=cancel.wait))
        except Exception:messages.put({'status':'unconfirmed'})
    thread=threading.Thread(target=work,args=(key,),daemon=True,name='ntfy-status-watch');key=None
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping; an already transmitted message may have been accepted.')
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(200,poll);return
        app._web_research_active=False
        try:result=messages.get_nowait()
        except queue.Empty:result={'status':'unconfirmed'}
        if closing:dlg.destroy();return
        state.set({'provider_accepted':'Provider accepted notification. Check the receiving device.','watch_expired':'Watch expired without a notification.'}.get(result['status'],'Stopped or outcome unconfirmed. Check the provider before sending again.'))
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel watch',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(200,poll)
