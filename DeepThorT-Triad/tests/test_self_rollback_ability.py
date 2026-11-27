import json,unittest
from test_self_installation_ability import InstallTests
from deepthort_local import self_installation as install,self_rollback as m
from deepthort_local.self_development import TARGET

class RollbackTests(InstallTests):
    def installed(self):
        body=self.ready()
        plan,_=install.review(self.root,self.state)
        install.install(self.root,self.state,plan,approval=True,idle=lambda:True)
        return self.state/'self-development'/body['key']
    def test_rollback_restores_only_reviewed_source(self):
        folder=self.installed()
        plan=m.review(self.root,self.state)
        marker=self.state/'user-project.txt';marker.write_bytes(b'keep')
        with self.assertRaises(PermissionError):
            m.restore(self.root,self.state,plan,idle=lambda:True)
        result=m.restore(self.root,self.state,plan,approval=True,idle=lambda:True)
        self.assertEqual((self.root/TARGET).read_bytes(),self.baseline)
        self.assertEqual(marker.read_bytes(),b'keep')
        self.assertEqual(result['state'],'restored')
        self.assertFalse(result['full_application_restored'])
        self.assertEqual(json.loads((folder/'rollback-receipt.json').read_text()),result)
        with self.assertRaises(ValueError):m.review(self.root,self.state)
    def test_rollback_rejects_changed_live_source_and_backup(self):
        folder=self.installed();plan=m.review(self.root,self.state)
        target=self.root/TARGET;candidate=target.read_bytes()
        target.write_bytes(candidate+b'\n# manual edit')
        with self.assertRaises(ValueError):
            m.restore(self.root,self.state,plan,approval=True,idle=lambda:True)
        target.write_bytes(candidate)
        (folder/'installed-baseline.py.txt').write_bytes(b'bad')
        with self.assertRaises(ValueError):
            m.restore(self.root,self.state,plan,approval=True,idle=lambda:True)
        self.assertEqual(target.read_bytes(),candidate)
    def test_rollback_expiry_and_late_busy(self):
        folder=self.installed();plan=m.review(self.root,self.state)
        candidate=(self.root/TARGET).read_bytes()
        with self.assertRaises(ValueError):
            m.restore(self.root,self.state,dict(plan,expires_at=0),approval=True,idle=lambda:True)
        calls=[]
        def idle():
            calls.append(1);return len(calls)==1
        with self.assertRaises(ValueError):
            m.restore(self.root,self.state,plan,approval=True,idle=idle)
        self.assertEqual((self.root/TARGET).read_bytes(),candidate)
        self.assertEqual(json.loads((folder/'rollback-receipt.json').read_text())['state'],'prepared')
if __name__=='__main__':unittest.main()
