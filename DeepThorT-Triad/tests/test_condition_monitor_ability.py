import hashlib
import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.condition_monitor import checked,observe,ConditionWatches

class ConditionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name).resolve();self.root=self.base/'project';self.root.mkdir()
        self.c=ConversationStore(self.base/'c.db');self.w=ConditionWatches(self.c)
        self.p=self.root/'result.txt';self.project=str(self.root)
    def test_real_file_predicates(self):
        self.assertTrue(observe(self.root,{'path':'result.txt','kind':'missing'})['matched'])
        self.p.write_bytes(b'hello')
        self.assertTrue(observe(self.root,{'path':'result.txt','kind':'exists'})['matched'])
        self.assertFalse(observe(self.root,{'path':'result.txt','kind':'size_at_least','value':6})['matched'])
        h=hashlib.sha256(b'hello').hexdigest()
        self.assertTrue(observe(self.root,{'path':'result.txt','kind':'sha256_equals','value':h})['matched'])
        self.assertFalse(observe(self.root,{'path':'result.txt','kind':'sha256_equals','value':'0'*64})['matched'])
    def test_unsafe_paths_and_exclusion(self):
        for p in ('../result.txt','state/a.txt','a:stream','NUL.txt','.hidden','a\\b','a/../b'):
            with self.assertRaises(ValueError):checked({'path':p,'kind':'exists'})
        self.p.write_bytes(b'hello')
        with self.assertRaises(ValueError):observe(self.root,{'path':'result.txt','kind':'exists'},['result.txt'])
        self.p.unlink();self.p.mkdir()
        with self.assertRaises(ValueError):observe(self.root,{'path':'result.txt','kind':'exists'})
    def test_persisted_transitions_and_error_baseline(self):
        s={'path':'result.txt','kind':'exists'}
        n=self.w.create(self.project,'c',s,60,4,approved=True,now=100)
        snap=self.w.due(self.project,['c'],now=100)
        self.assertEqual(self.w.finish(snap,observe(self.root,s),now=100)['status'],'baseline_false')
        self.assertIsNone(self.w.finish(snap,observe(self.root,s),now=100))
        self.p.write_bytes(b'hello')
        self.w=ConditionWatches(ConversationStore(self.c.path))
        self.assertEqual(self.w.finish(self.w.due(self.project,['c'],now=160),None,now=160)['status'],'error')
        self.assertEqual(self.w.finish(self.w.due(self.project,['c'],now=220),observe(self.root,s),now=220)['status'],'became_true')
        self.p.unlink()
        self.assertEqual(self.w.finish(self.w.due(self.project,['c'],now=400),observe(self.root,s),now=400)['status'],'became_false')
        self.assertEqual(len(self.w.history(n,self.project,'c')),4);self.assertEqual(self.w.rows(self.project,'c')[0]['state'],'finished')
    def test_scope_consent_and_stale_receipts(self):
        s={'path':'result.txt','kind':'exists'}
        with self.assertRaises(ValueError):self.w.create(self.project,'c',s,60,2)
        n=self.w.create(self.project,'c',s,60,2,approved=True,now=100)
        self.assertIsNone(self.w.due(self.project,['other'],now=100))
        snap=self.w.due(self.project,['c'],now=100)
        with self.assertRaises(ValueError):self.w.finish(snap,{'matched':True,'exists':False,'bytes':None,'sha256':None},now=100)
        self.assertTrue(self.w.cancel(n,self.project,'c'));self.assertIsNone(self.w.finish(snap,None,now=100))
        self.assertEqual(self.c.thread('c'),[])
