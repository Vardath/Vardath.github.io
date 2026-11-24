"""Chat, draft review, and explicit approval are separate durable states."""
import json
import tempfile
import unittest
from pathlib import Path

from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.job_queue import JobStore

class ConversationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root=Path(self.t.name)
        self.project=self.root/'project'
        self.project.mkdir()
        self.inbox=ConversationStore(self.root/'conversations.sqlite3')
        self.jobs=JobStore(self.root/'jobs.sqlite3')

    def test_chat_never_queues_work(self):
        ident=self.inbox.submit('chat-abc',str(self.project),'chat','Please assess this idea')
        self.assertEqual(self.jobs.items(str(self.project)),[])
        self.assertEqual(self.inbox.get(ident)['state'],'pending')
        self.assertEqual(self.inbox.next_pending()['id'],ident)

    def test_pending_message_survives_restart(self):
        ident=self.inbox.submit('chat-abc',str(self.project),'chat','Persist this')
        self.assertTrue(self.inbox.change(ident,'running','model busy',allowed=('pending',)))
        reopened=ConversationStore(self.root/'conversations.sqlite3')
        self.assertEqual(reopened.get(ident)['state'],'pending')
        self.assertEqual(self.jobs.items(str(self.project)),[])

    def test_draft_plan_requires_explicit_approval(self):
        n=self.inbox.submit('chat-abc',str(self.project),'draft_plan','Build a simple app')
        steps=[{'path':'src/main.py','description':'Executable app entrypoint'},
               {'path':'tests/test_main.py','description':'Automated regression tests'}]
        draft=self.inbox.save_draft(n,steps)
        self.assertEqual(self.jobs.items(str(self.project)),[])
        data=self.inbox.draft(draft)
        self.assertEqual(data['state'],'draft')
        job=self.jobs.submit_approved_build(data['project'],data['chat_id'],data['original_prompt'],
                                            data['steps'],f'draft:{draft}')
        self.assertTrue(self.inbox.approve(draft,job))
        self.assertEqual(self.jobs.get(job)['state'],'queued')
        self.assertEqual(len(self.jobs.steps(job)),2)
        self.assertEqual(job,self.jobs.submit_approved_build(data['project'],data['chat_id'],
                 data['original_prompt'],data['steps'],f'draft:{draft}'))
        self.assertEqual(len(self.jobs.items(str(self.project))),1)

    def test_revised_request_revokes_old_unapproved_plan(self):
        n=self.inbox.submit('chat-abc',str(self.project),'draft_plan','First spec')
        draft=self.inbox.save_draft(n,[{'path':'a.py','description':'first revision'}])
        self.inbox.submit('chat-abc',str(self.project),'draft_plan','Changed requirements')
        self.assertEqual(self.inbox.draft(draft)['state'],'discarded')
        self.assertIsNone(self.inbox.latest_draft('chat-abc',str(self.project)))

    def test_legacy_migration_idempotent(self):
        j=self.jobs.submit(str(self.project),'chat-abc','chat','Old unsent request')
        turn=self.inbox.submit('chat-abc',str(self.project),'chat','Old unsent request',source_job_id=j)
        same=self.inbox.submit('chat-abc',str(self.project),'chat','Old unsent request',source_job_id=j)
        self.assertEqual(same,turn)
        self.assertEqual(len(self.inbox.thread('chat-abc')),1)


    def test_diagnostic_export_redacts_chat_and_plan(self):
        from deepthort_local.flight_recorder import export_diagnostics
        import zipfile
        secret='VERY_PRIVATE_CONVERSATION_TEXT_51991'
        n=self.inbox.submit('chat-abc',str(self.project),'draft_plan',secret)
        self.inbox.save_draft(n,[{'path':'src/main.py','description':'Write local code'}])
        output=export_diagnostics(self.root,self.root/'support.zip',app_root=self.root)
        with zipfile.ZipFile(output) as z:
            text='\n'.join(z.read(x).decode('utf-8',errors='replace') for x in z.namelist())
            self.assertNotIn(secret,text)
            self.assertIn('conversations',text)
            self.assertIn('drafts',text)
            self.assertNotIn('sqlite3',str(z.namelist()))

    def test_unapproved_pre_v10_4_build_is_frozen(self):
        j=self.jobs.submit(str(self.project),'chat-abc','build','Generate an app')
        self.assertEqual(self.jobs.freeze_unapproved_legacy_builds(),1)
        self.assertEqual(self.jobs.get(j)['state'],'needs_input')
        self.assertEqual(self.jobs.freeze_unapproved_legacy_builds(),0)

if __name__=='__main__':unittest.main()
