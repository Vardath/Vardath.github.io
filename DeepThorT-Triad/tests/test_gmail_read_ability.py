import base64
import unittest
from unittest.mock import patch
from deepthort_local import gmail_read as tool

class GmailReadTests(unittest.TestCase):
    def test_exact_account_and_bounded_search(self):
        s={'operation':'search','account':'owner@example.com','query':'subject:test & more','limit':2}
        profile={'emailAddress':s['account']}
        msg={'id':'abc','snippet':'test','payload':{'headers':[{'name':'Subject','value':'Hello'}]}}
        with patch.object(tool,'request',side_effect=[(profile,'1'),({'messages':[{'id':'abc'}],'nextPageToken':'next'},'2'),(msg,'3'),(profile,'4')]) as req:
            r=tool.inspect(s,'dummy',approved=True)
            self.assertEqual(r['messages'][0]['headers']['subject'],'Hello')
            self.assertTrue(r['more_results']);self.assertFalse(r['remote_changed'])
            self.assertIn('q=subject%3Atest+%26+more',req.call_args_list[1].args[0])
            self.assertTrue(all(x.args[0].startswith(tool.BASE) for x in req.call_args_list))
        with patch.object(tool,'request',return_value=({'emailAddress':'other@example.com'},'x')):
            with self.assertRaises(ValueError):tool.inspect(s,'dummy',approved=True)
        with self.assertRaises(PermissionError):tool.inspect(s,'dummy')
    def test_plain_text_only_no_attachment(self):
        s={'operation':'read','account':'owner@example.com','message_id':'abc'}
        profile={'emailAddress':s['account']}
        encoded=base64.urlsafe_b64encode(b'Plain text').decode()
        row={'id':'abc','payload':{'mimeType':'multipart/mixed','parts':[
            {'mimeType':'text/plain','body':{'data':encoded}},
            {'mimeType':'text/html','body':{'data':encoded}},
            {'mimeType':'text/plain','filename':'attachment.txt','body':{'data':encoded}},
            {'mimeType':'text/plain','body':{'attachmentId':'other'}}]}}
        with patch.object(tool,'request',side_effect=[(profile,'1'),(row,'2'),(profile,'3')]) as req:
            result=tool.inspect(s,'dummy',approved=True)
            self.assertEqual(result['messages'][0]['plain_text'],'Plain text')
            self.assertFalse(result['attachments_downloaded'])
            self.assertEqual(req.call_count,3)
    def test_bounds(self):
        for bad in ('../abc','abc?foo',''):
            with self.assertRaises(ValueError):tool.checked({'operation':'read','account':'a@b.com','message_id':bad})

if __name__=='__main__':unittest.main()
