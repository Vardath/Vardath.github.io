"""Reviewed binding of future monitor events to ordinary conversation requests."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .lattice_ui import fit_dialog,source_scrollbars,scroll_text
from .scheduled_tasks import utc_stamp
from .event_triggers import MAX_OCCURRENCES

def show(app):
    project=app._project_key();chat=app.current_chat;store=app.event_triggers
    if not chat or chat not in {i for i,_ in app.chats.list(project)}:
        messagebox.showwarning('Event rules unavailable','Open the bound chat first.',parent=app);return
    dialog=tk.Toplevel(app);dialog.title('Event-triggered requests');fit_dialog(dialog,840,470);dialog.transient(app)
    ttk.Label(dialog,text='Bind future observed website or file-condition events to an exact conversation prompt. No historical replay, overlapping requests or new execution authority.',wraplength=810).pack(anchor='w',padx=8,pady=6)
    tree_frame=ttk.Frame(dialog);tree_frame.pack(fill='both',expand=True,padx=8,pady=6)
    tree=ttk.Treeview(tree_frame,columns=('state','source','event','remaining','request','prompt'),show='headings',selectmode='browse')
    for key,label,width in (('state','State',80),('source','Monitor',105),('event','Event',115),
                            ('remaining','Remaining',80),('request','Latest request',95),('prompt','Follow-up',330)):
        tree.heading(key,text=label);tree.column(key,width=width,stretch=key=='prompt')
    source_scrollbars(tree_frame,tree)
    detail_frame=ttk.Frame(dialog);detail_frame.pack(fill='x',padx=8,pady=4)
    detail=tk.Text(detail_frame,height=5,wrap='word',state='disabled');scroll_text(detail_frame,detail)
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
        chosen=choose_future_event(dialog,options)
        if not chosen:return
        r,event=options[chosen]
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
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8,before=tree_frame)
    for label,action in (('New rule…',add),('Cancel selected',cancel),('Refresh',refresh),('Close',dialog.destroy)):
        ttk.Button(bar,text=label,command=action).pack(side='left',padx=3)
    refresh();dialog.grab_set();app.wait_window(dialog)


def choose_future_event(parent,options):
    """Exact selection only; closing the selector cannot create a rule."""
    if not options:return None
    editor=tk.Toplevel(parent);editor.title('Select future event');editor.transient(parent)
    fit_dialog(editor,600,340)
    ttk.Label(editor,text='Exact monitor and event').pack(anchor='w',padx=8,pady=4)
    combo=ttk.Combobox(editor,values=list(options),state='readonly',width=45)
    combo.pack(fill='x',padx=8,pady=4);combo.current(0)
    chosen=[]
    def confirm():
        if combo.get() in options:
            chosen.append(combo.get());editor.destroy()
    bar=ttk.Frame(editor);bar.pack(fill='x',padx=8,pady=6)
    ttk.Button(bar,text='Cancel',command=editor.destroy).pack(side='right')
    ttk.Button(bar,text='Continue',command=confirm).pack(side='right',padx=5)
    frame=ttk.Frame(editor);frame.pack(fill='both',expand=True,padx=8,pady=6)
    detail=tk.Text(frame,wrap='word',height=5,state='disabled')
    scroll_text(frame,detail)
    def show_label(_=None):
        detail.configure(state='normal');detail.delete('1.0','end')
        detail.insert('1.0',options[combo.get()][0]['label']);detail.configure(state='disabled')
    combo.bind('<<ComboboxSelected>>',show_label);show_label()
    editor.bind('<Escape>',lambda event:editor.destroy())
    editor.grab_set()
    try:parent.wait_window(editor)
    finally:
        if parent.winfo_exists():parent.grab_set()
    return chosen[0] if chosen else None
