"""Execute reviewed role DAGs using the existing V39 conversation leases.

All generated designs are advisory text and all MIDI remains private staging.
No new grants, arbitrary commands or project writes are introduced.
"""
import json
import queue
import threading
import time
from .delegation import DelegationStore,DelegationError
from .team_plan import (parse_plan,plan_prompt,task_name,contract,KINDS,acceptance)
from .agent_contract import canonical_sha

class TeamDelegationStore(DelegationStore):
    def _receipt(self,db,task,stage):
        row=db.execute("""SELECT receipt FROM agent_stages_v39
            WHERE request_id=? AND attempt=? AND stage=? AND state='complete'""",
            (task['request_id'],task['attempt'],stage)).fetchone()
        if not row or not row[0]:raise DelegationError('Missing completed dependency receipt')
        return json.loads(row[0])

    def _finish(self,db,task,receipt):
        self._leased(db,task)
        db.execute("""UPDATE agent_stages_v39 SET state='complete',receipt=?
            WHERE request_id=? AND attempt=? AND stage=?""",
            (json.dumps(receipt),task['request_id'],task['attempt'],task['stage']))
        self._event(db,task['request_id'],task['attempt'],task['stage'],'complete')

    def plan(self,task,answer):
        if (task['stage'],task['role'])!=('plan','janus'):raise DelegationError('Wrong planning role')
        proposed=parse_plan(answer,task['brief'])
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._finish(db,task,proposed)

    def plan_for(self,task):
        with self.db() as db:
            self._leased(db,task)
            return self._receipt(db,task,'plan')

    def approve(self,task,verdict):
        if (task['stage'],task['role'])!=('review_plan','sentinel') or not acceptance(verdict):
            raise DelegationError('Sentinel did not accept the task graph')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._leased(db,task)
            plan=parse_plan(json.dumps(self._receipt(db,task,'plan')),task['brief'])
            ident,attempt=task['request_id'],task['attempt']
            nodes=[(task_name(t['id']),KINDS[t['kind']],
                    ('review_plan',)+tuple(task_name(d) for d in t['depends_on'])) for t in plan['tasks']]
            nodes.extend([('review_result','sentinel',tuple(n[0] for n in nodes)),
                          ('deliver','host',('review_result',))])
            for name,role,deps in nodes:
                db.execute("INSERT INTO agent_stages_v39 VALUES(?,?,?,?,'queued',NULL,NULL)",(ident,attempt,name,role))
                db.executemany('INSERT INTO agent_edges_v39 VALUES(?,?,?,?)',[(ident,attempt,name,d) for d in deps])
            self._finish(db,task,{'plan_sha256':canonical_sha(plan)})

    def _assignment(self,db,task):
        self._leased(db,task)
        plan=parse_plan(json.dumps(self._receipt(db,task,'plan')),task['brief'])
        if self._receipt(db,task,'review_plan')!={'plan_sha256':canonical_sha(plan)}:
            raise DelegationError('Plan approval identity changed')
        node=next((n for n in plan['tasks'] if task_name(n['id'])==task['stage']),None)
        if not node or KINDS[node['kind']]!=task['role']:raise DelegationError('Assignment identity changed')
        deps={d:self._receipt(db,task,task_name(d)) for d in node['depends_on']}
        return node,contract(task['brief'],task['scope'],plan,node,
                             {k:canonical_sha(v) for k,v in deps.items()}),deps

    def assignment(self,task):
        with self.db() as db:return self._assignment(db,task)

    def design_done(self,task,expected,answer):
        if not isinstance(answer,str) or not answer.strip() or len(answer)>400:
            raise DelegationError('Design result must be 1–400 characters; no silent truncation')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            node,bound,_=self._assignment(db,task)
            if node['kind']!='design' or expected!=bound:raise DelegationError('Design assignment changed')
            self._finish(db,task,{'contract':bound,'text':answer,'text_sha256':canonical_sha(answer)})

    def _midi_task(self,db,task):
        node,bound,deps=self._assignment(db,task)
        if node['kind']!='midi':raise DelegationError('Wrong creative adapter')
        design=[r['text'] for r in deps.values() if 'text' in r]
        for r in deps.values():
            if 'text' in r and r.get('text_sha256')!=canonical_sha(r['text']):
                raise DelegationError('Design dependency changed')
        brief=task['brief']+'\nAssigned direction: '+node['brief']
        if design:brief+='\nGranite advisory specification: '+'\n'.join(design)
        if len(brief)>1400:raise DelegationError('Exact MIDI brief exceeds adapter capacity')
        creative=dict(task,requester='implementation' if design else 'janus',
                      scope=task['scope']+':'+canonical_sha(bound)[:24],brief=brief)
        return bound,creative

    def midi_task(self,task):
        with self.db() as db:return self._midi_task(db,task)

    def midi_done(self,task,expected,folder,receipt):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            bound,creative=self._midi_task(db,task)
            if bound!=expected:raise DelegationError('Creative assignment changed')
            data=self._artifact(folder,receipt,creative)
            self._finish(db,task,{'contract':bound,'artifact':data,'creative':creative})

    def _results(self,db,task):
        self._leased(db,task)
        plan=parse_plan(json.dumps(self._receipt(db,task,'plan')),task['brief'])
        if self._receipt(db,task,'review_plan')!={'plan_sha256':canonical_sha(plan)}:
            raise DelegationError('Plan approval identity changed')
        results=[]
        for node in plan['tasks']:
            r=self._receipt(db,task,task_name(node['id']))
            deps={d:self._receipt(db,task,task_name(d)) for d in node['depends_on']}
            expected=contract(task['brief'],task['scope'],plan,node,{k:canonical_sha(v) for k,v in deps.items()})
            if r.get('contract')!=expected:raise DelegationError('Result contract changed')
            if node['kind']=='design':
                if r.get('text_sha256')!=canonical_sha(r['text']):raise DelegationError('Design result changed')
                results.append({'id':node['id'],'design':r['text'],'receipt_sha256':canonical_sha(r)})
            else:
                design=[v['text'] for v in deps.values() if 'text' in v]
                brief=task['brief']+'\nAssigned direction: '+node['brief']
                if design:brief+='\nGranite advisory specification: '+'\n'.join(design)
                creative={'scope':task['scope']+':'+canonical_sha(expected)[:24],
                          'requester':'implementation' if design else 'janus','brief':brief}
                if any(r['creative'].get(k)!=v for k,v in creative.items()):
                    raise DelegationError('Creative input identity changed')
                data=self._artifact(r['artifact']['folder'],r['artifact']['receipt'],creative)
                results.append({'id':node['id'],'artifact':data['folder']+'/score.mid',
                    'sha256':data['receipt']['sha256'],'notes':data['receipt']['notes'],
                    'bpm':data['receipt']['bpm'],'receipt_sha256':canonical_sha(r)})
        return results

    def results(self,task):
        with self.db() as db:return self._results(db,task)

    def review_results(self,task,expected,verdict):
        if (task['stage'],task['role'])!=('review_result','sentinel') or not acceptance(verdict):
            raise DelegationError('Sentinel did not accept staged results')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if self._results(db,task)!=expected:raise DelegationError('Reviewed results changed')
            self._finish(db,task,{'results_sha256':canonical_sha(expected)})

    def deliver_team(self,task):
        if (task['stage'],task['role'])!=('deliver','host'):raise DelegationError('Wrong delivery stage')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            results=self._results(db,task)
            if self._receipt(db,task,'review_result')!={'results_sha256':canonical_sha(results)}:
                raise DelegationError('Result review identity changed')
            answer='Staged team assignments completed. Designs are advisory, MIDI is structurally verified, and no project files were published. Musical quality is not established.\n'
            for r in results:
                answer+='\n'+r['id']+': '+(r['design'] if 'design' in r else r['artifact'])+'\n'
            self._finish(db,task,{'results_sha256':canonical_sha(results)})
            db.execute("UPDATE agent_batches_v39 SET state='complete' WHERE request_id=?",(task['request_id'],))
            db.execute("""UPDATE conversation_requests SET state='responded',response=?,
                detail='Reviewed staged team assignments completed',updated_at=CURRENT_TIMESTAMP
                WHERE id=? AND state='running'""",(answer,task['request_id']))
            return answer

