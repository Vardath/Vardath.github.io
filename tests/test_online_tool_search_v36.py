"""v36 read-only internet discovery: no implicit network calls or installation."""
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepthort_local.online_tool_search import winget_search_command

class WingetSearchTests(unittest.TestCase):
    def test_search_constructs_fixed_read_only_argv(self):
        cmd=winget_search_command('  FreeCAD  ',which=lambda name: 'C:/winget.exe' if name=='winget.exe' else None)
        self.assertEqual(cmd,['C:/winget.exe','search','--query','FreeCAD','--source','winget',
                              '--count','20','--accept-source-agreements','--disable-interactivity'])
        self.assertNotIn('install',cmd)
        self.assertNotIn('download',cmd)
    def test_rejects_command_injection_and_options(self):
        for q in ('', 'x','-help','--source msstore','x\ny','blender;del C:',
                  'bad|pipe','http://example.com',r'\\server\share','x'*101):
            with self.subTest(q=q),self.assertRaises(ValueError):
                winget_search_command(q,which=lambda name:'C:/winget.exe')
    def test_no_package_manager_is_not_an_install(self):
        with self.assertRaises(FileNotFoundError):
            winget_search_command('Blender',which=lambda _:None)
    def test_search_requires_explicit_button_consent(self):
        # The desktop method is tested with a minimal stand-in, no Tk/model/network.
        from desktop_app import DeepThorTDesktop
        obj=MagicMock()
        obj.disk_gate.gaming.return_value=False
        obj._start_command.return_value=True
        with patch('desktop_app.simpledialog.askstring',return_value='FreeCAD'), \
             patch('desktop_app.messagebox.askyesno',return_value=False), \
             patch('desktop_app.winget_search_command',return_value=['winget','search','--query','FreeCAD']), \
             patch('desktop_app.messagebox.showwarning'):
            DeepThorTDesktop._search_online_tools(obj)
        obj._start_command.assert_not_called()
    def test_approved_search_invokes_only_search_and_log(self):
        from desktop_app import DeepThorTDesktop
        obj=MagicMock()
        obj.disk_gate.gaming.return_value=False
        obj._start_command.return_value=True
        args=['winget','search','--query','FreeCAD']
        with patch('desktop_app.simpledialog.askstring',return_value='FreeCAD'), \
             patch('desktop_app.messagebox.askyesno',return_value=True), \
             patch('desktop_app.winget_search_command',return_value=args), \
             patch('desktop_app.messagebox.showwarning'):
            DeepThorTDesktop._search_online_tools(obj)
        obj._start_command.assert_called_once()
        positional,keyword=obj._start_command.call_args
        self.assertEqual(positional[0],args)
        self.assertEqual(keyword['kind'],'tool')
        self.assertEqual(keyword['label'],'Online winget search')
        obj.tabs.select.assert_called_once_with(4)
    def test_game_priority_stops_search_early(self):
        from desktop_app import DeepThorTDesktop
        obj=MagicMock();obj.disk_gate.gaming.return_value=True
        with patch('desktop_app.simpledialog.askstring') as ask, \
             patch('desktop_app.messagebox.showwarning') as warn:
            DeepThorTDesktop._search_online_tools(obj)
            ask.assert_not_called()
            warn.assert_called_once()
