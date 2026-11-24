"""Chronological chat rendering and CPU-efficient context regression tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from deepthort_local.chat_timeline import merged_chat_timeline
from deepthort_local.client import LocalModelClient
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.job_queue import JobStore


def legacy(i,stamp,role,text):
    return {'id':i,'created_at':stamp,'role':role,'content':text}

def row(i,stamp,prompt,state='pending',response='',mode='chat'):
    return {'id':i,'created_at':stamp,'chat_id':'test','project':'(general)',
            'mode':mode,'prompt':prompt,'state':state,'response':response,'detail':'Waiting for local AI'}

class TimelineTests(unittest.TestCase):
    def test_legacy_diagnostics_interleaved_with_conversation_requests_by_time(self):
        diagnostics=[legacy(1,'2026-11-21 00:51:00','user','Run local diagnosis'),
                     legacy(2,'2026-11-21 00:51:00','assistant','LOCAL COMPUTER DIAGNOSTIC #1'),
                     legacy(3,'2026-11-21 00:55:23','user','Self diagnosis'),
                     legacy(4,'2026-11-21 00:55:23','assistant','LOCAL COMPUTER DIAGNOSTIC #2')]
        requests=[row(1,'2026-11-21 00:53:51','hello?')]
        result=merged_chat_timeline(diagnostics,requests)
        self.assertEqual([x['kind'] for x in result],['legacy','request','legacy'])
        self.assertEqual(result[-1]['messages'][-1][1],'LOCAL COMPUTER DIAGNOSTIC #2')
        self.assertEqual(result[1]['row']['prompt'],'hello?')

    def test_duplicate_completions_are_not_repeated_or_discarded_incorrectly(self):
        legacy_msgs=[legacy(1,'2026-11-21 00:52:00','user','hi'),
                     legacy(2,'2026-11-21 00:52:00','assistant','hello'),
                     legacy(3,'2026-11-21 00:53:00','user','hi'),
                     legacy(4,'2026-11-21 00:53:00','assistant','hello')]
        req=[row(1,'2026-11-21 00:51:00','hi',state='responded',response='hello')]
        events=merged_chat_timeline(legacy_msgs,req)
        self.assertEqual(len(events),2)  # one fulfilled request, one separate legacy exchange
        self.assertEqual(sorted(x['kind'] for x in events),['legacy','request'])

    def test_approved_build_events_sorted_by_time(self):
        event=merged_chat_timeline([], [row(5,'2026-11-21 10:00:00','Discuss project')],
          [{'id':1,'created_at':'2026-11-21 10:01:00','mode':'build','state':'queued',
            'chat_id':'test','prompt':'Implement approved plan'}])
        self.assertEqual([x['kind'] for x in event],['request','job'])

    def test_local_diagnostic_dumps_not_fed_into_model_context(self):
        with tempfile.TemporaryDirectory() as temp:
            client=LocalModelClient(Path(temp)/'db')
            client.record_local_exchange('chat','self diagnose',
                       'LOCAL COMPUTER DIAGNOSTIC (not a generated AI response)\n' + 'Long diagnosis'*400)
            self.assertEqual(client.inference_context('chat'),[])
            body=b'{"choices":[{"message":{"content":"Hi!"}}]}'
            response=MagicMock();response.__enter__.return_value=response;response.read.return_value=body
            opener=MagicMock();opener.open.return_value=response
            with patch('urllib.request.build_opener',return_value=opener):
                self.assertEqual(client.chat('chat','hello',max_tokens=128),'Hi!')
            import json
            sent=json.loads(opener.open.call_args.args[0].data)
            self.assertEqual(len(sent['messages']),2)
            self.assertEqual(sent['messages'][-1]['content'],'hello')
            self.assertNotIn('LOCAL COMPUTER DIAGNOSTIC',str(sent))
            self.assertEqual(len(client.display_history('chat')),4)

    def test_legacy_timestamp_migration_is_idempotent_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            jobs=JobStore(path/'jobs.sqlite3')
            conversations=ConversationStore(path/'conversations.sqlite3')
            job=jobs.submit('(general)','chat','chat','old request')
            with jobs._conn() as db:db.execute("UPDATE jobs SET created_at='2026-11-20 22:50:36' WHERE id=?",(job,))
            ident=conversations.submit('chat','(general)','chat','old request',source_job_id=job)
            self.assertEqual(conversations.restore_legacy_creation_times(jobs.get),1)
            self.assertEqual(conversations.restore_legacy_creation_times(jobs.get),0)
            self.assertEqual(conversations.get(ident)['created_at'],'2026-11-20 22:50:36')
            self.assertEqual(conversations.get(ident)['prompt'],'old request')

if __name__=='__main__':unittest.main()
