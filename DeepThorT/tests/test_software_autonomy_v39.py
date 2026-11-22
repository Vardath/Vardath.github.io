"""Standing routine software permissions: bounded WinGet actions and no UAC bypass.

No real Windows installs, model calls or internet queries are executed by tests.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from deepthort_local.computer_inventory import INSTALL_CATALOG
from deepthort_local.software_autonomy import (
    default_policy, load_policy, set_policy, automatic_command, make_plan,
    verify_plan, audit_record, already_attempted, project_tool_plans,
    MAX_ACTIONS_PER_REQUEST)
from deepthort_local.reviewed_install import prepare_reviewed_install, approval_receipt
from deepthort_local.online_tool_search import inspect_show_output

EXEC='C:/Windows/System32/winget.exe'
WHICH=lambda name:EXEC if name=='winget.exe' else None
PKG='FreeCAD.FreeCAD'
SHOW=('Found FreeCAD [FreeCAD.FreeCAD]\nVersion: 1.1.1\nPublisher: FreeCAD\n'
      'Publisher Url: https://www.freecad.org/\nInstaller Type: exe\n'
      'Installer Url: https://github.com/FreeCAD/FreeCAD/releases/download/v1.1.1/FreeCAD.exe\n'
      'Installer SHA256: '+'a'*64+'\n')


class PolicyAndCommandTests(unittest.TestCase):
    def test_release_default_enabled_for_routine_tools_and_upgrades(self):
        p=default_policy()
        self.assertTrue(p['enabled']);self.assertTrue(p['allow_upgrades'])
        self.assertTrue(p['catalog_only']);self.assertEqual(p['source'],'winget')
    def test_one_preference_persists_and_can_be_revoked(self):
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/'policy.json'
            self.assertTrue(load_policy(file)['enabled'])
            set_policy(file,enabled=False,allow_upgrades=False)
            self.assertFalse(load_policy(file)['enabled'])
            set_policy(file,enabled=True)
            self.assertTrue(load_policy(file)['enabled'])
            file.write_text('{broken','utf-8')
            self.assertFalse(load_policy(file)['enabled'])
            with self.assertRaises(ValueError):set_policy(file,enabled='yes')
    def test_strict_catalog_and_two_operations_only(self):
        for name in ('NotInCatalog','Godot && del C:',None):
            with self.subTest(name=name),self.assertRaises(ValueError):
                automatic_command(name,'install',which=WHICH)
        for action in ('run','uninstall','install;reboot','upgrade --all'):
            with self.subTest(action=action),self.assertRaises(ValueError):
                automatic_command('Godot',action,which=WHICH)
    def test_no_privilege_suppression_or_signature_bypass(self):
        for op in ('install','upgrade'):
            with self.subTest(op=op):
                cmd=automatic_command('FreeCAD',op,which=WHICH)
                self.assertEqual(cmd[1:6],[op,'--id',PKG,'--exact','--source'])
                self.assertEqual(cmd[6],'winget')
                self.assertTrue({'--accept-package-agreements','--accept-source-agreements'}<=set(cmd))
                for bad in ('--all','--force','--override','--ignore-security-hash',
                            '--silent','--scope','--no-upgrade','--allow-reboot'):
                    self.assertNotIn(bad,cmd)
    def test_plan_hash_and_exact_argv_cannot_be_changed(self):
        plan=make_plan('FreeCAD','install','C:/Project',which=WHICH)
        verify_plan(plan,which=WHICH)
        self.assertEqual(audit_record(plan,'launch_requested')['status'],'launch_requested')
        for field,new in [('name','Git'),('package_id','Wrong.Wrong'),
                          ('operation','upgrade'),('argv',['powershell.exe','-Command','x'])]:
            with self.subTest(field=field):
                broken=plan.copy();broken[field]=new
                with self.assertRaises(ValueError):verify_plan(broken,which=WHICH)
        with self.assertRaises(ValueError):audit_record(plan,'verified_success')
    def test_first_request_is_bounded_and_upgrade_eligible(self):
        inventory={'tools':[{'name':'Godot','found':True},{'name':'Git','found':True}]}
        plans=project_tool_plans('Create 2d game from scratch',inventory,'C:/P',default_policy(),which=WHICH)
        self.assertEqual([(x['name'],x['operation']) for x in plans], [('Godot','upgrade'),('Git','upgrade')])
        p={**default_policy(),'allow_upgrades':False}
        self.assertEqual(project_tool_plans('Create 2d game',inventory,'C:/P',p,which=WHICH),[])
        many=project_tool_plans('Make a 3d animation cinematic video and novel with music and CAD',
                                 {'tools':[]},'C:/P',default_policy(),which=WHICH)
        self.assertLessEqual(len(many),MAX_ACTIONS_PER_REQUEST)
    def test_cooldown_and_unknown_requirements(self):
        inv={'tools':[]};now=datetime.now(timezone.utc)
        p=make_plan('FreeCAD','install','C:/P',which=WHICH)
        receipt=audit_record(p,'completed_unverified')
        self.assertTrue(already_attempted(receipt,PKG,'install',now=now))
        self.assertFalse(already_attempted(receipt,PKG,'install',now=now+timedelta(days=2)))
        history={PKG+':install':receipt}
        self.assertEqual(project_tool_plans('Design CAD part',inv,'C:/P',default_policy(),history,
                                            which=WHICH,now=now),
                         [x for x in project_tool_plans('Design CAD part',inv,'C:/P',default_policy(),
                                            which=WHICH,now=now) if x['name']!='FreeCAD'])
        self.assertEqual(project_tool_plans('Find all tools on random-web-site and install them',
                             inv,'C:/P',default_policy(),which=WHICH),[])


class DesktopIntegrationTests(unittest.TestCase):
    def mockapp(self):
        obj=MagicMock()
        obj._autonomy_policy=default_policy()
        obj._auto_tool_history={};obj._auto_tool_queue=[];obj._auto_tool_active=None
        obj._auto_tool_waiting=[];obj.project=Path('/tmp/example-project')
        obj.inventory={'tools':[]};obj.queue_paused=False
        obj._quitting=False;obj.install_process=None;obj.tool_process=None
        obj.disk_gate.gaming.return_value=False
        obj._start_command.return_value=True
        from desktop_app import DeepThorTDesktop
        obj._record_automatic_software.side_effect=(lambda *args, **kw:
            DeepThorTDesktop._record_automatic_software(obj,*args,**kw))
        return obj

    def test_project_request_enqueues_known_tools_not_arbitrary_commands(self):
        from desktop_app import DeepThorTDesktop
        obj=self.mockapp()
        with patch('desktop_app.shutil.which',side_effect=WHICH):
            DeepThorTDesktop._autonomy_queue_request(obj,'Create 2D game from scratch',str(obj.project))
        self.assertEqual([r['name'] for r in obj._auto_tool_queue],['Godot','Git'])
        obj._auto_tool_queue.clear()
        with patch('desktop_app.shutil.which',side_effect=WHICH):
            DeepThorTDesktop._autonomy_queue_request(obj,'Install my new remote admin tool from this URL',str(obj.project))
        self.assertFalse(obj._auto_tool_queue)

    def test_automatic_action_creates_audit_before_start(self):
        from desktop_app import DeepThorTDesktop
        obj=self.mockapp()
        plan=make_plan('FreeCAD','install',str(obj.project),which=WHICH)
        obj._auto_tool_queue=[plan]
        with tempfile.TemporaryDirectory() as temp, \
             patch('desktop_app.STATE',Path(temp)), \
             patch('desktop_app.shutil.which',side_effect=WHICH), \
             patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=4*1024**3)), \
             patch('desktop_app.os',type('FakeOS',(),{'name':'nt'})()):
            def verify_before_launch(cmd,**kw):
                receipt=json.loads((Path(temp)/'last-routine-software.json').read_text())
                self.assertEqual(receipt['status'],'launch_requested')
                self.assertEqual(receipt['argv'],cmd)
                self.assertEqual(kw['kind'],'automatic_software')
                return True
            obj._start_command.side_effect=verify_before_launch
            DeepThorTDesktop._automatic_tool_tick(obj)
            obj._start_command.assert_called_once()
            self.assertEqual(obj._auto_tool_active['package_id'],PKG)
            self.assertEqual(obj._auto_tool_queue,[])
            obj._refresh_inventory=MagicMock()
            DeepThorTDesktop._automatic_tool_finished(obj,0)
            saved=json.loads((Path(temp)/'last-routine-software.json').read_text())
            self.assertEqual(saved['status'],'completed_unverified')
            self.assertFalse(saved['independent_install_verified'])
            obj._refresh_inventory.assert_called_once()

    def test_automatic_operation_defers_for_game_pause_or_low_disk(self):
        from desktop_app import DeepThorTDesktop
        plan=make_plan('FreeCAD','upgrade','/tmp/example-project',which=WHICH)
        for kind in ('game','pause','low-disk','already-running'):
            obj=self.mockapp();obj._auto_tool_queue=[plan]
            if kind=='game':obj.disk_gate.gaming.return_value=True
            if kind=='pause':obj.queue_paused=True
            if kind=='already-running':obj.tool_process=MagicMock();obj.tool_process.poll.return_value=None
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as temp, \
                 patch('desktop_app.STATE',Path(temp)), \
                 patch('desktop_app.shutil.which',side_effect=WHICH), \
                 patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=0 if kind=='low-disk' else 4*1024**3)), \
                 patch('desktop_app.os',type('FakeOS',(),{'name':'nt'})()):
                DeepThorTDesktop._automatic_tool_tick(obj)
                obj._start_command.assert_not_called()
                self.assertEqual(len(obj._auto_tool_queue),1)

    def test_policy_revocation_clears_future_actions(self):
        from desktop_app import DeepThorTDesktop
        obj=self.mockapp()
        obj.autonomy_enabled=MagicMock();obj.autonomy_upgrades=MagicMock()
        obj.autonomy_enabled.get.return_value=False
        obj.autonomy_upgrades.get.return_value=False
        obj._auto_tool_queue=[make_plan('FreeCAD','install',str(obj.project),which=WHICH)]
        with tempfile.TemporaryDirectory() as temp,patch('desktop_app.STATE',Path(temp)),patch('desktop_app.record'):
            DeepThorTDesktop._set_tool_autonomy(obj)
            self.assertFalse(obj._autonomy_policy['enabled'])
            self.assertEqual(obj._auto_tool_queue,[])
            self.assertFalse(json.loads((Path(temp)/'routine-software-policy.json').read_text())['enabled'])

    def test_online_search_and_manual_catalog_install_skip_redundant_prompts(self):
        from desktop_app import DeepThorTDesktop
        obj=self.mockapp()
        obj.install_choice.get.return_value='Godot'
        obj.tabs=MagicMock()
        with patch('desktop_app.winget_command',return_value=[EXEC,'install','--id','GodotEngine.GodotEngine']),\
             patch('desktop_app.messagebox.askyesno') as ask:
            DeepThorTDesktop._approve_tool_install(obj)
            ask.assert_not_called()
            obj._start_command.assert_called_once()
        obj._start_command.reset_mock()
        with patch('desktop_app.simpledialog.askstring',return_value='FreeCAD'),\
             patch('desktop_app.winget_search_command',return_value=[EXEC,'search','--query','FreeCAD']),\
             patch('desktop_app.messagebox.askyesno') as ask:
            DeepThorTDesktop._search_online_tools(obj)
            ask.assert_not_called()
            obj._start_command.assert_called_once()

    def test_inspected_package_one_click_audit_does_not_claim_typed_consent(self):
        from desktop_app import DeepThorTDesktop
        row=inspect_show_output(PKG,SHOW)
        plan=prepare_reviewed_install(row,which=WHICH,standing_policy=True)
        self.assertNotIn('--scope',plan['argv']);self.assertNotIn('--no-upgrade',plan['argv'])
        self.assertNotIn('--silent',plan['argv'])
        with self.assertRaises(ValueError):approval_receipt(plan,consent='INSTALL '+PKG,status='launch_requested')
        receipt=approval_receipt(plan,consent=None,status='launch_requested',authorization='explicit_install_click')
        self.assertEqual(receipt['authorization_source'],'explicit_install_click')
        obj=self.mockapp();obj.last_package_inspection=row
        obj._pending_package_inspection=None;obj._pending_reviewed_install=None
        obj._windows_reviewed_install_enabled.return_value=True
        with tempfile.TemporaryDirectory() as temp,patch('desktop_app.STATE',Path(temp)),\
             patch('desktop_app.prepare_reviewed_install',return_value=plan),\
             patch('desktop_app.shutil.disk_usage',return_value=MagicMock(free=5*1024**3)),\
             patch('desktop_app.messagebox.askyesno') as ask,\
             patch('desktop_app.simpledialog.askstring') as typed:
            DeepThorTDesktop._approve_inspected_install(obj)
            ask.assert_not_called();typed.assert_not_called()
            obj._start_command.assert_called_once()
            saved=json.loads((Path(temp)/'last-reviewed-install.json').read_text())
            self.assertEqual(saved['authorization_source'],'explicit_install_click')
            self.assertEqual(obj._pending_reviewed_install['authorization'],'explicit_install_click')


if __name__=='__main__':unittest.main()
