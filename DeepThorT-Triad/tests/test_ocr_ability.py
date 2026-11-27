import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from deepthort_local.ocr import checked,parse_tsv,review,execute

HEADER='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
class OCRTests(unittest.TestCase):
    def fixture(self):
        b=io.BytesIO()
        with Image.new('RGB',(600,180),'white') as im:
            font=ImageFont.load_default(size=48)
            ImageDraw.Draw(im).text((30,40),'HELLO WORLD',font=font,fill='black')
            im.save(b,format='PNG')
        return b.getvalue()
    def test_actual_local_recognition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=self.fixture();(root/'image.png').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'image':'image.png','layout':'block'}))
            plan,p=review(root,'spec.json','result.json');r=execute(root,plan)
            result=json.loads((root/'result.json').read_text())
            self.assertEqual(result['text'],'HELLO WORLD')
            self.assertEqual(r['word_count'],2);self.assertFalse(r['recognition_accuracy_verified'])
            self.assertEqual(len(plan['guards']),4);self.assertEqual((root/'image.png').read_bytes(),raw)
    def test_parse_and_blank(self):
        raw=(HEADER+'5\t1\t1\t1\t1\t1\t2\t3\t10\t12\t91.5\tHello\n'+
             '5\t1\t1\t1\t1\t2\t15\t3\t12\t12\t90\tworld\n').encode()
        result=parse_tsv(raw,100,100)
        self.assertEqual(result['text'],'Hello world');self.assertEqual(result['words'][0]['box'],[2,3,10,12])
        self.assertEqual(parse_tsv(HEADER.encode(),100,100)['word_count'],0)
    def test_malformed_and_spec(self):
        with self.assertRaises(ValueError):parse_tsv((HEADER+'5\t1\t1\t1\t1\t1\t99\t3\t10\t12\t91\tHello\n').encode(),100,100)
        with self.assertRaises(ValueError):checked({'image':'a.png','layout':'arbitrary'})
    def test_stale_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();raw=self.fixture();p=root/'image.png';p.write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'image':'image.png','layout':'block'}))
            plan,_=review(root,'spec.json','result.json');out=root/'result.json';out.write_bytes(b'keep')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertEqual(out.read_bytes(),b'keep');out.unlink();p.write_bytes(raw+b'x')
            with self.assertRaises(ValueError):execute(root,plan)
