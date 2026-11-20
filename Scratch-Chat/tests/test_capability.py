"""Run: python -m unittest discover -s tests -p test_capability.py -v"""
import json
from pathlib import Path
import tempfile
import unittest
from capability.bpe import ByteBPE
from capability.corpus import prepare, fingerprint


class TokenizerTests(unittest.TestCase):
    def test_bytes_unambiguous(self):
        a = ['hello hello hello', 'a café 🌌 привет 你好!','\t  \n🙂🙂🙂']
        tok = ByteBPE.train(a, merges=80)
        for text in a + ['abc_0123 @#$ 🧠漢字', '<|eos|> literal user text']:
            self.assertEqual(tok.decode(tok.encode(text)), text)
        self.assertLess(len(tok.encode('hello hello hello')), len('hello hello hello'))

    def test_file_format(self):
        with tempfile.TemporaryDirectory() as td:
            tok = ByteBPE.train(['blue bear blue bear'], merges=25)
            file = Path(td) / 'model.json'
            tok.save(file)
            loaded = ByteBPE.load(file)
            self.assertEqual(tok.encode('blue bear'), loaded.encode('blue bear'))
            self.assertEqual(tok.special, loaded.special)

    def test_no_merges_still_lossless(self):
        tok = ByteBPE([])
        self.assertEqual(tok.decode(tok.encode('a\r\n文字 🌍')), 'a\r\n文字 🌍')


class CorpusTests(unittest.TestCase):
    def test_provenance_dedup_and_group_boundaries(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records = [
                {'text':'Some distinct original document number '+str(i)+' with sufficient length.',
                 'group':f'book-{i//2}'} for i in range(30)
            ]
            records.append(records[0])
            (root/'a.jsonl').write_text('\n'.join(json.dumps(item) for item in records), encoding='utf-8')
            (root/'manifest.json').write_text(json.dumps({'sources':[
                {'path':'a.jsonl','source':'Test data','license':'CC0', 'permission_to_train':True}
            ]}), encoding='utf-8')
            report = prepare(root/'manifest.json',root/'prepared')
            self.assertEqual(report['records']['exact_duplicates'], 1)
            self.assertEqual(report['records']['unique'], 30)
            grouped = {}
            digests = set()
            for split in ['train','validation','test']:
                for line in (root/'prepared'/f'{split}.jsonl').read_text().splitlines():
                    row = json.loads(line)
                    self.assertNotIn(row['sha256'], digests)
                    digests.add(row['sha256'])
                    grouped.setdefault(row['group'], set()).add(split)
            self.assertTrue(all(len(s)==1 for s in grouped.values()))
            out2 = root/'again'
            prepare(root/'manifest.json',out2)
            for split in ['train','validation','test']:
                self.assertEqual((root/'prepared'/f'{split}.jsonl').read_bytes(),
                                 (out2/f'{split}.jsonl').read_bytes())

    def test_reject_unlicensed_corpus(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'a.txt').write_text('Hello world.')
            (root/'manifest.json').write_text(json.dumps({'sources':[
                {'path':'a.txt', 'source':'unknown','license':'unknown', 'permission_to_train':False}
            ]}))
            with self.assertRaisesRegex(ValueError, 'permission_to_train'):
                prepare(root/'manifest.json',root/'prepared')

    def test_chat_fields_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record={'messages':[{'role':'user','content':'Hello'}, {'role':'assistant','content':'Hi'}]}
            (root/'a.jsonl').write_text(json.dumps(record)+'\n', encoding='utf-8')
            (root/'manifest.json').write_text(json.dumps({'sources':[
                {'path':'a.jsonl','source':'Author', 'license':'CC0','permission_to_train':True}
            ]}))
            prepare(root/'manifest.json',root/'prepared')
            all_rows=[]
            for split in ('train','validation','test'):
                all_rows += [json.loads(x) for x in (root/'prepared'/f'{split}.jsonl').read_text().splitlines()]
            self.assertEqual(all_rows[0]['kind'],'chat')
            self.assertIn('<|assistant|>',all_rows[0]['text'])
            self.assertEqual(all_rows[0]['messages'],record['messages'])

if __name__ == '__main__':
    unittest.main()
