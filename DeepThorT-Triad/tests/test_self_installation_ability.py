import json,sys,unittest
from pathlib import Path
from test_self_update_preparation_v71 import SelfUpdateTests
from deepthort_local.self_development import run_once,TARGET
from deepthort_local import self_installation as m

class InstallTests(SelfUpdateTests):
    def ready(self):
        self.stage()
        return run_once(self.root,self.state,self.client,lambda:False,update_python=sys.executable)
    def test_exact_owner_authorized_update(self):
        body=self.ready();plan,_=m.review(self.root,self.state)
        with self.assertRaises(PermissionError):m.install(self.root,self.state,plan,idle=lambda:True)
        with self.assertRaises(PermissionError):m.install(self.root,self.state,plan,approval=True)
        r=m.install(self.root,self.state,plan,approval=True,idle=lambda:True)
        self.assertEqual(r['state'],'installed');self.assertTrue(r['restart_required'])
        folder=self.state/'self-development'/body['key']
        self.assertEqual((folder/'installed-baseline.py.txt').read_bytes(),self.baseline)
        self.assertEqual(m.digest((self.root/TARGET).read_bytes()),plan['candidate_sha'])
        self.assertEqual(json.loads((folder/'install-receipt.json').read_text()),r)
    def test_tamper_and_expiry(self):
        body=self.ready();plan,_=m.review(self.root,self.state)
        with self.assertRaises(ValueError):m.install(self.root,self.state,dict(plan,expires_at=0),approval=True,idle=lambda:True)
        folder=self.state/'self-development'/body['key']
        (folder/body['update']['package']).write_bytes(b'tampered')
        with self.assertRaises((ValueError,__import__('zipfile').BadZipFile)):m.install(self.root,self.state,plan,approval=True,idle=lambda:True)
        self.assertEqual((self.root/TARGET).read_bytes(),self.baseline)
    def test_idle_rechecked_before_replace(self):
        body=self.ready();plan,_=m.review(self.root,self.state);calls=[]
        def idle():
            calls.append(1);return len(calls)==1
        with self.assertRaises(ValueError):m.install(self.root,self.state,plan,approval=True,idle=idle)
        self.assertEqual((self.root/TARGET).read_bytes(),self.baseline)
        self.assertEqual(json.loads((self.state/'self-development'/body['key']/'install-receipt.json').read_text())['state'],'prepared')
if __name__=='__main__':unittest.main()
