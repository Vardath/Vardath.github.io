import tempfile
import unittest
from pathlib import Path
from deepthort_local.mixed_roadmap import parse_tasks,MixedRoadmaps,pending_task,require_output
import json

class Workflows:
    def roadmap_members(self,request_id):return []

class MixedRoadmapTests(unittest.TestCase):
    def test_artifact_boundary_and_no_source_collision(self):
        with tempfile.TemporaryDirectory() as t:
            plan={'project':t,'schedule':[{'steps':[{'path':'main.py'}]}]}
            task={'after':1,'goal':'Render required texture','output':'texture.png'}
            self.assertEqual(parse_tasks(json.dumps({'artifacts':[task]}),plan,2),[dict(task,section=2)])
            for change in ({'after':2},{'output':'main.py'},{'output':'../bad.png'}):
                with self.assertRaises(ValueError):
                    parse_tasks(json.dumps({'artifacts':[dict(task,**change)]}),plan,2)
    def test_durable_obligation_and_gate(self):
        with tempfile.TemporaryDirectory() as t:
            s=MixedRoadmaps(Path(t)/'mixed.sqlite')
            task={'id':'task','after':1,'goal':'Render texture','output':'texture.png','sections':[2]}
            body={'request_id':4,'code_sha':'a'*64,'tasks':[task]}
            sha=s.save(body)
            plan=MixedRoadmaps(s.path).get(4,'a'*64)
            self.assertEqual(plan['sha'],sha)
            self.assertIsNone(pending_task(plan,Workflows(),1))
            self.assertEqual(pending_task(plan,Workflows(),2),task)
            s.bind_request('task',7)
            self.assertEqual(MixedRoadmaps(s.path).request_for('task'),7)
            with self.assertRaises(ValueError):s.save(dict(body,tasks=[]))
            with self.assertRaises(ValueError):require_output(task,{'stages':[{'output':'wrong.png'}]})
            self.assertTrue(require_output(task,{'stages':[{'output':'texture.png'}]}))
if __name__=='__main__':unittest.main()
