import unittest
from deepthort_local.memory_governor import parse_selection,fit,HEADER,govern,retrieve
from deepthort_local.memory_governor_probe import exercise
class MemoryGovernorTests(unittest.TestCase):
    def test_integration(self):
        result=exercise();self.assertEqual(result['status'],'passed',result)
    def test_exact_selection(self):
        self.assertEqual(parse_selection('{"keep":["N1"],"reason":"Relevant"}',{'N1'}),['N1'])
        for answer in ('{"keep":["N2"],"reason":"Invented"}','{"keep":["N1","N1"],"reason":"Duplicate"}',
                       '{"keep":["N1"],"reason":""}','{"keep":["N1"],"reason":"Fine","extra":"instruction"}'):
            with self.assertRaises(ValueError):parse_selection(answer,{'N1'})
    def test_complete_rows_only(self):
        text=HEADER+'{"id":"N1","observation":"first"}\n{"id":"N2","observation":"second"}\n'
        self.assertEqual(fit(text,len(HEADER)+35),HEADER+'{"id":"N1","observation":"first"}\n')
        self.assertEqual(fit(text,10),'')

    def test_changed_packet_withheld_and_fresh_review_required(self):
        import json
        import tempfile
        from pathlib import Path
        from deepthort_local.job_queue import JobStore
        from deepthort_local.reasoning_council import ReasoningCouncil,sha
        from deepthort_local.memory_governor_probe import FixtureClient
        for change in ('delete','edit','add'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                root=Path(folder);project=str(root/'project');spec='Keep sector ownership.'
                jobs=JobStore(root/'jobs.sqlite3')
                previous=jobs.submit(project,'chat','plan',spec)
                current=jobs.submit(project,'chat','plan',spec)
                jobs.remember(previous,'verification','sector ownership',sha(spec),sha('old'),
                              'Sector ownership regression: retain player owner.')
                args=dict(project=project,chat_id='chat',original=spec,focus='sector ownership',job_id=current,
                          scope='freshness-test',phase='implementation',budget=600)
                lookup={k:args[k] for k in ('project','chat_id','original','focus','job_id')}
                before=retrieve(jobs.path,**lookup)
                self.assertEqual(len(before),1)
                original_id=before[0]['id']
                class ChangingClient:
                    def chat_as(self,role,session,prompt,max_tokens):
                        self_outer.assertEqual(role,'sentinel')
                        if change=='add':
                            jobs.remember(previous,'verification','sector ownership',sha(spec),sha('new'),
                                          'Sector ownership corrected in a later test.')
                        else:
                            with jobs._conn() as db:
                                if change=='delete':
                                    db.execute('DELETE FROM task_memory_notes WHERE id=?',(int(original_id[1:]),))
                                else:
                                    db.execute('UPDATE task_memory_notes SET note=? WHERE id=?',
                                               ('Sector ownership observation superseded.',int(original_id[1:])))
                        return json.dumps({'keep':[original_id],'reason':'Was relevant.'})
                self_outer=self
                council=ReasoningCouncil(root/'council.sqlite3')
                self.assertEqual(govern(jobs,council,ChangingClient(),**args),'')
                with jobs._conn() as db:
                    row=db.execute('SELECT status,selected,context_sha FROM task_memory_reviews ORDER BY id DESC LIMIT 1').fetchone()
                self.assertEqual(row,('stale_packet_withheld','[]',sha('')))
                fresh=retrieve(jobs.path,**lookup)
                client=FixtureClient([fresh[0]['id']] if fresh else [])
                result=govern(jobs,council,client,**args)
                self.assertEqual(len(client.calls),1 if fresh else 0)
                if fresh:
                    self.assertIn(fresh[0]['observation'],result)
                else:
                    self.assertEqual(result,'')
