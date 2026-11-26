"""Real graph candidates, model-owned preference, exact peer routing."""
import json
import unittest
from unittest.mock import patch
from deepthort_local.worker_selection import choose
from deepthort_local.worker_notices import validate_notice,envelope,split_notice,PREFIX
from deepthort_local.peer_context import _collect,packet,checked,catalog_text
import test_dependency_ready_v60 as graph_fixture

class WorkerChoiceTests(unittest.TestCase):
    def setUp(self):
        self.f=graph_fixture.ReadyTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.start()
    def test_model_can_choose_other_ready_node_not_blocked_node(self):
        f=self.f;options=f.graph.ready_candidates(f.job,f.steps)
        self.assertEqual([s['path'] for s in options],['engine.py','docs.md'])
        class Client:
            def chat_as(self,role,session,prompt,max_tokens):
                self.role=role;self.prompt=prompt;return json.dumps({'step_id':1,'reason':'Independent guide is useful now'})
        c=Client()
        result=choose(c,f.job,f.job['prompt'],[],options,stopped=lambda:False)
        self.assertEqual(c.role,'implementation')
        self.assertEqual(result['step_id'],1)
        self.assertEqual(f.graph.ready_step(f.job,f.steps,preferred=1)['path'],'docs.md')
        self.assertNotIn('ui.py',c.prompt)
        with patch.object(c,'chat_as',return_value='{"step_id":3,"reason":"not ready"}'):
            self.assertEqual(choose(c,f.job,f.job['prompt'],[],options,stopped=lambda:False)['step_id'],2)
        with patch.object(c,'chat_as',side_effect=AssertionError('Singleton must not infer')):
            self.assertEqual(choose(c,f.job,f.job['prompt'],[],options[:1],stopped=lambda:False)['step_id'],2)
        self.assertIsNone(choose(c,f.job,f.job['prompt'],[],options,stopped=lambda:True))
    def test_exact_peer_target_and_original_scope(self):
        notice={'kind':'integration_hint','need':'Use an exact tempo','reason':'Interface requires it','peer_path':'audio/theme.mid'}
        c={'job_id':1,'step_id':2,'original_sha256':'a'*64}
        item=envelope('attempt',7,c,notice,'b'*64,'implementation',1)
        item['receipt_sha']='c'*64
        self.assertIn('multimedia',item['recipients'])
        self.assertEqual(split_notice(PREFIX+json.dumps(notice)+'\nsource'),(notice,'source'))
        with patch('deepthort_local.peer_context.observe_notices',return_value=[item]):
            self.assertIn('exact tempo',_collect('jobs',7,'a'*64,'audio/theme.mid','multimedia',650))
            self.assertEqual(_collect('jobs',8,'a'*64,'audio/theme.mid','multimedia',650),'')
            self.assertEqual(_collect('jobs',7,'x'*64,'audio/theme.mid','multimedia',650),'')
            self.assertEqual(_collect('jobs',7,'a'*64,'other.mid','multimedia',650),'')
            self.assertEqual(_collect('jobs',7,'a'*64,'audio/theme.mid','implementation',650),'')
        for path in ('../audio.mid','C:/audio.mid','/audio.mid','a//b'):
            with self.assertRaises(ValueError):validate_notice(dict(notice,peer_path=path))
        catalog=catalog_text(['engine.py','engine.py','x'*240,'ui.py'],180)
        self.assertIn('"engine.py"',catalog)
        self.assertIn('"ui.py"',catalog)
        self.assertEqual(catalog.count('"engine.py"'),1)
        self.assertNotIn('xxxxx',catalog)
        self.assertEqual(catalog_text(['engine.py'],10),'')
        p=packet('scope','advice')
        self.assertEqual(checked(p,'scope'),'advice')
        with self.assertRaises(ValueError):checked(dict(p,advice='modified'),'scope')
        with self.assertRaises(ValueError):checked(p,'other')
if __name__=='__main__':unittest.main()
