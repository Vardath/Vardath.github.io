"""Explicit user interface for one-time scheduled conversation requests."""
from __future__ import annotations
import time
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from .scheduled_tasks import utc_stamp,MAX_DELAY,MIN_INTERVAL,MAX_OCCURRENCES

def show(app):
    project=app._project_key();chat=app.current_chat
    if not chat or chat not in {i for i,_ in app.chats.list(project)}:
        messagebox.showwarning('Schedule unavailable','Open a chat first.',parent=app);return
    store=app.scheduled_tasks
    dialog=tk.Toplevel(app);dialog.title('Scheduled conversation requests');dialog.geometry('800x440')
    dialog.transient(app)
    ttk.Label(dialog,text='One-time or recurring local requests. Missed intervals are coalesced, not replayed. Runs only while dispatch is available; no new file/tool authority.',wraplength=770).pack(anchor='w',padx=8,pady=6)
    tree=ttk.Treeview(dialog,columns=('due','state','remaining','request','prompt'),show='headings',selectmode='browse')
    for key,label,width in (('due','Due (UTC)',180),('state','State',85),('remaining','Remaining',80),('request','Latest request',95),('prompt','Prompt',340)):
        tree.heading(key,text=label);tree.column(key,width=width,stretch=key=='prompt')
    tree.pack(fill='both',expand=True,padx=8,pady=6)
    details=tk.Text(dialog,height=5,wrap='word',state='disabled');details.pack(fill='x',padx=8,pady=4)
    def refresh():
        tree.delete(*tree.get_children())
        for row in store.rows(project,chat):
            tree.insert('','end',iid=str(row['id']),values=(utc_stamp(row['due_utc']),row['state'],
                row['remaining_runs'] if row['state']=='scheduled' else '',row['request_id'] or '',row['prompt'][:100].replace('\n',' ')))
    def select(_=None):
        sel=tree.selection()
        row=next((r for r in store.rows(project,chat) if sel and str(r['id'])==sel[0]),None)
        details.configure(state='normal');details.delete('1.0','end')
        if row:
            details.insert('1.0',row['prompt'])
            if row['interval_seconds']:
                details.insert('end',f"\n\nCadence: {row['interval_seconds']//60} minutes; admitted: {row['released_count']}; remaining: {row['remaining_runs']}.")
            for occurrence in store.occurrences(row['id'],project,chat)[:5]:
                details.insert('end',f"\n{utc_stamp(occurrence['released_utc'])}: request #{occurrence['request_id']} [{occurrence['request_state'] or 'missing'}]")
        details.configure(state='disabled')
    def add(recurring=False):
        if app._project_key()!=project or chat not in {i for i,_ in app.chats.list(project)}:
            messagebox.showwarning('Workspace changed','Reopen schedule management in the desired chat.',parent=dialog);return
        prompt=simpledialog.askstring('Schedule a conversation','Exact request to submit later (no attachments):',parent=dialog,
                                       initialvalue=app.input.get('1.0','end').strip()[:8000])
        if not prompt:return
        minutes=simpledialog.askinteger('When to submit','Minutes from now (1–525600):',minvalue=1,maxvalue=MAX_DELAY//60,parent=dialog)
        if minutes is None:return
        interval=None;occurrences=1
        if recurring:
            every=simpledialog.askinteger('Repeat interval','Minutes between scheduled requests (15–525600):',
                minvalue=MIN_INTERVAL//60,maxvalue=MAX_DELAY//60,parent=dialog)
            if every is None:return
            occurrences=simpledialog.askinteger('Occurrence limit','Maximum actual requests (2–1000):',
                minvalue=2,maxvalue=MAX_OCCURRENCES,parent=dialog)
            if occurrences is None:return
            interval=every*60
        now=int(time.time());due=now+minutes*60
        cadence=(f'Repeat every {interval//60} minutes, up to {occurrences} actual requests. Missed intervals are coalesced; never overlap pending requests. A failed or cancelled previous request stops recurrence.' if recurring else 'One-time request.')
        if not messagebox.askyesno('Confirm schedule',
            f'First due: {utc_stamp(due)}\n{cadence}\n\nSubmit this exact conversation request when dispatch is available?\n\n{prompt}\n\nNo build or tool execution is approved.',parent=dialog):return
        try:
            store.create(project,chat,prompt,due,user_approved=True,interval_seconds=interval,occurrences=occurrences)
            refresh()
        except (ValueError,OSError) as exc:messagebox.showwarning('Schedule not saved',str(exc),parent=dialog)
    def cancel():
        sel=tree.selection()
        if not sel:return
        if messagebox.askyesno('Cancel schedule','Cancel all future occurrences of this schedule? Released requests remain in the normal chat.',parent=dialog):
            if not store.cancel(int(sel[0]),project,chat):
                messagebox.showinfo('Already released or cancelled','Use normal chat controls for a released request.',parent=dialog)
            refresh()
    tree.bind('<<TreeviewSelect>>',select)
    bar=ttk.Frame(dialog);bar.pack(fill='x',padx=8,pady=8)
    for label,action in (('One-time…',add),('Recurring…',lambda:add(True)),('Cancel selected',cancel),('Refresh',refresh),('Close',dialog.destroy)):
        ttk.Button(bar,text=label,command=action).pack(side='left',padx=3)
    refresh();dialog.grab_set();app.wait_window(dialog)
