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
        dispatch=exercise_dispatch_gate()
        if dispatch['status']!='passed':raise ValueError('Dispatch review failed')
        search=exercise_search_index()
        if search['status']!='passed':raise ValueError('Indexed search failed')
        consolidated=exercise_consolidation()
        if consolidated['status']!='passed':raise ValueError('Memory consolidation failed')
        compacted=exercise_context_compaction()
        if compacted['status']!='passed':raise ValueError('Context compaction failed')
        return {'status':'passed','detail':'Complete-exchange context compaction, named test memory consolidation and contradiction detection, long-history term index, mutation invalidation, indexed section recall, cancellation and nonblocking dispatch review passed. Real scoped memory store, scripted Sentinel selection: relevance, source/record integrity, cross-project/chat/revision isolation, cached decisions, invalid-ID refusal and journal persistence passed. No live model inference.'}


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


def exercise_dispatch_gate():
    """Non-blocking, one-shot dispatch review, with a deterministic test worker."""
    from .dispatch_memory import DispatchMemoryGate
    from threading import Event
    import time
    def wait(gate):
        deadline=time.monotonic()+3
        while gate.busy() and time.monotonic()<deadline:time.sleep(.005)
        if gate.busy():raise ValueError('Dispatch review fixture stalled')
    gate=DispatchMemoryGate();release=Event();entered=Event();calls=[]
    def review():
        calls.append('original');entered.set()
        if not release.wait(3):raise ValueError('Fixture timeout')
    if gate.check('original',review):raise ValueError('Dispatch allowed before review')
    try:
        if not entered.wait(3):raise ValueError('Review did not start')
        if gate.check('other',lambda:calls.append('other')):raise ValueError('Concurrent dispatch allowed')
    finally:release.set()
    wait(gate)
    if gate.check('changed',lambda:calls.append('changed')):raise ValueError('Stale review authorized changed operation')
    wait(gate)
    if not gate.check('changed',lambda:None):raise ValueError('Completed matching review not usable')
    if calls!=['original','changed']:raise ValueError('Unexpected review calls')
    def reject():raise ValueError('rejected')
    if gate.check('reject',reject):raise ValueError('Rejected review prematurely accepted')
    wait(gate)
    try:gate.check('reject',lambda:None)
    except ValueError:pass
    else:raise ValueError('Rejected review authorized dispatch')
    # Exercise the real workflow dispatch boundary as well as the gate.
    from .tool_workflows import ToolWorkflows,freeze
    from .janus_engine import JanusStore
    from .workflow_design import source_binding
    with tempfile.TemporaryDirectory(prefix='triad-workflow-memory-') as folder:
        root=Path(folder);exe=root/'fixture.exe';exe.write_bytes(b'fixture')
        class Recipes:
            def _recipe_row(self,ident,project):
                return {'id':ident,'title':'Produce checked output','name':'fixture',
                        'artifact':f'out{ident}.json','args_json':'["{{output}}"]','script_path':''}
            def _build_recipe_command(self,row,rel,*,allow_future_input=False):
                return [str(exe),str(root/row['artifact'])]
        source={'id':1,'chat_id':'chat','project':str(root.resolve()),'mode':'draft_plan',
                'prompt':'Produce a checked JSON artifact.'}
        class Conversations:
            def get(self,ident):return source if ident==1 else None
            def latest_project_request(self,chat,project):return source
        conversations=Conversations()
        janus=JanusStore(root/'janus.sqlite')
        workflows=ToolWorkflows(janus)
        manifest=freeze(Recipes(),root,[{'recipe_id':1,'input':''},{'recipe_id':2,'input':''}])
        manifest['specification']=source_binding(source)
        ident=workflows.approve(manifest,user_approved=True)
        seen=[]
        def deferred(run,approved,ordinal,stage,guards):
            seen.append((run['id'],ordinal,stage['argv']))
            return False
        workflows.tick(conversations=conversations,before_dispatch=deferred)
        if seen!=[(ident,1,manifest['stages'][0]['argv'])] or janus.actions():
            raise ValueError('Workflow dispatched before memory review')
        def change_source(*args):
            source['prompt']='Amended requirements.'
            return True
        workflows.tick(conversations=conversations,before_dispatch=change_source)
        if janus.actions() or workflows.get(ident)['state']!='cancelled':
            raise ValueError('Workflow accepted a superseded specification')
        manifest['specification']=source_binding(source)
        second=workflows.approve(manifest,user_approved=True)
        def change_guard(*args):
            (root/'out1.json').write_text('{}',encoding='utf-8')
            return True
        workflows.tick(conversations=conversations,before_dispatch=change_guard)
        if janus.actions() or workflows.get(second)['state']!='blocked':
            raise ValueError('Workflow accepted a changed output guard')
        (root/'out1.json').unlink()
        third=workflows.approve(manifest,user_approved=True)
        workflows.tick(conversations=conversations,before_dispatch=lambda *args:True)
        actions=janus.actions()
        if len(actions)!=1 or workflows.stages(third)[0]['state']!='dispatched':
            raise ValueError('Unchanged approved workflow did not dispatch')
        workflows.stop(third)
    return {'status':'passed','detail':'Nonblocking one-shot dispatch review, changed-operation isolation, rejection and real workflow source/guard rechecks passed.'}


