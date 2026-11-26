import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from deepthort_local.git_observation import observe,shared,advisory
from deepthort_local.agent_repository_tools import RepositoryTools

@unittest.skipUnless(shutil.which('git'),'Git required')
class GitObservationTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name).resolve();self.exe=shutil.which('git')
        self.git('init','-q')
        self.git('config','user.name','Fixture')
        self.git('config','user.email','private@example.invalid')
        self.write('a.py','a=1\n');self.git('add','a.py');self.git('commit','-qm','First private subject')
        self.write('b.py','b=1\n');self.git('add','b.py');self.git('commit','-qm','Second')
    def git(self,*args):
        return subprocess.check_output([self.exe,'-C',str(self.root),*args],stderr=subprocess.STDOUT).decode('utf-8').strip()
    def write(self,name,text):(self.root/name).write_text(text,encoding='utf-8')
    def test_exact_observation_and_path_history(self):
        self.write('a.py','a=2\n');self.write('untracked.txt','keep\n')
        before=self.git('status','--porcelain')
        row=observe(self.exe,self.root)
        self.assertEqual(row['head'],self.git('rev-parse','HEAD'))
        self.assertEqual(len(row['history']),2)
        self.assertEqual({x['path'] for x in row['changes']},{'a.py','untracked.txt'})
        self.assertEqual(before,self.git('status','--porcelain'))
        path=observe(self.exe,self.root,relative='a.py')
        self.assertEqual(len(path['history']),1)
        self.assertIn('First',path['history'][0]['subject'])
        with self.assertRaises(ValueError):observe(self.exe,self.root,relative='a.py',exclude=['a.py'])
        with self.assertRaises(ValueError):shared(path)
    def test_shared_advisory_privacy_expiry_and_agent(self):
        receipt=shared(observe(self.exe,self.root))
        items=advisory(receipt,self.root,now=receipt['observed_at']+1)
        self.assertEqual(len(items),1)
        self.assertNotIn('private',str(items));self.assertNotIn('a.py',str(items))
        self.assertEqual(advisory(receipt,self.root,now=receipt['observed_at']+901),[])
        self.assertEqual(advisory(receipt,self.root/'other'),[])
        tools=RepositoryTools(None,self.root,git_observation=lambda:advisory(receipt,self.root))
        request={'tool':'git_history','args':{}}
        result=tools.execute(request)
        self.assertTrue(result['items'][0]['historical_only'])
        self.assertTrue(tools.valid(result,request))
        self.assertNotIn('git_history',RepositoryTools(None,self.root).available())
    def test_unborn_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([self.exe,'-C',tmp,'init','-q'],check=True)
            row=observe(self.exe,tmp)
            self.assertIsNone(row['head']);self.assertEqual(row['history'],[])
if __name__=='__main__':unittest.main()
