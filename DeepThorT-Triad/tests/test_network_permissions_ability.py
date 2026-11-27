import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from deepthort_local import network_permissions as m
from deepthort_local.website_monitor import resolve_public,PinnedHTTPS

class NetworkPermissionsTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'network-permissions.json'
        self.addCleanup(patch.stopall)
        patch.object(m,'POLICY_PATH',self.path).start()
    def test_default_approval_model_and_persistence(self):
        self.assertEqual(m.current()['mode'],'reviewed')
        policy=m.from_text('api.github.com, www.googleapis.com')
        with self.assertRaises(PermissionError):m.save(policy)
        self.assertEqual(m.save(policy,approval=True),policy)
        self.assertTrue(m.require('api.github.com'))
        with self.assertRaises(PermissionError):m.require('github.com')
        with self.assertRaises(ValueError):m.from_text('*.github.com')
        self.assertEqual(m.current()['hosts'],['api.github.com','www.googleapis.com'])
    def test_block_before_dns_and_connect(self):
        resolver=Mock()
        connection=PinnedHTTPS('api.github.com','8.8.8.8')
        m.save(m.from_text('blocked'),approval=True)
        with self.assertRaises(PermissionError):resolve_public('api.github.com',resolver)
        resolver.assert_not_called()
        with patch('deepthort_local.website_monitor.socket.socket') as sock:
            with self.assertRaises(PermissionError):connection.connect()
            sock.assert_not_called()
        with patch('http.client.HTTPSConnection.request') as request:
            with self.assertRaises(PermissionError):connection.request('GET','/')
            request.assert_not_called()
        connection.close()
    def test_malformed_policy_fails_closed_and_repair(self):
        self.path.write_bytes(b'{')
        with self.assertRaises(PermissionError):m.require('api.github.com')
        m.save(m.from_text('reviewed'),approval=True)
        self.assertTrue(m.require('api.github.com'))
if __name__=='__main__':unittest.main()
