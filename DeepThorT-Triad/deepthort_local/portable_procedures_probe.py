"""Exercise actual persistent recipe/evidence APIs, with synthetic process receipts."""
import json
import tempfile
from pathlib import Path
from .janus_engine import JanusStore
from .tool_acquisition import ToolAcquisition
from .portable_procedures import PortableProcedures

def fixture(root):
    src=root/'source';src.mkdir()
    dest=root/'destination';dest.mkdir()
    exe=root/'python.exe';exe.write_bytes(b'not executed: fixture')
    janus=JanusStore(root/'janus.sqlite3')
    acquisition=ToolAcquisition(root/'tools.sqlite3')
    acquisition.discover([{'name':'Python','location':str(exe),'found':True}])
    action=acquisition.authorize_probe('Python',src,janus,user_approved=True)
    log=root/'help.log';log.write_text('Python command help: input and output')
    janus.update_action(action,'succeeded',detail='synthetic fixture',returncode=0,output_file=str(log))
    (src/'old-input.py').write_text('print(1)')
    recipe=acquisition.propose_recipe_for_goal('Python',src,'Create XML',
        json.dumps({'title':'Source conversion','purpose':'Produce XML from selected input','args':['{{input}}','{{output}}'],'artifact':'old-output.xml'}))
    action=acquisition.authorize_recipe(recipe,src,janus,user_approved=True,input_file='old-input.py')
    log=root/'run.log';log.write_text('synthetic receipt')
    (src/'old-output.xml').write_text('<root/>')
    janus.update_action(action,'succeeded',detail='synthetic fixture',returncode=0,output_file=str(log))
    return acquisition,janus,src,dest,recipe,exe

def exercise():
    with tempfile.TemporaryDirectory(prefix='triad-procedure-test-') as folder:
        root=Path(folder)
        try:
            acq,janus,src,dest,recipe,exe=fixture(root)
        except (ValueError,OSError) as exc:
            return {'status':'failed','detail':'Procedure fixture precondition: '+type(exc).__name__+': '+str(exc)[:180]}
        library=PortableProcedures(acq)
        try:
            row=library.preview(recipe,src,janus)
        except (ValueError,OSError) as exc:
            return {'status':'failed','detail':'Procedure evidence preview: '+type(exc).__name__+': '+str(exc)[:180]}
        if 'old-' in json.dumps(row) or str(root) in json.dumps(row):
            return {'status':'failed','detail':'Source paths leaked into portable template'}
        try:library.publish(recipe,src,janus,expected_version=row['version'])
        except PermissionError:pass
        else:return {'status':'failed','detail':'Sharing did not require approval'}
        library.publish(recipe,src,janus,expected_version=row['version'],user_approved=True)
        reopened=PortableProcedures(ToolAcquisition(acq.path))
        if reopened.list()!=[row]:return {'status':'failed','detail':'Shared procedure did not persist'}
        before=len(janus.actions())
        candidate=reopened.bind(row['version'],dest,'new.xml',janus,user_approved=True)
        record=acq._recipe_row(candidate,dest)
        if record['status']!='candidate' or record['action_id'] or len(janus.actions())!=before or (dest/'new.xml').exists():
            return {'status':'failed','detail':'Prior execution authority transferred'}
        (dest/'new.py').write_text('print(2)')
        preview=acq.preview_recipe(candidate,dest,input_file='new.py')
        if preview['argv']!=[str(exe.resolve()),str((dest/'new.py').resolve()),str((dest/'new.xml').resolve())]:
            return {'status':'failed','detail':'New paths not bound correctly'}
        (dest/'wrong.txt').write_text('wrong format')
        try:acq.preview_recipe(candidate,dest,input_file='wrong.txt')
        except ValueError:pass
        else:return {'status':'failed','detail':'Wrong input format accepted'}
        try:reopened.bind(row['version'],dest,'new.xml',janus,user_approved=True)
        except ValueError:pass
        else:return {'status':'failed','detail':'Existing candidate silently overwritten'}
        if not reopened.hints('Python','new.xml',janus):return {'status':'failed','detail':'No reusable procedure hint'}
        exe.write_bytes(b'changed executable')
        try:reopened.bind(row['version'],dest,'another.xml',janus,user_approved=True)
        except ValueError:pass
        else:return {'status':'failed','detail':'Changed tool accepted'}
        return {'status':'passed','detail':'Synthetic process receipts: verified template publication, persistent storage, fresh candidate/paths, input type, no inherited execution, and stale-tool rejection passed.'}
