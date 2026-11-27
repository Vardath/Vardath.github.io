import csv
import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from deepthort_local.interactive_table import review,execute,CORE_JS,SCRIPT,STYLE,hash_source

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[];self.active=None;self.attrs=[]
    def handle_starttag(self,tag,attrs):
        self.attrs.append((tag,dict(attrs)))
        if tag=='script':self.scripts.append('');self.active=len(self.scripts)-1
    def handle_data(self,data):
        if self.active is not None:self.scripts[self.active]+=data
    def handle_endtag(self,tag):
        if tag=='script':self.active=None

class InteractiveTableTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.csv=self.root/'data.csv';self.spec=self.root/'spec.json'
        self.rows=[['Name','Value'],['<script>alert(1)</script>','<img src=x onerror=alert(1)>'],['Alpha','002'],['Beta','=1+1']]
        with self.csv.open('w',encoding='utf-8',newline='') as f:csv.writer(f).writerows(self.rows)
        self.data={'csv':'data.csv','delimiter':',','columns':['Name','Value'],'title':'A <table> & data','page_size':25}
        self.save()
    def save(self):self.spec.write_text(json.dumps(self.data),encoding='utf-8')
    def test_literal_html_and_csp(self):
        original=self.csv.read_bytes();plan,preview=review(self.root,'spec.json','table.html');r=execute(self.root,plan)
        p=Inspect();p.feed((self.root/'table.html').read_text(encoding='utf-8'))
        self.assertEqual(len(p.scripts),2);self.assertEqual(json.loads(p.scripts[0]),{'columns':self.rows[0],'rows':self.rows[1:]})
        self.assertNotIn('<',p.scripts[0]);self.assertEqual(p.scripts[1],SCRIPT)
        self.assertFalse(any(tag=='img' or any(k.startswith('on') for k in attrs) for tag,attrs in p.attrs))
        csp=next(a['content'] for t,a in p.attrs if t=='meta' and a.get('http-equiv')=='Content-Security-Policy')
        self.assertIn(hash_source(SCRIPT),csp);self.assertIn(hash_source(STYLE),csp);self.assertIn("connect-src 'none'",csp)
        self.assertEqual(r['embedded_data_sha256'],preview['embedded_data_sha256']);self.assertEqual(self.csv.read_bytes(),original)
    def test_actual_javascript_filter_sort_page(self):
        program=CORE_JS+'''
const assert = require('node:assert/strict');
const data={columns:['Name','Value'],rows:[['Beta','2'],['alpha','1'],['ALPHA','3'],['Gamma','2']]};
assert.deepEqual(selectRows(data,'alpha',-1,false,1,25).rows,[['alpha','1'],['ALPHA','3']]);
assert.deepEqual(selectRows(data,'',0,false,1,2).rows,[['alpha','1'],['ALPHA','3']]);
assert.deepEqual(selectRows(data,'',0,true,1,2).rows,[['Gamma','2'],['Beta','2']]);
assert.deepEqual(selectRows(data,'',0,false,9,2).rows,[['Beta','2'],['Gamma','2']]);
assert.equal(selectRows(data,'missing',0,false,9,2).page,1);
assert.equal(data.rows[0][0],'Beta');
'''
        # Allow hosted Windows process-start and scheduling delays; never skip assertions.
        result=subprocess.run(['node','-e',program],capture_output=True,text=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_missing_column_and_bad_page(self):
        self.data['columns']=['missing'];self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','table.html')
        self.data['columns']=['Name'];self.data['page_size']=12;self.save()
        with self.assertRaises(ValueError):review(self.root,'spec.json','table.html')
    def test_stale_and_no_overwrite(self):
        plan,_=review(self.root,'spec.json','table.html');out=self.root/'table.html';out.write_bytes(b'keep')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertEqual(out.read_bytes(),b'keep');out.unlink();self.csv.write_text('Changed\n',encoding='utf-8')
        with self.assertRaises(ValueError):execute(self.root,plan)
        self.assertFalse(out.exists())
