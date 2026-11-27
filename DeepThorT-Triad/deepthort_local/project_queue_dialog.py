"""Native two-level owner queue controls."""
import tkinter as tk
from tkinter import ttk,messagebox
from pathlib import Path
from .project_queue import grouped

def show(app):
    dlg=tk.Toplevel(app);dlg.title('Project and task queues');dlg.geometry('1000x560')
    ttk.Label(dlg,text='Projects and task chats run in priority order when eligible. Pause holds new stages; an already admitted operation may finish safely. Blocked tasks can yield to eligible work.',wraplength=940).pack(padx=10,pady=8)
    panes=ttk.Panedwindow(dlg,orient='horizontal');panes.pack(fill='both',expand=True,padx=8,pady=4)
    left=ttk.Frame(panes);right=ttk.Frame(panes);panes.add(left,weight=1);panes.add(right,weight=3)
    pt=ttk.Treeview(left,columns=('status','tasks'),show='tree headings',selectmode='browse')
    pt.heading('#0',text='Project');pt.heading('status',text='State');pt.heading('tasks',text='Tasks')
    pt.column('#0',width=150);pt.column('status',width=90);pt.column('tasks',width=55);pt.pack(fill='both',expand=True)
    tt=ttk.Treeview(right,columns=('state','prompt'),show='headings',selectmode='browse')
    tt.heading('state',text='State');tt.heading('prompt',text='Task / current prompt');tt.column('state',width=200);tt.column('prompt',width=430)
    tt.pack(fill='both',expand=True)
    state={'projects':{},'ids':{},'tasks':{},'view':None}
    def selected_project():
        sel=pt.selection();return state['ids'].get(sel[0]) if sel else None
    def selected_chat():
        sel=tt.selection();return state['tasks'].get(sel[0]) if sel else None
    def tasks(_=None,keep=None):
        p=selected_project();old=keep or selected_chat();tt.delete(*tt.get_children());state['tasks']={}
        if not p:return
        view=state['view']
        for i,(chat,rows) in enumerate(state['projects'][p].items(),1):
            key=str(i);state['tasks'][key]=chat
            active=any(r['state'] in ('running','waiting_sources') for r in rows)
            paused=not view.allowed({'project':p,'chat_id':chat})
            states=', '.join(dict.fromkeys(r['state'] for r in rows))
            status=(('Pause requested — ' if active else 'Paused — ')+states) if paused else states
            tt.insert('','end',iid=key,values=(status,rows[0]['preview']))
            if old==chat:tt.selection_set(key)
    def refresh():
        oldp=selected_project();oldc=selected_chat()
        try:
            rows=app._project_queue_rows();view=app.project_queue.snapshot()
            groups=grouped(rows,view)
            pt.delete(*pt.get_children());state.update(projects=groups,ids={},view=view)
            for i,(p,ts) in enumerate(groups.items(),1):
                key=str(i);state['ids'][key]=p
                pt.insert('','end',iid=key,text=Path(p).name or p,values=('Paused' if not view.allowed({'project':p}) else 'Ready',len(ts)))
                if p==oldp:pt.selection_set(key)
            if not pt.selection() and pt.get_children():pt.selection_set(pt.get_children()[0])
            tasks(keep=oldc)
        except Exception as exc:messagebox.showerror('Queue unavailable',str(exc),parent=dlg)
    def change(scope,op):
        p=selected_project();c=selected_chat() if scope=='task' else None
        if not p or (scope=='task' and not c):return
        try:
            if op in (-1,1):
                visible=list(state['projects'][p]) if c else list(state['projects'])
                app.project_queue.move(p,c,delta=op,visible=visible)
            else:app.project_queue.hold(p,c,held=(op=='pause'))
            refresh();app._refresh_jobs()
        except Exception as exc:messagebox.showerror('Queue change refused',str(exc),parent=dlg)
    for frame,scope in ((left,'project'),(right,'task')):
        bar=ttk.Frame(frame);bar.pack(fill='x',pady=5)
        for label,op in (('Up',-1),('Down',1),('Pause','pause'),('Resume','resume')):
            ttk.Button(bar,text=label,command=lambda s=scope,o=op:change(s,o)).pack(side='left',padx=2)
    footer=ttk.Frame(dlg);footer.pack(fill='x',padx=8,pady=6)
    ttk.Button(footer,text='Refresh',command=refresh).pack(side='left')
    def remove_project():
        p=selected_project()
        if not p:return
        if not messagebox.askyesno('Remove project from queue',
            'Remove this project and hold all its tasks?\\n\\n'+p+
            '\\n\\nAn admitted operation may finish safely. Files, chats, approvals and task history are retained. Restore the project to queue it again.',parent=dlg):return
        try:
            app.project_queue.remove(p);refresh();app._refresh_jobs()
        except Exception as exc:messagebox.showerror('Remove refused',str(exc),parent=dlg)
    def restore_project():
        removed=sorted(app.project_queue.snapshot().removed)
        if not removed:
            messagebox.showinfo('Removed projects','No removed projects.',parent=dlg);return
        win=tk.Toplevel(dlg);win.title('Restore removed project');win.geometry('740x300')
        ttk.Label(win,text='Choose a project. Restored projects return at the end of the queue, paused.').pack(padx=8,pady=8)
        box=tk.Listbox(win,exportselection=False);box.pack(fill='both',expand=True,padx=8)
        for p in removed:box.insert('end',p)
        def restore():
            sel=box.curselection()
            if not sel:return
            p=removed[sel[0]]
            if not messagebox.askyesno('Restore project','Restore this project in paused state?\\n'+p,parent=win):return
            try:app.project_queue.restore(p);win.destroy();refresh();app._refresh_jobs()
            except Exception as exc:messagebox.showerror('Restore refused',str(exc),parent=win)
        ttk.Button(win,text='Restore selected',command=restore).pack(pady=8)
    ttk.Button(footer,text='Remove project…',command=remove_project).pack(side='left',padx=5)
    ttk.Button(footer,text='Restore project…',command=restore_project).pack(side='left',padx=5)
    def open_task():
        p=selected_project();c=selected_chat()
        if not p or not c:return
        if not Path(p).is_dir():messagebox.showwarning('Project unavailable',p,parent=dlg);return
        app._set_project(Path(p))
        if c in app.chat_ids:
            app.current_chat=c;app.chat_tabs.select(app.chat_ids.index(c));app._reload_chat()
        dlg.destroy()
    def cancel_pending():
        p=selected_project();c=selected_chat()
        if not p or not c:return
        prompts=[r for r in state['projects'][p][c] if r['kind']=='prompt' and r['state']=='pending']
        if len(prompts)!=1:return
        if messagebox.askyesno('Cancel pending prompt','Cancel this waiting prompt only? Approved jobs are unchanged.',parent=dlg):
            app.conversations.change(prompts[0]['id'],'cancelled','Pending project prompt cancelled by user',allowed=('pending',))
            refresh();app._refresh_jobs()
    ttk.Button(footer,text='Open selected task chat',command=open_task).pack(side='left',padx=5)
    ttk.Button(footer,text='Cancel pending prompt',command=cancel_pending).pack(side='left',padx=5)
    pt.bind('<<TreeviewSelect>>',tasks)
    refresh()