def exercise_search_index():
    """Legacy migration, long history, scope, restart and change invalidation."""
    with tempfile.TemporaryDirectory(prefix='triad-term-index-') as folder:
        root=Path(folder);jobs=JobStore(root/'jobs.sqlite3')
        project=str(root/'space');chat='chat';spec='Preserve docking clearance.'
        old=jobs.submit(project,chat,'plan',spec)
        alien=jobs.submit(str(root/'other'),chat,'plan',spec)
        other_chat=jobs.submit(project,'other','plan',spec)
        digest=sha(spec)
        with jobs._conn() as db:
            def insert(job,role,focus,note,evidence,revision=digest):
                return db.execute('INSERT INTO task_memory_notes(job_id,role,focus,spec_sha,evidence_sha,note) VALUES(?,?,?,?,?,?)',
                    (job,role,focus,revision,sha(evidence),note)).lastrowid
            oldest=insert(old,'verification','docking clearance','Clearance regression: preserve docking clearance.','oldest')
            for i in range(1200):
                insert(old,'verification','unrelated paint',f'Palette observation {i}',f'paint-{i}')
            for i in range(80):
                insert(old,'janus','docking clearance',f'Proposed docking clearance changes {i}',f'advice-{i}')
            insert(alien,'verification','docking clearance','OTHER PROJECT','alien')
            insert(other_chat,'verification','docking clearance','OTHER CHAT','chat')
            insert(old,'verification','docking clearance','OTHER REVISION','revision',sha(spec+' revised'))
        args=dict(project=project,chat_id=chat,original=spec,focus='docking clearance',job_id=old)
        found=retrieve(jobs.path,**args)
        if not found or found[0]['id']!='N'+str(oldest):
            raise ValueError('Old relevant evidence lost behind newer history')
        if any(x['observation'].startswith('OTHER') for x in found):raise ValueError('Index scope leak')
        if len(found)>8 or len(json.dumps(found,ensure_ascii=True,separators=(',',':'),sort_keys=True))>2300:
            raise ValueError('Index exceeded candidate budget')
        reopened=JobStore(jobs.path)
        if retrieve(reopened.path,**args)!=found:raise ValueError('Index changed across restart')
        with reopened._conn() as db:
            if db.execute('SELECT count(*) FROM memory_term_dirty_v23').fetchone()[0]!=3:
                raise ValueError('Index did not isolate dirty scope')
            db.execute('UPDATE task_memory_notes SET focus=?,note=? WHERE id=?',
                ('paint palette','Repaint hull',oldest))
            replacement=insert(old,'verification','docking clearance','New clearance observation','new')
        updated=retrieve(reopened.path,**args)
        if any(x['id']=='N'+str(oldest) for x in updated) or updated[0]['id']!='N'+str(replacement):
            raise ValueError('Index did not reflect edited and inserted notes')
        with reopened._conn() as db:db.execute('DELETE FROM task_memory_notes WHERE id=?',(replacement,))
        final=retrieve(reopened.path,**args)
        if any(x['id']=='N'+str(replacement) for x in final):raise ValueError('Deleted note remained searchable')
        if any(x['kind']=='historical_verification' for x in final):raise ValueError('Unexpected evidence remained')
        return {'status':'passed','detail':'1284 legacy notes, oldest relevant record, advisory flood, scope isolation, bounded packet, restart and insert/edit/delete invalidation passed.'}


