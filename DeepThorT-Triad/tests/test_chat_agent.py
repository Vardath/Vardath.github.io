import unittest
from deepthort_local.chat_agent import run_agent, selection, eligible, sha


class FakeCouncil:
    def __init__(self, plan='DOCS: model-qwen3\nAPPROACH: inspect model documentation', verdict='ACCEPT'):
        self.plan = plan
        self.verdict = verdict
        self.roles = []
    def _run(self, client, *, role, **kwargs):
        self.roles.append(role)
        return self.plan if role.startswith('JANUS') else self.verdict


class FakeClient:
    def __init__(self):
        self.roles = []
    def chat_as(self, role, session, prompt, max_tokens):
        self.roles.append(role)
        return 'A bounded proposal, not a completed change.'


class AgentTests(unittest.TestCase):
    def exercise(self, request='Look online at available models', plan=None, verdict='ACCEPT', fail=False, network=True):
        council = FakeCouncil(verdict=verdict, **({'plan':plan} if plan is not None else {}))
        client = FakeClient()
        calls, audits = [], []
        url = 'https://example.invalid/model-card'
        def document(key, *, online):
            calls.append(key)
            if fail:
                raise OSError('network failure')
            return {'url':url, 'text':'Public model card', 'sha256':sha('Public model card')}
        answer = run_agent(client, council, session='chat-1', original=request,
                           packet=request+'\nLocal evidence', route='self_review',
                           docs={'model-qwen3':url}, document=document,
                           excerpt=lambda item, original, limit: item['text'],
                           cancelled=lambda:False, network_ok=lambda:network,
                           stage=lambda message:None, audit=lambda **kw:audits.append(kw))
        return answer, calls, council.roles, client.roles, audits[0]

    def test_collaboration_and_receipt(self):
        answer, calls, roles, workers, audit = self.exercise()
        self.assertEqual(roles,['JANUS_CHAT_ROUTE','SENTINEL_CHAT_REVIEW'])
        self.assertEqual(workers,['implementation'])
        self.assertEqual(calls,['model-qwen3'])
        self.assertIn('SHA-256',answer)
        self.assertTrue(audit['sentinel_accepted'])
        self.assertFalse(audit['execution_authorized'])

    def test_reject_withholds_unverified_draft(self):
        answer, _, _, _, audit = self.exercise(verdict='REJECT')
        self.assertIn('withheld',answer)
        self.assertNotIn('A bounded proposal',answer)
        self.assertFalse(audit['sentinel_accepted'])

    def test_no_network_without_permission(self):
        for request in ('Inspect your source', 'Do not look online', 'Explain why internet access is unavailable'):
            with self.subTest(request=request):
                answer, calls, _, _, audit = self.exercise(request)
                self.assertEqual(calls,[])
                self.assertEqual(audit['documents'],0)
        self.assertEqual(self.exercise(network=False)[1],[])

    def test_unknown_identifier_and_failure_are_explicit(self):
        answer, calls, _, _, _ = self.exercise(plan='DOCS: https://bad.invalid')
        self.assertEqual(calls,[])
        self.assertIn('valid documentation selection',answer)
        answer, calls, _, _, audit = self.exercise(fail=True)
        self.assertEqual(calls,['model-qwen3'])
        self.assertIn('Reference failures',answer)
        self.assertEqual(audit['documents'],0)

    def test_bounded_routes_and_parser(self):
        self.assertFalse(eligible('conversation','hi'))
        self.assertFalse(eligible('self_review','x'*3601))
        self.assertEqual(selection('DOCS: x,x',('x',)),((),False))
        self.assertEqual(selection('DOCS: NONE',()),((),True))


if __name__=='__main__':
    unittest.main()
