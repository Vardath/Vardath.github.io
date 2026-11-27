import unittest
from unittest.mock import patch
from deepthort_local import social_publish as tool

class SocialPublishTests(unittest.TestCase):
    def setUp(self):
        self.s={'account':'owner','text':'Hello & world','visibility':'unlisted'}
        self.account={'id':'123','acct':'owner','username':'owner'}
        self.token='dummy_token'
    def test_exact_account_and_single_post(self):
        posted={'id':'456','visibility':'unlisted','account':self.account}
        with patch.object(tool,'request',side_effect=[self.account,posted]) as req:
            r=tool.publish(self.s,self.token,approved=True)
            self.assertEqual(r['post_id'],'456')
            self.assertEqual(req.call_count,2)
            self.assertEqual(req.call_args_list[0].args[0],'/api/v1/accounts/verify_credentials')
            self.assertEqual(req.call_args_list[1].kwargs['body'],b'status=Hello+%26+world&visibility=unlisted')
            self.assertFalse(r['rendered_text_verified'])
        with self.assertRaises(PermissionError):tool.publish(self.s,self.token)
    def test_mismatch_and_uncertain_never_retry(self):
        with patch.object(tool,'request',return_value=dict(self.account,acct='different')) as req:
            with self.assertRaises(ValueError):tool.publish(self.s,self.token,approved=True)
            self.assertEqual(req.call_count,1)
        with patch.object(tool,'request',side_effect=[self.account,OSError('unknown')]) as req:
            with self.assertRaises(OSError):tool.publish(self.s,self.token,approved=True)
            self.assertEqual(req.call_count,2)
        with patch.object(tool,'request',side_effect=[self.account,{'id':'bad'}]) as req:
            with self.assertRaises(ValueError):tool.publish(self.s,self.token,approved=True)
            self.assertEqual(req.call_count,2)
    def test_bounds(self):
        for change in ({'account':'owner@elsewhere'},{'visibility':'direct'},{'text':'a'*401},{'text':'a\x00b'},{'text':'  '}):
            with self.assertRaises(ValueError):tool.checked(dict(self.s,**change))

if __name__=='__main__':unittest.main()
