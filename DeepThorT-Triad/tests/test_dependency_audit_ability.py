import json
import tempfile
import unittest
from pathlib import Path
from deepthort_local.dependency_audit import review,audit

class DependencyAuditTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.req=self.root/'requirements.txt'
        self.req.write_text('Django==4.2.0\nnot-pinned>=2\n',encoding='utf-8')
        (self.root/'package-lock.json').write_text(json.dumps({'lockfileVersion':3,'packages':{
            '':{'name':'private-project'},
            'node_modules/@scope/pkg':{'version':'1.2.3','resolved':'https://private.example/token'},
            'node_modules/a/node_modules/b':{'version':'2.0.0'},
            'node_modules/local':{'link':True}}}),encoding='utf-8')
    def test_scope_and_real_result_parsing(self):
        plan,observed=review(self.root)
        self.assertEqual(observed['omitted'],2)
        self.assertEqual(plan['count'],3)
        def lookup(queries):
            raw=json.dumps(queries)
            self.assertNotIn('private',raw)
            self.assertNotIn('not-pinned',raw)
            self.assertEqual(queries[0],{'package':{'ecosystem':'PyPI','name':'django'},'version':'4.2.0'})
            return {'results':[{'vulns':[{'id':'GHSA-1234-5678-9012'}]}, {}, {}]}
        result=audit(self.root,plan,query=lookup)
        self.assertEqual(result['status'],'advisories_found')
        self.assertEqual(result['findings'][0]['advisories'],['GHSA-1234-5678-9012'])
        self.assertFalse(result['complete_project_security_verified'])
    def test_stale_or_invalid_response(self):
        plan,_=review(self.root)
        with self.assertRaises(ValueError):audit(self.root,plan,query=lambda q:{'results':[]})
        self.req.write_text('Django==4.2.1',encoding='utf-8')
        with self.assertRaises(ValueError):audit(self.root,plan,query=lambda q:self.fail('Stale plan sent data'))
    def test_partial_and_no_known(self):
        plan,_=review(self.root)
        result=audit(self.root,plan,query=lambda q:{'results':[{'next_page_token':'more'},{},{}]})
        self.assertEqual(result['status'],'inconclusive')
        self.assertEqual(result['paginated_results'],1)
        self.req.write_text('Django==4.2.0',encoding='utf-8')
        (self.root/'package-lock.json').unlink()
        plan,_=review(self.root)
        result=audit(self.root,plan,query=lambda q:{'results':[{}]})
        self.assertEqual(result['status'],'no_known_advisories_for_queried_versions')
        self.assertFalse(result['python_transitive_dependencies_verified'])
    def test_changes_during_lookup(self):
        plan,_=review(self.root)
        def lookup(queries):
            self.req.write_text('Django==4.2.9',encoding='utf-8')
            return {'results':[{} for _ in queries]}
        with self.assertRaises(ValueError):audit(self.root,plan,query=lookup)
