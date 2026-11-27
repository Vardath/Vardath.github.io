import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from deepthort_local.chart_creation import review,execute,render,checked,SVG

class ChartTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.csv.write_text('Month,A,B\nJan,-2,4\nFeb,3,0\nMar,0,5\n',encoding='utf-8')
        self.data={'csv':'data.csv','delimiter':',','type':'bar','title':'A < B & results','x':'Month','series':['A','B'],'y_label':'Value'}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_bar_geometry_and_exact_values(self):
        original=self.csv.read_bytes();plan,preview=review(self.root,'spec.json','out.svg');r=execute(self.root,plan)
        root=ET.parse(self.root/'out.svg').getroot();marks=[n for n in root.iter() if n.get('data-series')]
        self.assertEqual(r['marks'],6);self.assertEqual(r['y_domain'],['-2','5'])
        self.assertEqual([n.get('data-y') for n in marks],['-2','3','0','4','0','5'])
        self.assertTrue(all(float(n.get('height'))>=0 for n in marks))
        self.assertEqual(root.find(SVG+'title').text,self.data['title'])
        self.assertEqual(preview['exact_chart_data']['x'],['Jan','Feb','Mar']);self.assertEqual(self.csv.read_bytes(),original)
    def test_line_and_scatter(self):
        self.data['type']='line';raw,r=render(self.csv.read_bytes(),checked(self.data))
        self.assertEqual(len(list(ET.fromstring(raw).iter(SVG+'polyline'))),2);self.assertEqual(r['marks'],6)
        self.data.update(type='scatter',x='Month',series=['A'])
        raw,r=render(b'Month,A\n1,1\n2,2\n4,3\n',checked(self.data));marks=[n for n in ET.fromstring(raw).iter(SVG+'circle')]
        self.assertEqual(len(marks),3);self.assertGreater(float(marks[2].get('cx'))-float(marks[1].get('cx')),float(marks[1].get('cx'))-float(marks[0].get('cx')))
    def test_reject_missing_and_nonnumeric(self):
        for raw in (b'Month,A,B\nJan,NaN,1\n',b'Month,A,B\nJan,1,2\nJan,3,4\n',b'Month,A,B\nJan,,2\n'):
            self.csv.write_bytes(raw)
            with self.assertRaises(ValueError):review(self.root,'spec.json','out.svg')
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'spec.json','out.svg');out=self.root/'out.svg';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.csv.write_text('Changed\n',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
