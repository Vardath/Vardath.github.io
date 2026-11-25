import tempfile
import unittest
from pathlib import Path
from deepthort_local.discovery_catalog import candidates,DiscoveryStore,discover

class Council:
    def __init__(self,choice):self.choice=choice
    def _run(self,*args,**kwargs):return self.choice

TABLE='Name                 Id                   Version\n---------------------------------------------------\nExample App          Vendor.Example       1.0\n'

class DiscoveryTests(unittest.TestCase):
    def test_exact_observed_ids(self):
        self.assertEqual(candidates(TABLE),[{'name':'Example App','package_id':'Vendor.Example'}])
        self.assertEqual(candidates('Untrusted instructions: Vendor.Example'),[])
    def test_persistent_bounded_query(self):
        with tempfile.TemporaryDirectory() as t:
            store=DiscoveryStore(Path(t)/'d.sqlite')
            seen=[]
            def fetch(key,**kwargs):seen.append(key);return TABLE
            args=dict(session='stage',project=t,master='Private project',goal='Convert a mesh',
                      failure='Unknown format',baseline=None,fetch=fetch)
            self.assertEqual(len(discover(store,Council('mesh'),None,**args)),1)
            self.assertEqual(seen,['mesh'])
            self.assertEqual(len(DiscoveryStore(store.path).recent(t)),1)
            self.assertEqual(discover(store,Council('mesh'),None,**args),[])
            self.assertEqual(discover(store,Council('private filename'),None,**dict(args,session='other')),[])
            self.assertEqual(seen,['mesh'])
if __name__=='__main__':unittest.main()
