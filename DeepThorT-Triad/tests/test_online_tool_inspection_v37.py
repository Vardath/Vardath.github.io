"""v37 read-only WinGet package inspection and approval boundary tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepthort_local.online_tool_search import (
    MAX_INSPECTION_BYTES, format_inspection, inspect_show_output,
    validate_package_id, winget_show_command,
)

ID='FreeCAD.FreeCAD'
REPORT='''Found FreeCAD [FreeCAD.FreeCAD]
Version: 1.1.1
Publisher: FreeCAD Project
Publisher Url: https://www.freecad.org/
Homepage: https://www.freecad.org/
License: LGPL-2.1
Installer Type: nullsoft
Installer Url: https://github.com/FreeCAD/FreeCAD/releases/download/v1.1.1/FreeCAD.exe
Installer SHA256: {sha}
'''.format(sha='a'*64)


class PackageMetadataTests(unittest.TestCase):
    def test_exact_fixed_show_argv_cannot_install(self):
        cmd=winget_show_command(ID,which=lambda s:'C:/winget.exe' if s=='winget.exe' else None)
        self.assertEqual(cmd,['C:/winget.exe','show','--id',ID,'--exact',
                              '--source','winget','--locale','en-US',
                              '--accept-source-agreements','--disable-interactivity'])
        self.assertNotIn('install',cmd)
        self.assertNotIn('download',cmd)

    def test_malformed_command_injection_and_lookalikes_rejected(self):
        bad=['',None,'x','-evil.Package','x'*129,'hello world','Foo..Bar',
             'Foo.Bar.', '.Foo.Bar','Foo\\Bar','Foo/Bar','Foo:Bar',
             'Foo.Bar;whoami','Foo.Bar\ninstall','https://a.b','Foo. B',
             'Foo.✓','Foo.Bar&dir','Foo.Bar%00','Foo.Bar@somewhere']
        for item in bad:
            with self.subTest(item=item),self.assertRaises(ValueError):
                validate_package_id(item)
        self.assertEqual(validate_package_id(ID),ID)

    def test_verified_command_exit_is_only_metadata_not_consent(self):
        row=inspect_show_output(ID,REPORT)
        self.assertEqual(row['name'],'FreeCAD')
        self.assertEqual(row['package_id'],ID)
        self.assertEqual(row['version'],'1.1.1')
        self.assertEqual(row['publisher'],'FreeCAD Project')
        self.assertEqual(row['installer_sha256_manifest'],'a'*64)
        self.assertEqual(row['installer_url'].split('/')[2],'github.com')
        self.assertEqual(row['schema'],'deepthort-winget-show-inspection-v1')
        self.assertEqual(len(row['output_sha256']),64)
        self.assertFalse(row['install_authorized'])
        self.assertFalse(row['download_authorized'])
        self.assertIn('NOT INSTALL AUTHORIZATION',row['confidence'])
        self.assertIn('not independently verified',format_inspection(row))

    def test_incomplete_or_ambiguous_reports_cannot_be_accepted(self):
        bad=[REPORT.replace('FreeCAD.FreeCAD','Someone.Else'),
             REPORT+'\nFound Another [Another.Package]\n',
             REPORT.replace('Version: 1.1.1',''),
             REPORT.replace('Publisher: FreeCAD Project',''),
             REPORT.replace('Installer SHA256: '+'a'*64,'Installer SHA256: broken'),
             REPORT.replace('Version: 1.1.1','Version: 1.1.1\nVersion: 2.0'),
             REPORT+'\x1b[3m',REPORT+'A'*(MAX_INSPECTION_BYTES+100),
             REPORT+'\nDescription: '+'A'*2100,
             'No package found matching input criteria.']
        for output in bad:
            with self.subTest(bad=output[:45]),self.assertRaises(ValueError):
                inspect_show_output(ID,output)
        with self.assertRaises(ValueError):
            inspect_show_output(ID,REPORT,exit_code=1)

    def test_reject_untrusted_url_but_keep_metadata_read_only(self):
        for malicious in ['http://bad.example/installer.exe',
                          'https://localhost/installer.exe',
                          'https://user:pass@attacker.example/installer.exe',
                          'https://127.0.0.1/install.exe','https://bad.example:444/install.exe']:
            with self.subTest(malicious=malicious):
                report=REPORT.replace('https://www.freecad.org/',malicious)
                row=inspect_show_output(ID,report)
                self.assertTrue(row['unsafe_urls_rejected'])
                self.assertEqual(row['publisher_url'],'')
                self.assertEqual(row['homepage'],'')
                self.assertFalse(row['install_authorized'])


class DesktopConsentTests(unittest.TestCase):
    def test_declined_exact_package_does_not_queue_command(self):
        from desktop_app import DeepThorTDesktop
        obj=MagicMock();obj._pending_package_inspection=None
        obj.disk_gate.gaming.return_value=False
        with patch('desktop_app.simpledialog.askstring',return_value=ID), \
             patch('desktop_app.winget_show_command',return_value=['winget','show']), \
             patch('desktop_app.messagebox.askyesno',return_value=False):
            DeepThorTDesktop._inspect_package_id(obj)
        obj._start_command.assert_not_called()
        self.assertIsNone(obj._pending_package_inspection)

    def test_approved_package_inspection_only_queues_read_only_command(self):
        from desktop_app import DeepThorTDesktop
        obj=MagicMock();obj._pending_package_inspection=None
        obj.disk_gate.gaming.return_value=False
        obj._start_command.return_value=True
        cmd=['C:/winget.exe','show','--id',ID,'--exact']
        with patch('desktop_app.simpledialog.askstring',return_value=ID), \
             patch('desktop_app.winget_show_command',return_value=cmd), \
             patch('desktop_app.messagebox.askyesno',return_value=True):
            DeepThorTDesktop._inspect_package_id(obj)
        obj._start_command.assert_called_once()
        args,kw=obj._start_command.call_args
        self.assertEqual(args[0],cmd)
        self.assertEqual(kw['kind'],'package_inspection')
        self.assertEqual(obj._pending_package_inspection,{'package_id':ID,'argv':cmd})
        obj.tabs.select.assert_called_once_with(4)

    def test_inspection_is_blocked_while_gaming_or_running(self):
        from desktop_app import DeepThorTDesktop
        obj=MagicMock();obj._pending_package_inspection=None
        obj.disk_gate.gaming.return_value=True
        with patch('desktop_app.simpledialog.askstring') as ask, \
             patch('desktop_app.messagebox.showwarning'):
            DeepThorTDesktop._inspect_package_id(obj)
        ask.assert_not_called()
        obj.disk_gate.gaming.return_value=False
        obj._pending_package_inspection={'package_id':ID}
        with patch('desktop_app.simpledialog.askstring') as ask, \
             patch('desktop_app.messagebox.showinfo'):
            DeepThorTDesktop._inspect_package_id(obj)
        ask.assert_not_called()

    def test_reconcile_captures_only_a_matching_finite_report(self):
        from desktop_app import DeepThorTDesktop
        cmd=['C:/winget.exe','show','--id',ID,'--exact']
        with tempfile.TemporaryDirectory() as folder, \
             patch('desktop_app.STATE',Path(folder)), \
             patch('desktop_app.messagebox.showinfo'), \
             patch('desktop_app.record'):
            obj=MagicMock()
            obj._pending_package_inspection={'package_id':ID,'argv':cmd}
            result={'argv':cmd,'lines':REPORT.splitlines(),'truncated':False}
            DeepThorTDesktop._receive_package_inspection(obj,0,result)
            self.assertIsNone(obj._pending_package_inspection)
            receipt=json.loads((Path(folder)/'last-package-inspection.json').read_text())
            self.assertFalse(receipt['install_authorized'])
            self.assertEqual(receipt['package_id'],ID)
            obj._start_command.assert_not_called()

    def test_changed_args_or_truncation_rejects_evidence(self):
        from desktop_app import DeepThorTDesktop
        cmd=['winget','show','--id',ID]
        for result in [{'argv':['winget','install','--id',ID],
                        'lines':REPORT.splitlines()},
                       {'argv':cmd,'lines':REPORT.splitlines(),'truncated':True},
                       {'argv':cmd,'lines':REPORT.splitlines()[:2]}]:
            with self.subTest(result=result), \
                 patch('desktop_app.messagebox.showwarning') as warn:
                obj=MagicMock();obj._pending_package_inspection={'package_id':ID,'argv':cmd}
                DeepThorTDesktop._receive_package_inspection(obj,0,result)
                warn.assert_called_once()
                self.assertIsNone(obj._pending_package_inspection)
                obj._start_command.assert_not_called()

if __name__=='__main__':unittest.main()
