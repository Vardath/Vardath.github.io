import unittest
from unittest.mock import patch
from deepthort_local import gmail_organise as tool

class GmailOrganiseTests(unittest.TestCase):
    def spec(self):
        return {'account':'owner@example.com','query':'subject:test','limit':2,'add':['Label_123'],'remove':['INBOX']}
    def row(self,ident='abc',labels=None):
        return {'id':ident,'labelIds':['INBOX','UNREAD'] if labels is None else labels,'snippet':'test','payload':{'headers':[{'name':'Subject','value':'Hello'}]}}
    def plan(self):
        s=self.spec();p={'emailAddress':s['account']}
        with patch.object(tool,'request',side_effect=[(p,'1'),({'messages':[{'id':'abc'}]},'2'),(self.row(),'3'),(p,'4')]):
            return tool.preview(s,'dummy',approved=True)
    def test_preview_and_exact_mutation(self):
        plan=self.plan();p={'emailAddress':plan['account']}
        self.assertEqual(plan['rows'][0]['target_labels'],['Label_123','UNREAD'])
        with patch.object(tool,'request',side_effect=[(p,'1'),(self.row(),'2'),(p,'3'),(self.row(),'4')]),patch.object(tool,'modify',return_value=({'id':'abc','labelIds':['Label_123','UNREAD']},'5')) as post:
            result=tool.apply(plan,'dummy',approved=True)
            self.assertEqual(result['status'],'reviewed_labels_modified')
            self.assertEqual(post.call_args.args[:3],('abc',['Label_123'],['INBOX']))
            self.assertEqual(result['confirmed'][0]['inverse_add'],['INBOX'])
    def test_stale_and_uncertain_no_retry(self):
        plan=self.plan();p={'emailAddress':plan['account']}
        with patch.object(tool,'request',side_effect=[(p,'1'),(self.row(labels=['INBOX']),'2')]),patch.object(tool,'modify') as post:
            with self.assertRaises(ValueError):tool.apply(plan,'dummy',approved=True)
            post.assert_not_called()
        with patch.object(tool,'request',side_effect=[(p,'1'),(self.row(),'2'),(p,'3'),(self.row(),'4')]),patch.object(tool,'modify',side_effect=TimeoutError) as post:
            r=tool.apply(plan,'dummy',approved=True)
            self.assertEqual(r['status'],'stopped_uncertain');self.assertEqual(post.call_count,1)
        with self.assertRaises(PermissionError):tool.apply(plan,'dummy')
    def test_no_destructive_labels(self):
        for label in ('TRASH','SPAM','SENT','../abc'):
            with self.assertRaises(ValueError):tool.checked(dict(self.spec(),add=[label]))

if __name__=='__main__':unittest.main()
