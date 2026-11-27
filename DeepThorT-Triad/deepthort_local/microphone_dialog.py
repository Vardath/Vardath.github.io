"""Visible finite recording, then separate explicit project WAV publication."""
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .microphone_input import capture,save,MAX_SECONDS

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and
                not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    seconds=simpledialog.askinteger('Recording duration','Record the Windows default microphone for 1–30 seconds:',minvalue=1,maxvalue=MAX_SECONDS,parent=app)
    if seconds is None:return
    if not messagebox.askyesno('Approve microphone recording','Record the default microphone for '+str(seconds)+' seconds, locally in memory? Recording starts immediately; no network, playback, transcription or saving until separately approved.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Microphone recording');dlg.geometry('640x220');dlg.transient(app)
    state=tk.StringVar(value='RECORDING — microphone active for up to '+str(seconds)+' seconds.')
    ttk.Label(dlg,textvariable=state,wraplength=600).pack(fill='x',padx=12,pady=12)
    cancel=threading.Event();messages=queue.Queue(maxsize=1);closing=False;app._web_research_active=True
    def worker():
        try:messages.put(capture(seconds,cancel.is_set,approved=True))
        except Exception:messages.put(None)
    thread=threading.Thread(target=worker,daemon=True,name='local-microphone')
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping microphone…')
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(100,poll);return
        app._web_research_active=False
        try:payload=messages.get_nowait()
        except queue.Empty:payload=None
        if closing or cancel.is_set():dlg.destroy();return
        if payload is None:state.set('No recording retained. Check Windows microphone availability and permissions.')
        else:
            state.set('Microphone stopped. Recording held in memory only.')
            if permitted():
                relative=simpledialog.askstring('Save recording','New project-relative WAV path (existing directory; no overwrite). Cancel to discard:',parent=dlg)
                if relative and permitted() and messagebox.askyesno('Approve recording save','Save only to '+relative+' in the selected project?',parent=dlg) and permitted():
                    try:
                        result=save(project,relative,app.inspection_exclusions.paths(project),payload,seconds,approved=True)
                        state.set('Saved '+result['output']+'. No transcription or upload performed.')
                    except Exception:state.set('Recording not saved; output unavailable or protected.')
                else:state.set('Recording discarded.')
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel and discard',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(100,poll);dlg.grab_set();app.wait_window(dlg)
