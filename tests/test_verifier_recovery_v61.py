import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from deepthort_local.verifier_recovery import missing_verifier,recovery_action,install_plan
from deepthort_local.software_autonomy import default_policy,audit_record,make_plan

class VerifierRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime.now(timezone.utc)
        self.policy=default_policy()
        self.receipt={'tool':'Godot','status':'not_found','observed_at':self.now.isoformat()}
        self.which=lambda name:'winget.exe' if name=='winget.exe' else None
    def test_missing_fixed_executable(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'project.godot').touch()
            self.assertEqual(missing_verifier(p,None,which=self.which),'Godot')
            self.assertEqual(missing_verifier(p,['npm.cmd','test'],which=self.which),'Node.js')
    def test_independent_probe_precedes_install(self):
        self.assertEqual(recovery_action('Godot',self.policy,{},None,now=self.now)[0],'probe')
        self.assertEqual(recovery_action('Godot',self.policy,{},self.receipt,now=self.now)[0],'install')
        plan=install_plan('Godot','project',self.policy,{},self.receipt,which=self.which,now=self.now)
        self.assertEqual(plan['package_id'],'GodotEngine.GodotEngine')
        self.assertEqual(plan['operation'],'install')
    def test_no_repeat_or_unlisted_install(self):
        plan=make_plan('Godot','install','project',which=self.which)
        audit=audit_record(plan,'failed',exit_code=1)
        audit['observed_at']=(self.now-timedelta(seconds=10)).isoformat()
        history={plan['package_id']+':install':audit}
        self.assertEqual(recovery_action('Godot',self.policy,history,self.receipt,now=self.now)[0],'blocked')
        self.assertEqual(recovery_action('.NET SDK',self.policy,{},None,now=self.now)[0],'blocked')
        self.assertEqual(recovery_action('Godot',dict(self.policy,enabled=False),{},None,now=self.now)[0],'blocked')
    def test_newer_install_requires_fresh_probe(self):
        plan=make_plan('Godot','install','project',which=self.which)
        audit=audit_record(plan,'completed_unverified',exit_code=0)
        audit['observed_at']=self.now.isoformat()
        receipt=dict(self.receipt,observed_at=(self.now-timedelta(seconds=1)).isoformat())
        self.assertEqual(recovery_action('Godot',self.policy,{plan['package_id']+':install':audit},receipt,now=self.now)[0],'probe')

if __name__=='__main__':unittest.main()
