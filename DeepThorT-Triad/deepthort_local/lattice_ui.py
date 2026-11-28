"""Nordic lattice visual tokens and a searchable, scrollable native tool shelf.

UI only: filtering never invokes a tool or changes its authorization.
"""
import tkinter as tk
from tkinter import ttk

PALETTE = {
    'base': '#10181b', 'panel': '#19262a', 'input': '#131f23',
    'text': '#ecf2f0', 'muted': '#b0c4c6', 'accent': '#8edbd0',
    'control': '#25383c', 'hover': '#354e52', 'selected': '#355956',
    'success': '#9ad9b6', 'warning': '#f1c184',
}


def dragon_mark(parent):
    """Small scalable-by-layout angular serpent mark, no external assets."""
    canvas = tk.Canvas(parent, width=36, height=36, bg=PALETTE['base'],
                       highlightthickness=0, takefocus=False)
    canvas.create_polygon(18, 2, 33, 10, 33, 26, 18, 34, 3, 26, 3, 10,
                          fill='', outline=PALETTE['selected'], width=1)
    canvas.create_line(7, 23, 13, 12, 23, 12, 28, 7, 27, 17, 20, 21,
                       14, 20, 11, 26, 18, 30, 25, 26,
                       fill=PALETTE['accent'], width=2, joinstyle='miter')
    canvas.create_line(13, 12, 9, 7, 19, 9, fill=PALETTE['accent'], width=1)
    canvas.create_oval(21, 14, 23, 16, fill=PALETTE['warning'], outline='')
    return canvas


