import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.language_server import analyze,review,execute
from deepthort_local.python_language_server import frame,read
class LspTests(unittest.TestCase):
    def test_real_session_symbols_and_inert_source(self):
        raw=b'raise RuntimeError("not executed")\nclass Example:\n    def method(self):\n        pass\n'
        r=analyze(raw)
        self.assertEqual(r['diagnostics'],[])
        self.assertEqual(r['symbols'][0]['name'],'Example')
        self.assertEqual(r['symbols'][0]['children'][0]['name'],'method')
        self.assertEqual(r['position_encoding'],'utf-16')
    def test_syntax_and_framing(self):
        r=analyze(b'def broken(:\n')
        self.assertEqual(r['diagnostics'][0]['severity'],1);self.assertEqual(r['symbols'],[])
        m={'jsonrpc':'2.0','id':1,'result':'test'}
        self.assertEqual(read(io.BytesIO(frame(m))),m)
        with self.assertRaises(ValueError):read(io.BytesIO(b'Content-Length: 10000000\r\n\r\n'))
    def test_exact_approval(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);doc=root/'test.py';doc.write_text('def f(): pass\n',encoding='utf-8')
            (root/'spec.json').write_text(json.dumps({'document':'test.py'}),encoding='utf-8')
            plan,_=review(root,'spec.json','symbols.json')
            self.assertFalse(execute(root,plan)['source_executed'])
            self.assertEqual(json.loads((root/'symbols.json').read_text())['symbols'][0]['name'],'f')
            plan,_=review(root,'spec.json','later.json');doc.write_text('changed = 1\n',encoding='utf-8')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
