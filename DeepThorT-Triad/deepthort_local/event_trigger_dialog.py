"""Reviewed binding of future monitor events to ordinary conversation requests."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog
from .scheduled_tasks import utc_stamp
from .event_triggers import MAX_OCCURRENCES

def show(app):
    project=app._project_key();chat=app.current_chat;store=app.event_triggers
    if not chat or chat not in {i for i,_ in app.chats.list(project)}:
        messagebox.showwarning('Event rules unavailable','Open the bound chat first.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title('Event-triggered requests');fit_dialog(dialog,840,470);dialog.transient(app)
    ttk.Label(dialog,text='Bind future observed website or file-condition events to an exact conversation prompt. No historical replay, overlapping requests or new execution authority.',wraplength=810).pack(anchor='w',padx=8,pady=6)
    tree=ttk.Treeview(dialog,columns=('state','source','event','remaining','request','prompt'),show='headings',selectmode='browse')
    for key,label,width in (('state','State',80),('source','Monitor',105),('event','Event',115),
                            ('remaining','Remaining',80),('request','Latest request',95),('prompt','Follow-up',330)):
        tree.heading(key,text=label);tree.column(key,width=width,stretch=key=='prompt')
    tree.pack(fill='both',expand=True,padx=8,pady=6)
    detail=tk.Text(dialog,height=7,wrap='word',state='disabled');detail.pack(fill='x',padx=8,pady=4)
    def refresh():
        tree.delete(*tree.get_children())
        for r in store.rows(project,chat):
            tree.insert('','end',iid=str(r['id']),values=(r['state'],r['source_kind']+' #'+str(r['source_id']),
                r['event'],r['remaining'],r['last_request_id'] or '',r['prompt'][:100].replace('\n',' ')))
    def select(_=None):
        sel=tree.selection();detail.configure(state='normal');detail.delete('1.0','end')
        if sel:
            row=next((r for r in store.rows(project,chat) if str(r['id'])==sel[0]),None)
            if row:detail.insert('end',row['prompt']+'\n\n')
            for h in store.history(int(sel[0]),project,chat):
                detail.insert('end',f"{utc_stamp(h['observed_utc'])} → request #{h['request_id']} [{h['request_state'] or 'missing'}]\n")
        detail.configure(state='disabled')
    def add():
        if app._project_key()!=project or chat not in {i for i,_ in app.chats.list(project)}:return
        sources=store.available(project,chat)
        if not sources:
            messagebox.showinfo('No active monitors','Create a website monitor or condition watch in this chat first.',parent=dialog);return
        options={}
        for r in sources:
            for event in r['events']:
                options[f"{r['kind']}:{r['id']}:{event}"]=(r,event)
        editor=tk.Toplevel(dialog);editor.title('Select future event');editor.transient(dialog)
        ttk.Label(editor,text='Exact monitor and event').pack(anchor='w',padx=8,pady=4)
        combo=ttk.Combobox(editor,values=list(options),state='readonly',width=45);combo.pack(fill='x',padx=8,pady=4);combo.current(0)
        label=tk.StringVar(value=options[combo.get()][0]['label'])
        ttk.Label(editor,textvariable=label,wraplength=480).pack(anchor='w',padx=8,pady=6)
        combo.bind('<<ComboboxSelected>>',lambda _:label.set(options[combo.get()][0]['label']))
        chosen=[]
        def confirm():
            chosen.append(combo.get());editor.destroy()
        ttk.Button(editor,text='Continue',command=confirm).pack(padx=8,pady=8);editor.grab_set();dialog.wait_window(editor);dialog.grab_set()
        if not chosen:return
        r,event=options[chosen[0]]
        prompt=simpledialog.askstring('Follow-up prompt','Exact request to submit when the event occurs:',parent=dialog)
        if not prompt:return
        count=simpledialog.askinteger('Follow-up limit','Maximum future admissions (1–1000):',minvalue=1,maxvalue=MAX_OCCURRENCES,parent=dialog)
        if count is None:return
        if not messagebox.askyesno('Confirm future event rule',
            f"Monitor {r['kind']} #{r['id']}: {r['label']}\nEvent: {event}\nUp to {count} admissions.\n\nExact prompt:\n{prompt}\n\nNo build or tool execution is approved.",parent=dialog):return
        try:
            store.create(project,chat,r['kind'],r['id'],event,prompt,count,approved=True);refresh()
        except (ValueError,OSError) as exc:messagebox.showwarning('Rule not saved',str(exc),parent=dialog)
    def cancel():
        sel=tree.selection()
        if sel and messagebox.askyesno('Cancel event rule','Stop future admissions? Existing conversation requests are unchanged.',parent=dialog):
            store.cancel(int(sel[0]),project,chat);refresh()
    tree.bind('<<TreeviewSelect>>',select)
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8)
    for label,action in (('New rule…',add),('Cancel selected',cancel),('Refresh',refresh),('Close',dialog.destroy)):
        ttk.Button(bar,text=label,command=action).pack(side='left',padx=3)
    refresh();dialog.grab_set();app.wait_window(dialog)
