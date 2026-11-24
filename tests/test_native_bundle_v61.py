import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from deepthort_local.native_bundle import review_bundle, materialize_bundle

def bundle(extra=()):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for path,data in [('test_pe/index/macros.xml',b'<diff/>'),
                          ('test_pe/index/components.xml',b'<diff/>'),
                          ('test_pe/assets/hull.xmf',b'\x00\x01\x02'),
                          ('Preview_MainHull_and_Rock.obj',b'preview'),
                          *extra]:
            z.writestr(path,data)
    return out.getvalue()

class NativeBundleTests(unittest.TestCase):
    def test_materialize_resumes_and_preserves_binary(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            blob=bundle()
            approved=review_bundle(blob,'test_pe',root)
            self.assertEqual(len(approved['files']),3)
            first=materialize_bundle(blob,'test_pe',root,approved)
            self.assertEqual(first['created'],3)
            self.assertEqual((root/'assets/hull.xmf').read_bytes(),b'\x00\x01\x02')
            self.assertFalse((root/'Preview_MainHull_and_Rock.obj').exists())
            again=materialize_bundle(blob,'test_pe',root,approved)
            self.assertEqual(again['created'],0)
            self.assertEqual(again['verified'],3)

    def test_conflict_before_import_never_overwrites(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            blob=bundle()
            approved=review_bundle(blob,'test_pe',root)
            (root/'assets').mkdir()
            (root/'assets/hull.xmf').write_bytes(b'existing')
            with self.assertRaises(ValueError):
                materialize_bundle(blob,'test_pe',root,approved)
            self.assertEqual((root/'assets/hull.xmf').read_bytes(),b'existing')
            self.assertFalse((root/'index').exists())

    def test_reject_unsafe_member_and_changed_approval(self):
        with tempfile.TemporaryDirectory() as t:
            for name in ('test_pe/assets/../escape.xmf','test_pe/assets/CON.xmf','test_pe/assets/a:b.xmf',
                         'other/assets/mesh.xmf','test_pe/assets/HULL.xmf'):
                with self.subTest(name=name),self.assertRaises(ValueError):
                    review_bundle(bundle([(name,b'x')]),'test_pe',t)
            blob=bundle()
            approved=review_bundle(blob,'test_pe',t)
            with self.assertRaises(ValueError):
                materialize_bundle(bundle([('test_pe/assets/other.xmf',b'a')]),'test_pe',t,approved)
            self.assertFalse(any(Path(t).iterdir()))

if __name__=='__main__':
    unittest.main()
