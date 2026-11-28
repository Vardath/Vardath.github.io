import io,json,struct,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import model_format_conversion as m
from deepthort_local import model_format_export as reverse

T={'layer.weight':('F32',(2,2),struct.pack('<4f',1,-2,3.5,0.125)),
   'layer.bias':('F16',(2,),struct.pack('<2e',.5,-.25)),
   'counter':('I64',(),struct.pack('<q',42))}

class FormatConversionTests(unittest.TestCase):
    def test_exact_two_direction_roundtrip(self):
        saf=m.write_safetensors(T);npz,r=m.convert(saf,'npz')
        self.assertEqual(m.read_npz(npz),T)
        back,r2=m.convert(npz,'safetensors')
        self.assertEqual(m.read_safetensors(back),T)
        self.assertTrue(r2['tensor_bytes_exact']);self.assertFalse(r2['architecture_converted'])
    def test_bad_offsets_metadata_and_pickle_rejected(self):
        for h in ({'x':{'dtype':'F32','shape':[1],'data_offsets':[1,5]}},
                  {'__metadata__':{'x':'y'},'x':{'dtype':'F32','shape':[1],'data_offsets':[0,4]}}):
            b=json.dumps(h).encode();raw=struct.pack('<Q',len(b))+b+b'12345'
            with self.assertRaises(ValueError):m.read_safetensors(raw)
        h=b"{'descr': '|O', 'fortran_order': False, 'shape': (1,)}"
        h+=b' '*((-(10+len(h)+1))%64)+b'\n'
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('x.npy',b'\x93NUMPY\x01\x00'+struct.pack('<H',len(h))+h+b'x')
        with self.assertRaises(ValueError):m.read_npz(buf.getvalue())
    def test_project_guards_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=m.write_npz(T);(root/'weights.npz').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'weights':'weights.npz'}),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.safetensors')
            self.assertTrue(m.execute(root,plan)['tensor_bytes_exact'])
            self.assertEqual((root/'weights.npz').read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            (root/'spec.json').write_text(json.dumps({'weights':'out.safetensors'}),encoding='utf8')
            plan,_=reverse.review(root,'spec.json','out.npz')
            self.assertEqual(reverse.execute(root,plan)['tensor_count'],3)
            plan,_=reverse.review(root,'spec.json','other.npz');(root/'out.safetensors').write_bytes(b'changed')
            with self.assertRaises(ValueError):reverse.execute(root,plan)
            self.assertFalse((root/'other.npz').exists())
if __name__=='__main__':unittest.main()
