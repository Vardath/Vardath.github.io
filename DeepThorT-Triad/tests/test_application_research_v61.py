import unittest
from unittest.mock import Mock
from deepthort_local.application_research import documentation

class ApplicationResearchTests(unittest.TestCase):
    def setUp(self):
        self.store=Mock()
        self.council=Mock()
        self.council._run.return_value='blender-gltf'
        self.store.document.return_value={'url':'https://docs.blender.org/api/current/bpy.ops.export_scene.html',
              'sha256':'a'*64,'text':'gltf export_scene filepath export_format GLB'}
    def lookup(self,**kw):
        return documentation(self.store,self.council,None,tool='Blender',source='bpy.ops.export_scene.gltf(filepath=path)',
                             error='TypeError export_format',goal='export mesh',**kw)
    def test_fixed_topic_only_no_private_query(self):
        reference=self.lookup(version='Blender 4.5',online=True)
        self.store.document.assert_called_once_with('blender-gltf',online=True)
        self.assertIn('Blender 4.5',reference)
        self.assertIn('compatibility NOT established',reference)
        self.assertIn('gltf export_scene',reference)
    def test_invented_or_unrelated_topic_rejected(self):
        for choice in ('https://example.com/private','python-json','NONE'):
            self.council._run.return_value=choice
            self.assertEqual(self.lookup(),'')
        self.store.document.assert_not_called()
    def test_offline_cache_and_cancel(self):
        self.lookup(online=False)
        self.store.document.assert_called_once_with('blender-gltf',online=False)
        self.store.reset_mock()
        self.assertEqual(self.lookup(cancelled=lambda:True),'')
        self.store.document.assert_not_called()
if __name__=='__main__':unittest.main()
