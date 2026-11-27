import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.website_crawling import crawl,checked,robots_policy,review,execute
from deepthort_local.webpage_retrieval import extract

HOST='https://example.org'
SPEC={'seed':HOST+'/docs/','path_prefix':'/docs/','max_pages':3,'max_depth':2}
class Fixture:
    def __init__(self):self.now=0;self.calls=[]
    def clock(self):return self.now
    def sleep(self,s):self.now+=s
    def fetch(self,url,approved,cancelled):
        self.calls.append(url)
        if url.endswith('/robots.txt'):return extract(url,b'User-agent: *\nDisallow: /docs/private*\nCrawl-delay: 3','text/plain','utf-8')
        if url==SPEC['seed']:
            body=b'<p>Index</p><a href="/docs/private">Denied</a><a href="/docs/a">A</a><a href="https://example.net/docs/">External</a><a href="/other">Other</a><a href="/docs/a?x=1">Query</a><a href="/docs/%2e%2e/x">Escape</a>'
        elif url.endswith('/a'):body=b'<p>A</p><a href="/docs/b">B</a><a href="/docs/">Cycle</a>'
        else:body=b'<p>B</p><a href="/docs/c">Too deep</a>'
        return extract(url,body,'text/html','utf-8')
    def run(self,s,approved):return crawl(s,approved=approved,retrieve=self.fetch,clock=self.clock,sleep=self.sleep)
class CrawlTests(unittest.TestCase):
    def test_real_static_link_traversal(self):
        f=Fixture();r=f.run(SPEC,True)
        self.assertEqual(f.calls,[HOST+'/robots.txt',HOST+'/docs/',HOST+'/docs/a',HOST+'/docs/b'])
        self.assertEqual(len(r['pages']),3);self.assertEqual(r['robots_blocked'][0]['url'],HOST+'/docs/private')
        self.assertEqual(f.now,9);self.assertFalse(r['external_links_followed'])
    def test_robots_conservative_and_scope(self):
        allow,delay=robots_policy('User-agent: *\nDisallow: /docs/*/secret$\nAllow: /docs/a/secret\nCrawl-delay: 4')
        self.assertFalse(allow('/docs/a/secret'));self.assertTrue(allow('/docs/a/secret-more'));self.assertEqual(delay,4)
        for text in ('not robots','User-agent: *\nDisallow: /%2f','User-agent: *\nCrawl-delay: 60','User-agent: *\nRequest-rate: 1/60'):
            with self.assertRaises(ValueError):robots_policy(text)
        for s in (dict(SPEC,seed=HOST+'/other'),dict(SPEC,path_prefix='/docs'),dict(SPEC,max_pages=6),dict(SPEC,seed=HOST+'/docs/%2f')):
            with self.assertRaises(ValueError):checked(s)
    def test_consent_and_robots_failure(self):
        f=Fixture()
        with self.assertRaises(ValueError):f.run(SPEC,False)
        self.assertEqual(f.calls,[])
        def fail(*a,**kw):raise OSError('robots unavailable')
        with self.assertRaises(OSError):crawl(SPEC,approved=True,retrieve=fail)
    def test_review_publish_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'spec.json').write_text(json.dumps(SPEC))
            plan,_=review(root,'spec.json','crawl.json');f=Fixture();r=execute(root,plan,run=f.run)
            self.assertEqual(r['pages'],3)
            self.assertFalse(json.loads((root/'crawl.json').read_text())['site_completeness_verified'])
            with self.assertRaises(ValueError):execute(root,plan,run=f.run)

class DownloadTests(unittest.TestCase):
    def fixture(self):
        import hashlib
        from deepthort_local.webpage_elements import extract_elements
        data=b'%PDF-1.7\nfixture'
        url=HOST+'/docs/'
        html=b'<html><body><a href="/docs/file.pdf">Download</a></body></html>'
        report=extract_elements(url,html,'text/html','utf-8')
        anchor=next(x for x in report['elements'] if x['tag']=='a')
        spec={'inspection':'inspection.json','locator':anchor['locator'],'path_prefix':'/docs/',
              'destination':HOST+'/docs/file.pdf','mime':'application/pdf','max_bytes':100,
              'expected_sha256':hashlib.sha256(data).hexdigest()}
        return spec,report,data
    def test_reviewed_download_bundle_and_scope(self):
        import zipfile
        from deepthort_local.website_file_download import review,execute,run,checked
        from deepthort_local.webpage_elements import extract_elements
        spec,report,data=self.fixture();f=Fixture()
        def retrieve(url,**kw):
            f.calls.append(url)
            if url.endswith('/robots.txt'):return extract(url,b'User-agent: *\nDisallow: /private','text/plain','utf-8')
            return report
        def download(s,**kw):
            f.calls.append(s['destination']);return data
        def runner(s,evidence,approved):
            return run(s,evidence,approved=approved,retrieve=retrieve,download=download,clock=f.clock,sleep=f.sleep)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            (root/'spec.json').write_text(json.dumps(spec));(root/'inspection.json').write_text(json.dumps(report))
            plan,_=review(root,'spec.json','file.zip')
            result=execute(root,plan,runner=runner)
            self.assertEqual(f.calls,[HOST+'/robots.txt',HOST+'/docs/',spec['destination']])
            with zipfile.ZipFile(root/'file.zip') as z:
                self.assertEqual(z.read('payload.bin'),data)
                receipt=json.loads(z.read('receipt.json'));self.assertTrue(receipt['expected_digest_matched'])
                self.assertFalse(receipt['browser_used'])
            self.assertEqual(result['payload_sha256'],spec['expected_sha256'])
            with self.assertRaises(ValueError):execute(root,plan,runner=runner)
            with self.assertRaises(ValueError):review(root,'spec.json','file.zip')
            (root/'spec.json').write_text(json.dumps(dict(spec,destination=HOST+'/outside/file.pdf')))
            with self.assertRaises(ValueError):review(root,'spec.json','other.zip')
    def test_download_refusals(self):
        from deepthort_local.website_file_download import run,selection
        from deepthort_local.website_control_selection import selected
        spec,report,data=self.fixture();evidence=selected(selection(spec),report);f=Fixture()
        def retrieve(url,**kw):
            if url.endswith('/robots.txt'):return extract(url,b'User-agent: *\nDisallow: /docs/file.pdf','text/plain','utf-8')
            self.fail('Forbidden source read')
        with self.assertRaises(ValueError):run(spec,evidence,approved=True,retrieve=retrieve,clock=f.clock,sleep=f.sleep)
        def allowed(url,**kw):
            if url.endswith('/robots.txt'):return extract(url,b'User-agent: *\nDisallow: /private','text/plain','utf-8')
            return report
        with self.assertRaises(ValueError):run(spec,evidence,approved=True,retrieve=allowed,download=lambda *a,**k:b'wrong',clock=f.clock,sleep=f.sleep)
        with self.assertRaises(ValueError):run(spec,evidence,approved=False,retrieve=allowed)

