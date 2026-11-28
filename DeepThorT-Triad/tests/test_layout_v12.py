"""Protect the original v10.9 chat layout against status-banner regressions."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Tk display required')
class OriginalWindowLayoutTests(unittest.TestCase):
    def setUp(self):
        import desktop_app
        self.desktop_app=desktop_app
        self.tmp=tempfile.TemporaryDirectory()
        self.state=patch.object(desktop_app,'STATE',Path(self.tmp.name)/'state')
        self.inventory=patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda self:None)
        self.state.start();self.inventory.start()
        self.app=desktop_app.DeepThorTDesktop()

    def tearDown(self):
        self.app._quit()
        self.inventory.stop();self.state.stop();self.tmp.cleanup()

    def _assert_action_buttons_visible(self):
        self.app.update_idletasks()
        buttons=[w for row in self.app.chat_actions.winfo_children()
                for w in row.winfo_children() if w.winfo_class()=='TButton']
        labels=[b.cget('text') for b in buttons]
        self.assertIn('Draft project plan',labels)
        self.assertIn('Approve plan & queue',labels)
        self.assertIn('Revise existing file',labels)
        self.assertTrue(all(b.winfo_ismapped() for b in buttons),labels)
        bottom=self.app.winfo_rooty()+self.app.winfo_height()
        self.assertLessEqual(max(b.winfo_rooty()+b.winfo_height() for b in buttons),bottom)

    def test_no_second_status_row_and_original_buttons_fit_at_default(self):
        self.assertIs(self.app.reply_notice,self.app.chat_connection)
        self.assertFalse(hasattr(self.app,'reply_banner'))
        self.app.geometry('1320x860');self.app.update()
        self.assertEqual(int(self.app.input.cget('height')),5)
        self.app.input.insert('1.0','Preserve draft')
        self.app.expanded_composer.set(True);self.app._resize_composer()
        self.assertEqual(int(self.app.input.cget('height')),12)
        self.assertEqual(self.app.input.get('1.0','end-1c'),'Preserve draft')
        self.app.expanded_composer.set(False);self.app._resize_composer()
        self._assert_action_buttons_visible()

    def test_buttons_not_clipped_in_screenshot_sized_window(self):
        self.app.geometry('1138x765');self.app.update()
        self.assertLess(int(self.app.input.cget('height')),12)
        self._assert_action_buttons_visible()

    def test_connection_updates_do_not_erase_active_reply(self):
        self.app.active_conversation=7
        self.app.conversations.get=lambda _:{'mode':'chat','chat_id':self.app.current_chat}
        self.app.reply_stage='Waiting for local model'
        import time
        self.app.reply_started=time.monotonic()-15
        self.app._render_reply_notice()
        self.app._set_connection_status('AI READY')
        self.assertIn('IN PROGRESS',self.app.chat_connection.get())
        self.app.active_conversation=None
        self.app.reply_stage=''
        self.app._render_reply_notice()
        self.assertEqual(self.app.chat_connection.get(),'AI READY')

    def test_lattice_tool_shelf_filters_without_invoking_commands(self):
        self.app.geometry('1138x765')
        self.app.tabs.select(7)
        self.app.update()
        shelf=self.app.media_shelf
        buttons=[button for _,_,items in shelf._index for button,_ in items]
        self.assertGreater(len(buttons),100)
        labels=[button.cget('text') for button in buttons]
        self.assertIn('Search internet…',labels)
        self.assertIn('Test OS restricted-token boundary…',labels)
        shelf.query.set('restricted-token')
        self.app.update_idletasks()
        self.assertEqual(shelf.count.get(),f'1 / {len(buttons)} tools')
        matching=[button.cget('text') for button in buttons if button.winfo_manager()=='pack']
        self.assertEqual(matching,['Test OS restricted-token boundary…'])
        shelf.query.set('zzzz-no-such-tool')
        self.app.update_idletasks()
        self.assertEqual(shelf.count.get(),f'0 / {len(buttons)} tools')
        shelf.query.set('')
        self.app.update_idletasks()
        self.assertEqual(shelf.count.get(),f'{len(buttons)} / {len(buttons)} tools')
        self.assertEqual([button.cget('text') for button in buttons if button.winfo_manager()=='pack'],labels)
        self.assertTrue(shelf.canvas.winfo_ismapped())
        self.assertTrue(self.app.image_info.winfo_ismapped())
