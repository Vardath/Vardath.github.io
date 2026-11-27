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
