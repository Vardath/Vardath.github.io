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