class ToolShelf(ttk.Frame):
    """Keep all original controls and callbacks; filter by visible button label."""
    def __init__(self, parent):
        super().__init__(parent)
        bar = ttk.Frame(self)
        bar.pack(fill='x', pady=(2, 4))
        ttk.Label(bar, text='Tool library · Search').pack(side='left', padx=(0, 8))
        self.category = tk.StringVar(self,value='All tools')
        self.categories={}
        self.category_choice=ttk.Combobox(bar,textvariable=self.category,state='readonly',width=17,values=('All tools',))
        self.category_choice.pack(side='left',padx=(0,6))
        self.query = tk.StringVar(self)
        self.search = ttk.Entry(bar, textvariable=self.query)
        self.search.pack(side='left', fill='x', expand=True)
        self.count = tk.StringVar(self, value='')
        ttk.Label(bar, textvariable=self.count, style='Muted.TLabel').pack(side='right', padx=8)
        self.search.bind('<Escape>', lambda event: self.query.set(''))
        viewport = ttk.Frame(self)
        viewport.pack(fill='both', expand=True)
        viewport.columnconfigure(0, weight=1)
        viewport.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(viewport, bg=PALETTE['base'], height=165,
                                highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        vertical = ttk.Scrollbar(viewport, orient='vertical', command=self.canvas.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal = ttk.Scrollbar(viewport, orient='horizontal', command=self.canvas.xview)
        horizontal.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.rows = ttk.Frame(self.canvas)
        self.canvas.create_window(0, 0, anchor='nw', window=self.rows)
        self.rows.bind('<Configure>', self._region)
        self.canvas.bind('<Configure>', self._region)
        self._index = []
        self.query.trace_add('write', self._filter)
        self.category.trace_add('write',self._filter)

    def set_category(self,row,category):
        self.categories[row]=category

    def _region(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all') or (0, 0, 0, 0))

    def _wheel(self, event):
        delta = getattr(event, 'delta', 0)
        direction = -1 if delta > 0 or getattr(event, 'num', 0) == 4 else 1
        self.canvas.yview_scroll(direction, 'units')
        return 'break'

    @staticmethod
    def _pack_options(widget):
        options = widget.pack_info()
        options.pop('in', None)
        return options

    def index_buttons(self):
        self._index = []
        for row in self.rows.winfo_children():
            buttons = [(w, self._pack_options(w)) for w in row.winfo_children()
                       if isinstance(w, ttk.Button) and w.winfo_manager() == 'pack']
            if buttons:
                self._index.append((row, self._pack_options(row), buttons))
                for widget in [row] + [w for w, _ in buttons]:
                    for event in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
                        widget.bind(event, self._wheel, add='+')
        for event in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self.canvas.bind(event, self._wheel, add='+')
        self.category_choice.configure(values=('All tools',*sorted(set(self.categories.values()))))
        self._filter()

    def _filter(self, *args):
        words = self.query.get().casefold().split()
        total = shown = 0
        for row, options, buttons in self._index:
            row.pack_forget()
            for button, _ in buttons:
                button.pack_forget()
            found = False
            for button, button_options in buttons:
                total += 1
                if (self.category.get()=='All tools' or self.categories.get(row)==self.category.get()) and all(word in str(button.cget('text')).casefold() for word in words):
                    button.pack(**button_options)
                    found = True
                    shown += 1
            if found:
                row.pack(**options)
        self.count.set(f'{shown} / {total} tools')
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.after_idle(self._region)


def action_menu(parent, label, actions):
    """Expose existing callbacks without invoking any during construction."""
    control = ttk.Menubutton(parent, text=label)
    menu = tk.Menu(control, tearoff=False, bg=PALETTE['panel'],
                   fg=PALETTE['text'], activebackground=PALETTE['selected'],
                   activeforeground=PALETTE['text'])
    for title, callback in actions:
        menu.add_command(label=title, command=callback)
    control.configure(menu=menu)
    return control


def scroll_text(parent, text):
    """Keep the original Text widget and its bindings; add a native scrollbar."""
    scrollbar = ttk.Scrollbar(parent, orient='vertical', command=text.yview)
    scrollbar.pack(side='right', fill='y')
    text.configure(yscrollcommand=scrollbar.set)
    text.pack(side='left', fill='both', expand=True)
    return scrollbar


def composer_rows(height, expanded=False):
    maximum = 12 if expanded else 5
    return max(3, min(maximum, maximum - max(0, (860-height+19)//20)))


def matches_query(label, query):
    return all(word in str(label).casefold() for word in str(query).casefold().split())


class SearchPicker(tk.Toplevel):
    """Filter display labels, retain exact row IDs, require explicit selection."""
    def __init__(self, parent, title, rows, callback):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.configure(bg=PALETTE['base'])
        self.geometry('560x390')
        self.minsize(300, 220)
        self.rows = tuple(rows)
        self.visible = []
        self.callback = callback
        self.query = tk.StringVar(self)
        self.summary = tk.StringVar(self)
        bar = ttk.Frame(self)
        bar.pack(fill='x', padx=12, pady=10)
        ttk.Label(bar, text='Search').pack(side='left')
        self.entry = ttk.Entry(bar, textvariable=self.query)
        self.entry.pack(side='left', fill='x', expand=True, padx=8)
        ttk.Label(bar, textvariable=self.summary).pack(side='right')
        body = ttk.Frame(self)
        body.pack(fill='both', expand=True, padx=12)
        self.items = tk.Listbox(body, exportselection=False,
                                bg=PALETTE['input'], fg=PALETTE['text'],
                                selectbackground=PALETTE['selected'],
                                selectforeground=PALETTE['text'])
        scroll_text(body, self.items)
        footer = ttk.Frame(self)
        footer.pack(fill='x', padx=12, pady=10)
        ttk.Button(footer, text='Cancel', command=self.destroy).pack(side='right')
        self.open_button = ttk.Button(footer, text='Open selected', command=self.open_selected)
        self.open_button.pack(side='right', padx=8)
        self.query.trace_add('write', self.filter)
        self.items.bind('<<ListboxSelect>>', self.selection_changed)
        self.items.bind('<Double-1>', lambda event: self.open_selected())
        self.items.bind('<Return>', lambda event: self.open_selected())
        self.bind('<Escape>', lambda event: self.destroy())
        self.filter()
        self.entry.focus_set()

    def filter(self, *args):
        self.visible = [(ident,label) for ident,label in self.rows
                        if matches_query(label,self.query.get())]
        self.items.delete(0,'end')
        for _,label in self.visible:
            self.items.insert('end',label)
        self.summary.set(f'{len(self.visible)} / {len(self.rows)}')
        self.selection_changed()

    def selection_changed(self, event=None):
        self.open_button.configure(state='normal' if self.items.curselection() else 'disabled')

    def open_selected(self):
        chosen = self.items.curselection()
        if not chosen:return
        ident = self.visible[chosen[0]][0]
        self.destroy()
        self.callback(ident)


# Display groups only; never used for dispatch, cancellation or approval.
STATUS_GROUPS = {
    'Active': {'queued','pending','running','approved','resuming','building','testing','repairing'},
    'Waiting / blocked': {'waiting_approval','waiting_sources','waiting','blocked','paused','interrupted','needs_input','waiting_verification','waiting_repair'},
    'Completed / stopped': {'done','complete','completed','succeeded','failed','cancelled','stopped','responded'},
}

def filter_status_rows(rows, state, query):
    group = STATUS_GROUPS.get(state)
    return [(ident,values) for ident,values in rows
            if (state=='All states' or
                str(values[0]).casefold() in (group if group is not None else {state.casefold()}))
            and matches_query(' '.join(str(value) for value in values),query)]

def sync_table(tree, rows):
    """Update existing rows by exact ID; never select a new target automatically."""
    existing = set(tree.get_children())
    wanted = {ident for ident,_ in rows}
    for ident in existing-wanted:
        tree.delete(ident)
    for position,(ident,values) in enumerate(rows):
        if ident in existing:
            tree.item(ident,values=values)
        else:
            tree.insert('','end',iid=ident,values=values)
        if tree.index(ident)!=position:
            tree.move(ident,'',position)


def proposal_code(text):
    """Match the existing proposal editor convention; never alter ordinary source."""
    return text.split('\n',2)[-1] if text.startswith('PROPOSED CODE —') else text


def source_scrollbars(parent, widget):
    y = ttk.Scrollbar(parent, command=widget.yview)
    x = ttk.Scrollbar(parent, orient='horizontal', command=widget.xview)
    widget.configure(yscrollcommand=y.set,xscrollcommand=x.set)
    widget.grid(row=0,column=0,sticky='nsew')
    y.grid(row=0,column=1,sticky='ns')
    x.grid(row=1,column=0,sticky='ew')
    parent.grid_rowconfigure(0,weight=1)
    parent.grid_columnconfigure(0,weight=1)
    return y,x


def highlight_diff(widget):
    """Colour exact unchanged diff text; no parsing into a writeable payload."""
    widget.tag_configure('diff_add', foreground=PALETTE['success'])
    widget.tag_configure('diff_remove', foreground=PALETTE['warning'])
    widget.tag_configure('diff_header', foreground=PALETTE['accent'])
    for n,line in enumerate(widget.get('1.0','end-1c').splitlines(),1):
        tag = ('diff_header' if line.startswith(('+++','---','@@')) else
               'diff_add' if line.startswith('+') else 'diff_remove' if line.startswith('-') else None)
        if tag:widget.tag_add(tag,f'{n}.0',f'{n}.end')


class SourceNavigator(ttk.Frame):
    """Read-only navigation over the actual editor buffer."""
    def __init__(self,parent,widget):
        super().__init__(parent)
        self.widget=widget
        self.term=tk.StringVar(self)
        self.line=tk.StringVar(self)
        self.notice=tk.StringVar(self)
        ttk.Label(self,text='Find').pack(side='left')
        entry=ttk.Entry(self,textvariable=self.term,width=18)
        entry.pack(side='left',fill='x',expand=True,padx=3)
        ttk.Button(self,text='Find next',command=self.find).pack(side='left',padx=3)
        entry.bind('<Return>',lambda event:(self.find(),'break')[1])
        ttk.Label(self,text='Line').pack(side='left',padx=(8,2))
        number=ttk.Entry(self,textvariable=self.line,width=6)
        number.pack(side='left')
        ttk.Button(self,text='Go to line',command=self.goto).pack(side='left',padx=3)
        number.bind('<Return>',lambda event:(self.goto(),'break')[1])
        ttk.Label(self,textvariable=self.notice,style='Muted.TLabel').pack(side='left',padx=4)
        widget.tag_configure('source_match',background=PALETTE['selected'],foreground=PALETTE['text'])
        widget.tag_configure('source_line',background=PALETTE['selected'])
        self.reset()

    def reset(self):
        self.widget.tag_remove('source_match','1.0','end')
        self.widget.tag_remove('source_line','1.0','end')
        self.widget.mark_set('source_find','1.0')
        self.notice.set('')

    def find(self):
        term=self.term.get()
        if not term:return
        widget=self.widget
        widget.tag_remove('source_match','1.0','end')
        start=widget.index('source_find')
        hit=widget.search(term,start,stopindex='end',exact=True) or widget.search(term,'1.0',stopindex=start,exact=True)
        if not hit:self.notice.set('No match');return
        finish=widget.index(f'{hit}+{len(term)}c')
        widget.tag_add('source_match',hit,finish)
        widget.mark_set('source_find',finish)
        widget.see(hit)
        self.notice.set('Line '+hit.split('.')[0])

    def goto(self):
        widget=self.widget
        try:
            number=int(self.line.get())
            last=int(widget.index('end-1c').split('.')[0])
            if not 1<=number<=last:raise ValueError
        except ValueError:
            self.notice.set('Invalid line');return
        widget.tag_remove('source_line','1.0','end')
        widget.tag_add('source_line',f'{number}.0',f'{number}.end')
        widget.see(f'{number}.0')
        self.notice.set(f'Line {number}')


def measured_process_rows(measured):
    """Render only actual samples; no aggregate claims or inferred percentages."""
    return [(str(row['pid'])+':'+str(row['name']),
             (row['name'],row['pid'],f"{row['system_cpu_percent']:.1f}",
              f"{row['working_set_bytes']/2**20:.1f}",f"{row['private_bytes']/2**20:.1f}"))
            for row in measured]


def replace_readonly(widget,text):
    """Refresh a read-only evidence panel without snapping its reader to the top."""
    if widget.get('1.0','end-1c')==text:return
    y=widget.yview()[0]
    x=widget.xview()[0]
    widget.configure(state='normal')
    widget.delete('1.0','end')
    widget.insert('1.0',text)
    widget.configure(state='disabled')
    widget.yview_moveto(y)
    widget.xview_moveto(x)


OPERATIVES = (
    ('janus','JANUS','Executive coordination'),
    ('sentinel','Sentinel','Independent oversight'),
    ('implementation','Granite','Technical development'),
    ('gemma','Gemma','Multimedia production'),
    ('memory','Memory','Independent contextual retrieval'),
)


def operative_rows(health, broker_pid, creative_active=False):
    """Reject stale broker reports; Gemma thread state is not model residency."""
    current=health if isinstance(health,dict) and broker_pid and health.get('pid')==broker_pid else {}
    models=current.get('models',{})
    if not isinstance(models,dict):models={}
    rows=[]
    for key,label,responsibility in OPERATIVES:
        if key=='gemma':
            state='Creative lane active' if creative_active else 'No active creative lane observed'
            pid='—'
        else:
            row=current.get('memory_model',{}) if key=='memory' else models.get(key,{})
            row=row if isinstance(row,dict) else {}
            if not row:
                state='Not observed';pid='—'
            else:
                state=('Generating' if row.get('generating') else 'Busy' if row.get('busy') else 'Resident') if row.get('resident') else 'Not resident'
                pid=row.get('pid') if row.get('resident') and type(row.get('pid')) is int else '—'
        rows.append((key,(label,responsibility,state,pid)))
    return rows


class SocietyLattice(ttk.Frame):
    """Topology of recorded recursive roles; edges represent architecture, not traffic."""
    def __init__(self,parent):
        super().__init__(parent)
        import json
        from .janus_cognition import CORE_NAMES
        self.names=CORE_NAMES
        self.records={'JANUS':{},'Sentinel':{}}
        self.role='Front'
        self.society=tk.StringVar(self,value='JANUS')
        bar=ttk.Frame(self);bar.pack(fill='x')
        ttk.Label(bar,text='Recorded core appraisals · select a society and core').pack(side='left')
        choice=ttk.Combobox(bar,textvariable=self.society,values=('JANUS','Sentinel'),state='readonly',width=10)
        choice.pack(side='right')
        choice.bind('<<ComboboxSelected>>',lambda e:self.redraw())
        self.canvas=tk.Canvas(self,bg=PALETTE['base'],height=210,highlightthickness=0)
        self.canvas.pack(fill='x',pady=3)
        self.canvas.bind('<Configure>',lambda e:self.redraw())
        nav=ttk.Frame(self);nav.pack(fill='x')
        self.selected=tk.StringVar(self,value='Front')
        core=ttk.Combobox(nav,textvariable=self.selected,values=self.names,state='readonly',width=14)
        core.pack(side='left')
        core.bind('<<ComboboxSelected>>',lambda e:self.select(self.selected.get()))
        ttk.Label(nav,text='7 specialists → both hemispheres → Front → Interface',style='Muted.TLabel').pack(side='left',padx=8)
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        self.detail=tk.Text(frame,bg=PALETTE['input'],fg=PALETTE['text'],height=9,wrap='word',state='disabled',font=('Consolas',10))
        scroll_text(frame,self.detail)
        self.redraw()

    def update_records(self,main,watch):
        self.records={'JANUS':main if isinstance(main,dict) else {},
                      'Sentinel':watch if isinstance(watch,dict) else {}}
        self.redraw()

    def select(self,name):
        if name not in self.names:return
        self.role=name;self.selected.set(name);self.redraw()

    def redraw(self):
        import json
        canvas=self.canvas
        canvas.delete('all')
        width=max(280,canvas.winfo_width())
        top=[(name, (i+1)*width/8,30) for i,name in enumerate(self.names[:7])]
        lower=[('Left',width*.30,86),('Right',width*.70,86),('Front',width*.50,139),('Interface',width*.50,190)]
        positions={name:(x,y) for name,x,y in top+lower}
        for name,_,_ in top:
            for target in ('Left','Right'):
                canvas.create_line(*positions[name],*positions[target],fill=PALETTE['selected'])
        for source,target in [('Left','Front'),('Right','Front'),('Front','Interface')]:
            canvas.create_line(*positions[source],*positions[target],fill=PALETTE['selected'],arrow='last')
        records=self.records.get(self.society.get(),{})
        for name,x,y in top+lower:
            recorded=isinstance(records.get(name),dict) and bool(records.get(name))
            colour=PALETTE['accent'] if recorded else PALETTE['muted']
            tag='core_'+name
            radius=9
            canvas.create_polygon(x,y-radius,x+radius,y,x,y+radius,x-radius,y,
                                  fill=PALETTE['selected'] if name==self.role else PALETTE['panel'],
                                  outline=colour,width=2 if name==self.role else 1,tags=(tag,))
            canvas.create_text(x,y+16,text=name,fill=colour,font=('Segoe UI',8),tags=(tag,))
            canvas.tag_bind(tag,'<Button-1>',lambda event,n=name:self.select(n))
        data=records.get(self.role)
        body=json.dumps(data,indent=2,ensure_ascii=False) if isinstance(data,dict) and data else 'No recorded appraisal for this core.'
        replace_readonly(self.detail,self.society.get()+' · '+self.role+'\nRecorded observations, not a neural thought transcript.\n'+body)


def inventory_rows(tools,evidence):
    """Discovery, verification and execution authority are separate concepts."""
    return [(str(tool['name']),(str(tool['name']),'Found' if tool.get('found') else 'Missing',
             str(tool.get('purpose') or ''),str(tool.get('location') or '—'),
             str(evidence.get(tool['name'],'Not verified')))) for tool in tools]


def command_project_rows(groups,view):
    return [(project,(str(i),project,'Held' if not view.allowed({'project':project}) else 'Eligible by priority',
                      str(len(tasks)),str(sum(len(items) for items in tasks.values()))))
            for i,(project,tasks) in enumerate(groups.items(),1)]


def command_job_rows(jobs):
    relevant={'queued','running','waiting_approval','needs_input','waiting_verification',
              'waiting_repair','paused','complete','failed','cancelled'}
    return [(str(j['id']),(str(j['id']),j['state'],str(j.get('mode','')),
                           str(j.get('target') or ''),str(j.get('detail') or '')))
            for j in jobs if j['state'] in relevant and
            (j.get('mode') not in ('chat','plan','edit') or j['state']=='waiting_approval')]


class CommandCentre(ttk.Frame):
    """Read-only overview with navigation to existing reviewed operations."""
    def __init__(self,parent,refresh,open_job,navigation,project_queues):
        super().__init__(parent)
        self.open_job=open_job
        self.notice=tk.StringVar(self,value='Open this screen or refresh to read saved records.')
        self.live_status=tk.StringVar(self,value='No live sample yet')
        self.counts=tk.StringVar(self,value='')
        header=ttk.Frame(self);header.pack(fill='x',pady=5)
        ttk.Label(header,text='COMMAND CENTRE',style='Muted.TLabel').pack(side='left')
        ttk.Button(header,text='Refresh overview',command=refresh).pack(side='right')
        ttk.Label(self,textvariable=self.live_status,wraplength=620).pack(anchor='w',pady=3)
        ttk.Label(self,textvariable=self.notice,style='Muted.TLabel',wraplength=620).pack(anchor='w',pady=3)
        links=ttk.Frame(self);links.pack(fill='x',pady=3)
        action_menu(links,'Go to workspace',navigation).pack(side='left')
        ttk.Button(links,text='Project queues…',command=project_queues).pack(side='left',padx=4)
        panels=ttk.Notebook(self);panels.pack(fill='both',expand=True)
        projects=ttk.Frame(panels);jobs=ttk.Frame(panels);workers=ttk.Frame(panels)
        for page,title in ((projects,'Project priorities'),(jobs,'Workspace jobs'),(workers,'Live operatives')):
            panels.add(page,text=title)
        ttk.Label(projects,text='Bounded queue inventory; priority is not a guarantee of execution.',wraplength=620).pack(anchor='w',pady=4)
        project_frame=ttk.Frame(projects);project_frame.pack(fill='both',expand=True)
        self.projects=self._table(project_frame,[('priority','Order',55),('project','Workspace',275),
                ('state','State',125),('tasks','Task chats',70),('records','Records',65)])
        ttk.Label(jobs,textvariable=self.counts,wraplength=620).pack(anchor='w',pady=4)
        bar=ttk.Frame(jobs);bar.pack(fill='x')
        self.query=tk.StringVar(self);self.state=tk.StringVar(self,value='All states')
        ttk.Combobox(bar,textvariable=self.state,state='readonly',width=18,
            values=('All states','Active','Waiting / blocked','Completed / stopped')).pack(side='left')
        ttk.Entry(bar,textvariable=self.query).pack(side='left',fill='x',expand=True,padx=4)
        ttk.Button(bar,text='Filter jobs',command=self.filter_jobs).pack(side='left')
        ttk.Button(jobs,text='Open selected job',command=self._open_selected).pack(anchor='w',pady=3)
        job_frame=ttk.Frame(jobs);job_frame.pack(fill='both',expand=True)
        self.jobs=self._table(job_frame,[('id','Job',50),('state','State',125),('mode','Type',80),
                   ('target','Recorded target',160),('detail','Recorded evidence',250)])
        self.jobs.bind('<Double-1>',lambda e:self._open_selected())
        self.job_rows=[]
        worker_frame=ttk.Frame(workers);worker_frame.pack(fill='both',expand=True)
        self.workers=self._table(worker_frame,[('role','Operative',85),('responsibility','Responsibility',190),
                    ('state','Observed state',175),('pid','PID',65)])
        ttk.Label(workers,text='Actual model/creative-lane observations; no inferred assignment or completion.',wraplength=620).pack(anchor='w',pady=4)

    def _table(self,parent,columns):
        tree=ttk.Treeview(parent,columns=[c[0] for c in columns],show='headings',selectmode='browse')
        for key,label,width in columns:
            tree.heading(key,text=label);tree.column(key,width=width,stretch=key in ('project','detail','responsibility'))
        source_scrollbars(parent,tree)
        return tree

    def render(self,project,projects,jobs,counts):
        if getattr(self,'project',None)!=project:
            selected=self.jobs.selection()
            if selected:self.jobs.selection_remove(*selected)
            self.query.set('');self.state.set('All states')
        self.project=project;self.job_rows=jobs
        self.notice.set('Workspace: '+project+' · saved-record snapshot')
        self.counts.set('Stored state counts: '+(', '.join(f'{k}: {v}' for k,v in sorted(counts.items())) or 'none')+
                        ' · recent bounded job list')
        sync_table(self.projects,projects)
        self.filter_jobs()

    def filter_jobs(self):
        state=self.state.get();group=STATUS_GROUPS.get(state)
        rows=[(ident,values) for ident,values in self.job_rows if
              (state=='All states' or values[1] in (group or {state})) and
              matches_query(' '.join(values),self.query.get())]
        sync_table(self.jobs,rows)

    def _open_selected(self):
        selected=self.jobs.selection()
        if selected:self.open_job(selected[0])

    def live(self,status,workers,samples):
        self.live_status.set(status+f' · {samples} measured PID samples')
        sync_table(self.workers,workers)


def approval_job_rows(jobs):
    states={'waiting_approval','waiting_verification','waiting_repair','needs_input'}
    return [(str(job['id']),(str(job['id']),job['state'],str(job.get('target') or ''),
            str(job.get('detail') or ''))) for job in jobs if job['state'] in states]


def pc_action_rows(actions):
    return [(str(action['id']),(str(action['id']),str(action.get('status','')),
            str(action.get('label','')),str(action.get('approval_source','')),
            str(action.get('approved_at','')))) for action in actions]


class ApprovalCentre(ttk.Frame):
    """Read-only record inspection. Never grant, launch, cancel or replay here."""
    def __init__(self,parent,refresh,inspect_job,inspect_action,links):
        super().__init__(parent)
        self.notice=tk.StringVar(self,value='Refresh to inspect saved records.')
        header=ttk.Frame(self);header.pack(fill='x',pady=5)
        ttk.Label(header,text='APPROVALS & PC ACTIVITY',style='Muted.TLabel').pack(side='left')
        ttk.Button(header,text='Refresh approvals',command=refresh).pack(side='right')
        ttk.Label(self,textvariable=self.notice,wraplength=620).pack(anchor='w',pady=4)
        bar=ttk.Frame(self);bar.pack(fill='x',pady=3)
        action_menu(bar,'Existing permission controls',links).pack(side='left')
        tabs=ttk.Notebook(self);tabs.pack(fill='both',expand=True)
        jobs=ttk.Frame(tabs);actions=ttk.Frame(tabs)
        tabs.add(jobs,text='Workspace review & blockers')
        tabs.add(actions,text='Recorded PC actions')
        self.job_table,self.job_detail=self._pane(jobs,
            'Pending review and blocked job records. Review is not approval.',
            [('id','Job',50),('state','State',135),('target','Target',160),('detail','Evidence',230)],inspect_job)
        self.action_table,self.action_detail=self._pane(actions,
            'Recent JANUS action ledger, across workspaces. Not a complete operating-system audit.',
            [('id','Action',55),('state','State',95),('label','Action label',210),
             ('source','Approval source',125),('stamp','Approved at',150)],inspect_action)

    def _pane(self,parent,caption,columns,inspect):
        ttk.Label(parent,text=caption,wraplength=620).pack(anchor='w',pady=4)
        frame=ttk.Frame(parent);frame.pack(fill='both',expand=True)
        tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show='headings',selectmode='browse',height=7)
        for key,label,width in columns:
            tree.heading(key,text=label);tree.column(key,width=width,stretch=key in ('detail','label'))
        source_scrollbars(frame,tree)
        detail_frame=ttk.Frame(parent);detail_frame.pack(fill='x',pady=4)
        detail=tk.Text(detail_frame,height=9,state='disabled',wrap='word',
                       bg=PALETTE['input'],fg=PALETTE['text'])
        scroll_text(detail_frame,detail)
        def show():
            selected=tree.selection()
            if selected:replace_readonly(detail,inspect(selected[0]))
        ttk.Button(parent,text='Inspect selected record',command=show).pack(anchor='w')
        return tree,detail

    def render(self,project,jobs,actions):
        if getattr(self,'project',None)!=project:
            selected=self.job_table.selection()
            if selected:self.job_table.selection_remove(*selected)
        self.project=project
        sync_table(self.job_table,jobs)
        sync_table(self.action_table,actions)
        replace_readonly(self.job_detail,'Select a workspace record for historical evidence.')
        replace_readonly(self.action_detail,'Select a PC action to inspect its recorded approval and result.')
        self.notice.set(f'{project} · {len(jobs)} review/blocker rows · {len(actions)} recent PC action records')


class KnowledgeMemoryCentre(ttk.Frame):
    """Workspace-scoped historical recall inspection, not a new retrieval path."""
    def __init__(self,parent,refresh,open_library):
        super().__init__(parent)
        self.notice=tk.StringVar(self,value='Open or refresh to inspect saved records.')
        self.worker=tk.StringVar(self,value='No observer sample yet')
        bar=ttk.Frame(self);bar.pack(fill='x',pady=5)
        ttk.Button(bar,text='Refresh memory overview',command=refresh).pack(side='left',padx=3)
        ttk.Button(bar,text='Project knowledge…',command=open_library).pack(side='left',padx=3)
        ttk.Label(self,textvariable=self.notice,wraplength=620).pack(anchor='w',pady=5)
        ttk.Label(self,textvariable=self.worker,style='Muted.TLabel',wraplength=620).pack(anchor='w',pady=4)
        ttk.Label(self,text='Independent recall remains required. Historical findings are advisory, not current proof or execution authority. JANUS and Sentinel receive eligible reports through existing review paths.',wraplength=620).pack(anchor='w',pady=4)
        filterbar=ttk.Frame(self);filterbar.pack(fill='x',pady=3)
        self.query=tk.StringVar(self)
        ttk.Entry(filterbar,textvariable=self.query).pack(side='left',fill='x',expand=True)
        ttk.Button(filterbar,text='Filter memory receipts',command=self.filter).pack(side='left',padx=4)
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        columns=[('job','Job',55),('request','Request',65),('outcome','Outcome',145),
                 ('focus','Focus',240),('count','Findings',65)]
        self.table=ttk.Treeview(frame,columns=[c[0] for c in columns],show='headings',selectmode='browse',height=7)
        for key,label,width in columns:
            self.table.heading(key,text=label);self.table.column(key,width=width,stretch=key=='focus')
        source_scrollbars(frame,self.table)
        ttk.Button(self,text='Inspect memory receipt',command=self.inspect).pack(anchor='w',pady=4)
        details=ttk.Frame(self);details.pack(fill='both',expand=True)
        self.detail=tk.Text(details,height=9,state='disabled',wrap='word',bg=PALETTE['input'],fg=PALETTE['text'])
        scroll_text(details,self.detail)
        self.records={}

    def render(self,project,records,worker):
        if getattr(self,'project',None)!=project:
            selected=self.table.selection()
            if selected:self.table.selection_remove(*selected)
            self.query.set('')
        self.project=project
        self.records={r['work_id']:r for r in records}
        self.notice.set(f'{project} · {len(records)} bounded historical recall receipts')
        self.worker.set(f"Global observer: {'thread alive' if worker['thread_alive'] else 'not observed running'}"
                        f" · active: {worker['active']} · pending: {worker['pending']}"
                        f" · cached reports: {worker['cached_reports']}")
        self.filter()
        replace_readonly(self.detail,'Select a receipt. Its current delivery eligibility has not been revalidated here.')

    def filter(self):
        rows=[]
        for ident,r in self.records.items():
            values=(str(r['job_id']),str(r['request_id']),r['outcome'],r['focus'],str(r['finding_count']))
            if matches_query(' '.join(values),self.query.get()):rows.append((ident,values))
        sync_table(self.table,rows)

    def inspect(self):
        import json
        selected=self.table.selection()
        if not selected:return
        row=self.records.get(selected[0])
        if not row:return
        replace_readonly(self.detail,'Historical receipt · no authority · current relevance not checked\n'+
                         json.dumps(row,indent=2,ensure_ascii=False))


STUDIO_CATEGORIES=('All tools','Images & textures','Music & audio','Video & animation','3D & models',
                   'Documents','Data & analysis','Games & development','Research & web','Communication')

ARTIFACT_EXTENSIONS={
 'Image':{'.png','.jpg','.jpeg','.webp','.svg','.bmp','.gif','.tif','.tiff'},
 'Audio':{'.wav','.mp3','.ogg','.flac','.mid','.midi','.m4a'},
 'Video':{'.mp4','.webm','.avi','.mov','.mkv'},
 '3D model':{'.obj','.stl','.gltf','.glb','.blend','.fbx'},
 'Document':{'.pdf','.docx','.odt','.pptx','.xlsx','.epub','.md','.txt'},
 'Data':{'.csv','.json','.tsv','.ipynb'},
 'Package':{'.zip','.apk','.exe','.msi','.pck'},
}

def studio_artifact_rows(paths):
    from pathlib import PurePath
    rows=[]
    for path in paths:
        suffix=PurePath(path).suffix.casefold()
        category=next((name for name,exts in ARTIFACT_EXTENSIONS.items() if suffix in exts),None)
        if category:rows.append((path,(category,path,suffix)))
    return rows


class StudioCentre(ttk.Frame):
    """Category routing to original controls and a bounded read-only workspace file index."""
    def __init__(self,parent,refresh,tools,inspect):
        super().__init__(parent)
        self.inspect_callback=inspect
        self.notice=tk.StringVar(self,value='Open or refresh the Studio.')
        bar=ttk.Frame(self);bar.pack(fill='x',pady=4)
        ttk.Label(bar,text='STUDIO',style='Muted.TLabel').pack(side='left')
        ttk.Button(bar,text='Refresh artifacts',command=refresh).pack(side='right')
        ttk.Label(self,text='Production tools · choose a category to navigate, not execute.',wraplength=620).pack(anchor='w',pady=4)
        action_menu(self,'Production categories',[(cat,lambda c=cat:tools(c)) for cat in STUDIO_CATEGORIES]).pack(anchor='w',pady=4)
        ttk.Label(self,textvariable=self.notice,wraplength=620).pack(anchor='w',pady=4)
        ttk.Label(self,text='Bounded workspace file snapshot only; large or excluded files may not appear. Presence is not proof of production or testing.',style='Muted.TLabel',wraplength=620).pack(anchor='w',pady=4)
        filters=ttk.Frame(self);filters.pack(fill='x')
        self.category=tk.StringVar(self,value='All states')
        ttk.Combobox(filters,textvariable=self.category,state='readonly',width=13,values=('All states',*ARTIFACT_EXTENSIONS)).pack(side='left')
        self.query=tk.StringVar(self)
        ttk.Entry(filters,textvariable=self.query).pack(side='left',fill='x',expand=True,padx=4)
        ttk.Button(filters,text='Filter artifacts',command=self.filter).pack(side='left')
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        self.table=ttk.Treeview(frame,columns=('category','path','extension'),show='headings',selectmode='browse')
        for key,label,width in (('category','Type',95),('path','Workspace path',390),('extension','Format',70)):
            self.table.heading(key,text=label);self.table.column(key,width=width,stretch=key=='path')
        source_scrollbars(frame,self.table)
        ttk.Button(self,text='Inspect artifact metadata',command=self.inspect).pack(anchor='w',pady=4)
        detail_frame=ttk.Frame(self);detail_frame.pack(fill='x')
        self.detail=tk.Text(detail_frame,height=5,state='disabled',wrap='word',bg=PALETTE['input'],fg=PALETTE['text'])
        scroll_text(detail_frame,self.detail)
        self.rows=[]

    def render(self,project,rows):
        if getattr(self,'project',None)!=project:
            selection=self.table.selection()
            if selection:self.table.selection_remove(*selection)
            self.query.set('');self.category.set('All states')
        self.project=project;self.rows=rows
        self.notice.set(f'{project} · {len(rows)} matching file formats in bounded workspace snapshot')
        self.filter()
        replace_readonly(self.detail,'Select a file to inspect its metadata. No file is executed.')

    def filter(self):
        sync_table(self.table,filter_status_rows(self.rows,self.category.get(),self.query.get()))

    def inspect(self):
        selected=self.table.selection()
        if selected:replace_readonly(self.detail,self.inspect_callback(selected[0]))


def settings_policy_rows(project,tools,network):
    enabled=lambda policy,key:'Enabled' if policy.get(key) is True else 'Disabled' if policy.get(key) is False else 'Unknown'
    return [
        ('project',('Unattended approved project steps',enabled(project,'enabled'),'Job-bound grants only')),
        ('tools',('Routine software management',enabled(tools,'enabled'),'Existing approved software policy')),
        ('upgrades',('Tool upgrades preference',enabled(tools,'allow_upgrades'),'Effective only with routine management')),
        ('network',('Shared HTTPS restrictions',str(network),'Not an OS-wide firewall; existing approvals still apply')),
        ('cpu',('Configured CPU ceiling','50%','Windows supervised launcher; not measured usage')),
        ('commit',('Configured maximum RAM-sized commit','65%','Actual admission may be lower; not physical working set')),
        ('inference',('Primary text inference','Local OpenVINO CPU','External services are separate reviewed integrations')),
    ]


class SettingsCentre(ttk.Frame):
    """Settings directory; existing owners remain authoritative for all writes."""
    def __init__(self,parent,refresh,groups):
        super().__init__(parent)
        self.notice=tk.StringVar(self,value='Open or refresh to read saved settings.')
        bar=ttk.Frame(self);bar.pack(fill='x',pady=4)
        ttk.Label(bar,text='SETTINGS & INTEGRATIONS',style='Muted.TLabel').pack(side='left')
        ttk.Button(bar,text='Refresh settings overview',command=refresh).pack(side='right')
        ttk.Label(self,textvariable=self.notice,wraplength=620).pack(anchor='w',pady=4)
        ttk.Label(self,text='Existing controls own all setting changes. Opening this overview does not grant permission, connect accounts or expose credentials.',wraplength=620).pack(anchor='w',pady=4)
        menus=ttk.Frame(self);menus.pack(fill='x',pady=4)
        for i,(label,actions) in enumerate(groups):
            menu=action_menu(menus,label,actions)
            menu.grid(row=i//2,column=i%2,sticky='ew',padx=3,pady=3)
        menus.columnconfigure(0,weight=1);menus.columnconfigure(1,weight=1)
        frame=ttk.Frame(self);frame.pack(fill='both',expand=True)
        self.table=ttk.Treeview(frame,columns=('policy','value','boundary'),show='headings')
        for key,label,width in (('policy','Saved / configured policy',230),('value','Value',170),('boundary','Scope and limits',300)):
            self.table.heading(key,text=label);self.table.column(key,width=width,stretch=key=='boundary')
        source_scrollbars(frame,self.table)

    def render(self,rows,model_status,project):
        self.notice.set(model_status+' · '+project+' · policy snapshot, not runtime verification')
        sync_table(self.table,rows)
