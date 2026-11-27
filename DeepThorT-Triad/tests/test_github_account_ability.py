import time
import unittest
from unittest.mock import patch
from deepthort_local import github_account as g
from deepthort_local.github_oauth import Session

def row(name='example/one',ident=2):
    return {'full_name':name,'id':ident,'owner':{'login':'example'},'private':False,'default_branch':'main','fork':False,'archived':False,'disabled':False,'description':'not returned'}

class AccountTests(unittest.TestCase):
    def setUp(self):self.s=Session('example',1,time.monotonic()+900,'fixture_token')
    def test_inventory_and_scope(self):
        account={'login':'example','id':1,'email':'not returned'}
        with patch.object(g,'_request',side_effect=[(account,'a'),([row()],'b'),(account,'c')]) as req:
            result=g.inspect(self.s,2,approved=True)
        self.assertEqual([c.args[0] for c in req.call_args_list],['GET']*3)
        self.assertEqual(req.call_args_list[1].args[1],'/users/example/repos?type=owner&sort=full_name&direction=asc&per_page=30&page=2')
        self.assertEqual(result['repositories'][0]['repository'],'example/one')
        self.assertNotIn('fixture_token',str(result));self.assertNotIn('not returned',str(result))
        self.assertFalse(result['complete_inventory_verified'])
    def test_refusals(self):
        with patch.object(g,'_request') as req:
            with self.assertRaises(PermissionError):g.inspect(self.s,1)
            with self.assertRaises(ValueError):g.inspect(self.s,11,approved=True)
            self.s.disconnect()
            with self.assertRaises(ValueError):g.inspect(self.s,1,approved=True)
            req.assert_not_called()
        for rows in ([dict(row(),private=True)],[row(),row()],[row('other/one')],[dict(row(),default_branch='../bad')]):
            with self.assertRaises(ValueError):g.repositories(rows,'example')
    def test_identity_change(self):
        with patch.object(g,'_request',side_effect=[({'login':'example','id':1},'a'),([row()],'b'),({'login':'example','id':3},'c')]):
            with self.assertRaises(ValueError):g.inspect(self.s,1,approved=True)
