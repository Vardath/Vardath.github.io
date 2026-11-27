import io,json,tempfile,unittest,zipfile
from pathlib import Path
from deepthort_local import audio_plugin as m

class PluginTests(unittest.TestCase):
    def spec(self):return {'name':'JANUS Gain','gain_db':0,'balance':0,'ceiling':.8}
    def test_reference_math(self):
        s=self.spec()
        self.assertEqual(m.reference(s,.25,-.5),[.25,-.5])
        self.assertEqual(m.reference(s,1,-1),[.8,-.8])
        self.assertEqual(m.reference(dict(s,balance=1),.5,.5),[0,.5])
        self.assertEqual(m.reference(dict(s,balance=-1),.5,.5),[.5,0])
        self.assertAlmostEqual(m.reference(dict(s,gain_db=6),.2,0)[0],.2*10**.3)
    def test_source_and_bounds(self):
        src=m.source(self.spec())
        for token in (b'desc:JANUS Gain',b'slider1:0.00',b'@sample',b'spl0 = max',b'spl1 = max'):
            self.assertIn(token,src)
        for change in ({'name':'Bad\n@init'},{'gain_db':float('nan')},{'balance':2},{'ceiling':0},{'gain_db':.001}):
            with self.assertRaises(ValueError):m.source(dict(self.spec(),**change))
    def test_verified_bundle_and_stale_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();p=root/'spec.json';p.write_text(json.dumps(self.spec()),encoding='utf8')
            plan,_=m.review(root,'spec.json','effect.zip')
            result=m.execute(root,plan)
            self.assertFalse(result['native_host_verified'])
            with zipfile.ZipFile(root/'effect.zip') as z:
                self.assertEqual(z.read('JANUS-effect.jsfx'),m.source(self.spec()))
                self.assertEqual(json.loads(z.read('PLUGIN.json'))['source_sha256'],result['source_sha256'])
            with self.assertRaises(ValueError):m.execute(root,plan)
            plan,_=m.review(root,'spec.json','other.zip')
            p.write_text(json.dumps(dict(self.spec(),gain_db=1)),encoding='utf8')
            with self.assertRaises(ValueError):m.execute(root,plan)
            self.assertFalse((root/'other.zip').exists())

if __name__=='__main__':unittest.main()
