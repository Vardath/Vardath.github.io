"""v56 regression: Chat reply retry and JANUS instruction retry are distinct.

No ONNX inference or file execution is started by these UI controls.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deepthort_local.instruction_inbox import InstructionInbox


class ScopedInstructionRetryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.db=InstructionInbox(self.base/'inbox.sqlite3')
        self.a=str(self.base/'project_a')
        self.b=str(self.base/'project_b')

    def failed(self, project, msg):
        ident=self.db.enqueue(project,'chat',msg)
        self.assertEqual(self.db.claim()['id'],ident)
        self.assertTrue(self.db.fail(ident,'Model response was not valid JSON'))
        return ident

    def test_retry_latest_failure_is_project_scoped_and_atomic(self):
        old=self.failed(self.a,'Old failed')
        other=self.failed(self.b,'Other workspace')
        new=self.failed(self.a,'Newest failed')
        self.assertEqual(self.db.retry_latest_failed(self.a),new)
        states={x['id']:x['state'] for x in self.db.list()}
        self.assertEqual(states[new],'pending')
        self.assertEqual(states[old],'needs_review')
        self.assertEqual(states[other],'needs_review')
        self.assertEqual(self.db.retry_latest_failed(self.a),old)
        self.assertIsNone(self.db.retry_latest_failed(self.a))
        self.assertEqual(self.db.claim()['id'],old)

    def test_staged_or_reviewable_advice_is_never_reinterpreted(self):
        ident=self.db.enqueue(self.a,'chat','Advisory guidance')
        self.db.claim()
        self.assertTrue(self.db.finish(ident,'j','s','Proposed action','Check actual evidence',needs_review=True))
        self.assertIsNone(self.db.retry_latest_failed(self.a))
        self.assertEqual(self.db.list(self.a)[0]['state'],'needs_review')
        self.assertFalse(self.db.retry_interpretation(ident))
        self.assertTrue(self.db.review(ident,allow_planning=True))
        self.assertIsNone(self.db.retry_latest_failed(self.a))

    def test_invalid_project_is_rejected(self):
        with self.assertRaises(ValueError):self.db.retry_latest_failed('')


class VisibleInstructionRetryGuiTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt' or os.environ.get('DISPLAY'),'Requires Tk')
    def test_separate_top_tab_retry_and_popup_selection(self):
        import tkinter as tk
        from tkinter import ttk
        import desktop_app as m
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            project=root/'x4mods';project.mkdir()
            with patch.object(m,'STATE',root/'state'), \
                 patch.object(m.DeepThorTDesktop,'_refresh_inventory',lambda self:None), \
                 patch.object(m.messagebox,'showinfo') as info:
                app=m.DeepThorTDesktop()
                try:
                    app._set_project(project)
                    ident=app.instruction_inbox.enqueue(str(project),'chat','Check PE ship model')
                    app.instruction_inbox.claim()
                    app.instruction_inbox.fail(ident,'Bad JSON')
                    self.assertTrue(has_button(app,'Retry latest failed JANUS instruction'))
                    self.assertTrue(has_button(app,'Retry failed reply'))
                    self.assertTrue(has_button(app,'Instruction inbox…'))
                    app._show_instruction_inbox()
                    windows=[x for x in app.winfo_children() if isinstance(x,tk.Toplevel)]
                    self.assertEqual(len(windows),1)
                    window=windows[0]
                    self.assertTrue(has_button(window,'Retry selected failed interpretation'))
                    tree=find_widget(window,ttk.Treeview)
                    self.assertEqual(tree.selection(),(str(ident),))
                    # The popup retry, not Chat retry, resets only this instruction.
                    retry=find_button(window,'Retry selected failed interpretation')
                    retry.invoke()
                    self.assertEqual(app.instruction_inbox.list(str(project))[0]['state'],'pending')
                    window.destroy()
                    # New failure can be requeued through a directly accessible main-tab button.
                    app.instruction_inbox.claim();app.instruction_inbox.fail(ident,'Still invalid')
                    app._retry_latest_janus_instruction()
                    self.assertEqual(app.instruction_inbox.list(str(project))[0]['state'],'pending')
                    self.assertFalse(info.called)
                    self.assertEqual(app.jobs.items(str(project)),[])
                finally:
                    app._quit()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def find_button(root, label):
    from tkinter import ttk
    return next(x for x in descendants(root) if isinstance(x,ttk.Button) and x.cget('text')==label)


def has_button(root,label):
    try:find_button(root,label);return True
    except StopIteration:return False


def find_widget(root,cls):
    return next(x for x in descendants(root) if isinstance(x,cls))


if __name__=='__main__':unittest.main()
