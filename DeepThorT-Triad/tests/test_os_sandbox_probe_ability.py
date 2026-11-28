import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import os_sandbox_probe as m

SPEC={'probe':'restricted_token_files'}
GOOD={k:True for k in ('baseline_allowed_read','baseline_protected_read','baseline_write_open',
    'restricted_thread_token_verified','restricted_allowed_read','restricted_protected_read_denied',
    'restricted_protected_write_denied','restricted_allowed_write_denied',
    'reverted_to_original_identity','fixture_contents_unchanged')}

class OSSandboxTests(unittest.TestCase):
    def test_evidence_is_narrow_and_complete(self):
        r=m.assess(GOOD)
        self.assertTrue(r['os_access_check_verified'])
        self.assertFalse(r['arbitrary_code_sandbox'])
        self.assertFalse(r['process_wide_restriction_verified'])
        self.assertFalse(r['network_isolation_verified'])
    def test_missing_or_failed_access_denial_rejected(self):
        for k in GOOD:
            with self.assertRaises(ValueError):m.assess(dict(GOOD,**{k:False}))
        with self.assertRaises(ValueError):m.checked({'probe':'run_arbitrary_program'})
    def test_review_output_and_failure(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.json')
            self.assertEqual(m.execute(root,plan,backend=lambda _:GOOD.copy())['backend'],'injected_fixture')
            with self.assertRaises(ValueError):m.execute(root,plan,backend=lambda _:self.fail('overwrite'))
            plan,_=m.review(root,'spec.json','bad.json')
            with self.assertRaises(ValueError):m.execute(root,plan,backend=lambda _:dict(GOOD,restricted_allowed_read=False))
            self.assertFalse((root/'bad.json').exists())
if __name__=='__main__':unittest.main()
