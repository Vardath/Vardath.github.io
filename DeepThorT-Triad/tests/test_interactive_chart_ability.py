import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from deepthort_local.interactive_chart import review,execute,CORE_JS,SCRIPT,STYLE,hash_source

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__();self.tags=[];self.scripts=[];self.active=None
    def handle_starttag(self,tag,attrs):
        self.tags.append((tag,dict(attrs)))
        if tag=='script':self.scripts.append('');self.active=len(self.scripts)-1
    def handle_data(self,data):
        if self.active is not None:self.scripts[self.active]+=data
    def handle_endtag(self,tag):
        if tag=='script':self.active=None

class InteractiveChartTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.csv.write_text('Month,A,B\n"<script>alert(1)</script>",-2,4\nFeb,3,0\nMar,0,5\n',encoding='utf-8')
        self.data={'csv':'data.csv','delimiter':',','type':'bar','title':'A < B & results','x':'Month','series':['A','B'],'y_label':'Value'}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_embedded_svg_data_and_safe_fixed_script(self):
        original=self.csv.read_bytes();plan,preview=review(self.root,'spec.json','out.html');r=execute(self.root,plan)
        p=Inspect();p.feed((self.root/'out.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.scripts),2);self.assertEqual(p.scripts[1],SCRIPT);self.assertNotIn('<',p.scripts[0])
        data=json.loads(p.scripts[0]);self.assertEqual(data['x'],preview['exact_chart_data']['x'])
        marks=[a for t,a in p.tags if 'data-series' in a]
        self.assertEqual(len(marks),6);self.assertEqual(marks[0]['data-x'],'<script>alert(1)</script>')
        self.assertFalse(any(t=='img' or any(k.startswith('on') for k in a) for t,a in p.tags))
        csp=next(a['content'] for t,a in p.tags if t=='meta' and a.get('http-equiv')=='Content-Security-Policy')
        self.assertIn(hash_source(SCRIPT),csp);self.assertIn(hash_source(STYLE),csp)
        self.assertEqual(r['marks'],6);self.assertEqual(self.csv.read_bytes(),original)
    def test_actual_javascript_point_selection(self):
        script=CORE_JS+'''
const assert=require('node:assert/strict');
const d={names:['A','B'],x:['one','two'],series:{A:['1','2'],B:['0','-4']}};
assert.deepEqual(pointState(d,1,1,[true,false]),{name:'B',row:1,x:'two',y:'-4',visible:false});
assert.deepEqual(pointState(d,0,0,[true,false]),{name:'A',row:0,x:'one',y:'1',visible:true});
assert.equal(pointState(d,2,0,[true,false]),null);
assert.equal(pointState(d,1,-1,[true,false]),null);
'''
        result=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_missing_and_invalid_data_refused(self):
        self.data['series']=['missing'];self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','out.html')
        self.data['series']=['A'];self.data['type']='scatter';self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','out.html')
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'spec.json','out.html');out=self.root/'out.html';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.csv.write_text('Changed\n',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
