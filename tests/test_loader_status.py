"""Real Node.js local status + worker-thread inference contract without AI weights."""
from __future__ import annotations
import contextlib
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]


def unused_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

@unittest.skipUnless(shutil.which('node'), 'Node.js is required for the integration check')
class LoaderStatusTests(unittest.TestCase):
    def test_readiness_and_chat_only_after_real_worker_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            shutil.copy2(ROOT/'inference_server.mjs',base/'inference_server.mjs')
            (base/'package.json').write_text('{"type":"module"}')
            (base/'inference_worker.mjs').write_text('''
import {parentPort} from 'node:worker_threads';
parentPort.postMessage({kind:'stage',message:'Mock local model initialization',elapsed_seconds:0});
setTimeout(()=>parentPort.postMessage({kind:'ready'}),750);
parentPort.on('message',m=>{if(m.kind==='generate')parentPort.postMessage({kind:'answer',id:m.id,output:'local test response'});});
''')
            port=unused_port()
            env=os.environ.copy();env['DEEPTHORT_TEST_PORT']=str(port)
            proc=subprocess.Popen(['node',str(base/'inference_server.mjs')],cwd=base,
                                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
            try:
                status=None
                for _ in range(60):
                    try:
                        with urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as res:
                            status=json.load(res)
                        break
                    except (URLError, ConnectionError, TimeoutError):
                        time.sleep(.025)
                self.assertIsNotNone(status,'server must expose health before model ready')
                self.assertFalse(status['ready'],'must not falsely report ready on process start')
                self.assertEqual(status['model'],'deepthort-qwen-coder-onnx')
                self.assertTrue(status['offline'])
                request=Request(f'http://127.0.0.1:{port}/v1/chat/completions',method='POST',
                      data=json.dumps({'messages':[{'role':'user','content':'Test'}],'max_tokens':8}).encode(),
                      headers={'Content-Type':'application/json'})
                with self.assertRaises(HTTPError) as ctx:urlopen(request,timeout=1)
                self.assertEqual(ctx.exception.code,503)
                for _ in range(50):
                    with urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as res:
                        status=json.load(res)
                    if status['ready']:break
                    time.sleep(.03)
                self.assertTrue(status['ready'],'ready must come from model worker')
                with urlopen(request,timeout=2) as res:
                    answer=json.load(res)
                self.assertEqual(answer['choices'][0]['message']['content'],'local test response')
            finally:
                proc.terminate()
                try:proc.communicate(timeout=3)
                except subprocess.TimeoutExpired:proc.kill();proc.communicate(timeout=3)

    def test_dead_worker_exits_with_failure_instead_of_loading_forever(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            shutil.copy2(ROOT/'inference_server.mjs',base/'inference_server.mjs')
            (base/'package.json').write_text('{"type":"module"}')
            (base/'inference_worker.mjs').write_text("throw new Error('Intentional missing native ONNX binary');")
            env=os.environ.copy();env['DEEPTHORT_TEST_PORT']=str(unused_port())
            proc=subprocess.run(['node',str(base/'inference_server.mjs')],cwd=base,env=env,
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=8,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('[AI LOAD FAILED]',proc.stdout)
            self.assertIn('Intentional missing native ONNX binary',proc.stdout)

if __name__=='__main__':unittest.main()
