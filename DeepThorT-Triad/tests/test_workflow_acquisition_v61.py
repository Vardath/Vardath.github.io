import tempfile
import unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import Mock
from deepthort_local.workflow_design import WorkflowDrafts,source_binding
from deepthort_local.conversation_workflow import ConversationStore
from deepthort_local.workflow_acquisition import next_operation,still_required
from deepthort_local.software_autonomy import default_policy

class WorkflowAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.c=ConversationStore(root/'chat.sqlite')
        self.d=WorkflowDrafts(root/'draft.sqlite')
        self.source=self.c.get(self.c.submit('chat',str(root),'draft_plan','Create a Blender model'))
        self.ident=self.c.submit('chat',str(root),'chat','Design workflow')
        self.d.queue(self.ident,source_binding(self.source),'Generate model')
        self.c.change(self.ident,'responded','missing')
        self.set_gap('Blender')
        self.acq=Mock();self.acq.tool.side_effect=ValueError('not installed')
        self.ver=Mock();self.ver.get.return_value=None
        self.policy=default_policy()
        self.now=datetime.now(timezone.utc)
    def set_gap(self,name):
        self.d.save(self.ident,dict(stages=[],missing=[dict(capability=name,goal='Generate model',output='mesh.glb')]),None)
    def operation(self,history=None):
        return next_operation(self.d,self.c,self.acq,self.ver,self.source,self.policy,history or {},
                              which=lambda name:'winget.exe',now=self.now)
    def receipt(self,status):
        self.ver.get.return_value=dict(tool='Blender',status=status,observed_at=self.now.isoformat())
    def test_probe_before_exact_catalog_install(self):
        self.assertEqual(self.operation()['action'],'probe')
        self.receipt('not_found')
        result=self.operation()
        self.assertEqual(result['action'],'install')
        self.assertEqual(result['plan']['package_id'],'BlenderFoundation.Blender')
        self.assertEqual(result['request_id'],self.ident)
    def test_no_install_from_generic_unknown_or_failed_probe(self):
        self.receipt('probe_failed')
        self.assertIsNone(self.operation())
        self.receipt('not_found')
        for name in ('mesh converter','unknown tool','Visual Studio Code'):
            self.set_gap(name);self.assertIsNone(self.operation())
    def test_installed_tool_and_disabled_policy_not_reinstalled(self):
        self.receipt('not_found')
        self.acq.tool.side_effect=None
        self.assertIsNone(self.operation())
        self.acq.tool.side_effect=ValueError('missing')
        self.policy['enabled']=False
        self.assertIsNone(self.operation())
    def test_verified_receipt_restores_or_reprobes(self):
        self.receipt('version_verified')
        self.ver.current.return_value={'executable':'fixture.exe'}
        self.assertEqual(self.operation()['action'],'restore')
        self.ver.current.return_value=None
        self.assertEqual(self.operation()['action'],'probe')
    def test_current_binding_and_exact_requirement_at_launch(self):
        self.assertTrue(still_required(self.d,self.c,self.source,self.ident,'Blender'))
        self.set_gap('Python')
        self.assertFalse(still_required(self.d,self.c,self.source,self.ident,'Blender'))
        self.set_gap('Blender')
        self.c.amend_project('chat',self.source['project'],'No Blender')
        self.assertFalse(still_required(self.d,self.c,self.source,self.ident,'Blender'))
        self.assertIsNone(self.operation())

if __name__=='__main__':unittest.main()
