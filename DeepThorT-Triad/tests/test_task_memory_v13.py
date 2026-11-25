import tempfile
import unittest
from pathlib import Path
from deepthort_local.job_queue import JobStore
from deepthort_local.task_memory import sha
from deepthort_local.task_memory_probe import exercise

class TaskMemoryTests(unittest.TestCase):
    def test_acceptance_probe(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_step_events_restart_dedup_and_scope(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            s=JobStore(root/'jobs.sqlite3')
            project=str(root/'game');spec='Create sectors and docks'
            job=s.submit(project,'chat','plan',spec)
            s.add_plan(job,[{'path':'map.py','description':'Sectors'}])
            s.set_step(s.steps(job)[0]['id'],'saved','Source saved, not tested')
            self.assertTrue(s.remember(job,'janus','sectors',sha(spec),sha('evidence'),'Historical advice'))
            self.assertFalse(s.remember(job,'janus','sectors',sha(spec),sha('evidence'),'Duplicate'))
            path=s.journal(job)
            self.assertIn('map.py: saved',path.read_text('utf-8'))
            self.assertEqual(path.read_text('utf-8').count('Historical advice'),1)
            s.change(job,'running','Active')
            restored=JobStore(root/'jobs.sqlite3')
            self.assertEqual(restored.get(job)['state'],'paused')
            self.assertIn('Interrupted by previous shutdown',restored.journal(job).read_text('utf-8'))
            other=restored.submit(project,'other-chat','plan',spec)
            self.assertNotIn('Historical advice',restored.memory_context(restored.get(other),spec,'sectors',800))
            same=restored.submit(project,'chat','plan',spec)
            self.assertIn('Historical advice',restored.memory_context(restored.get(same),spec,'sectors',800))
            self.assertEqual(restored.memory_context(restored.get(same),spec,'sectors',100),'')
            self.assertLessEqual(len(restored.memory_context(restored.get(job),spec,'sectors',400)),400)
