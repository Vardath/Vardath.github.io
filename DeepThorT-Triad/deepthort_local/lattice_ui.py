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
