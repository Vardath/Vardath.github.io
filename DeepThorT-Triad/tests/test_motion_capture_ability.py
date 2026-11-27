import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local import motion_capture as m
from deepthort_local.action_guards import snapshot_file

SPEC={'video':'clip.mp4','start_frame':0,'end_frame':3,'radius':2,'max_error':0,
      'markers':[{'name':'left','box':[2,2,4,4]},{'name':'right','box':[12,8,4,4]}]}
SIZE=(24,18)
def frames(lost=False):
    w,h=SIZE;out=[]
    for i in range(3):
        a=bytearray(w*h*3)
        for j,(x,y) in enumerate(((2+i,2),(12,8+i))):
            if lost and i==2 and j==1:continue
            for yy in range(4):
                for xx in range(4):
                    value=30+10*(yy*4+xx)
                    k=((y+yy)*w+x+xx)*3
                    a[k:k+3]=bytes((value,20,10) if j==0 else (10,20,value))
        out.append(bytes(a))
    return b''.join(out)

class CaptureTests(unittest.TestCase):
    def test_synchronised_centres_and_time(self):
        r=m.capture(frames(),SIZE,SPEC,24)
        self.assertTrue(r['complete_interval']);self.assertIsNone(r['stop'])
        self.assertEqual(r['samples'][2]['markers'][0]['center_xy'],[5.5,3.5])
        self.assertEqual(r['samples'][2]['markers'][1]['center_xy'],[13.5,11.5])
        self.assertAlmostEqual(r['samples'][2]['time_seconds'],2/24)
        self.assertFalse(r['depth_recovered'])
    def test_loss_and_invalid_markers(self):
        r=m.capture(frames(True),SIZE,SPEC,24)
        self.assertFalse(r['complete_interval']);self.assertEqual(len(r['samples']),2)
        self.assertEqual(r['stop']['markers'],['right'])
        for markers in ([SPEC['markers'][0],dict(SPEC['markers'][0],name='same-box')],
                        [SPEC['markers'][0],dict(SPEC['markers'][1],name='LEFT')]):
            with self.assertRaises(ValueError):m.checked(dict(SPEC,markers=markers))
    def test_review_and_source_guards(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'clip.mp4').write_bytes(b'fixture')
            (root/'spec.json').write_text(json.dumps(SPEC),encoding='utf8')
            for n in ('ff','fp'):(root/n).write_bytes(n.encode())
            tools=tuple(snapshot_file(root/n) for n in ('ff','fp'))
            with patch.object(m,'installed',return_value=tools),patch.object(m,'probe',return_value={'width':24,'height':18,'fps':24,'frames':3}),patch.object(m,'decode',return_value=frames()):
                plan,_=m.review(root,'spec.json','out.json')
                self.assertTrue(m.execute(root,plan)['complete_interval'])
                self.assertEqual(len(json.loads((root/'out.json').read_text())['samples']),3)
                with self.assertRaises(ValueError):m.execute(root,plan)
                plan,_=m.review(root,'spec.json','other.json');(root/'clip.mp4').write_bytes(b'changed')
                with self.assertRaises(ValueError):m.execute(root,plan)
                self.assertFalse((root/'other.json').exists())
if __name__=='__main__':unittest.main()
