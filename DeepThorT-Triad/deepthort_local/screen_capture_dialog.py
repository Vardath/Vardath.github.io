"""User-initiated, single bounded screen region; preview before save or model use."""
import io
import tkinter as tk
from tkinter import ttk,messagebox,simpledialog
from pathlib import Path
from .screen_capture import primary_size,region,capture,save,prompt_for

def show(app):
    project=app.project;chat=app.current_chat
    if not project or not chat:return
    project_key=app._project_key()
    def permitted():
        return (not app._quitting and app.project==project and app.current_chat==chat
                and not app.queue_paused and not app._explicit_model_stop and not app.disk_gate.gaming()
                and not app.janus.status().get('paused') and app._queue_view().allowed({'project':project_key,'chat_id':chat}))
    if not permitted() or getattr(app,'_web_research_active',False):return
    try:screen=primary_size()
    except Exception:
        messagebox.showwarning('Screen capture unavailable','Protected Windows primary monitor unavailable.',parent=app);return
    entered=simpledialog.askstring('Primary monitor region',
        f'Primary screen: {screen[0]} × {screen[1]}. Enter x,y,width,height (max 2 megapixels). Only this region is retained.',
        initialvalue=f'0,0,{min(screen[0],1280)},{min(screen[1],720)}',parent=app)
    if not entered:return
    try:box=region(tuple(int(x.strip()) for x in entered.split(',')),screen)
    except ValueError:
        messagebox.showwarning('Invalid region','Choose a bounded rectangle within the primary screen.',parent=app);return
    if not messagebox.askyesno('Approve single screenshot',
        'Capture the specified visible screen region once, after a 3-second countdown. Close or cover sensitive windows first. Preview stays in memory; no upload, model processing or saving without separate approval.',parent=app):return
    if not permitted():return
    dlg=tk.Toplevel(app);dlg.title('Screen capture');dlg.transient(app);dlg.geometry('600x170')
    state=tk.StringVar(value='Capture in 3 seconds. Cancel to discard.')
    ttk.Label(dlg,textvariable=state,wraplength=550).pack(padx=12,pady=12)
    cancelled=False
    app._web_research_active=True
    def close():
        nonlocal cancelled
        cancelled=True
        app._web_research_active=False
        dlg.destroy()
    ttk.Button(dlg,text='Cancel',command=close).pack(pady=8)
    dlg.protocol('WM_DELETE_WINDOW',close)
    def take():
        if cancelled:return
        if not permitted():close();return
        try:
            # Withdraw only the countdown, not other applications.
            dlg.withdraw();dlg.update_idletasks()
            if primary_size()!=screen:raise ValueError('Monitor changed')
            payload=capture(box,screen,approved=True)
        except Exception:
            close();messagebox.showwarning('Screen capture unavailable','No screenshot retained. Check display scaling and local Pillow installation.',parent=app);return
        close()
        if not permitted():return
        from PIL import Image,ImageTk
        preview=tk.Toplevel(app);preview.title('Review captured region');preview.transient(app)
        with Image.open(io.BytesIO(payload)) as image:
            image.thumbnail((800,440));photo=ImageTk.PhotoImage(image.copy(),master=preview)
        label=ttk.Label(preview,image=photo);label.image=photo;label.pack(padx=10,pady=8)
        ttk.Label(preview,text='Local snapshot only. Save a new project PNG, or discard.').pack(pady=4)
        def publish():
            if not permitted():preview.destroy();return
            relative=simpledialog.askstring('Save screenshot','New project-relative PNG path (no overwrite):',initialvalue='screen-snapshot.png',parent=preview)
            if not relative or not permitted():return
            if not messagebox.askyesno('Approve screenshot save','Save the reviewed snapshot only to '+relative+'?',parent=preview) or not permitted():return
            try:r=save(project,relative,app.inspection_exclusions.paths(project),payload,approved=True)
            except Exception:
                messagebox.showwarning('Screenshot not saved','Output unavailable, excluded or already exists.',parent=preview);return
            preview.destroy()
            if permitted() and messagebox.askyesno('Interpret saved screenshot',
                'Queue this exact saved snapshot for the existing local offline vision model? Its caption is not verified and will appear in the job history.',parent=app) and permitted():
                app._queue_special('vision',prompt_for(r['sha256']),[str(Path(project).resolve()/relative)])
        buttons=ttk.Frame(preview);buttons.pack(pady=8)
        ttk.Button(buttons,text='Save reviewed screenshot…',command=publish).pack(side='left',padx=5)
        ttk.Button(buttons,text='Discard',command=preview.destroy).pack(side='left',padx=5)
        preview.grab_set();app.wait_window(preview)
    dlg.after(3000,take)
    dlg.grab_set();app.wait_window(dlg)
