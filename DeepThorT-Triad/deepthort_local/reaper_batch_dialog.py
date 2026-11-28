"""Explicit local REAPER batch approval and result display."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog,filedialog
from .lattice_ui import fit_dialog
from .reaper_batch import review,render,EXE
from .source_security import exclusions

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    source=simpledialog.askstring('Reviewed audio','Project-relative PCM16 WAV:',parent=app)
    if not source:return
    exe=filedialog.askopenfilename(parent=app,title='Select trusted installed REAPER executable',filetypes=[('REAPER',EXE)])
    if not exe:return
    output=simpledialog.askstring('New audio file','New project-relative .wav path:',parent=app)
    if not output:return
    target=simpledialog.askinteger('Target sample rate','22050, 44100 or 48000 Hz:',parent=app)
    if target is None:return
    try:plan=review(project,source,output,exe,target,app.inspection_exclusions.paths(project))
    except Exception:messagebox.showwarning('REAPER batch unavailable','Check trusted installed REAPER, PCM16 WAV, different target rate and new output path.',parent=app);return
    dlg=tk.Toplevel(app);dlg.title('Review REAPER audio conversion');fit_dialog(dlg,820,620);dlg.transient(app)
    state=tk.StringVar(value='Review exact WAV, installed REAPER and fixed sample-rate conversion. Creates one new verified WAV. Sound quality is not verified. Resource cap is not a security sandbox.')
    ttk.Label(dlg,textvariable=state,wraplength=780).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word');view.pack(fill='both',expand=True,padx=8,pady=8)
    view.insert('1.0',json.dumps(plan,ensure_ascii=False,indent=2));view.configure(state='disabled')
    cancel=threading.Event();messages=queue.Queue(maxsize=1);thread=None;app._web_research_active=True
    def close():
        cancel.set()
        if thread is None:app._web_research_active=False;dlg.destroy()
        else:state.set('Stopping local REAPER batch…')
    def work():
        try:messages.put(render(project,plan,cancel.is_set,approved=True))
        except Exception:messages.put(None)
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        try:result=messages.get_nowait()
        except queue.Empty:result=None
        if result:
            view.configure(state='normal');view.delete('1.0','end');view.insert('1.0',json.dumps(result,ensure_ascii=False,indent=2));view.configure(state='disabled')
        state.set('New WAV saved; listening quality unverified.' if result else 'REAPER batch stopped or unavailable. No successful output confirmed.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    def start():
        nonlocal thread
        if not permitted():close();return
        try:
            if exclusions(app.inspection_exclusions.paths(project))!=plan['exclude']:raise ValueError('Scope changed')
        except Exception:close();return
        approve.configure(state='disabled');state.set('Running approved REAPER batch under existing cap…')
        thread=threading.Thread(target=work,daemon=True,name='local-reaper-batch');thread.start();dlg.after(150,poll)
    approve=ttk.Button(dlg,text='Approve exact audio, REAPER and new file',command=start);approve.pack(pady=4)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=4)
    dlg.protocol('WM_DELETE_WINDOW',close);dlg.grab_set();app.wait_window(dlg)