def run_team(store,ident,client,create_midi,stopped,notify,*,overlap_allowed=None):
    """Dispatch dependency-ready work; at most one lease per production role.

    Planning/review/delivery remain exclusive. Only independent design and MIDI
    tasks can overlap, and only with a positive live resource admission decision.
    On a failure invalidate the batch before draining sibling calls; never replay
    an uncertain native action or release the lane while a sibling is in flight.
    """
    abort=threading.Event()
    def cancelled():return abort.is_set() or stopped()
    def ask(task,prompt,tokens):
        if cancelled():raise DelegationError('Team task interrupted')
        session='team-'+str(ident)+'-'+str(task['attempt'])+'-'+task['stage']
        answer=client.chat_as(task['role'],session,prompt,max_tokens=tokens)
        if cancelled():raise DelegationError('Team task interrupted')
        return answer
    def execute(task):
        if cancelled():raise DelegationError('Team task interrupted')
        stage=task['stage'];notify(task['role']+': '+stage)
        original=task['brief']
        if stage=='plan':
            store.plan(task,ask(task,plan_prompt(original),400))
        elif stage=='review_plan':
            p=store.plan_for(task)
            verdict=ask(task,'Review scoped staged graph against exact request. Reject omitted requirements, unsafe instructions, or unsupported execution claims. Only design advice and one explicit MIDI are available. Return exactly ACCEPT or REJECT.\n'+original+'\n'+json.dumps(p),96)
            store.approve(task,verdict)
        elif stage=='review_result':
            results=store.results(task)
            verdict=ask(task,'Review exact request and staged result evidence. Reject unsupported completion or contradictory design. Artifact metadata does not prove musical quality. Return exactly ACCEPT or REJECT.\n'+original+'\n'+json.dumps(results),96)
            store.review_results(task,results,verdict)
        elif stage=='deliver':
            return store.deliver_team(task)
        elif task['role']=='implementation':
            node,bound,deps=store.assignment(task)
            answer=ask(task,'Provide concise read-only design advice for the assigned task, not code execution or a completion claim. If downstream music is requested, give a compact MIDI specification. Maximum 400 characters.\nEXACT REQUEST:\n'+original+'\nASSIGNMENT:\n'+node['brief']+'\nDEPENDENCIES:\n'+json.dumps(deps),112)
            store.design_done(task,bound,answer)
        elif task['role']=='multimedia':
            bound,creative=store.midi_task(task)
            folder,receipt=create_midi(requester=creative['requester'],scope=creative['scope'],
                brief=creative['brief'],cancelled=cancelled,notify=notify)
            if cancelled():raise DelegationError('Team task interrupted')
            store.midi_done(task,bound,folder,receipt)
        else:raise DelegationError('Unsupported task')
    production=('implementation','multimedia')
    roles=('janus','sentinel',*production,'host')
    finished=queue.Queue()
    active={}
    claims=0
    last_admission=-float('inf')

    def launch(task):
        role=task['role']
        def work():
            try:
                execute(task)
            except BaseException as exc:
                abort.set()
                finished.put((role,exc))
            else:
                finished.put((role,None))
        thread=threading.Thread(target=work,name='Team-'+role,daemon=True)
        active[role]=thread
        thread.start()

    def collect(item):
        role,error=item
        thread=active.pop(role)
        thread.join()
        if error is not None:raise error

    try:
        while True:
            # Consume completed work first. Its durable receipt, not the
            # thread's return, is the gate for any dependent assignment.
            while True:
                try:item=finished.get_nowait()
                except queue.Empty:break
                collect(item)
            if stopped():raise DelegationError('Team task interrupted')
            if abort.is_set():
                # The failing worker sets abort before publishing its error.
                # Do not race it by claiming another task.
                collect(finished.get())
                continue
            task=None
            if claims<8:
                if not active:
                    for role in roles:
                        task=store.claim(ident,role)
                        if task:break
                elif len(active)==1 and overlap_allowed is not None and time.monotonic()-last_admission>=1.0:
                    last_admission=time.monotonic()
                    role=next(r for r in production if r not in active)
                    try:allowed=overlap_allowed(tuple(active),role) is True
                    except Exception:allowed=False
                    if allowed:task=store.claim(ident,role)
            if task:
                claims+=1
                if task['role'] in production:
                    launch(task)
                else:
                    # All production calls must have drained before delivery.
                    answer=execute(task)
                    if task['stage']=='deliver':return answer
                continue
            if active:
                try:item=finished.get(timeout=.25)
                except queue.Empty:continue
                collect(item)
            else:
                raise DelegationError('Team graph exceeded stage budget' if claims>=8 else 'No dependency-ready task')
    except BaseException as exc:
        abort.set()
        # Invalidate every queued/running lease before waiting for a possibly
        # non-cancellable HTTP call; sibling results cannot be delivered.
        store.fail(ident,str(exc),interrupted=stopped())
        raise
    finally:
        abort.set()
        for thread in active.values():thread.join()
