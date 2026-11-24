import tempfile,zipfile,unittest
from pathlib import Path
from deepthort_local.media_tools import (classify,validate_attachment,extract_attachment,composed_prompt,
                                         cli_image_args,validate_image_output_path)

class MediaTests(unittest.TestCase):
    def test_text_attachment(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'notes.md';p.write_text('requirements here',encoding='utf8')
            self.assertEqual(classify(p),'text')
            self.assertIn('requirements here',composed_prompt('Build this',[str(p)]))
            with self.assertRaisesRegex(ValueError,'maximum'):
                composed_prompt('x'*7499,[str(p)])
    def test_docx_extraction(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'notes.docx'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('word/document.xml','''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Read this</w:t></w:r></w:p></w:body></w:document>''')
            self.assertEqual(extract_attachment(p),'Read this')
    def test_image_refuses_false_text(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.png';p.write_bytes(b'fake img')
            self.assertEqual(classify(p),'image')
            with self.assertRaisesRegex(RuntimeError,'vision'):
                extract_attachment(p)
    def test_no_path_escape(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):validate_image_output_path(td,'../outside.png')
    def test_image_args_bound(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'model';p.mkdir()
            a=cli_image_args('python',Path(td)/'image.py',p,'A tiny spaceship',Path(td)/'x.png',384,384,10)
            self.assertIn('--prompt',a)
            with self.assertRaisesRegex(ValueError,'Only bounded'):
                cli_image_args('python',Path(td)/'image.py',p,'A',Path(td)/'x.png',1024,1024,10)

if __name__=='__main__':unittest.main()
