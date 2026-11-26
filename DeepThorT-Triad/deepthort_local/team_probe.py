"""Fixed structural role graph acceptance probe; no native inference."""
import json
import tempfile
from pathlib import Path
from .conversation_workflow import ConversationStore
from .team_delegation import TeamDelegationStore,run_team

def exercise(cancelled=lambda:False):
    if cancelled():return {'status':'cancelled','detail':'Team graph probe cancelled'}
    try:
        with tempfile.TemporaryDirectory(prefix='triad-team-') as tmp:
            root=Path(tmp)
            conversations=ConversationStore(root/'conversations.sqlite3')
            store=TeamDelegationStore(conversations.path,root/'creative-tasks')
            req=conversations.submit('a','fixture','chat','/delegate design Specify an interface.')
            other=conversations.submit('b','fixture','chat','Explain a concept.')
            if not store.start(req):raise ValueError('No team assignment')
            roles=[]
            class Client:
                def chat_as(self,role,session,prompt,max_tokens):
                    roles.append(role)
                    if store.next_foreground()['id']!=other:raise ValueError('Foreground head blocked')
                    if role=='janus':
                        return json.dumps({'tasks':[{'id':'a','kind':'design','brief':'Specify interface','depends_on':[]},
                            {'id':'b','kind':'design','brief':'Check interface','depends_on':['a']}]})
                    if role=='implementation':
                        return 'Read-only design fixture.'
                    return 'ACCEPT'
            def no_media(**kw):raise ValueError('Design fixture cannot run a creative adapter')
            answer=run_team(store,req,Client(),no_media,cancelled,lambda s:None)
            if roles!=['janus','sentinel','implementation','implementation','sentinel'] or store.summary(req)['state']!='complete' or 'Read-only design fixture.' not in answer:
                raise ValueError('Role graph or delivery mismatch')
        return {'status':'cancelled' if cancelled() else 'passed',
                'detail':'Reviewed dynamic role DAG, dependency-bound staged design receipts and independent conversation head verified with scripted roles; no native inference.'}
    except Exception as exc:
        return {'status':'cancelled' if cancelled() else 'failed','detail':'Team graph: '+type(exc).__name__+': '+str(exc)[:180]}
