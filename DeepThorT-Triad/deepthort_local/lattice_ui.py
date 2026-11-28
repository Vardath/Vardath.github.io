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
                if all(word in str(button.cget('text')).casefold() for word in words):
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
    'Waiting / blocked': {'waiting_approval','waiting_sources','waiting','blocked','paused','interrupted'},
    'Completed / stopped': {'done','completed','succeeded','failed','cancelled','stopped'},
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
