"""Review exact multilingual text and installed voice identities before rendering."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog,filedialog
from .local_speech import WindowsSpeech
from .multilingual_speech import review,render
from .source_security import exclusions

def show(app,mode='multilingual'):
    if mode=='podcast':
        from .podcast_generation import review as review_tool,render as render_tool
        title='Podcast generation';suffix='ZIP bundle'
        example={'title':'Episode title','description':'Episode summary','turns':[{'section':section,'speaker':'Host','culture':'en-AU','voice_id':'EXACT ID FROM INVENTORY','text':section+' text'} for section in ('intro','body','outro')],'pause_ms':300}
    elif mode=='audiobook':
        from .audiobook_generation import review as review_tool,render as render_tool
        title='Short audiobook generation';suffix='ZIP bundle'
        example={'title':'Book title','author':'Author','culture':'en-AU','voice_id':'EXACT ID FROM INVENTORY','chapters':[{'title':'Chapter one','passages':['First passage','Second passage']}],'pause_ms':300}
    elif mode=='dialogue':
        from .dialogue_generation import review as review_tool,render as render_tool
        title='Multi-speaker dialogue';suffix='ZIP bundle'
        example={'title':'Scene title','description':'Scene context','turns':[{'speaker':speaker,'culture':'en-AU','voice_id':'EXACT DISTINCT ID FROM INVENTORY','text':speaker+' text'} for speaker in ('Character A','Character B')],'pause_ms':250}
    elif mode=='multilingual':
        review_tool,render_tool=review,render
        title='Multilingual speech';suffix='WAV'
        example={'segments':[{'culture':'en-AU','voice_id':'EXACT ID FROM INVENTORY','text':'Your supplied text'}],'pause_ms':300}
    else:raise ValueError('Unknown reviewed speech mode')
    if getattr(app,'_web_research_active',False):return
    project=app.project;chat=app.current_chat
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat and not app.queue_paused
                and not app._explicit_model_stop and not app.disk_gate.gaming() and not app.janus.status().get('paused'))
    if not project or not permitted():return
    dlg=tk.Toplevel(app);dlg.title(title);dlg.geometry('820x620');dlg.transient(app)
    state=tk.StringVar(value='Discovering installed offline Windows voices…')
    ttk.Label(dlg,textvariable=state,wraplength=780).pack(fill='x',padx=8,pady=8)
    view=tk.Text(dlg,wrap='word');view.pack(fill='both',expand=True,padx=8,pady=8)
    cancel=threading.Event();messages=queue.Queue();backend=WindowsSpeech();app._web_research_active=True
    thread=None;voices=None;plan=None
    def write(value):
        view.configure(state='normal');view.delete('1.0','end');view.insert('1.0',json.dumps(value,ensure_ascii=False,indent=2));view.configure(state='disabled')
    def work(which):
        try:
            if which=='voices':messages.put(('voices',backend.voices(cancel.is_set)))
            else:messages.put(('result',render_tool(project,plan,cancel.is_set,approved=True,backend=backend,stage=lambda i:messages.put(('stage',i)))))
        except Exception:messages.put(('error',None))
    def launch(which):
        nonlocal thread
        thread=threading.Thread(target=work,args=(which,),daemon=True,name='multilingual-speech');thread.start();dlg.after(150,poll)
    def close():
        cancel.set()
        if thread and thread.is_alive():state.set('Stopping local speech…')
        else:app._web_research_active=False;dlg.destroy()
    def poll():
        nonlocal voices
        if not permitted():cancel.set()
        if thread.is_alive():dlg.after(150,poll);return
        if cancel.is_set():app._web_research_active=False;dlg.destroy();return
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='voices':
                    voices=value;write({'installed_voices':voices,'example_spec':example})
                    state.set('Select a project JSON specification using exact installed voice IDs. No translation is performed.');choose.configure(state='normal')
                elif kind=='result':
                    write(value);state.set('New '+suffix+' saved. Pronunciation and listening quality unverified.')
                elif kind=='error':state.set('Local speech unavailable; no successful output confirmed.')
        except queue.Empty:pass
    def select_spec():
        nonlocal plan
        if not permitted():return
        plan=None;approve.configure(state='disabled')
        from pathlib import Path
        file=filedialog.askopenfilename(parent=dlg,initialdir=project,title='Choose reviewed speech JSON',filetypes=[('JSON','*.json')])
        if not file:return
        output=simpledialog.askstring('New audio output','New project-relative '+suffix+' path:',parent=dlg)
        if not output:return
        try:
            relative=Path(file).relative_to(Path(project)).as_posix()
            plan,spec=review_tool(project,relative,output,voices,app.inspection_exclusions.paths(project))
        except Exception:state.set('Invalid specification or missing exact installed voice.');return
        write({'review':plan,'specification':spec});approve.configure(state='normal')
        state.set('Review the exact text, regional voices and output. No substitutions or translation.')
    def start():
        if not permitted() or plan is None:return
        try:
            if exclusions(app.inspection_exclusions.paths(project))!=plan['exclude']:raise ValueError('Scope changed')
        except Exception:state.set('Inspection scope changed. Review again.');return
        choose.configure(state='disabled');approve.configure(state='disabled')
        state.set('Rendering approved local language segments…');launch('render')
    choose=ttk.Button(dlg,text='Select project JSON…',state='disabled',command=select_spec);choose.pack(pady=4)
    approve=ttk.Button(dlg,text='Approve exact narration and '+suffix+' output',state='disabled',command=start);approve.pack(pady=4)
    ttk.Button(dlg,text='Close / cancel',command=close).pack(pady=4)
    dlg.protocol('WM_DELETE_WINDOW',close);launch('voices');dlg.grab_set();app.wait_window(dlg)