def exercise_consolidation():
    from .memory_consolidation import record_trace,PREFIX
    with tempfile.TemporaryDirectory(prefix='triad-memory-consolidation-') as folder:
        root=Path(folder);project=str(root.resolve());jobs=JobStore(root/'jobs.sqlite3')
        original='Preserve docking clearance.';digest=sha(original)
        old=jobs.submit(project,'chat','plan',original)
        current=jobs.submit(project,'chat','plan',original)
        name='tests.test_docking.Cases.test_clearance'
        def trace(job,status,baseline='one',run='a'):
            h=sha(baseline)
            return {'schema':'deepthort-test-execution-v1','job_id':job,'project':project,
                'spec_sha256':digest,'source_hashes':{'tests/test_docking.py':h},
                'argv_sha256':sha('command'),'complete_named_run':True,
                'exit_code':0 if status=='passed' else 1,'output_sha256':sha(run),
                'files':[{'path':'tests/test_docking.py','sha256':h,
                          'tests':[{'test':name,'status':status}]}]}
        first=trace(old,'passed')
        if record_trace(jobs,jobs.get(old),original,first)!=1:raise ValueError('Observed result not recorded')
        if record_trace(jobs,jobs.get(old),original,first)!=0:raise ValueError('Repeated trace duplicated')
        second=trace(current,'passed',run='b')
        record_trace(jobs,jobs.get(current),original,second)
        args=dict(project=project,chat_id='chat',original=original,focus='Named test clearance')
        rows=retrieve(jobs.path,**args)
        if len(rows)!=1 or '2 recorded observation(s)' not in rows[0]['observation']:
            raise ValueError('Repeated named results not consolidated')
        initial=rows[0]['evidence']
        failed=trace(current,'failed',run='c')
        record_trace(jobs,jobs.get(current),original,failed)
        rows=retrieve(jobs.path,**args)
        if len(rows)!=1 or 'Conflicting named test outcomes' not in rows[0]['observation'] or rows[0]['evidence']==initial:
            raise ValueError('Conflicting identical-baseline outcomes not surfaced')
        record_trace(jobs,jobs.get(current),original,trace(current,'passed',baseline='two',run='d'))
        rows=retrieve(jobs.path,**args)
        if len(rows)!=2 or sum('Conflicting' in x['observation'] for x in rows)!=1:
            raise ValueError('Distinct baseline wrongly treated as contradiction')
        wrong=trace(current,'passed',run='e');wrong['complete_named_run']=False
        if record_trace(jobs,jobs.get(current),original,wrong):raise ValueError('Incomplete trace promoted')
        other=jobs.submit(project,'other','plan',original)
        record_trace(jobs,jobs.get(other),original,trace(other,'failed',baseline='two'))
        if retrieve(jobs.path,**args)!=rows:raise ValueError('Cross-chat claim affected recall')
        reopened=JobStore(jobs.path)
        if retrieve(reopened.path,**args)!=rows:raise ValueError('Consolidated recall changed after restart')
        with jobs._conn() as db:
            stored=db.execute('SELECT count(*) FROM task_memory_notes WHERE job_id IN (?,?) AND note LIKE ?', (old,current,PREFIX+'%')).fetchone()[0]
            if stored!=4:raise ValueError('Consolidation destroyed original observations')
            db.execute('DELETE FROM task_memory_notes WHERE job_id=? AND evidence_sha=?',
                       (current,__import__('deepthort_local.test_execution_trace',fromlist=['fingerprint']).fingerprint(failed)))
        if any('Conflicting' in x['observation'] for x in retrieve(jobs.path,**args)):
            raise ValueError('Deleted contradiction persisted')
        return {'status':'passed','detail':'Exact repeated traces deduplicated, same-baseline outcomes consolidated, contradictions surfaced, different baselines isolated, incomplete traces withheld and original history preserved.'}


