import io,json,struct,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import model_quantisation as m
from deepthort_local import model_format_conversion as formats

T={'weight':('F32',(4,),struct.pack('<4f',-1,0,.3,1)),
   'bias':('F16',(2,),struct.pack('<2e',.25,-.5)),
   'zero':('F16',(2,),struct.pack('<2e',0,0))}
SPEC={'weights':'weights.safetensors','tensors':['weight','zero'],'max_abs_error':.01}

class QuantisationTests(unittest.TestCase):
    def test_stored_quantized_weights_and_scale(self):
        raw=formats.write_safetensors(T);payload,r=m.bundle(raw,SPEC)
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            q=formats.read_safetensors(z.read('quantized.safetensors'))
            self.assertEqual(json.loads(z.read('quantization.json')),r)
        self.assertEqual(q['bias'],T['bias'])
        self.assertEqual(struct.unpack('4b',q['weight'][2]),(-127,0,38,127))
        self.assertEqual(q['zero'][2],b'\0\0')
        self.assertEqual(r['quantized_tensors']['zero']['scale'],1.)
        self.assertLess(r['output_tensor_bytes'],r['source_tensor_bytes'])
        self.assertTrue(r['weight_error_verified']);self.assertFalse(r['model_accuracy_verified'])
    def test_error_bound_missing_and_nonfinite(self):
        raw=formats.write_safetensors(T)
        with self.assertRaises(ValueError):m.bundle(raw,dict(SPEC,max_abs_error=0))
        with self.assertRaises(ValueError):m.bundle(raw,dict(SPEC,tensors=['missing']))
        bad={'weight':('F32',(1,),struct.pack('<f',float('nan')))}
        with self.assertRaises(ValueError):m.bundle(formats.write_safetensors(bad),dict(SPEC,tensors=['weight']))
    def test_exact_source_and_new_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=formats.write_safetensors(T)
            (root/'weights.safetensors').write_bytes(raw);(root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            plan,_=m.review(root,'spec.json','out.zip')
            self.assertTrue(m.execute(root,plan)['source_unchanged'])
            self.assertEqual((root/'weights.safetensors').read_bytes(),raw)
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.zip');(root/'weights.safetensors').write_bytes(b'changed')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.zip').exists())
if __name__=='__main__':unittest.main()
