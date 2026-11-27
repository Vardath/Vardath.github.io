from email import policy
from email.parser import BytesParser
import unittest
from unittest.mock import patch
from deepthort_local import gmail_send as tool

class GmailSendTests(unittest.TestCase):
    def spec(self):
        return {'account':'owner@example.com','to':'friend@example.net','subject':'Hello 世界','body':'Plain text\nSecond line'}
    def test_exact_plain_text_and_no_extra_recipient(self):
        s=self.spec();msg=BytesParser(policy=policy.default).parsebytes(tool.prepare(s))
        self.assertEqual(str(msg['To']),s['to']);self.assertEqual(str(msg['Subject']),s['subject'])
        # SMTP wire format uses CRLF. Normalize only line endings; preserve body whitespace.
        self.assertEqual(msg.get_content().replace('\r\n','\n'),s['body']+'\n');self.assertIsNone(msg['Bcc'])
        self.assertIsNone(msg['Cc']);self.assertEqual(str(msg['From']),s['account'])
        self.assertEqual(msg.get_content_type(),'text/plain')
        for to in ('a@b.com,c@d.com','a@b.com\nBcc: c@d.com','a@b..com'):
            with self.assertRaises(ValueError):tool.prepare(dict(s,to=to))
        with self.assertRaises(ValueError):tool.prepare(dict(s,subject='Hello\nBcc: c@d.com'))
    def test_approval_account_and_single_send(self):
        s=self.spec()
        with patch.object(tool,'request',return_value=({'emailAddress':s['account']},'1')),patch.object(tool,'send_request',return_value=({'id':'abc'},'2')) as post:
            r=tool.send(s,'dummy',approved=True)
            self.assertEqual(r['status'],'provider_send_accepted');self.assertFalse(r['delivery_verified'])
            self.assertEqual(post.call_count,1)
        with patch.object(tool,'request',return_value=({'emailAddress':'other@example.com'},'1')),patch.object(tool,'send_request') as post:
            with self.assertRaises(ValueError):tool.send(s,'dummy',approved=True)
            post.assert_not_called()
        with self.assertRaises(PermissionError):tool.send(s,'dummy')
    def test_no_retry_on_uncertain_response(self):
        s=self.spec()
        with patch.object(tool,'request',return_value=({'emailAddress':s['account']},'1')),patch.object(tool,'send_request',side_effect=TimeoutError) as post:
            with self.assertRaises(TimeoutError):tool.send(s,'dummy',approved=True)
            self.assertEqual(post.call_count,1)

if __name__=='__main__':unittest.main()
