"""Fixed structural probe; no real model execution or staged artifact certification."""
import tempfile
from pathlib import Path
from .conversation_workflow import ConversationStore
from .delegation import DelegationStore

def exercise(cancelled=lambda:False):
    if cancelled():return {'status':'cancelled','detail':'Delegation check stopped'}
    try:
        with tempfile.TemporaryDirectory(prefix='triad-delegation-') as tmp:
            root=Path(tmp)
            chats=ConversationStore(root/'conversations.sqlite3')
            store=DelegationStore(chats.path,root/'creative-tasks')
            creative=chats.submit('A','fixture','chat','Compose a short MIDI melody.')
            later=chats.submit('A','fixture','chat','Explain the result.')
            other=chats.submit('B','fixture','chat','Plan a station layout.')
            if (store.next_candidate()['id']!=creative or store.next_foreground()['id']!=other
                    or not store.start(creative) or store.claim(creative,'host') is not None):
                raise ValueError('Independent queue or dependency ordering incorrect')
            task=store.claim(creative,'multimedia')
            if not task or store.claim(creative,'multimedia') is not None:
                raise ValueError('Exclusive creative lease not established')
            if store.next_foreground()['id']!=other:
                raise ValueError('Unrelated foreground task blocked by creative lease')
            reopened=ConversationStore(chats.path)
            recovered=DelegationStore(reopened.path,root/'creative-tasks')
            if recovered.recover()!=1 or reopened.get(creative)['state']!='failed':
                raise ValueError('Interrupted lease was not safely reconciled')
            if recovered.start(creative) or recovered.current(creative):
                raise ValueError('Lost creative operation replayed without retry')
            if recovered.next_foreground()['id']!=later:
                raise ValueError('Unrelated thread head was not released')
        return {'status':'cancelled' if cancelled() else 'passed',
                'detail':'Durable creative leases, dependency order, independent foreground dispatch and restart interruption verified on temporary records; no native inference in this probe.'}
    except Exception as exc:
        return {'status':'failed','detail':'Delegation: '+type(exc).__name__+': '+str(exc)[:200]}
