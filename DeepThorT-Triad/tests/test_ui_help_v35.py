"""v35 offline help, official source and expanded advisory regression tests."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.ui_help import TOOLTIPS, TABS, _tab_description
from deepthort_local.computer_inventory import INSTALL_CATALOG, plan_tool_needs
from deepthort_local.tool_sources import OFFICIAL_SOURCES, official_source

class OfficialSourceTests(unittest.TestCase):
    def test_all_installable_packages_have_reviewed_publisher_page(self):
        self.assertEqual(set(OFFICIAL_SOURCES), set(INSTALL_CATALOG))
        for name in INSTALL_CATALOG:
            with self.subTest(name=name):
                row = official_source(name)
                self.assertEqual(row['package_id'], INSTALL_CATALOG[name][0])
                self.assertTrue(row['url'].startswith('https://'))
                self.assertIn('information_only', row['action'])
    def test_no_model_url_or_unrecognized_package_allowed(self):
        for payload in ('https://untrusted.invalid/setup.exe','Godot.exe','',None):
            self.assertIsNone(official_source(payload))
    def test_new_category_advice_is_curated_for_routine_installation(self):
        inventory = {'tools': []}
        examples = [('write a novel and EPUB', 'Pandoc'),
                    ('make a podcast audio recording', 'Audacity'),
                    ('edit a cinematic video', 'FFmpeg'),
                    ('create vector graphic illustration', 'Inkscape'),
                    ('design a 3d print CAD object', 'FreeCAD')]
        for request, expected in examples:
            with self.subTest(request=request):
                row = {x['name']: x for x in plan_tool_needs(request,inventory)}
                self.assertIn(expected,row)
                self.assertTrue(row[expected]['proposed_install'])

@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Tk display required')
class DesktopHelpTests(unittest.TestCase):
    def setUp(self):
        import desktop_app
        self.module = desktop_app
        self.tmp = tempfile.TemporaryDirectory()
        self.state = patch.object(desktop_app,'STATE',Path(self.tmp.name)/'state')
        self.inventory = patch.object(desktop_app.DeepThorTDesktop,'_refresh_inventory',lambda _:None)
        self.state.start(); self.inventory.start()
        self.app = desktop_app.DeepThorTDesktop()
        self.app.update_idletasks()

    def tearDown(self):
        self.app._quit()
        self.inventory.stop(); self.state.stop(); self.tmp.cleanup()

    def walk(self, parent):
        for w in parent.winfo_children():
            yield w
            yield from self.walk(w)

    def test_f1_and_every_primary_button_has_help(self):
        buttons = [w for w in self.walk(self.app) if w.winfo_class()=='TButton']
        names = [w.cget('text') for w in buttons]
        self.assertIn('User guide', names)
        self.assertIn('Find official tool page…', names)
        for name in names:
            with self.subTest(button=name):
                self.assertTrue(TOOLTIPS.get(name), f'No actual tooltip for {name}')
        self.assertGreaterEqual(len(self.app._tooltip_handles), len(buttons))
        self.assertEqual(len(self.app.tabs.tabs()),12)
        self.assertTrue(self.app.bind_all('<F1>'))
        self.assertTrue(self.app.input.bind('<Enter>'))

    def test_notebook_hover_resolves_the_tab_label(self):
        self.app.geometry('1320x860')
        self.app.update()
        for i in range(len(self.app.tabs.tabs())):
            box = self.app.tabs.bbox(i)
            if not box:continue
            x, y, w, h = box
            if w<=0:continue
            desc = _tab_description(self.app.tabs, type('Pt',(),{'x':x+w//2,'y':y+h//2})())
            tab_name = self.app.tabs.tab(i,'text')
            self.assertEqual(desc,TABS[tab_name])

    def test_guide_opens_local_file_only(self):
        with patch.object(self.module.webbrowser,'open',return_value=True) as browser:
            self.app._open_user_guide()
            url=browser.call_args.args[0]
            self.assertTrue(url.startswith('file:///'))
            self.assertIn('USER_GUIDE.html',url)

    def test_official_lookup_requires_consent_and_never_installs(self):
        self.app.install_choice.set('Blender')
        with patch.object(self.module.messagebox,'askyesno',return_value=False),\
             patch.object(self.module.webbrowser,'open') as browser,\
             patch.object(self.app,'_start_command') as runner:
            self.app._find_official_tool_page()
            browser.assert_not_called()
            runner.assert_not_called()
        with patch.object(self.module.messagebox,'askyesno',return_value=True),\
             patch.object(self.module.webbrowser,'open') as browser,\
             patch.object(self.app,'_start_command') as runner:
            self.app._find_official_tool_page()
            browser.assert_called_once_with('https://www.blender.org/download/')
            runner.assert_not_called()

if __name__=='__main__': unittest.main()
