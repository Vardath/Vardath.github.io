import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.code_refactoring import refactor,review,execute
S={'document':'source.py','function':'compute','old_name':'total','new_name':'result'}
RAW='total = 100\n# total comment\ndef compute(x):\n    total = x + 1\n    text = "total"\n    return total + len("é")\ndef other():\n    return total\n'.encode()
class RefactorTests(unittest.TestCase):
    def test_scoped_exact_edits(self):
        output,r=refactor(RAW,S)
        self.assertEqual(output,RAW.replace(b'    total = x',b'    result = x').replace(b'    return total +',b'    return result +'))
        self.assertEqual(r['changed_occurrences'],2)
        self.assertTrue(r['ast_comparison_verified']);self.assertFalse(r['runtime_equivalence_verified'])
    def test_unsafe_bindings_and_collision(self):
        for body in ('    global total\n    total = x\n','    total = x\n    return locals()\n',
                     '    total = x\n    result = 1\n','    total = x\n    return [total for x in range(2)]\n',
                     '    total = x\n    def nested(): return total\n'):
            with self.subTest(body=body),self.assertRaises(ValueError):
                refactor(('def compute(x):\n'+body).encode(),S)
    def test_review_copy_and_stale_source(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);doc=root/'source.py';doc.write_bytes(RAW)
            (root/'spec.json').write_text(json.dumps(S),encoding='utf-8')
            plan,preview=review(root,'spec.json','new.py')
            self.assertEqual(preview['reviewed_rename']['changed_occurrences'],2)
            self.assertTrue(execute(root,plan)['source_unchanged'])
            self.assertEqual((root/'new.py').read_bytes(),refactor(RAW,S)[0]);self.assertEqual(doc.read_bytes(),RAW)
            plan,_=review(root,'spec.json','later.py');doc.write_bytes(RAW+b'\n')
            with self.assertRaises(ValueError):execute(root,plan)
