import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from deepthort_local.agent_tool_selection import shortlist,pack,compact
from deepthort_local.agent_repository_tools import RepositoryTools,gather,REGISTRY
from deepthort_local.repository_index import RepositoryIndex

class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name);self.root=root/'project';self.root.mkdir()
        (self.root/'market.py').write_text('def buy(amount):\n    return amount * 5\n')
        self.index=RepositoryIndex(root/'index.sqlite');self.index.refresh(self.root)
        self.tools=RepositoryTools(self.index,self.root)
    def test_ranked_available_only(self):
        available=self.tools.available()
        chosen=shortlist(available,'Find callers and dependencies')
        self.assertEqual(set(chosen),{'search','references','impact','done','more_tools'})
        self.assertNotIn('diagnostics',chosen)
        self.assertEqual(shortlist(available,'anything',expanded=True),available)
        with self.assertRaises(ValueError):
            self.tools.execute({'tool':'more_tools','args':{}})
    def test_observation_enables_source_read(self):
        request={'tool':'search','args':{'query':'buy'}}
        result=self.tools.execute(request)
        chosen=shortlist(self.tools.available(),'Find purchase function',[(request,result,None)])
        self.assertIn('read_lines',chosen)
    def test_fallback_full_registry(self):
        council=Mock()
        council._run.side_effect=['{"tool":"more_tools","args":{}}',
            '{"tool":"read_lines","args":{"path":"market.py","start":1,"end":2}}',
            '{"tool":"done","args":{}}']
        text=gather(self.tools,council,None,session='fallback',original='Purchase items',goal='Find callers',budget=900)
        self.assertIn('return amount * 5',text)
        first=council._run.call_args_list[0].kwargs['prompt']
        second=council._run.call_args_list[1].kwargs['prompt']
        self.assertIn('"more_tools":{}',first)
        self.assertIn('"read_lines":{',second)
        self.assertNotIn('"more_tools":{}',second)
    def test_omitted_request_does_not_execute_before_fallback(self):
        council=Mock()
        req='{"tool":"read_lines","args":{"path":"market.py","start":1,"end":2}}'
        council._run.side_effect=[req,req,'{"tool":"done","args":{}}']
        out=gather(self.tools,council,None,session='hidden',original='Purchase items',goal='Find callers and dependencies',budget=900)
        self.assertIn('return amount * 5',out)
        self.assertIn('Tool was not offered',council._run.call_args_list[1].kwargs['prompt'])
    def test_context_prioritizes_exact_whole_records(self):
        broad=({'tool':'search'},{'tool':'search','items':[{'name':'buy','signature':'x'*180}]},1)
        exact=({'tool':'read_lines'},{'tool':'read_lines','items':[{'source':'return amount * 5'}]},2)
        budget=len(compact(exact[1]))+1
        self.assertEqual(pack([broad,exact],budget),[exact])
        self.assertEqual(pack([exact,exact],budget),[exact])
        self.assertEqual(pack([broad,exact],0),[])
    def test_changed_observation_removed_before_next_prompt(self):
        council=Mock()
        calls=[]
        # Changing source during the second neural call means the stale
        # result must not enter the final implementation context.
        def choose(*args,**kwargs):
            calls.append(kwargs['prompt'])
            if len(calls)==1:return '{"tool":"search","args":{"query":"buy"}}'
            (self.root/'market.py').write_text('def buy(amount): return 0\n')
            return '{"tool":"done","args":{}}'
        council._run.side_effect=choose
        self.assertEqual(gather(self.tools,council,None,session='stale',original='Buy items',goal='Find buy'), '')
if __name__=='__main__':unittest.main()
