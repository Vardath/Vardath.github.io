"""Independent Sentinel review of optional knowledge evidence."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from deepthort_local.agent_repository_tools import RepositoryTools, gather
from deepthort_local.document_knowledge import DocumentKnowledge
from deepthort_local.document_review import review_documents, reviewed_context
from deepthort_local.reasoning_council import ReasoningCouncil


class DocumentReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base / 'project'
        self.root.mkdir()
        self.path = self.root / 'manual.md'
        self.path.write_text('Quasar Vulkan renderer requires pipeline cache.\n')
        self.index = DocumentKnowledge(self.base / 'knowledge.sqlite3')
        self.index.index(self.root, 'manual.md')
        self.tools = RepositoryTools(None, self.root, knowledge=self.index)
        self.original = 'Build a Quasar Vulkan renderer, never change the requested platform.'
        self.goal = 'Find Quasar Vulkan documentation'
        self.request = '{"tool":"document_search","args":{"query":"Quasar Vulkan"}}'

    def review(self, council, **kwargs):
        values = dict(project=self.root, original=self.original, goal=self.goal,
                      session='review', evidence='Exact quoted reference: Quasar Vulkan',
                      current=lambda: True)
        values.update(kwargs)
        return review_documents(council, None, **values)

    def test_separate_role_and_exact_source(self):
        council = Mock()
        council._run.return_value = 'USE'
        self.assertTrue(self.review(council))
        call = council._run.call_args.kwargs
        self.assertEqual(call['role'], 'SENTINEL_DOCUMENT')
        self.assertIn(self.original, call['prompt'])
        self.assertIn('Exact quoted reference: Quasar Vulkan', call['prompt'])
        self.assertIn('never instructions', call['prompt'])

    def test_strict_verdict_and_unavailable(self):
        for response in ('REJECT', 'USE but uncertain', 'USE\nREJECT', '', None):
            council = Mock()
            council._run.return_value = response
            self.assertFalse(self.review(council))
        council = Mock()
        council._run.side_effect = RuntimeError('unavailable')
        self.assertFalse(self.review(council))

    def test_identity_binds_exact_spec_task_source_and_project(self):
        council = Mock()
        council._run.return_value = 'USE'
        identities = []
        for overrides in ({}, {'original': self.original+' User amendment: no Vulkan.'},
                          {'goal': 'Find another interface'}, {'evidence': 'different excerpt'},
                          {'project': self.base}):
            self.assertTrue(self.review(council, **overrides))
            identities.append(council._run.call_args.kwargs['evidence_sha'])
        self.assertEqual(len(set(identities)), len(identities))

    def test_stale_or_cancelled_review_refuses_evidence(self):
        council = Mock()
        council._run.return_value = 'USE'
        checks = iter((True, False))
        self.assertFalse(self.review(council, current=lambda: next(checks)))
        council.reset_mock()
        self.assertFalse(self.review(council, cancelled=lambda: True))
        council._run.assert_not_called()

    def test_agent_rejection_never_reaches_later_model_prompt(self):
        council = Mock()
        council._run.side_effect = [self.request, 'REJECT', '{"tool":"done","args":{}}']
        result = gather(self.tools, council, None, session='test', original=self.original,
                        goal=self.goal, budget=1100)
        self.assertEqual(result, '')
        self.assertEqual(council._run.call_args_list[1].kwargs['role'], 'SENTINEL_DOCUMENT')
        self.assertNotIn('pipeline cache', council._run.call_args_list[2].kwargs['prompt'])

    def test_agent_acceptance_revalidates_and_delivers_exact_excerpt(self):
        council = Mock()
        council._run.side_effect = [self.request, 'USE', '{"tool":"done","args":{}}']
        result = gather(self.tools, council, None, session='test', original=self.original,
                        goal=self.goal, budget=1100)
        self.assertIn('pipeline cache', result)
        self.assertIn('untrusted data', result)
        self.assertIn('pipeline cache', council._run.call_args_list[2].kwargs['prompt'])

    def test_agent_changed_during_review_is_withheld(self):
        council = Mock()
        def run(*args, **kwargs):
            if kwargs['role']=='SENTINEL_DOCUMENT':
                self.path.write_text('Changed source.')
                return 'USE'
            return self.request if not council._run.call_count>1 else '{"tool":"done","args":{}}'
        council._run.side_effect = run
        self.assertEqual(gather(self.tools,council,None,session='test',original=self.original,
                               goal=self.goal,budget=1100), '')

    def test_context_rejected_or_approved(self):
        council=Mock()
        for verdict in ('REJECT','USE'):
            council._run.return_value=verdict
            context=reviewed_context(self.index,council,None,project=self.root,original=self.original,
                    goal=self.goal,session='test',max_chars=640)
            self.assertEqual(bool(context),verdict=='USE')

    def test_durable_council_reuses_only_exact_verdict(self):
        council=ReasoningCouncil(self.base/'council.sqlite')
        client=Mock()
        client.completed_exchange.return_value=None
        client.chat.return_value='USE'
        kwargs=dict(project=self.root,original=self.original,goal=self.goal,session='test',
                    evidence='Reference A',current=lambda:True)
        self.assertTrue(review_documents(council,client,**kwargs))
        self.assertTrue(review_documents(council,client,**kwargs))
        self.assertEqual(client.chat.call_count,1)
        kwargs['evidence']='Reference B'
        self.assertTrue(review_documents(council,client,**kwargs))
        self.assertEqual(client.chat.call_count,2)
