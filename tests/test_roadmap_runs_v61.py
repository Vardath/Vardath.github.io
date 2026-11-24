import tempfile
import unittest
from pathlib import Path
from deepthort_local.roadmap_runs import RoadmapRuns

class RoadmapRunsTests(unittest.TestCase):
    def test_consent_reservation_and_restart(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'runs.sqlite3'
            store=RoadmapRuns(path)
            reviewed=dict(request_id=1,project=t,chat_id='chat',manifest_sha256='a'*64)
            key='milestone:1:1:0123456789abcdef'
            job={'id':7,'approval_key':key}
            self.assertFalse(store.reserve(1,1,key,'a'*64))
            store.approve(reviewed)
            self.assertFalse(store.reserve(1,1,key,'b'*64))
            self.assertTrue(store.reserve(1,1,key,'a'*64))
            self.assertFalse(store.dispatch_allowed(job))
            self.assertFalse(store.reserve(1,1,key,'a'*64))
            store=RoadmapRuns(path)
            self.assertFalse(store.dispatch_allowed(job))
            self.assertTrue(store.finish(key,7,True))
            self.assertTrue(store.dispatch_allowed(job))
            self.assertFalse(store.dispatch_allowed(dict(job,id=8)))
            self.assertTrue(store.change(1,'paused','user paused'))
            self.assertFalse(store.reserve(1,2,'milestone:1:2:0123456789abcdef','a'*64))

    def test_changed_manifest_cannot_replace_consent(self):
        with tempfile.TemporaryDirectory() as t:
            store=RoadmapRuns(Path(t)/'runs.sqlite3')
            reviewed=dict(request_id=1,project=t,chat_id='chat',manifest_sha256='a'*64)
            store.approve(reviewed)
            with self.assertRaises(ValueError):
                store.approve(dict(reviewed,manifest_sha256='b'*64))

if __name__=='__main__':unittest.main()
