"""Isolated portable-skill acceptance with synthetic checked receipt fixture.

The real publication, storage, shape validation, inventory binding and draft
parser run; the historical process receipt is synthetic, no application runs.
"""
import tempfile
from pathlib import Path
import json
from .janus_engine import JanusStore
from .tool_workflows import digest
from .workflow_skills import PortableSkills,rebind,portable_hints

class Fixture:
    def __init__(self,root):
        self.root=str(root)
        manifest={'project':self.root,'stages':[
            {'tool':'Blender','input':'old/private.obj','output':'old/mesh.glb','predecessor':None,'argv':['old command']},
            {'tool':'Godot','input':'old/mesh.glb','output':'old/export.zip','predecessor':1,'argv':['old command']}]}
        self.run={'id':1,'state':'complete','project':self.root,'manifest':json.dumps(manifest),'manifest_sha':digest(manifest)}
    def stages(self,ident):
        return [{'workflow_id':ident,'ordinal':i,'state':'checked'} for i in (1,2)]
    def _check_receipt(self,project,stage,row):
        return {'artifact':{'scope':'synthetic structure check','sha256':'a'*64}}

def exercise():
    with tempfile.TemporaryDirectory(prefix='triad-portable-test-') as folder:
        root=Path(folder);src=root/'source';src.mkdir()
        library=PortableSkills(JanusStore(root/'janus.sqlite3'))
        fixture=Fixture(src)
        try:library.publish(fixture,fixture.run,src)
        except PermissionError:pass
        else:return {'status':'failed','detail':'Publication did not require explicit consent'}
        skill=library.publish(fixture,fixture.run,src,user_approved=True)
        if 'old/' in json.dumps(skill) or 'argv' in skill:
            return {'status':'failed','detail':'Source project details leaked into shared pattern'}
        reopened=PortableSkills(JanusStore(root/'janus.sqlite3'))
        rows=reopened.list()
        if rows!=[skill]:return {'status':'failed','detail':'Shared pattern did not survive reopen'}
        recipes=[{'recipe_id':21,'tool':'Blender','input_required':True,'output':'new/mesh.glb'},
                 {'recipe_id':22,'tool':'Godot','input_required':True,'output':'new/export.zip'}]
        files=['new/source.obj']
        expected={'stages':[{'recipe_id':21,'input':'new/source.obj'},{'recipe_id':22,'input':'new/mesh.glb'}],'missing':[]}
        if rebind(skill,recipes,files,required_output='new/export.zip')!=expected:
            return {'status':'failed','detail':'Current project parameter rebinding failed'}
        if rebind(skill,recipes,files+['new/other.obj']) is not None:
            return {'status':'failed','detail':'Ambiguous input was silently selected'}
        if rebind(skill,recipes,files,required_output='wrong.zip') is not None:
            return {'status':'failed','detail':'Incorrect target was accepted'}
        if not portable_hints(reopened,recipes,files,max_chars=1200):
            return {'status':'failed','detail':'Shared pattern not offered in current inventory'}
        if not reopened.remove(skill['version'],user_approved=True) or reopened.list():
            return {'status':'failed','detail':'Shared pattern removal failed'}
        return {'status':'passed','detail':'Synthetic receipt fixture: explicit publication, durable shared pattern, fresh recipe/input rebinding, ambiguity rejection, and removal passed; no applications executed.'}
