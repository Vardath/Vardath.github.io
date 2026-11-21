import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from deepthort_local.client import LocalModelClient, MODEL_ID
from deepthort_local.win_cpu_cap import calculate_ram_limit, run_capped
from deepthort_local.disk_gate import DiskGate, configured_game_names
import download_model

class Tests(unittest.TestCase):
    def test_model_locked_to_local_cpu_onnx(self):
        self.assertEqual(MODEL_ID, 'deepthort-qwen-coder-onnx')
        self.assertEqual(download_model.REPO, 'onnx-community/Qwen2.5-Coder-1.5B-Instruct')
        self.assertEqual(list(download_model.FILES).count('onnx/model_q4.onnx'),1)
        self.assertNotIn('model.onnx', download_model.FILES)
    def test_reject_remote_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            for url in ['http://host:8765','https://127.0.0.1:8765','http://127.0.0.1.evil.com:8765','http://localhost:8765','http://127.0.0.1:8765/evil']:
                with self.assertRaises(ValueError): LocalModelClient(Path(tmp)/'db', url)
    def test_sqlite_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'db'
            c=LocalModelClient(db)
            with c._connect() as conn:
                conn.execute("INSERT INTO messages(session_id,role,content) VALUES('a','user','Hello')")
            self.assertEqual(LocalModelClient(db).history('a'),[{'role':'user','content':'Hello'}])
            self.assertEqual(LocalModelClient(db).history('b'),[])
    def test_client_calls_loopback_only_and_saves_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            client=LocalModelClient(Path(tmp)/'db')
            body=json.dumps({'choices':[{'message':{'content':'def answer(): return 42'}}]}).encode()
            mock=MagicMock();mock.__enter__.return_value=mock;mock.read.return_value=body
            # json.load requires .read on the response object.
            opener=MagicMock();opener.open.return_value=mock
            with patch('urllib.request.build_opener',return_value=opener) as make:
                self.assertEqual(client.chat('test','Write a function'), 'def answer(): return 42')
            req=opener.open.call_args.args[0]
            self.assertEqual(req.full_url,'http://127.0.0.1:8765/v1/chat/completions')
            self.assertEqual(len(client.history('test')),2)
            self.assertTrue(make.called)
    def test_ram_math(self):
        gib=1024**3
        self.assertEqual(calculate_ram_limit(16*gib, 10*gib),16*gib//5)
        with self.assertRaises(RuntimeError): calculate_ram_limit(16*gib,3*gib)
    def test_no_uncapped_launch(self):
        if os.name!='nt':
            with self.assertRaisesRegex(RuntimeError,'refusing uncapped'): run_capped(['node','inference_server.mjs'])
    def test_disk_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'games';p.write_text('X4.exe\n')
            self.assertEqual(configured_game_names(p),frozenset({'x4.exe'}))
            flag=Path(tmp)/'flag'; gate=DiskGate(game_names_path=p,game_flag=flag,game_probe=lambda:False)
            self.assertFalse(gate.gaming());flag.touch();self.assertTrue(gate.gaming())
    def test_download_resume_no_network_for_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(download_model,'MODEL',Path(tmp)):
                path=Path(tmp)/'config.json';path.write_text('{}' * 100)
                with patch('download_model.urlopen') as fetch:
                    download_model.download('config.json',100)
                    fetch.assert_not_called()

if __name__=='__main__': unittest.main()
