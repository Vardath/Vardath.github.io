"""Fixed isolated structural probe for approved project role handoffs."""
import json
import tempfile
from pathlib import Path
from .task_graph import TaskGraphStore,GraphError
from .project_assignments import ProjectAssignments,ProjectRoleClient,sha
from .project_authority import issue_grant,authorize_file,record_file
from .workspace import apply_approved_file

def fixture_receipt(original,proposal):
    # Deliberately scripted receipt: this is a host-boundary probe, not native
    # semantic review or a claim that the model actually ran.
    return {'accepted':True,'verified':False,'original_sha':sha(original),
            'proposal_sha':sha(proposal),'evidence_sha':sha('fixture:'+proposal)}

def exercise(cancelled=lambda:False):
    if cancelled():return {'status':'cancelled','detail':'Project assignment probe cancelled'}
    try:
        with tempfile.TemporaryDirectory(prefix='triad-project-role-') as tmp:
            root=Path(tmp);project=root/'fixture';project.mkdir()
            original='Create a module with a fixed answer of 42.'
            job={'id':1,'mode':'build','state':'queued','project':str(project),
                 'chat_id':'fixture','approval_key':'draft:1','prompt':original}
            step={'id':1,'sequence':0,'path':'answer.py','description':'Implement answer','state':'planned'}
            steps=[step]
            graph=TaskGraphStore(root/'task-graph.sqlite3')
            store=ProjectAssignments(graph)
            grants=root/'grants'
            issue_grant(grants,job,steps);graph.create(job,steps)
            job['state']='running'
            attempt,contract=store.begin(job,steps,step,original,[],grants,enabled=True)
            plan=json.dumps({'path':step['path'],'description':step['description']},ensure_ascii=False)
            store.review(attempt,'plan',plan,fixture_receipt(original,plan))
            class Client:
                def chat_as(self,role,session,prompt,max_tokens):
                    if role!='implementation' or not session.startswith('project-role-'):
                        raise GraphError('Production role binding absent')
                    return 'def answer():\n    return 42\n'
            candidate=ProjectRoleClient(Client(),contract).chat('fixture','Implement answer')
            store.review(attempt,'code',candidate,fixture_receipt(original,candidate))
            store.seal(attempt,candidate)
            if (project/'answer.py').exists():raise GraphError('Unexpected premature write')
            try:store.validate(attempt,job,steps,step,original,[],grants,candidate+'# changed',enabled=True)
            except GraphError:pass
            else:raise GraphError('Changed candidate was accepted')
            if cancelled():return {'status':'cancelled','detail':'Project assignment probe cancelled before write'}
            checked=authorize_file(grants,job,steps,step,enabled=True)
            lease=graph.begin_action(job,steps,'write','file:1')
            store.commit(attempt,job,steps,step,original,[],grants,candidate,lease,enabled=True)
            apply_approved_file(project,step['path'],candidate,root/'backups',expected_existing_sha=checked['before_sha256'])
            receipt=record_file(grants,job,steps,step,enabled=True)
            graph.record_artifact(job,steps,step,receipt['sha256'])
            store.saved(attempt,job['id'],receipt['sha256'])
            graph.finish_action(lease,job['id'],'saved')
            if (project/'answer.py').read_bytes()!=candidate.encode() or store.summary(job['id'])[0]['state']!='saved':
                raise GraphError('Source or role receipt mismatch')
        return {'status':'cancelled' if cancelled() else 'passed',
                'detail':'Isolated approved source assignment, explicit implementation role, exact scripted review, stale-candidate refusal and actual host file receipt verified. Native inference and functional project acceptance not tested.'}
    except Exception as exc:
        return {'status':'cancelled' if cancelled() else 'failed','detail':'Project role fixture: '+type(exc).__name__+': '+str(exc)[:180]}
