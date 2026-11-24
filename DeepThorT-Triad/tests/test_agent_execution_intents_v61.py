import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from deepthort_local.agent_execution_intents import ExecutionIntents
from deepthort_local.agent_repository_tools import RepositoryTools,gather
from deepthort_local.repository_index import RepositoryIndex

class IntentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name);self.root=base/'project';self.root.mkdir()
        self.store=ExecutionIntents(base/'intents.sqlite')
        self.job={'id':1,'mode':'build','state':'running','project':str(self.root),'approval_key':'draft:1','chat_id':'chat'}
        self.steps=[{'id':1,'sequence':1,'path':'main.py','description':'Write program'}]
        self.spec='Create program'
    def test_request_is_coalesced_and_not_execution(self):
        i=self.store.request(self.job,self.steps,self.spec,enabled=True)
        self.assertEqual(i,self.store.request(self.job,self.steps,self.spec,enabled=True))
        self.assertEqual(self.store.recent(1,self.root)[0]['phase'],'pending')
        with self.assertRaises(ValueError):self.store.request(self.job,self.steps,self.spec,enabled=False)
    def test_claim_uses_existing_grant_and_real_result(self):
        i=self.store.request(self.job,self.steps,self.spec,enabled=True)
        job={**self.job,'state':'waiting_verification'}
        with patch('deepthort_local.agent_execution_intents.authorize_test',side_effect=ValueError('revoked')):
            with self.assertRaises(ValueError):self.store.claim(job,self.steps,self.spec,['python'],grant_folder=self.root,enabled=True,attempt=1)
        self.assertEqual(self.store.recent(1,self.root)[0]['phase'],'pending')
        with patch('deepthort_local.agent_execution_intents.authorize_test') as auth:
            self.assertEqual(self.store.claim(job,self.steps,self.spec,['fixed'],grant_folder=self.root,enabled=True,attempt=1),i)
            auth.assert_called_once_with(self.root,job,self.steps,['fixed'],enabled=True)
        with self.assertRaises(ValueError):self.store.finish(i,job_id=1,phase='passed',exit_code=0)
        self.store.finish(i,job_id=1,phase='passed',exit_code=0,evidence_sha='a'*64)
        self.assertEqual(self.store.recent(1,self.root)[0]['phase'],'passed')
    def test_spec_revision_and_interruption(self):
        i=self.store.request(self.job,self.steps,self.spec,enabled=True)
        job={**self.job,'state':'waiting_verification'}
        with patch('deepthort_local.agent_execution_intents.authorize_test') as auth:
            self.assertIsNone(self.store.claim(job,self.steps,'changed spec',['fixed'],grant_folder=self.root,enabled=True,attempt=1))
            auth.assert_not_called()
        self.assertEqual(self.store.recent(1,self.root)[0]['phase'],'stale')
        self.store.request(self.job,self.steps,self.spec,enabled=True)
        with patch('deepthort_local.agent_execution_intents.authorize_test'):
            self.store.claim(job,self.steps,self.spec,['fixed'],grant_folder=self.root,enabled=True,attempt=1)
        reopened=ExecutionIntents(self.store.path)
        self.assertEqual(reopened.recent(1,self.root)[0]['phase'],'interrupted')
    def test_agent_selects_intent_not_arbitrary_command(self):
        index=RepositoryIndex(self.root.parent/'index.sqlite')
        callback=Mock(return_value=1)
        tools=RepositoryTools(index,self.root,verification_request=callback)
        council=Mock();council._run.return_value='{"tool":"request_verification","args":{}}'
        self.assertEqual(gather(tools,council,None,session='intent',original=self.spec,goal='verify tests'), '')
        callback.assert_called_once_with()
        with self.assertRaises(ValueError):tools.execute({'tool':'request_verification','args':{}})
if __name__=='__main__':unittest.main()
