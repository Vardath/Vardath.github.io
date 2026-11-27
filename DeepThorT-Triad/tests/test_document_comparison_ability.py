import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.document_comparison import review,execute,compare_lines
from deepthort_local.document_conversion import review as conversion_review,execute as convert

class DocumentComparisonTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve()
        self.a=self.root/'before.txt';self.b=self.root/'after.txt'
        self.a.write_bytes(b'Keep\nOld value\nRemove me\nAnchor\n')
        self.b.write_bytes(b'Keep\nNew value\nAnchor\nAdded\n')
    def test_real_changes_and_sources_preserved(self):
        old=self.a.read_bytes();new=self.b.read_bytes()
        receipt=execute(self.root,review(self.root,'before.txt','after.txt','diff.json'))
        report=json.loads((self.root/'diff.json').read_text('utf-8'))
        self.assertFalse(receipt['same_extracted_text'])
        self.assertEqual(receipt['counts']['removed_lines'],2)
        self.assertEqual(receipt['counts']['added_lines'],2)
        self.assertEqual(receipt['counts']['unchanged_lines'],2)
        self.assertEqual(report['changes'][0]['before_text'],['Old value','Remove me'])
        self.assertEqual(report['changes'][0]['after_text'],['New value'])
        self.assertEqual(self.a.read_bytes(),old);self.assertEqual(self.b.read_bytes(),new)
        self.assertFalse(report['full_document_equivalence_verified'])
    def test_cross_format_equality_not_byte_equality(self):
        convert(self.root,conversion_review(self.root,'before.txt','before.docx'))
        receipt=execute(self.root,review(self.root,'before.txt','before.docx','diff.json'))
        self.assertTrue(receipt['same_extracted_text'])
        self.assertFalse(receipt['same_file_bytes'])
    def test_stale_excluded_and_existing_output(self):
        plan=review(self.root,'before.txt','after.txt','diff.json')
        (self.root/'diff.json').write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual((self.root/'diff.json').read_bytes(),b'keep')
        (self.root/'diff.json').unlink();self.b.write_bytes(b'changed')
        with self.assertRaises(ValueError):execute(self.root,plan)
        with self.assertRaises(ValueError):review(self.root,'before.txt','after.txt','../diff.json')
        with self.assertRaises(ValueError):review(self.root,'before.txt','after.txt','diff.json',['after.txt'])
        with self.assertRaises(ValueError):review(self.root,'before.txt','before.txt','diff.json')
    def test_bounded_diff_and_exact_whitespace(self):
        with self.assertRaises(ValueError):compare_lines(['x']*2000,['y']*2000)
        counts,changes=compare_lines(['x '],['x'])
        self.assertEqual(counts['replace_blocks'],1)
        self.assertEqual(changes[0]['before_text'],['x '])
