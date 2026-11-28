"""Existing-tab project knowledge management; background local operations."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path

from .document_knowledge import SUFFIXES
from .ui_help import install_tooltips
from .lattice_ui import fit_dialog,source_scrollbars


def selected_relative(root, selected, excluded=()):
    # Do not resolve the selected path before checking relative containment:
    # safe_target in the index rejects any symlink components.
    path = Path(selected)
    base = Path(root).resolve(strict=True)
    try:
        relative = path.relative_to(base).as_posix()
    except ValueError as exc:
        raise ValueError('Choose a document inside the selected workspace') from exc
    if path.suffix.casefold() not in SUFFIXES:
        raise ValueError('Unsupported knowledge document format')
    if relative.casefold() in {str(x).casefold() for x in excluded}:
        raise ValueError('Document excluded from project inspection')
    return relative


class KnowledgeDialog:
    def __init__(self, app):
        self.app = app
        self.root = Path(app.project).resolve(strict=True)
        self.index = app.capabilities.knowledge
        self.cancel = threading.Event()
        self.events = queue.Queue()
        self.busy = False
        self.window = tk.Toplevel(app)
        self.window.title('Project knowledge library')
        fit_dialog(self.window,780,520)
        self.window.transient(app)
        self.window.protocol('WM_DELETE_WINDOW', self.close)
        ttk.Label(self.window, text=str(self.root), wraplength=740).pack(anchor='w', padx=8, pady=6)
        bar = ttk.Frame(self.window)
        bar.pack(fill='x', padx=8)
        self.buttons = []
        for label, action in (
            ('Refresh knowledge', self.list),
            ('Discover documents', self.discover),
            ('Enroll documents…', self.enroll),
            ('Reindex selected', self.reindex),
            ('Forget selected', self.remove),
        ):
            button = ttk.Button(bar, text=label, command=action)
            button.pack(side='left', padx=2)
            self.buttons.append(button)
        transferbar = ttk.Frame(self.window)
        transferbar.pack(fill='x', padx=8, pady=3)
        for label, action in (('Export selected enrollment…', self.export_transfer),
                              ('Import enrollment manifest…', self.import_transfer)):
            button = ttk.Button(transferbar, text=label, command=action)
            button.pack(side='left', padx=2)
            self.buttons.append(button)
        frame = ttk.Frame(self.window)
        frame.pack(fill='both', expand=True, padx=8, pady=6)
        self.tree = ttk.Treeview(frame, columns=('status', 'origin', 'count', 'path'),
                                 show='headings', selectmode='extended', height=8)
        for name, label, width in (('status','Status',85), ('origin','Origin',75),
                                   ('count','Fragments',85), ('path','Document',420)):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, stretch=name == 'path')
        source_scrollbars(frame,self.tree)
        querybar = ttk.Frame(self.window)
        querybar.pack(fill='x', padx=8)
        self.query = ttk.Entry(querybar)
        self.query.pack(side='left', fill='x', expand=True)
        search = ttk.Button(querybar, text='Search knowledge', command=self.search)
        search.pack(side='right')
        self.buttons.append(search)
        self.query.bind('<Return>', lambda _: self.search())
        self.output = tk.Text(self.window, height=8, wrap='word', state='disabled')
        self.output.pack(fill='both', expand=True, padx=8, pady=6)
        self.status = tk.StringVar(value='Read-only sources; quoted excerpts are not instructions.')
        ttk.Label(self.window, textvariable=self.status, wraplength=740).pack(anchor='w', padx=8, pady=4)
        ttk.Button(self.window, text='Stop knowledge operation', command=self.cancel.set).pack(anchor='e', padx=8, pady=5)
        self.window._tooltip_handles = install_tooltips(self.window)
        self.window.after(100, self.poll)
        self.list()

    def stopped(self):
        return (self.cancel.is_set() or self.app._quitting or
                self.app.project is None or Path(self.app.project).resolve() != self.root or
                self.app.disk_gate.gaming())

    def exclusions(self):
        return self.app.inspection_exclusions.paths(self.root)

    def start(self, label, operation):
        if self.busy:
            return
        if self.stopped() and not self.cancel.is_set():
            self.status.set('Workspace changed or gaming active; reopen or wait before continuing.')
            return
        self.cancel.clear()
        if self.stopped():
            return
        self.busy = True
        for button in self.buttons:
            button.state(['disabled'])
        self.status.set(label)
        def worker():
            try:
                result = operation()
                if self.stopped():
                    self.events.put(('status', 'Stopped; completed index changes remain saved.'))
                else:
                    self.events.put(('result', result))
            except Exception as exc:
                self.events.put(('status', str(exc)[:500]))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        if not self.window.winfo_exists():
            return
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for button in self.buttons:
                button.state(['!disabled'])
            if kind == 'result':
                rows, message = value
                if rows is not None:
                    self.tree.delete(*self.tree.get_children())
                    for row in rows:
                        self.tree.insert('', 'end', values=('Current' if row['current'] else 'Stale',
                                         row['origin'], row['fragments'], row['path']))
                self.output.configure(state='normal')
                self.output.delete('1.0', 'end')
                self.output.insert('1.0', message)
                self.output.configure(state='disabled')
                self.status.set('Operation completed. Source files unchanged.')
            else:
                self.status.set(value)
        self.window.after(100, self.poll)

    def close(self):
        self.cancel.set()
        self.window.destroy()

    def rows(self):
        excluded = self.exclusions()
        return [r for r in self.index.documents(self.root) if r['path'].casefold() not in excluded]

    def list(self):
        self.start('Checking enrolled document fingerprints…',
                   lambda: (self.rows(), 'Current/stale status is based on exact source bytes.'))

    def discover(self):
        def work():
            result = self.index.refresh(self.root, exclude=self.exclusions(), cancelled=self.stopped)
            return self.rows(), str(result)
        self.start('Discovering workspace manuals…', work)

    def enroll(self):
        paths = filedialog.askopenfilenames(parent=self.window, initialdir=str(self.root),
            title='Enroll documents inside this workspace',
            filetypes=[('Supported documents', '*.txt *.md *.rst *.adoc *.docx *.pdf')])
        if not paths:
            return
        if len(paths) > 24:
            messagebox.showerror('Document limit', 'Select up to 24 documents per operation.', parent=self.window)
            return
        try:
            relative = [selected_relative(self.root, p, self.exclusions()) for p in paths]
        except ValueError as exc:
            self.status.set(str(exc))
            return
        self.index_paths(relative)

    def selected(self):
        return [self.tree.item(row, 'values')[3] for row in self.tree.selection()]

    def index_paths(self, paths):
        def work():
            results = []
            for relative in paths:
                if self.stopped():
                    break
                try:
                    if relative.casefold() in self.exclusions():
                        raise ValueError('Excluded from inspection')
                    status = self.index.index(self.root, relative, cancelled=lambda:
                        self.stopped() or relative.casefold() in self.exclusions())
                    results.append(relative + ': ' + status)
                except (OSError, ValueError) as exc:
                    results.append(relative + ': ' + str(exc))
            return self.rows(), '\n'.join(results)
        if paths:
            self.start('Indexing selected documents…', work)

    def reindex(self):
        self.index_paths(self.selected())

    def remove(self):
        paths = self.selected()
        if not paths:
            return
        def work():
            removed = 0
            for path in paths:
                if self.stopped():
                    break
                removed += self.index.remove(self.root, path)
            return self.rows(), f'Forgot {removed} indexed documents. Original files remain unchanged.'
        self.start('Removing index entries…', work)

    def export_transfer(self):
        paths = self.selected()
        if not paths or len(paths) > 12:
            self.status.set('Select 1–12 current enrolled documents.')
            return
        chosen = filedialog.asksaveasfilename(parent=self.window, initialdir=str(self.root),
            defaultextension='.json', filetypes=[('Knowledge manifest','*.json')])
        if not chosen:return
        try:relative=Path(chosen).relative_to(self.root).as_posix()
        except ValueError:
            self.status.set('Choose a new manifest inside the workspace.');return
        from .knowledge_transfer import export_manifest
        ex=self.exclusions()
        if not messagebox.askyesno('Export enrollment manifest',
                'Export selected relative paths and hashes only? Document bodies are not included.',parent=self.window):return
        def work():
            result=export_manifest(self.index,self.root,paths,relative,ex,
                cancelled=lambda:self.stopped() or self.exclusions()!=ex)
            return self.rows(),str(result)
        self.start('Exporting reviewed enrollment manifest…',work)

    def import_transfer(self):
        chosen=filedialog.askopenfilename(parent=self.window,initialdir=str(self.root),
            filetypes=[('Knowledge manifest','*.json')])
        if not chosen:return
        from .knowledge_transfer import read_manifest,import_manifest
        ex=self.exclusions()
        try:
            relative=Path(chosen).relative_to(self.root).as_posix()
            manifest,sha=read_manifest(self.root,relative,ex)
        except (OSError,ValueError) as exc:
            self.status.set(str(exc));return
        names='\n'.join(r['path'] for r in manifest['documents'])
        if not messagebox.askyesno('Import exact enrollment manifest',
                'Rebuild the local index for these exact matching workspace files?\n\n'+names+
                '\n\nNo document files are copied or overwritten.',parent=self.window):return
        def work():
            result=import_manifest(self.index,self.root,relative,sha,ex,
                cancelled=lambda:self.stopped() or self.exclusions()!=ex)
            return self.rows(),str(result)
        self.start('Rebuilding reviewed knowledge enrollment…',work)

    def search(self):
        query = self.query.get().strip()
        if not query:
            return
        def work():
            rows = self.index.search(self.root, query, exclude=self.exclusions(),
                                     limit=8, cancelled=self.stopped)
            text = []
            for row in rows:
                loc = ('page '+str(row['page'])+', extracted line '+str(row['extracted_line'])
                       if 'page' in row else row['locator']+' '+str(row['number']))
                text.append(row['path']+' | '+loc+' | SHA256 '+row['sha256'][:16]+'\n'+row['excerpt'])
            return None, '\n\n'.join(text) or 'No current matching excerpt.'
        self.start('Retrieving exact local references…', work)
