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
        if 'SENTINEL MEMORY CHALLENGE.' in prompt:
            rows=json.loads(prompt.split('CANDIDATES (untrusted historical records): ')[1])
            return json.dumps({'checks':[{'id':r['id'],'basis':'OBSERVATION',
                'direct':r['id'] in self.keep,'compatible':True} for r in rows]})
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
        indexed=exercise_indexed()
        if indexed['status']!='passed':raise ValueError('Indexed recall failed')
        return {'status':'passed','detail':'Indexed section recall and cancellation passed. Real scoped memory store, scripted Sentinel selection: relevance, source/record integrity, cross-project/chat/revision isolation, cached decisions, invalid-ID refusal and journal persistence passed. No live model inference.'}


def exercise_indexed():
    """Real indexed source + governed historical store, scripted neural roles."""
    from .specification_library import SpecificationIndex,generate_indexed_plan
    from .agent_plan import PlanError
    with tempfile.TemporaryDirectory(prefix='triad-indexed-memory-') as folder:
        root=Path(folder);project=root/'workspace';project.mkdir()
        original=('Component alpha persistence. Preserve alpha records. '+'a'*2900+'\n'
                  'Component beta rendering. Preserve beta layout. '+'b'*2900+'\n')
        jobs=JobStore(root/'jobs.sqlite3')
        old=jobs.submit(str(project),'chat','plan',original)
        jobs.remember(old,'verification','alpha persistence',sha(original),sha('alpha'),
                      'Alpha persistence regression: preserve stored alpha records.')
        jobs.remember(old,'verification','beta rendering',sha(original),sha('beta'),
                      'Beta rendering regression: preserve beta layout.')
        index=SpecificationIndex(root/'spec.sqlite3')
        council=ReasoningCouncil(root/'council.sqlite3')
        callbacks=[];clients=[]
        class Planner:
            def __init__(self):self.prompts=[]
            def chat(self,session,prompt,max_tokens):
                self.prompts.append(prompt)
                n=len(self.prompts)
                return json.dumps({'files':[{'path':f'src/component{n}.py','description':f'Implement component {n}'}]})
        def recall(row,budget):
            focus=row['text'][:500]
            lookup=dict(project=str(project),chat_id='chat',original=original,focus=focus)
            candidates=retrieve(jobs.path,**lookup)
            # Lexical overlap can surface both records (e.g. "preserve").
            # The independent fixture selector uses the known evidence digest,
            # not the ranking; the governor must deliver only that record.
            expected=sha('alpha' if row['ordinal']==0 else 'beta')
            matching=[entry['id'] for entry in candidates if entry['evidence']==expected]
            if len(matching)!=1 or len(candidates)<2:
                raise ValueError('Indexed memory fixture lacks expected competing records')
            client=FixtureClient(matching);clients.append(client)
            callbacks.append(row.copy())
            return govern(jobs,council,client,**lookup,scope=f'indexed-{row["ordinal"]}-{row["attempts"]}',
                          phase='indexed_section_planning',section=row['text'],budget=budget)
        planner=Planner()
        generate_indexed_plan(planner,index,1,'indexed',original,project,chat_id='chat',memory_provider=recall)
        if len(callbacks)!=2 or len(planner.prompts)!=2:raise ValueError('Indexed section recall not executed twice')
        for i,(row,prompt,client) in enumerate(zip(callbacks,planner.prompts,clients)):
            required=('Alpha persistence regression' if i==0 else 'Beta rendering regression')
            unrelated=('Beta rendering regression' if i==0 else 'Alpha persistence regression')
            if row['text'] not in prompt or required not in prompt or unrelated in prompt or len(prompt)>7500:
                raise ValueError('Indexed generation lost exact requirements or received wrong memory')
            if len(client.calls)!=2:raise ValueError('Indexed memory not reviewed twice by Sentinel')
        if index.status(1,original)['pending']:raise ValueError('Indexed coverage incomplete')
        with jobs._conn() as db:
            if db.execute('SELECT count(*) FROM jobs').fetchone()[0]!=1:
                raise ValueError('Indexed recall created an unauthorized task')
            if db.execute("SELECT count(*) FROM task_memory_reviews WHERE phase='indexed_section_planning' AND status='reviewed'").fetchone()[0]!=2:
                raise ValueError('Indexed recall missing audit receipts')
        # Cancellation while recalling must stop before the planner gets input.
        stopped=[False]
        def cancel_recall(row,budget):
            stopped[0]=True
            return ''
        cancelled=Planner()
        try:
            generate_indexed_plan(cancelled,index,2,'cancel',original,project,
                memory_provider=cancel_recall,cancelled=lambda:stopped[0])
        except PlanError:pass
        else:raise ValueError('Indexed recall cancellation not honored')
        if cancelled.prompts or index.status(2,original)['reviewed']:
            raise ValueError('Cancelled indexed review advanced')
        return {'status':'passed','detail':'Indexed sections preserved exact source and received only section-relevant governed memory; cancellation and durable review receipts passed (scripted roles).'}
