import tempfile
import unittest
from pathlib import Path
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.task_memory_probe import exercise
from deepthort_local.task_memory import sha,tool_observations
from deepthort_local.agent_tool_receipts import ToolReceipts

class ExtendedMemoryTests(unittest.TestCase):
    def test_full_probe(self):
        result=exercise()
        self.assertEqual(result['status'],'passed',result)
    def test_planning_interruption_and_amendment(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);project=str(root/'space')
            store=ConversationStore(root/'conversations.sqlite3')
            rid=store.submit('chat',project,'draft_plan','Build a sector map')
            store.change(rid,'running','Inspect dependencies')
            store=ConversationStore(root/'conversations.sqlite3')
            journal=store.journal(rid)
            self.assertIn('Recovered after app restart',journal.read_text('utf-8'))
            revised=store.amend_project('chat',project,'Add asteroid fields')
            self.assertIn('Add asteroid fields',store.journal(revised).read_text('utf-8'))
            self.assertIn('Superseded by explicit user amendment',store.journal(rid).read_text('utf-8'))
    def test_tool_observation_spec_and_project_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);project=str(root/'space')
            ledger=ToolReceipts(root/'agent-tool-receipts-v61.sqlite3')
            ledger.record(job_id=1,project=project,spec_sha=sha('spec'),session='test',turn=0,
                request={'tool':'symbol_search'},result={'items':['private source']})
            rows=tool_observations(root/'jobs.sqlite3',1,project,sha('spec'))
            self.assertEqual(len(rows),1)
            self.assertNotIn('private source',str(rows))
            self.assertEqual(tool_observations(root/'jobs.sqlite3',1,project,sha('changed')),[])
            self.assertEqual(tool_observations(root/'jobs.sqlite3',1,str(root/'other'),sha('spec')),[])
