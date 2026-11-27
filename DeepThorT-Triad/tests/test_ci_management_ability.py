import copy
import unittest
from unittest.mock import patch
from deepthort_local import ci_management as tool

class CIManagementTests(unittest.TestCase):
    def data(self):
        s={'repository':'Owner/Repo','run_id':42,'commit':'a'*40,'required_jobs':['source','windows']}
        run={'id':42,'head_sha':s['commit'],'repository':{'full_name':'Owner/Repo'},'run_attempt':2,'status':'completed','conclusion':'success'}
        jobs={'total_count':2,'jobs':[{'name':n,'id':i,'run_id':42,'head_sha':s['commit'],'run_attempt':2,'status':'completed','conclusion':'success'} for i,n in enumerate(s['required_jobs'],1)]}
        return s,run,jobs
    def test_green_requires_exact_jobs(self):
        s,r,j=self.data()
        self.assertTrue(tool.assess(s,r,j,r)['required_jobs_green'])
        j['jobs'][0]['conclusion']='failure'
        self.assertFalse(tool.assess(s,r,j,r)['required_jobs_green'])
        j['jobs'].pop();j['total_count']=1
        self.assertFalse(tool.assess(s,r,j,r)['required_jobs_green'])
        j['total_count']=2
        with self.assertRaises(ValueError):tool.assess(s,r,j,r)
    def test_attempt_and_read_only_requests(self):
        s,r,j=self.data()
        with self.assertRaises(ValueError):tool.assess(s,r,j,dict(r,run_attempt=3))
        with patch.object(tool,'_request',side_effect=[(r,'1'),(j,'2'),(copy.deepcopy(r),'3')]) as request:
            result=tool.inspect(s,'dummy',approved=True)
            self.assertTrue(result['required_jobs_green'])
            self.assertFalse(result['merge_authorized'])
            self.assertEqual([x.args[0] for x in request.call_args_list],['GET']*3)
            self.assertIn('/attempts/2/jobs',request.call_args_list[1].args[1])
        with self.assertRaises(PermissionError):tool.inspect(s,'dummy')

if __name__=='__main__':unittest.main()
