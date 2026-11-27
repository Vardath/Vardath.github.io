import io
import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.image_composition import checked,compose,review,execute
from deepthort_local.texture_pixels import decode,image_module

def raw(mode,size,color):
    stream=io.BytesIO()
    with image_module().new(mode,size,color) as im:im.save(stream,format='PNG')
    return stream.getvalue()

def layer(name,x=0,y=0,width=1,height=1,opacity=255):
    return dict(image=name,x=x,y=y,width=width,height=height,opacity=opacity)

def specification():
    return dict(width=3,height=2,background=[0,0,0],
                layers=[layer('red.png',width=2),layer('blue.png',x=1)])

class CompositionTests(unittest.TestCase):
    def test_order_and_placement(self):
        spec=specification()
        out,r=compose([raw('RGB',(1,1),(255,0,0)),raw('RGB',(1,1),(0,0,255))],spec)
        self.assertEqual(decode(out,('RGB',))[3],bytes([255,0,0,0,0,255,0,0,0]+[0]*9))
        self.assertEqual(r['layers'][0]['source_dimensions'],[1,1])
        self.assertFalse(r['visual_quality_verified'])
    def test_alpha_and_opacity(self):
        spec=specification();spec['layers'][1]['opacity']=128
        out,_=compose([raw('RGB',(1,1),(255,0,0)),raw('RGBA',(1,1),(0,0,255,128))],spec)
        self.assertEqual(decode(out,('RGB',))[3][3:6],bytes([191,0,64]))
        out,_=compose([raw('RGB',(1,1),(255,0,0)),raw('RGBA',(1,1),(0,0,255,0))],spec)
        self.assertEqual(decode(out,('RGB',))[3][3:6],bytes([255,0,0]))
    def test_invalid_geometry_and_source(self):
        spec=specification();spec['layers'][1]['width']=3
        with self.assertRaises(ValueError):checked(spec)
        spec=specification();spec['layers'][1]['image']='RED.PNG'
        with self.assertRaises(ValueError):checked(spec)
        with self.assertRaises(ValueError):compose([raw('RGB',(1,1),(0,0,0)),raw('P',(1,1),0)],specification())
    def test_review_publication_and_stale_second_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            a=raw('RGB',(1,1),(255,0,0));b=raw('RGB',(1,1),(0,0,255))
            (root/'red.png').write_bytes(a);(root/'blue.png').write_bytes(b)
            (root/'spec.json').write_text(json.dumps(specification()))
            plan,preview=review(root,'spec.json','out.png')
            self.assertEqual(len(plan['guards']),3)
            r=execute(root,plan);self.assertEqual(r['pixel_sha256'],preview['pixel_sha256'])
            self.assertEqual((root/'red.png').read_bytes(),a);self.assertEqual((root/'blue.png').read_bytes(),b)
            with self.assertRaises(ValueError):execute(root,plan)
            (root/'out.png').unlink();(root/'blue.png').write_bytes(a)
            with self.assertRaises(ValueError):execute(root,plan)