def exercise_context_compaction():
    from .context_compaction import select_history,fit_native
    from .client import LocalModelClient
    from unittest.mock import patch
    from types import SimpleNamespace
    import io
    with tempfile.TemporaryDirectory(prefix='triad-context-') as folder:
        client=LocalModelClient(Path(folder)/'sessions.sqlite3')
        def pair(u,a):return [{'role':'user','content':u},{'role':'assistant','content':a}]
        older=pair('Docking clearance must remain unchanged.','Earlier docking tests failed.')
        recent=pair('Correction: retain docking clearance for player ships.','Correction noted.')
        unrelated=pair('Discuss paint palettes.','Blue and red.')
        huge=pair('x'*8100,'Oversized prior answer')
        diag=pair('Check computer','LOCAL COMPUTER DIAGNOSTIC '+ 'z'*3000)
        rows=older+unrelated+huge+diag+recent
        with client._connect() as db:
            db.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',
                [('fixture',r['role'],r['content']) for r in rows])
            db.executemany('INSERT INTO messages(session_id,role,content) VALUES(?,?,?)',
                [('other',r['role'],r['content']) for r in pair('OTHER CHAT PRIVATE','OTHER CHAT ANSWER')])
        before=client.display_history('fixture')
        prompt='Repair docking clearance without changing ownership.'
        chosen=select_history(before,prompt,4800)
        if chosen!=older+recent:raise ValueError('Relevant/recent history was not compacted correctly')
        if select_history(before,prompt,5):raise ValueError('Tiny context budget admitted partial history')
        payloads=[]
        class Opener:
            def open(self,request,timeout):
                payloads.append(json.loads(request.data))
                from .triad_profiles import MODEL_ID
                return io.BytesIO(json.dumps({'model':MODEL_ID,'triad_role':payloads[-1]['triad_role'],
                    'choices':[{'message':{'content':'fixture reply'}}]}).encode())
        with patch('urllib.request.build_opener',return_value=Opener()):
            client.chat('fixture',prompt,max_tokens=128)
            client.chat_as('sentinel','fixture','Review exact evidence.',max_tokens=384)
        if payloads[0]['messages'][1:-1]!=older+recent or payloads[0]['messages'][-1]['content']!=prompt:
            raise ValueError('Actual client request did not preserve current prompt and compacted history')
        if len(payloads[1]['messages'])!=2:raise ValueError('Independent review inherited historical replies')
        if client.display_history('fixture')[:len(before)]!=before:
            raise ValueError('Context compaction mutated the durable transcript')
        full=[{'role':'system','content':'system'},*older,*recent,{'role':'user','content':prompt}]
        def prepare(messages):return messages, sum(len(m['content']) for m in messages)
        cap=sum(len(m['content']) for m in full[0:1]+full[3:])+16
        fitted,count,removed=fit_native(full,16,cap,prepare)
        if removed!=1 or fitted!=[full[0],*recent,full[-1]] or count+16>cap:
            raise ValueError('Native context lost a correction or split an exchange')
        try:fit_native(full,16,20,prepare)
        except ValueError:pass
        else:raise ValueError('Oversized active prompt was silently truncated')
        return {'status':'passed','detail':'Compacted complete historical exchanges, retained current prompt, excluded diagnostics, isolated council review, preserved transcript and enforced native token budget with a scripted tokenizer.'}
