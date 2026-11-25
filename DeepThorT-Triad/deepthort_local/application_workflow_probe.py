"""Scripted model/receipt tests of real video planning and acquisition boundaries."""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from .video_planning import create_plan,save_plan,load_plan,describe
from .reasoning_council import ReasoningCouncil
from .conversation_workflow import ConversationStore
from .workflow_design import WorkflowDrafts,source_binding
from .workflow_acquisition import next_operation,review_recovery
from .software_autonomy import default_policy

def exercise():
    with tempfile.TemporaryDirectory(prefix='triad-applications-') as folder:
        root=Path(folder)
        request={'id':1,'project':str(root),'chat_id':'video-chat','prompt':'/video Make a 45 second vertical fictional video about a moon garden.'}
        outline={'title':'Moon garden','audience':'General','language':'English','style':'Fictional','aspect':'9:16','target_seconds':45,
                 'scenes':[{'title':'Arrival','intent':'Arrive at the garden'},{'title':'Bloom','intent':'Show the flowers'}]}
        scene={'narration':'The moon garden is waking up beneath a silver sky.','visual':'Illustration of lunar flowers',
               'asset_source':'generate','research_needed':[]}
        class Model:
            def __init__(self):self.calls=[]
            def chat_as(self,role,session,prompt,max_tokens):
                self.calls.append((role,prompt))
                return json.dumps(outline if len(self.calls)==1 else scene)
        model=Model();reviewed=[]
        def review(value,focus):reviewed.append(focus);return {'accepted':True}
        council=ReasoningCouncil(root/'council.sqlite3')
        plan=create_plan(model,council,request,review=review)
        if len(model.calls)!=3 or len(reviewed)!=3 or any(role!='janus' or request['prompt'] not in p for role,p in model.calls):
            raise ValueError('Video planning omitted source or review')
        if plan['outline']['aspect']!='9:16' or plan['outline']['target_seconds']!=45 or plan['rendered']:
            raise ValueError('Video draft changed requested properties or claimed render')
        dest=save_plan(root/'video-plans',request,plan)
        if load_plan(dest,request)!=plan or 'NOT a rendered video' not in describe(plan,dest):
            raise ValueError('Video manifest round trip failed')
        no_calls=Model()
        again=create_plan(no_calls,ReasoningCouncil(root/'council.sqlite3'),request,review=review)
        if no_calls.calls or again!=plan:raise ValueError('Video plan could not resume completed model passes')
        try:create_plan(Model(),council,dict(request,id=2),review=lambda *a:{'accepted':False})
        except ValueError:pass
        else:raise ValueError('Rejected storyboard accepted')
        try:create_plan(Model(),council,dict(request,id=3),review=review,cancelled=lambda:True)
        except ValueError:pass
        else:raise ValueError('Cancelled video planning continued')
        try:load_plan(dest,dict(request,prompt=request['prompt']+' New instruction'))
        except ValueError:pass
        else:raise ValueError('Stale video plan accepted')
        # Real workflow records, synthetic installed capability receipt.
        conversations=ConversationStore(root/'chat.sqlite3')
        drafts=WorkflowDrafts(root/'drafts.sqlite3')
        source=conversations.get(conversations.submit('chat',str(root),'draft_plan','Build a Blender model'))
        ident=conversations.submit('chat',str(root),'chat','Design workflow')
        drafts.queue(ident,source_binding(source),'Generate model')
        conversations.change(ident,'responded','missing')
        drafts.save(ident,dict(stages=[],missing=[dict(capability='Blender',goal='Generate model',output='mesh.glb')]),None)
        acq=Mock();acq.tool.side_effect=ValueError('not installed')
        verification=Mock();verification.get.return_value=None
        policy=default_policy()
        def operation():return next_operation(drafts,conversations,acq,verification,source,policy,{},which=lambda n:'winget.exe')
        op=operation()
        def gate(*a):return False
        if op['action']!='probe' or review_recovery(op,source,conversations,drafts,gate,operation,enabled=lambda:True):
            raise ValueError('Probe dispatched during pending review')
        if not review_recovery(op,source,conversations,drafts,lambda *a:True,operation,enabled=lambda:True):
            raise ValueError('Matching reviewed probe was withheld')
        from datetime import datetime,timezone
        verification.get.return_value={'tool':'Blender','status':'version_verified','observed_at':datetime.now(timezone.utc).isoformat()}
        verification.current.return_value={'executable':'fixture.exe'}
        restore=operation()
        if restore['action']!='restore':raise ValueError('Restore fixture invalid')
        def change(*a):verification.current.return_value={'executable':'different.exe'};return True
        try:review_recovery(restore,source,conversations,drafts,change,operation,enabled=lambda:True)
        except ValueError:pass
        else:raise ValueError('Changed restore evidence accepted')
        conversations.amend_project('chat',str(root),'Do not use Blender')
        try:review_recovery(op,source,conversations,drafts,lambda *a:True,operation,enabled=lambda:True)
        except ValueError:pass
        else:raise ValueError('Superseded capability accepted')
        return {'status':'passed','detail':'Video outline and scene scripts, original brief/review binding, durable manifest, cached resume, rejection/cancellation and stale-plan checks passed. Workflow probe/restore review and changed-evidence refusal passed. Scripted model/receipts only; no generated media or real app execution.'}
