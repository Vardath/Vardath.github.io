"""Finite external task inbox; only exact owner-reviewed items become conversation requests."""
import hashlib
import threading
import uuid

MAX_ITEMS=2
def checked(value):
    if not isinstance(value,dict) or set(value)!={'submission_id','prompt'}:raise ValueError('Expected exact submission ID and prompt')
    ident=value['submission_id'];prompt=value['prompt']
    if not isinstance(ident,str) or str(uuid.UUID(ident))!=ident:raise ValueError('Expected canonical UUID')
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>8000 or any((ord(c)<32 and c not in '\n\t\r') or 0xd800<=ord(c)<=0xdfff for c in prompt):
        raise ValueError('Invalid bounded prompt')
    return dict(value)

class Inbox:
    def __init__(self,project,chat,*,approved=False):
        if approved is not True:raise PermissionError('Explicit inbox approval required')
        if not isinstance(project,str) or not project or not isinstance(chat,str) or not chat:raise ValueError('Exact project and chat required')
        self.project=project;self.chat=chat;self.lock=threading.RLock();self.items={};self.closed=False
    def receive(self,value):
        item=checked(value);ident=item['submission_id']
        with self.lock:
            if self.closed:raise ValueError('Inbox closed')
            if ident in self.items:raise ValueError('Duplicate submission ID; no retry')
            if len(self.items)>=MAX_ITEMS:raise ValueError('Inbox limit reached')
            self.items[ident]={'prompt':item['prompt'],'state':'awaiting_owner_review'}
        return {'schema':'janus-task-receipt-v1','submission_id':ident,'state':'awaiting_owner_review',
                'prompt_sha256':hashlib.sha256(item['prompt'].encode('utf-8')).hexdigest(),
                'conversation_created':False,'execution_approved':False}
    def pending(self):
        with self.lock:return [(ident,row['prompt']) for ident,row in self.items.items() if row['state']=='awaiting_owner_review']
    def review(self,ident,exact_prompt,project,chat,submit,*,approved=False):
        if approved is not True:raise PermissionError('Exact owner review required')
        with self.lock:
            row=self.items.get(ident)
            if self.closed or project!=self.project or chat!=self.chat or row is None or row['state']!='awaiting_owner_review' or row['prompt']!=exact_prompt:
                raise ValueError('Submission or scope changed')
            # No repeat after an uncertain DB outcome.
            row['state']='admission_attempted'
            result=submit(self.chat,self.project,'chat',exact_prompt)
            if type(result) is not int or result<=0:raise ValueError('Unconfirmed conversation receipt')
            row['state']='admitted';row['request_id']=result
            return result
    def discard(self):
        with self.lock:
            self.closed=True;self.items.clear()
