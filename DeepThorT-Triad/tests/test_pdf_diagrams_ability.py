import io
import json
import tempfile
import unittest
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from deepthort_local.pdf_diagrams import analyze,review,execute,checked

def fixture():
    stream=io.BytesIO();c=Canvas(stream,pagesize=(300,200))
    c.rect(20,100,80,40);c.drawString(35,115,'JANUS')
    c.rect(180,100,80,40);c.drawString(195,115,'Granite')
    c.line(100,120,180,120);c.line(5,5,15,15)
    c.showPage();c.save();return stream.getvalue()
class DiagramTests(unittest.TestCase):
    def test_vector_graph(self):
        r=analyze(fixture(),[1]);page=r['pages'][0]
        self.assertEqual([n['label'] for n in page['nodes']],['JANUS','Granite'])
        self.assertEqual(len(page['connectors']),1)
        self.assertIsNone(page['connectors'][0]['direction']);self.assertFalse(r['semantic_verification'])
    def test_bounds(self):
        for p in ([1,1],[0],[],[True]):
            with self.assertRaises(ValueError):checked({'document':'a.pdf','pages':p})
        with self.assertRaises(ValueError):analyze(fixture(),[2])
    def test_exact_source_and_new_output(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=fixture();(root/'a.pdf').write_bytes(raw)
            (root/'spec.json').write_text(json.dumps({'document':'a.pdf','pages':[1]}),encoding='utf-8')
            plan,_=review(root,'spec.json','graph.json')
            self.assertEqual(execute(root,plan)['connectors'],1)
            self.assertEqual(json.loads((root/'graph.json').read_text()),analyze(raw,[1]))
            plan,_=review(root,'spec.json','later.json')
            (root/'a.pdf').write_bytes(raw+b'changed')
            with self.assertRaises(ValueError):execute(root,plan)
            self.assertFalse((root/'later.json').exists())
