import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from deepthort_local.native_inputs import list_native_inputs
from deepthort_local.action_guards import MAX_HASH_BYTES,snapshot_file,verify_guards
from deepthort_local.workspace import MAX_READ_BYTES,list_project_files
from deepthort_local.workflow_design import inventory,parse_draft
from deepthort_local.tool_workflows import freeze

class Recipes:
    def __init__(self,root):
        self.root=Path(root)
        self.exe=self.root/'converter.exe'
        self.exe.write_bytes(b'fixture tool')
    def _recipe_row(self,ident,project):
        return dict(id=1,name='converter',title='Convert asteroid mesh',
                    purpose='Convert asteroid mesh',artifact='asteroid.glb',
                    args_json=json.dumps(['{{input}}','{{output}}']),script_path='',status='candidate')
    def recipes(self,project):return [self._recipe_row(1,project)]
    def script_needs_review(self,*args):return False
    def _build_recipe_command(self,row,relative,*,allow_future_input=False):
        return [str(self.exe),str(self.root/relative),str(self.root/row['artifact'])]

class NativeInputTests(unittest.TestCase):
    def test_large_native_input_visible_without_expanding_editor(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            (root/'dist').mkdir()
            source=root/'dist'/'asteroid.fbx'
            source.write_bytes(b'm'* (MAX_READ_BYTES+1))
            (root/'large.py').write_bytes(b'x'*(MAX_READ_BYTES+1))
            (root/'node_modules').mkdir()
            (root/'node_modules'/'skip.glb').write_bytes(b'x')
            (root/'.hidden.glb').write_bytes(b'x')
            (root/'empty.png').touch()
            with (root/'oversize.blend').open('wb') as f:f.truncate(MAX_HASH_BYTES+1)
            self.assertEqual(list_native_inputs(root),['dist/asteroid.fbx'])
            self.assertNotIn('dist/asteroid.fbx',list_project_files(root))
            acq=Recipes(root)
            recipes,files=inventory(acq,root,'Convert asteroid mesh',required_output='asteroid.glb')
            self.assertIn('dist/asteroid.fbx',files)
            self.assertNotIn('large.py',files)
            proposal=parse_draft(json.dumps({'stages':[{'recipe_id':1,'input':'dist/asteroid.fbx'}],'missing':[]}),
                                 recipes,files,continuation=True)
            manifest=freeze(acq,root,proposal['stages'],continuation=True)
            guards=manifest['stages'][0]['guards']
            self.assertEqual(guards[0]['kind'],'sha256')
            verify_guards(guards)
            source.write_bytes(b'n'*(MAX_READ_BYTES+1))
            with self.assertRaises(ValueError):verify_guards(guards)

    def test_scan_bound_and_symlinks(self):
        with tempfile.TemporaryDirectory() as t, tempfile.TemporaryDirectory() as outside:
            root=Path(t)
            target=Path(outside)/'asset.glb';target.write_bytes(b'x')
            try:(root/'alias.glb').symlink_to(target)
            except (OSError,NotImplementedError):pass
            for i in range(10):(root/f'{i}.obj').write_bytes(b'x')
            self.assertNotIn('alias.glb',list_native_inputs(root))
            self.assertLessEqual(len(list_native_inputs(root,max_entries=3)),3)
            with self.assertRaises(ValueError):list_native_inputs(root,max_entries=0)

    def test_content_guard_bounded_and_detects_change(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'model.fbx';p.write_bytes(b'abcd')
            with patch('deepthort_local.action_guards.MAX_HASH_BYTES',3):
                with self.assertRaises(ValueError):snapshot_file(p)
            guard=snapshot_file(p);verify_guards([guard])
            p.write_bytes(b'efgh')
            with self.assertRaises(ValueError):verify_guards([guard])

if __name__=='__main__':unittest.main()
