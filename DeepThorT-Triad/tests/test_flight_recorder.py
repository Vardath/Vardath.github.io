import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from deepthort_local.flight_recorder import export_diagnostics, record, scrub
from deepthort_local.job_queue import JobStore


class RecorderTests(unittest.TestCase):
    def test_logs_are_persistent_json_without_secret_tokens(self):
        with tempfile.TemporaryDirectory() as temp:
            state=Path(temp)/'state'
            record(state,'desktop','startup',message='API_KEY=supersecretvalue',private_token='sensitive')
            log=state/'logs'/'desktop.jsonl'
            self.assertTrue(log.is_file())
            data=json.loads(log.read_text().strip())
            self.assertEqual(data['event'],'startup')
            self.assertEqual(data['data']['private_token'],'[REDACTED]')
            self.assertNotIn('supersecretvalue',log.read_text())

    def test_export_does_not_include_raw_conversation_or_model_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);state=root/'state';state.mkdir()
            jobs=JobStore(state/'jobs.sqlite3')
            secret='PERSONAL_USER_PROMPT_UNIQUE_123'
            jobid=jobs.submit('(general)','chat-123','chat',secret)
            jobs.change(jobid,'needs_input','Model not responding',allowed=('queued',))
            record(state,'desktop','model_ready')
            (root/'models').mkdir()
            (root/'models'/'big-model.bin').write_bytes(b'MODELWEIGHTS')
            out=export_diagnostics(state,root/'support.zip',app_root=root,
                                   app_state={'model_ready':True,'private_password':'mysecret'})
            with zipfile.ZipFile(out) as z:
                names=z.namelist()
                self.assertIn('summary.json',names)
                self.assertTrue(any(n.startswith('logs/') for n in names))
                self.assertFalse(any('sqlite3' in n or 'model.bin' in n for n in names))
                contents='\n'.join(z.read(n).decode('utf-8',errors='replace') for n in names)
                self.assertNotIn(secret,contents)
                self.assertNotIn('mysecret',contents)
                summary=json.loads(z.read('summary.json'))
                self.assertEqual(summary['storage']['jobs']['counts'][0]['state'],'needs_input')

    def test_queue_can_dispatch_across_projects(self):
        with tempfile.TemporaryDirectory() as temp:
            queue=JobStore(Path(temp)/'jobs.sqlite3')
            first=queue.submit('other-project','chat-1','chat','Hello')
            queue.submit('current-project','chat-2','chat','World')
            self.assertEqual(queue.next_any_queued()['id'],first)
            queue.change(first,'responded','Completed',allowed=('queued',))
            self.assertEqual(queue.next_any_queued()['project'],'current-project')

    def test_scrubber_removes_auth_material(self):
        self.assertNotIn('abcdef123456789012345',scrub('Bearer abcdef123456789012345'))
        self.assertEqual(scrub({'api_key':'abc','message_body':'something'}),
                         {'api_key':'[REDACTED]','message_body':'[REDACTED]'})

if __name__=='__main__': unittest.main()