class UploadTests(unittest.TestCase):
    def test_reviewed_multipart_and_stale_guard(self):
        import hashlib
        from deepthort_local.website_file_upload import review,execute,multipart
        s={'url':HOST+'/upload','file':'source.txt','field':'document','filename':'public.txt'}
        raw=b'approved public document'
        calls=[]
        def send(spec,data,approved):
            self.assertTrue(approved);self.assertEqual(data,raw)
            boundary,body=multipart(spec,data);self.assertIn(raw,body)
            self.assertIn(b'filename="public.txt"',body);self.assertNotIn(b'source.txt',body)
            self.assertTrue(body.endswith(('--'+boundary+'--\r\n').encode()))
            calls.append(spec)
            return {'http_status':201,'response_bytes':0,'response_sha256':hashlib.sha256(b'').hexdigest()}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();(root/'spec.json').write_text(json.dumps(s));(root/'source.txt').write_bytes(raw)
            plan,preview=review(root,'spec.json','receipt.json')
            self.assertEqual(preview['file_sha256'],hashlib.sha256(raw).hexdigest())
            (root/'source.txt').write_bytes(b'changed')
            with self.assertRaises(ValueError):execute(root,plan,sender=send)
            self.assertEqual(calls,[])
            (root/'source.txt').write_bytes(raw)
            plan,_=review(root,'spec.json','receipt.json');execute(root,plan,sender=send)
            receipt=json.loads((root/'receipt.json').read_text())
            self.assertTrue(receipt['http_success']);self.assertFalse(receipt['remote_storage_verified'])
            with self.assertRaises(ValueError):execute(root,plan,sender=send)
            self.assertEqual(len(calls),1)
    def test_upload_refuses_unsafe_scope(self):
        from deepthort_local.website_file_upload import checked,send
        s={'url':HOST+'/upload','file':'source.txt','field':'document','filename':'public.txt'}
        for patch in ({'url':'http://example.org/upload'},{'url':HOST+'/upload?token=123'},
                      {'filename':'../source.txt'},{'filename':'a.exe'},{'field':'password'},{'file':'source.exe'}):
            with self.assertRaises(ValueError):checked(dict(s,**patch))
        with self.assertRaises(PermissionError):send(s,b'hello',approved=False)

class FormCompletionTests(unittest.TestCase):
    def fixture(self):
        from deepthort_local.webpage_elements import extract_elements
        report=extract_elements(HOST+'/docs/form',b'<form method="post"><input name="title" type="text" required><input name="quantity" type="number" required><input name="password" type="password"><input name="hidden" type="hidden"><input name="disabled" disabled></form>','text/html','utf-8')
        form=next(x for x in report['elements'] if x['tag']=='form')
        title=next(x for x in report['elements'] if x.get('name')=='title')
        spec={'inspection':'inspection.json','form_locator':form['locator'],'path_prefix':'/docs/',
              'fields':[{'locator':title['locator'],'name':'title','value':'A & B'}]}
        return spec,report
    def test_static_form_preparation(self):
        from deepthort_local.website_form_completion import review,execute
        spec,report=self.fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            (root/'spec.json').write_text(json.dumps(spec));(root/'inspection.json').write_text(json.dumps(report))
            plan,preview=review(root,'spec.json','form.json')
            self.assertEqual(preview['urlencoded_preview'],'title=A+%26+B')
            self.assertEqual(preview['required_controls_unmapped'][0]['name'],'quantity')
            self.assertFalse(preview['submitted'])
            execute(root,plan);self.assertEqual(json.loads((root/'form.json').read_text()),preview)
            with self.assertRaises(ValueError):execute(root,plan)
    def test_static_form_rejects_wrong_controls(self):
        from deepthort_local.website_form_completion import prepare
        s,report=self.fixture()
        with self.assertRaises(ValueError):prepare(dict(s,fields=[dict(s['fields'][0],value='')]),report)
        with self.assertRaises(ValueError):prepare(dict(s,fields=[dict(s['fields'][0],name='mismatch')]),report)
        for name in ('password','disabled'):
            row=next(x for x in report['elements'] if x.get('name')==name)
            with self.assertRaises(ValueError):prepare(dict(s,fields=[{'locator':row['locator'],'name':name,'value':'x'}]),report)
        with self.assertRaises(ValueError):prepare(s,dict(report,elements_truncated=True))
