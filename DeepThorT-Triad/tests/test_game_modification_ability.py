import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from deepthort_local import game_modification as tool

class GameModificationTests(unittest.TestCase):
    def spec(self):
        return {'asset':'data/ships.json','mod_id':'ship_balance','edits':[
            {'path':['ships',0,'speed'],'expected':10,'value':20},
            {'path':['ships',0,'enabled'],'expected':False,'value':True}]}
    def raw(self):
        return b'{"ships":[{"speed":10,"enabled":false,"crew":5}],"unrelated":[1,2]}'

    def test_bundle_preserves_other_data(self):
        data,receipt=tool.generate(self.raw(),self.spec())
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(sorted(z.namelist()),['janus-mod-receipt.json','override/data/ships.json'])
            self.assertEqual(json.loads(z.read('override/data/ships.json')),
                {'ships':[{'speed':20,'enabled':True,'crew':5}],'unrelated':[1,2]})
        self.assertTrue(receipt['semantic_rollback_verified'])
        self.assertFalse(receipt['installed'])

    def test_refuses_wrong_types_paths_and_original_values(self):
        for path in ('../ships.json','data/CON.json','data/.secret.json','data/ships.json:ads'):
            s=self.spec();s['asset']=path
            with self.assertRaises(ValueError):tool.generate(self.raw(),s)
        for value in (True,9):
            s=self.spec();s['edits'][0]['expected']=value
            with self.assertRaises(ValueError):tool.generate(self.raw(),s)
        s=self.spec();s['edits'].append(copy.deepcopy(s['edits'][0]))
        with self.assertRaises(ValueError):tool.generate(self.raw(),s)

    def test_review_stale_guard_and_nonoverwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();(root/'data').mkdir();asset=root/'data/ships.json'
            asset.write_bytes(self.raw());(root/'spec.json').write_text(json.dumps(self.spec()))
            plan,_=tool.review(root,'spec.json','mod.zip')
            asset.write_bytes(self.raw()+b' ')
            with self.assertRaises(ValueError):tool.execute(root,plan)
            plan,_=tool.review(root,'spec.json','mod.zip')
            self.assertTrue(tool.execute(root,plan)['source_unchanged'])
            self.assertEqual(asset.read_bytes(),self.raw()+b' ')
            with self.assertRaises(ValueError):tool.execute(root,plan)

if __name__=='__main__':unittest.main()
