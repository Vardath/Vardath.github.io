"""v38: reviewed, exact-version, user-consented installation boundary.

Does not execute WinGet or download software; verifies safety of constructed
arguments, single-use GUI consent and persisted unverified status.
"""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from deepthort_local.online_tool_search import inspect_show_output
from deepthort_local.reviewed_install import (prepare_reviewed_install,
    exact_consent_phrase, approval_receipt)

ID='FreeCAD.FreeCAD'
REPORT='''Found FreeCAD [FreeCAD.FreeCAD]
Version: 1.1.1
Publisher: FreeCAD Project
Publisher Url: https://www.freecad.org/
Homepage: https://www.freecad.org/
License: LGPL-2.1
License Url: https://www.freecad.org/license.html
Installer Type: nullsoft
Installer Url: https://github.com/FreeCAD/FreeCAD/releases/download/v1.1.1/FreeCAD.exe
Installer SHA256: {sha}
'''.format(sha='a'*64)


def inspection():
    return inspect_show_output(ID, REPORT)


def plan(row=None, now=None):
    return prepare_reviewed_install(row or inspection(), now=now,
          which=lambda n:'C:/Windows/winget.exe' if n=='winget.exe' else None)


class ReviewedPlanTests(unittest.TestCase):
    def test_exact_install_argv_and_no_security_bypass(self):
        p=plan()
        self.assertEqual(p['argv'],['C:/Windows/winget.exe','install','--id',ID,
             '--exact','--version','1.1.1','--source','winget','--scope','user',
             '--no-upgrade','--accept-source-agreements','--accept-package-agreements',
             '--disable-interactivity'])
        self.assertNotIn('--ignore-security-hash',p['argv'])
        self.assertNotIn('--force',p['argv'])
        self.assertNotIn('--override',p['argv'])
        self.assertNotIn('--silent',p['argv'])
        self.assertFalse(p['approval'])
        self.assertFalse(p['install_started'])
        self.assertEqual(len(p['plan_sha256']),64)
        self.assertEqual(p['manifest_installer_sha256'],'a'*64)
        self.assertEqual(p['license_url'],'https://www.freecad.org/license.html')

    def test_catalog_and_receipt_never_preapprove(self):
        p=plan()
        for key,value in [('schema','other'),('source','msstore'),
                          ('install_authorized',True),('download_authorized',True),
                          ('confidence','VERIFIED'),('state','inconclusive')]:
            raw=inspection();raw[key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):
                plan(raw)
        bad=inspection();bad['unsafe_urls_rejected']=['installer_url']
        with self.assertRaises(ValueError):plan(bad)

    def test_required_provenance_and_hash(self):
        overrides=[('installer_sha256_manifest',''),
                   ('installer_sha256_manifest','z'*64),
                   ('installer_url','http://bad.example/a.exe'),
                   ('publisher_url','http://bad.example/'),
                   ('homepage','http://bad.example/'),
                   ('version','1.1.1 --force'),
                   ('package_id','FreeCAD..Other'),
                   ('output_sha256','abc'),
                   ('installer_type','evil')]
        for key,value in overrides:
            raw=inspection();raw[key]=value
            if key=='homepage':raw['publisher_url']=''
            with self.subTest(key=key),self.assertRaises(ValueError):plan(raw)
        raw=inspection();raw['publisher_url']='';raw['homepage']=''
        with self.assertRaises(ValueError):plan(raw)
        raw=inspection();raw['observed_at']='not a date'
        with self.assertRaises(ValueError):plan(raw)

    def test_stale_and_future_receipts_not_accepted(self):
        now=datetime(2026,11,23,6,0,tzinfo=timezone.utc)
        raw=inspection()
        raw['observed_at']=(now-timedelta(hours=2,seconds=1)).isoformat()
        with self.assertRaises(ValueError):plan(raw,now=now)
        raw['observed_at']=(now+timedelta(seconds=1)).isoformat()
        with self.assertRaises(ValueError):plan(raw,now=now)
        raw['observed_at']=(now-timedelta(minutes=15)).isoformat()
        self.assertEqual(plan(raw,now=now)['version'],'1.1.1')

    def test_typed_exact_consent_and_no_reusable_authorization(self):
        p=plan()
        phrase=exact_consent_phrase(p)
        self.assertEqual(phrase,'INSTALL '+ID)
        for bad in (None,'',phrase.lower(),phrase+'\n','INSTALL FreeCAD.Other'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                approval_receipt(p,consent=bad,status='launch_requested')
        row=approval_receipt(p,consent=phrase,status='launch_requested')
        self.assertFalse(row['reusable_approval'])
        self.assertFalse(row['publisher_verified_independently'])
        self.assertFalse(row['installation_verified_independently'])
        self.assertEqual(row['package_id'],ID)
        self.assertEqual(row['argv'],p['argv'])
        with self.assertRaises(ValueError):
            approval_receipt(p,consent=phrase,status='verified_success')

    def test_changed_review_plan_cannot_reuse_consent(self):
        original=plan()
        for key,value in [('package_id','Someone.Else'),('version','99.0'),
                          ('argv',['C:/Windows/winget.exe','install','--force']),
                          ('publisher_url','https://changed.example/')]:
            row=copy.deepcopy(original);row[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                approval_receipt(row,consent='INSTALL '+ID,status='launch_requested')

    def test_output_sha_variant_read_only(self):
        changed=REPORT.replace('Installer SHA256:','SHA256:')
        row=inspect_show_output(ID,changed)
        self.assertEqual(row['installer_sha256_manifest'],'a'*64)


class DesktopInstallReviewTests(unittest.TestCase):
    def make_mock(self):
        obj=MagicMock()
        obj.last_package_inspection=inspection()
        obj._pending_package_inspection=None
        obj._pending_reviewed_install=None
        obj.disk_gate.gaming.return_value=False
        obj._windows_reviewed_install_enabled.return_value=True
        obj.install_process=None;obj.tool_process=None
        obj._start_command.return_value=True
        return obj

    def patch_valid(self):
        # no actual WinGet subprocess, Windows installation or disk mutation
        return patch('desktop_app.prepare_reviewed_install',return_value=plan())

    def test_no_install_without_two_approvals(self):
        from desktop_app import DeepThorTDesktop
        for yes,phrase in [(False,None),(True,None),(True,'INSTALL Someone.Other')]:
            obj=self.make_mock()
            with self.subTest(yes=yes,phrase=phrase),\
                 self.patch_valid(),\
                 patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=2*1024**3)),\
                 patch('desktop_app.messagebox.askyesno',return_value=yes),\
                 patch('desktop_app.simpledialog.askstring',return_value=phrase):
                DeepThorTDesktop._approve_inspected_install(obj)
            obj._start_command.assert_not_called()

    def test_safety_states_stop_review(self):
        from desktop_app import DeepThorTDesktop
        for state in ('game','inspection','install','no-report','low-disk'):
            obj=self.make_mock()
            if state=='game':obj.disk_gate.gaming.return_value=True
            elif state=='inspection':obj._pending_package_inspection={'package_id':ID}
            elif state=='install':obj._pending_reviewed_install={'package_id':ID}
            elif state=='no-report':obj.last_package_inspection=None
            with self.subTest(state=state),\
                 self.patch_valid(),patch('desktop_app.shutil.disk_usage',
                    return_value=MagicMock(free=0 if state=='low-disk' else 2*1024**3)),\
                 patch('desktop_app.messagebox.askyesno') as yes:
                DeepThorTDesktop._approve_inspected_install(obj)
                yes.assert_not_called()
            obj._start_command.assert_not_called()

    def test_approved_install_needs_persistent_audit_and_exact_argv(self):
        from desktop_app import DeepThorTDesktop
        obj=self.make_mock()
        cmd=plan()['argv']
        with tempfile.TemporaryDirectory() as folder,\
             self.patch_valid(),\
             patch('desktop_app.STATE',Path(folder)),\
             patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=2*1024**3)),\
             patch('desktop_app.messagebox.askyesno',return_value=True),\
             patch('desktop_app.simpledialog.askstring',return_value='INSTALL '+ID):
            # Persist using actual save_snapshot, verifying no run until written.
            def check_saved(*args,**kwargs):
                saved=json.loads((Path(folder)/'last-reviewed-install.json').read_text())
                self.assertEqual(saved['status'],'launch_requested')
                self.assertEqual(saved['argv'],cmd)
                return True
            obj._start_command.side_effect=check_saved
            DeepThorTDesktop._approve_inspected_install(obj)
            obj._start_command.assert_called_once()
            args,kwargs=obj._start_command.call_args
            self.assertEqual(args[0],cmd)
            self.assertEqual(kwargs['kind'],'reviewed_install')
            self.assertFalse(json.loads((Path(folder)/'last-reviewed-install.json').read_text())['reusable_approval'])
            self.assertIsNotNone(obj._pending_reviewed_install)

    def test_persistence_failure_blocks_install(self):
        from desktop_app import DeepThorTDesktop
        obj=self.make_mock()
        with self.patch_valid(),\
             patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=2*1024**3)),\
             patch('desktop_app.messagebox.askyesno',return_value=True),\
             patch('desktop_app.simpledialog.askstring',return_value='INSTALL '+ID),\
             patch('desktop_app.save_snapshot',return_value=False):
            DeepThorTDesktop._approve_inspected_install(obj)
        obj._start_command.assert_not_called()

    def test_completed_zero_retains_unverified_status_and_consumes_consent(self):
        from desktop_app import DeepThorTDesktop
        obj=self.make_mock()
        p=plan()
        obj._pending_reviewed_install={'plan':p,'consent':'INSTALL '+ID,'argv':p['argv']}
        with tempfile.TemporaryDirectory() as folder,patch('desktop_app.STATE',Path(folder)),\
             patch('desktop_app.messagebox.showinfo'):
            DeepThorTDesktop._complete_inspected_install(obj,0)
            saved=json.loads((Path(folder)/'last-reviewed-install.json').read_text())
            self.assertEqual(saved['status'],'completed_unverified')
            self.assertFalse(saved['installation_verified_independently'])
        self.assertIsNone(obj._pending_reviewed_install)
        obj._refresh_inventory.assert_called_once()


if __name__=='__main__':unittest.main()
