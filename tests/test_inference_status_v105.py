"""Prove ONNX server health can expose real generation activity (stubbed worker)."""
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('node'), 'Node.js is not available')
class InferenceHealthTests(unittest.TestCase):
    def test_busy_and_elapsed_time_are_real_request_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            tmp=Path(d)
            shutil.copy(ROOT/'inference_server.mjs',tmp/'inference_server.mjs')
            # This model-free worker mirrors the ready and answer protocol. It
            # deliberately delays a response to make /health observably busy.
            (tmp/'inference_worker.mjs').write_text('''
import { parentPort } from 'node:worker_threads';
parentPort.postMessage({kind:'ready'});
parentPort.on('message', m=> {
 if(m.kind==='generate')setTimeout(()=>parentPort.postMessage(
  {kind:'answer',id:m.id,output:'Local reply from stub'}),1200);
});
''',encoding='utf-8')
            (tmp/'package.json').write_text('{"type":"module"}',encoding='utf-8')
            with socket.socket() as s:
                s.bind(('127.0.0.1',0));port=s.getsockname()[1]
            env={**os.environ,'DEEPTHORT_TEST_PORT':str(port)}
            proc=subprocess.Popen(['node',str(tmp/'inference_server.mjs')],cwd=tmp,env=env,
                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            base=f'http://127.0.0.1:{port}'
            try:
                for _ in range(80):
                    try:
                        with urlopen(base+'/health',timeout=.3) as response:
                            health=json.load(response)
                        if health['ready']:break
                    except (URLError,TimeoutError,ConnectionError):pass
                    time.sleep(.05)
                else:self.fail('stubbed model server never became ready')
                self.assertFalse(health['inference_busy'])
                self.assertEqual(health['inference_elapsed_seconds'],0)
                result=[]
                payload=json.dumps({'model':'deepthort-qwen-coder-onnx','messages':[
                  {'role':'user','content':'Say hello'}],'max_tokens':32}).encode()
                def send():
                    try:
                        with urlopen(Request(base+'/v1/chat/completions',data=payload,
                              headers={'Content-Type':'application/json'}),timeout=8) as r:result.append(json.load(r))
                    except Exception as e:result.append(e)
                thread=threading.Thread(target=send);thread.start()
                for _ in range(30):
                    with urlopen(base+'/health',timeout=1) as r:health=json.load(r)
                    if health['inference_busy']:break
                    time.sleep(.05)
                self.assertTrue(health['inference_busy'])
                self.assertEqual(health['inference_max_tokens'],32)
                self.assertEqual(health['inference_request_id'],1)
                self.assertGreaterEqual(health['inference_elapsed_seconds'],0)
                thread.join(5)
                self.assertFalse(thread.is_alive())
                self.assertEqual(result[0]['choices'][0]['message']['content'],'Local reply from stub')
                with urlopen(base+'/health',timeout=1) as r:after=json.load(r)
                self.assertFalse(after['inference_busy'])
            finally:
                proc.terminate()
                try:proc.wait(timeout=3)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()

if __name__ == '__main__': unittest.main()
