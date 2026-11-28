"""Native Tk shelf regression with no inference or tool execution."""
import tkinter as tk
from tkinter import ttk
import unittest
from deepthort_local.lattice_ui import ToolShelf, PALETTE, dragon_mark, action_menu, scroll_text, composer_rows


class LatticeShelfTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry('450x280')
        self.shelf = ToolShelf(self.root)
        self.shelf.pack(fill='both', expand=True)
        self.calls = []
        self.buttons = []
        for labels in [('Search internet…', 'Create PDF…'),
                       ('Test OS restricted-token boundary…', 'Generate image from prompt')]:
            row = ttk.Frame(self.shelf.rows)
            row.pack(fill='x')
            for label in labels:
                button = ttk.Button(row, text=label, command=lambda label=label: self.calls.append(label))
                button.pack(side='left')
                self.buttons.append(button)
        self.shelf.index_buttons()
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def labels(self):
        return [b.cget('text') for b in self.buttons if b.winfo_manager() == 'pack']

    def test_filter_empty_restore_and_exact_callback(self):
        original = self.labels()
        self.shelf.query.set('restricted-token')
        self.root.update()
        self.assertEqual(self.labels(), ['Test OS restricted-token boundary…'])
        self.assertEqual(self.shelf.count.get(), '1 / 4 tools')
        self.assertEqual(self.calls, [])
        self.buttons[2].invoke()
        self.assertEqual(self.calls, ['Test OS restricted-token boundary…'])
        self.shelf.query.set('no such operation')
        self.root.update()
        self.assertEqual(self.labels(), [])
        self.assertEqual(self.shelf.count.get(), '0 / 4 tools')
        self.shelf.query.set('')
        self.root.update()
        self.assertEqual(self.labels(), original)
        self.assertEqual(self.shelf.count.get(), '4 / 4 tools')

    def test_scroll_region_includes_original_controls(self):
        self.root.geometry('180x120')
        self.root.update()
        self.assertTrue(self.shelf.canvas.winfo_ismapped())
        box = self.shelf.canvas.bbox('all')
        self.assertGreater(box[2], self.shelf.canvas.winfo_width())
        self.shelf.canvas.xview_moveto(1)
        self.assertGreater(self.shelf.canvas.xview()[0], 0)

    def test_palette_and_mark(self):
        mark = dragon_mark(self.root)
        self.assertGreaterEqual(len(mark.find_all()), 4)
        self.assertEqual(mark.cget('bg'), PALETTE['base'])
        mark.destroy()


    def test_action_menu_is_inert_until_exact_choice(self):
        control = action_menu(self.root, 'System', [
            ('Start', lambda: self.calls.append('start')),
            ('Stop', lambda: self.calls.append('stop'))])
        menu = control.nametowidget(control.cget('menu'))
        self.assertEqual(self.calls, [])
        self.assertEqual(menu.entrycget(1, 'label'), 'Stop')
        menu.invoke(1)
        self.assertEqual(self.calls, ['stop'])

    def test_composer_resize_preserves_draft_and_scroll(self):
        frame = ttk.Frame(self.root)
        text = tk.Text(frame, height=5, undo=True)
        bar = scroll_text(frame, text)
        text.insert('1.0', 'unsent draft')
        for height, expanded, expected in [(860, False, 5), (860, True, 12),
                                           (650, True, 3), (765, False, 3)]:
            self.assertEqual(composer_rows(height, expanded), expected)
            text.configure(height=expected)
        self.assertEqual(text.get('1.0', 'end-1c'), 'unsent draft')
        self.assertTrue(text.cget('yscrollcommand'))
        self.assertTrue(bar.cget('command'))
