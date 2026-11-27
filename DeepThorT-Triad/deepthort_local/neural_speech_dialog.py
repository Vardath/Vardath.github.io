"""Review optional installed neural speech engine and exact synthesis controls."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog,filedialog
from .neural_speech import review,render
from .source_security import exclusions

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    exe=filedialog.askopenfilename(parent=app,title='Select trusted installed Piper 1.3+ executable (not a project executable)',filetypes=[('Piper','piper.exe')])
    if not exe:return
    model=filedialog.askopenfilename(parent=app,title='Select trusted installed single-speaker Piper ONNX voice',filetypes=[('Piper voice','*.onnx')])
    if not model:return
    text=simpledialog.askstring('Speech text','Plain text to synthesize (up to 1000 characters):',parent=app)
    if not text:return
    length=simpledialog.askfloat('Speech rate','Length scale 0.7–1.5 (higher is slower):',minvalue=.7,maxvalue=1.5,initialvalue=1.0,parent=app)
    if length is None:return
    noise=simpledialog.askfloat('Voice variation','Noise scale 0–1:',minvalue=0,maxvalue=1,initialvalue=.667,parent=app)
    if noise is None:return
    variation=simpledialog.askfloat('Phoneme timing variation','Noise width scale 0–1:',minvalue=0,maxvalue=1,initialvalue=.8,parent=app)
    if variation is None:return
    output=simpledialog.askstring('New WAV','New project-relative WAV path:',parent=app)
    if not output:return
    try:plan=review(project,exe,model,output,text,length,noise,variation,app.inspection_exclusions.paths(project))
    except Exception:messagebox.showwarning('Neural voice unavailable','Select trusted compatible installed engine and voice/config, exact supported settings and a new project WAV.',parent=app);return
    dlg=tk.Toplevel(app);dlg.title('Review optional neural speech');dlg.geometry('820x620');dlg.transient(app)
    state=tk.StringVar(value='Review exact engine, voice and text. Piper is optional and must already be installed; review its and the voice license. Cap is not a security sandbox.')
    ttk.Label(dlg,textvariable=state,wraplength=780).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word');view.pack(fill='both',expand=True,padx=8,pady=8)
    view.insert('1.0',json.dumps(plan,ensure_ascii=False,indent=2));view.configure(state='disabled')
    cancel=threading.Event();messages=queue.Queue(maxsize=1);thread=None;app._web_research_active=True
    def close():
        cancel.set()
        if thread is None:app._web_research_active=False;dlg.destroy()
        else:state.set('Stopping renderer…')
    def work():
        try:messages.put(render(project,plan,cancel.is_set,approved=True))
        except Exception:messages.put(None)
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        try:result=messages.get_nowait()
        except queue.Empty:result=None
        state.set('New WAV saved; listening and expressive quality unverified.' if result else 'Renderer stopped or unavailable. No successful output confirmed.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    def start():
        nonlocal thread
        if not permitted():close();return
        try:
            if exclusions(app.inspection_exclusions.paths(project))!=plan['exclude']:raise ValueError('Scope changed')
        except Exception:close();return
        approve.configure(state='disabled');state.set('Running approved local Piper under existing resource cap…')
        thread=threading.Thread(target=work,daemon=True,name='local-neural-speech');thread.start();dlg.after(150,poll)
    approve=ttk.Button(dlg,text='Approve exact engine, text and WAV output',command=start);approve.pack(pady=4)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=4)
    dlg.protocol('WM_DELETE_WINDOW',close);dlg.grab_set();app.wait_window(dlg)
