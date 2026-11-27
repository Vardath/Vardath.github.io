"""Reviewed transcription with visible progress and separate publication consent."""
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .audio_transcription import review,transcribe,save

def show(app):
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and not app.queue_paused
                and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    source=simpledialog.askstring('Reviewed recording','Project-relative 1–120 second mono 16 kHz PCM16 WAV:',parent=app)
    if not source:return
    output=simpledialog.askstring('New transcript','New project-relative JSON report path:',parent=app)
    if not output:return
    culture=simpledialog.askstring('Installed recognition culture','Exact Windows desktop recognizer culture, e.g. en-AU:',parent=app)
    if not culture:return
    try:plan,seconds=review(project,source,output,culture,app.inspection_exclusions.paths(project))
    except Exception:messagebox.showwarning('Invalid transcription review','Check audio format, protected paths and new JSON output.',parent=app);return
    if not messagebox.askyesno('Approve offline transcription',f'Recognize {source} ({seconds:.2f} s) in bounded windows using installed {culture} recognition. Preview timed report; separately approve saving to {output}. No upload or speaker identification. Window boundaries may split words.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Offline audio transcription');dlg.geometry('800x520');dlg.transient(app)
    state=tk.StringVar(value='Starting local recognition…')
    ttk.Label(dlg,textvariable=state,wraplength=760).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word',state='disabled');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancel=threading.Event();messages=queue.Queue();closing=False;app._web_research_active=True
    def work():
        try:messages.put(('result',transcribe(project,plan,cancel.is_set,approved=True,stage=lambda i:messages.put(('stage',i)))))
        except Exception:messages.put(('error',None))
    thread=threading.Thread(target=work,daemon=True,name='local-audio-transcription')
    def close():
        nonlocal closing
        closing=True;cancel.set();state.set('Stopping recognition; unsaved output discarded.')
    def poll():
        if not permitted():cancel.set()
        if thread.is_alive():
            try:
                while True:
                    kind,value=messages.get_nowait()
                    if kind=='stage':state.set('Recognizing audio window '+str(value)+'…')
                    else:messages.put((kind,value));break
            except queue.Empty:pass
            dlg.after(150,poll);return
        app._web_research_active=False
        if closing or cancel.is_set():dlg.destroy();return
        result=None
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='result':result=value
        except queue.Empty:pass
        if result is None:state.set('Recognition failed or unavailable. No report saved.')
        else:
            view.configure(state='normal')
            view.insert('1.0','\n'.join(f"[{r['start_seconds']:.2f}s] {r['text']}" for r in result['segments']) or 'No speech recognized.')
            view.configure(state='disabled');state.set('Unverified recognition. Review the timed text before saving.')
            def publish():
                if not permitted():return
                if not messagebox.askyesno('Save unverified transcript','Save the exact timed recognition report to '+output+'? Existing files will not be replaced.',parent=dlg):return
                if not permitted():return
                try:
                    from .source_security import exclusions
                    if exclusions(app.inspection_exclusions.paths(project))!=plan['exclude']:raise ValueError('Scope changed')
                    save(project,plan,result,approved=True)
                    state.set('Saved '+output+'. Accuracy remains unverified.');save_button.configure(state='disabled')
                except Exception:state.set('Not saved; input/output or scope changed.')
            save_button=ttk.Button(dlg,text='Save reviewed JSON report…',command=publish);save_button.pack(pady=4)
        button.configure(text='Close',command=dlg.destroy);dlg.protocol('WM_DELETE_WINDOW',dlg.destroy)
    button=ttk.Button(dlg,text='Cancel',command=close);button.pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close);thread.start();dlg.after(150,poll);dlg.grab_set();app.wait_window(dlg)
