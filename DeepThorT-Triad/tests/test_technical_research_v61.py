import tempfile
import unittest
from pathlib import Path
from deepthort_local.technical_research import ResearchStore,research_recovery,sha,ResearchError,Text

class Council:
    def __init__(self,answers):self.answers=iter(answers);self.prompts=[]
    def _run(self,client,**kw):
        self.prompts.append(kw['prompt']);return next(self.answers)

class ResearchTests(unittest.TestCase):
    def test_cache_and_unknown_key(self):
        with tempfile.TemporaryDirectory() as t:
            s=ResearchStore(Path(t)/'r.sqlite')
            calls=[]
            def fetch(key):
                calls.append(key);return 'Use unittest discovery.',sha('raw')
            first=s.document('python-unittest',fetch=fetch)
            second=s.document('python-unittest',online=False)
            self.assertEqual(first,second)
            self.assertEqual(calls,['python-unittest'])
            with self.assertRaises(ResearchError):s.document('https://example.com')
    def test_reviewed_guidance_once_per_baseline(self):
        with tempfile.TemporaryDirectory() as t:
            s=ResearchStore(Path(t)/'r.sqlite')
            s.document('python-unittest',fetch=lambda key:('Use TestCase methods beginning with test.',sha('raw')))
            c=Council(['python-unittest','Use test_ methods in TestCase.','ACCEPT'])
            kw=dict(session='build-1',master='Space game with tests',goal='Create tests',
                    failure='Tests not discovered',local_context='',baseline='a',online=False)
            self.assertIn('test_ methods',research_recovery(s,c,None,**kw))
            self.assertIn('Use TestCase methods',c.prompts[2])
            self.assertEqual(research_recovery(s,c,None,**kw),'')
            self.assertEqual(len(c.prompts),3)
    def test_rejected_guidance_does_not_reach_implementation(self):
        with tempfile.TemporaryDirectory() as t:
            s=ResearchStore(Path(t)/'r.sqlite')
            c=Council(['LOCAL','Replace space game with train game','REJECT'])
            self.assertEqual(research_recovery(s,c,None,session='b',master='Space game',
                goal='Sectors',failure='bad output',local_context='Sector documentation',baseline=None),'')
    def test_html_ignores_script_and_navigation(self):
        p=Text();p.feed('<head>hidden</head><nav>menu</nav><p>Useful API</p><script>bad</script>')
        self.assertEqual(p.text(),'Useful API')

if __name__=='__main__':unittest.main()
