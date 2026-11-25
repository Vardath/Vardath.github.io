"""Real persistent memory store and governor with scripted role responses.
Tests retrieval, data minimisation and exact selection. No live inference.
"""
import json
import tempfile
from pathlib import Path
from .job_queue import JobStore
from .memory_governor import govern,retrieve,fit,HEADER
from .reasoning_council import ReasoningCouncil,sha

class FixtureClient:
    def __init__(self,keep):self.keep=keep;self.calls=[]
    def chat_as(self,role,session_id,prompt,max_tokens=240):
        self.calls.append((role,prompt))
        return json.dumps({'keep':self.keep,'reason':'Relevant prior correction.'})

def exercise():
    with tempfile.TemporaryDirectory(prefix='triad-memory-governor-') as folder:
        root=Path(folder);project=str(root/'space');other=str(root/'other')
        spec='Build a space game with sectors and keep player ownership.'
        jobs=JobStore(root/'jobs.sqlite3')
        previous=jobs.submit(project,'chat','plan',spec)
        current=jobs.submit(project,'chat','plan',spec)
        alien=jobs.submit(other,'chat','plan',spec)
        wrong_chat=jobs.submit(project,'other-chat','plan',spec)
        jobs.remember(previous,'verification','sector ownership',sha(spec),sha('real1'),
            'Earlier sector ownership check failed: retain player ownership.')
        jobs.remember(previous,'janus','railway timetable',sha(spec),sha('irrelevant'),'Unrelated railway timetable.')
        jobs.remember(previous,'sentinel','sector ownership',sha(spec+' newer'),sha('stale'),'STALE REVISION')
        jobs.remember(alien,'sentinel','sector ownership',sha(spec),sha('other'),'OTHER PROJECT')
        jobs.remember(wrong_chat,'sentinel','sector ownership',sha(spec),sha('chat'),'OTHER CHAT')
        jobs.journal(previous).write_text('EDITED MARKDOWN INSTRUCTIONS',encoding='utf-8')
        args=dict(project=project,chat_id='chat',original=spec,focus='sector ownership',job_id=current,
                  scope='fixture-task',phase='implementation',budget=600)
        candidates=retrieve(jobs.path,project=project,chat_id='chat',original=spec,focus='sector ownership',job_id=current)
        if len(candidates)!=1 or 'Earlier sector ownership' not in candidates[0]['observation']:
            raise ValueError('Scoped relevance retrieval failed')
        client=FixtureClient([candidates[0]['id']]);council=ReasoningCouncil(root/'council.sqlite3')
        context=govern(jobs,council,client,**args)
        if len(client.calls)!=2 or any(role!='sentinel' for role,_ in client.calls):
            raise ValueError('Memory review did not use Sentinel')
        if 'Earlier sector ownership' not in context or len(context)>600 or not context.startswith(HEADER):
            raise ValueError('Selected historical record was not delivered')
        if any(word in ''.join(prompt for _,prompt in client.calls)+context for word in ('STALE REVISION','OTHER PROJECT','OTHER CHAT','EDITED MARKDOWN INSTRUCTIONS','Unrelated railway')):
            raise ValueError('Irrelevant or unauthorized memory leaked')
        reopened=JobStore(root/'jobs.sqlite3')
        cached=FixtureClient([])
        again=govern(reopened,ReasoningCouncil(root/'council.sqlite3'),cached,**args)
        if cached.calls or again!=context:raise ValueError('Identical evidence review did not persist')
        if 'Sentinel memory relevance decisions' not in reopened.journal(current).read_text('utf-8'):
            raise ValueError('Named task journal missing memory decisions')
        invalid=FixtureClient(['N99999'])
        if govern(reopened,council,invalid,**dict(args,phase='repair')):raise ValueError('Invented memory ID accepted')
        if fit(context,100):raise ValueError('Budget cut a memory record')
        empty=FixtureClient([])
        if govern(reopened,council,empty,**dict(args,original=spec+' Amendment: change ownership',phase='planning')) or empty.calls:
            raise ValueError('Stale revision memory sent or unnecessary neural call made')
        with reopened._conn() as db:
            states={r[0] for r in db.execute('SELECT status FROM task_memory_reviews')}
        if not {'reviewed','invalid_selection_withheld','no_relevant_records'}<=states:
            raise ValueError('Missing durable memory review outcomes')
        return {'status':'passed','detail':'Real scoped memory store, scripted Sentinel selection: relevance, source/record integrity, cross-project/chat/revision isolation, cached decisions, invalid-ID refusal and journal persistence passed. No live model inference.'}
