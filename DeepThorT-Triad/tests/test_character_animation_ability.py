import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import character_animation as m
from deepthort_local.texture_pixels import encode
from deepthort_local.action_guards import snapshot_file

class CharacterAnimationTests(unittest.TestCase):
    def setUp(self):
        self.spec={'character_name':'Hero','artwork':'art.png','mask':'mask.png','background':'bg.png',
            'fps':24,'frames':3,'parts':[{'name':'body','rect':[0,0,1,2],'keys':[[0,0,0],[2,2,0]]},
                {'name':'head','rect':[1,0,1,2],'keys':[[0,1,0],[2,3,0]]}]}
        self.red=bytes([220,10,20]);self.blue=bytes([30,40,200])
        self.raws=[encode(2,2,'RGB',(self.red+self.blue)*2),encode(2,2,'L',bytes([255,255,255,0])),
            encode(4,2,'RGB',bytes(24))]
    def test_independent_part_motion_preserves_exact_art(self):
        out,r=m.compose(self.raws,self.spec)
        self.assertEqual(bytes(out[:12]),self.red+self.blue+bytes(6))
        self.assertEqual(bytes(out[24:36]),bytes(3)+self.red+self.blue+bytes(3))
        self.assertEqual(bytes(out[48:60]),bytes(6)+self.red+self.blue)
        self.assertTrue(r['same_source_part_pixels_used'])
        self.assertFalse(r['neural_pose_generation'])
    def test_reject_uncovered_overlap_and_out_of_canvas(self):
        s=dict(self.spec,parts=self.spec['parts'][:1])
        with self.assertRaises(ValueError):m.assets(self.raws,s)
        s=dict(self.spec,parts=[self.spec['parts'][0],dict(self.spec['parts'][1],rect=[0,0,1,2])])
        with self.assertRaises(ValueError):m.assets(self.raws,s)
        s=dict(self.spec,parts=[self.spec['parts'][0],dict(self.spec['parts'][1],keys=[[0,1,0],[2,4,0]])])
        with self.assertRaises(ValueError):m.assets(self.raws,s)
    def test_review_execute_and_changed_art_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            for key,raw in zip(('artwork','mask','background'),self.raws):(root/self.spec[key]).write_bytes(raw)
            (root/'spec.json').write_text(json.dumps(self.spec),encoding='utf8')
            for n in ('ff','fp'):(root/n).write_bytes(n.encode())
            tools=tuple(snapshot_file(root/n) for n in ('ff','fp'))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'encode_verified',return_value=b'fixture') as codec:
                plan,_=m.review(root,'spec.json','out.mp4')
                result=m.execute(root,plan)
                self.assertEqual(result['status'],'consistent_character_cutout_frames_verified')
                self.assertEqual(codec.call_args.args[1:4],((4,2),24,3))
                plan,_=m.review(root,'spec.json','other.mp4')
                (root/'art.png').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.mp4').exists())
if __name__=='__main__':unittest.main()
