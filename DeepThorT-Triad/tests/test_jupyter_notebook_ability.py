import copy
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.jupyter_notebook import notebook,review,execute
S={'cells':[{'id':'intro','kind':'markdown','source':'# Experiment\nNotes'},
            {'id':'analysis','kind':'code','source':'x = 2\nprint(x)\n'}]}
class NotebookTests(unittest.TestCase):
    def test_standard_notebook_without_execution(self):
        n=notebook(S)
        self.assertEqual((n['nbformat'],n['nbformat_minor']),(4,5))
        self.assertEqual(n['metadata']['kernelspec']['name'],'python3')
        self.assertEqual(''.join(n['cells'][1]['source']),S['cells'][1]['source'])
        self.assertEqual(n['cells'][1]['outputs'],[])
        self.assertIsNone(n['cells'][1]['execution_count'])
    def test_invalid_cells(self):
        for change in ({'source':'if:'},{'id':'intro'},{'kind':'raw'}):
            s=copy.deepcopy(S);s['cells'][1].update(change)
            with self.assertRaises(ValueError):notebook(s)
    def test_inert_export_and_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);s=copy.deepcopy(S)
            s['cells'][1]['source']="from pathlib import Path\nPath('unwanted.txt').write_text('test')"
            (root/'spec.json').write_text(json.dumps(s),encoding='utf-8')
            plan,_=review(root,'spec.json','analysis.ipynb')
            r=execute(root,plan)
            self.assertFalse(r['code_executed']);self.assertFalse((root/'unwanted.txt').exists())
            self.assertEqual(json.loads((root/'analysis.ipynb').read_text()),notebook(s))
            plan,_=review(root,'spec.json','later.ipynb')
            (root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.ipynb').exists())
