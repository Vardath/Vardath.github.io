"""Explicit short-file dictation preview; transcript is not automatically sent."""
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .speech_to_text import review,recognize

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    relative=simpledialog.askstring('Reviewed audio','Project-relative WAV: 1–30 seconds, mono 16 kHz PCM16:',parent=app)
    if not relative:return
    culture=simpledialog.askstring('Installed recognition language','Exact installed Windows recognizer culture (for example en-AU or en-US):',parent=app)
    if not culture:return
    try:plan,seconds=review(project,relative,culture,app.inspection_exclusions.paths(project))
    except Exception:messagebox.showwarning('Audio unavailable','Invalid, protected or unsupported WAV or culture.',parent=app);return
    if not messagebox.askyesno('Approve offline dictation','Recognize '+relative+' ('+str(round(seconds,2))+' seconds) using the exact installed '+culture+' Windows desktop recognizer? No cloud, automatic chat submission or file changes.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Local speech-to-text');dlg.geometry('740x440');dlg.transient(app)
    state=tk.StringVar(value='Recognizing reviewed local WAV…')
    ttk.Label(dlg,textvariable=state,wraplength=700).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False;app._web_research_active=True
    def work():
        try:messages.put(recognize(project,plan,cancel.is_set,approved=True))
        except Exception:messages.put(None)
    thread=threading.Thread(target=work,daemon=True,name='local-dictation')
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping recognition…')
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(150,poll);return
        app._web_research_active=False
        try:result=messages.get_nowait()
        except queue.Empty:result=None
        if closing or cancel.is_set():dlg.destroy();return
        if result is None:state.set('Recognition unavailable. Check exact installed desktop recognizer and input format.')
        elif result['status']=='no_speech_recognized':state.set('No speech recognized; no transcript fabricated.')
        else:
            view.configure(state='normal');view.insert('1.0',result['text']);view.configure(state='disabled')
            state.set('Unverified local transcript. Review before copying; nothing submitted or saved.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
