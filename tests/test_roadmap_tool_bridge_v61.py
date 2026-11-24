import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.janus_engine import JanusStore
from deepthort_local.tool_workflows import ToolWorkflows,freeze
from deepthort_local.roadmap_tool_bridge import gate
from tests.test_tool_workflows_v61 import Recipes

class RoadmapToolTests(unittest.TestCase):
    def test_required_boundary_waits_and_checks_exact_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);j=JanusStore(p/'janus.sqlite');w=ToolWorkflows(j)
            m=freeze(Recipes(p),p,[{'recipe_id':1,'input':''},{'recipe_id':2,'input':'out1.json'}])
            m['roadmap']={'request_id':9,'manifest_sha256':'a'*64,'after':1,'project':str(p)}
            ident=w.approve(m,user_approved=True)
            self.assertIsNone(gate(w,9,'a'*64,1))
            self.assertIn('waiting',gate(w,9,'a'*64,2))
            self.assertIsNone(w.tick(roadmap_ready=lambda link:False))
            self.assertEqual(j.actions(),[])
            for n in (1,2):
                self.assertIn('queued',w.tick(roadmap_ready=lambda link:True))
                action=j.claim_next_action()
                (p/f'out{n}.json').write_text('{"ok":true}')
                log=p/f'{n}.log';log.write_text('ok')
                j.update_action(action['id'],'succeeded',detail='ok',returncode=0,output_file=str(log))
                self.assertIn('checked',w.tick(roadmap_ready=lambda link:True))
            self.assertIn('checked',w.tick(roadmap_ready=lambda link:True))
            self.assertIsNone(gate(w,9,'a'*64,2))
            self.assertEqual(w.get(ident)['state'],'complete')
            (p/'out2.json').write_text('{"ok":false}')
            with self.assertRaises(ValueError):gate(w,9,'a'*64,2)

if __name__=='__main__':unittest.main()
