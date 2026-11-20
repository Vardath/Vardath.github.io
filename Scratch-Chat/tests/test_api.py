"""Smoke-test the real local HTTP API with the trained model, not a mock."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.server = subprocess.Popen(
            [sys.executable, '-m', 'vardath_chat', 'serve', '--port', str(cls.port)],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for i in range(70):
            try:
                with urlopen(f'http://127.0.0.1:{cls.port}/health', timeout=2) as res:
                    if json.load(res)['status'] == 'ok':
                        return
            except (URLError, OSError):
                time.sleep(0.1)
        raise AssertionError('Server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=4)
        except subprocess.TimeoutExpired:
            cls.server.kill()

    def test_models(self):
        with urlopen(f'http://127.0.0.1:{self.port}/v1/models', timeout=5) as res:
            self.assertEqual(json.load(res)['data'][0]['id'], 'vardath-scratch-1')

    def test_completion(self):
        payload = json.dumps({'model': 'vardath-scratch-1',
                              'messages': [{'role': 'user', 'content': 'what is janus?'}],
                              'max_tokens': 96, 'temperature': 0}).encode('utf-8')
        request = Request(f'http://127.0.0.1:{self.port}/v1/chat/completions',
                          payload, {'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=20) as res:
            data = json.load(res)
        self.assertEqual(data['object'], 'chat.completion')
        self.assertIn('JANUS', data['choices'][0]['message']['content'])

    def test_streaming_rejected_explicitly(self):
        payload = json.dumps({'stream': True, 'messages': [{'role': 'user', 'content': 'hello'}]}).encode()
        request = Request(f'http://127.0.0.1:{self.port}/v1/chat/completions',
                          payload, {'Content-Type': 'application/json'}, method='POST')
        with self.assertRaises(HTTPError) as cm:
            urlopen(request, timeout=10)
        self.assertEqual(cm.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
