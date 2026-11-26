"""Roadmap-bound Gemma MIDI assignments. No arbitrary tools or overwrite rights.

The existing explicit roadmap approval includes an opt-in for this exact adapter.
Private staging, independent review and host publication are separate steps.
A lost generation or publication lease is never silently replayed.
"""
import json
import sqlite3
import hashlib
import os
import tempfile
import uuid
from pathlib import Path
from .agent_contract import canonical_sha,validate_creative_assignment
from .creative_core import request_packet,inspect_midi
from .project_authority import _safe_auto_path
from .artifact_acceptance import validate
from .tool_workflows import digest,artifact
from .task_graph import same_workspace

def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()

def supports(task):
    return (Path(task['output']).suffix.casefold() in ('.mid','.midi')
            and not task.get('imports') and
            set(task.get('acceptance',{}))<={'bpm','notes'})

def early_window(task,ordinal):
    """Explicitly reviewed one-milestone private preparation, never early publication."""
    return bool(type(ordinal) is int and ordinal>=1 and type(task.get('prepare_after')) is int
                and task['after']==ordinal and task['prepare_after']==ordinal-1 and supports(task))


def review_text(contract,score):
    return json.dumps({'task':contract['task'],'scope':contract['scope'],
        'score':score,'assurance':'bounded single-track MIDI; no audio playback or aesthetic verification'},
        ensure_ascii=False,sort_keys=True)

def native_route_available(run,task,mixed_roadmaps,workflows):
    """Use the existing explicit native consent and avoid duplicate producers."""
    return bool(run.get('creative_midi')==1 and supports(task)
                and not mixed_roadmaps.request_for(task['id'])
                and not any(json.loads(w['manifest']).get('mixed_task')==task
                            for w in workflows.roadmap_members(run['request_id'])))


def ready_independent(runs,conversations,hierarchies,index,jobs,mixed_roadmaps,workflows,creative,*,exclude_project):
    """Find a ready existing native artifact boundary in a separate workspace.

    The ordinary roadmap reconciliation, predecessor verification, mixed
    manifest and tool gates are reused. This discovery does not create a job,
    draft a tool workflow, alter approvals or reserve a creative assignment.
    The original begin/publish checks remain mandatory.
    """
    from .task_graph import independent_workspaces
    from .roadmap_runs import eligible_successor
    from .roadmap_tool_bridge import gate
    from .mixed_roadmap import pending_task
    for run in runs.active():
        if (not run.get('mixed_sha') or run.get('creative_midi')!=1
                or not independent_workspaces(run['project'],exclude_project)):
            continue
        ident=run['request_id']
        try:
            req=conversations.get(ident)
            result=eligible_successor(run,req,conversations,hierarchies,index,jobs)
            if not result:continue
            before=(hierarchies.status(index,ident,req['prompt'])['milestones_total']+1
                    if result['complete'] else result['milestone']['ordinal'])
            mixed=mixed_roadmaps.get(ident,result['manifest_sha256'])
            if not mixed or mixed['sha']!=run['mixed_sha']:continue
            task=pending_task(mixed,workflows,before,creative=creative)
            if not task or creative.status(task['id']):continue
            if not native_route_available(run,task,mixed_roadmaps,workflows):continue
            if gate(workflows,ident,result['manifest_sha256'],before):continue
            return run,mixed,task,req,before
        except (ValueError,OSError,KeyError,TypeError,sqlite3.Error):
            # Leave reconciliation/errors to the normal roadmap path. An
            # optional overlap scan cannot mark unrelated work failed.
            continue
    return None


def ready_same_project(runs,conversations,hierarchies,index,jobs,mixed_roadmaps,workflows,creative,*,active):
    """Only an explicitly approved independent future score may prepare early."""
    from .roadmap_runs import manifest,verified_prefix
    from .roadmap_tool_bridge import gate
    from .mixed_roadmap import pending_task
    key=active.get('approval_key') or ''
    parts=key.split(':')
    if (active.get('mode')!='build' or active.get('state')!='running'
            or len(parts)!=4 or parts[0]!='milestone'):return None
    try:
        ident,ordinal=int(parts[1]),int(parts[2])
        run=runs.get(ident);req=conversations.get(ident)
        if (not run or run['state']!='active' or run['creative_midi']!=1 or not run['mixed_sha']
                or not req or req['mode']!='draft_plan' or req['state']!='responded'
                or req['chat_id']!=active['chat_id'] or not same_workspace(req['project'],active['project'])):return None
        latest=conversations.latest_project_request(req['chat_id'],req['project'])
        if not latest or latest['id']!=ident or conversations.amendment_supersedes(ident,req['chat_id'],req['project']):return None
        current=manifest(hierarchies,index,req)
        if any(current[k]!=run[k] for k in ('project','chat_id','manifest_sha256')):return None
        if not 1<=ordinal<=len(current['schedule']):return None
        item=hierarchies.milestone(index,ident,req['prompt'],ordinal)
        if (item['state']!='queued' or item['job_id']!=active['id'] or item['approval_key']!=key
                or item['scope_prompt']!=active['prompt']):return None
        with runs.db() as db:
            dispatch=db.execute("SELECT * FROM roadmap_dispatch WHERE approval_key=?",(key,)).fetchone()
            if (not dispatch or dispatch['state']!='ready' or dispatch['job_id']!=active['id']
                    or dispatch['request_id']!=ident or dispatch['ordinal']!=ordinal):return None
        verified_prefix(current,req,hierarchies,index,jobs,ordinal)
        mixed=mixed_roadmaps.get(ident,current['manifest_sha256'])
        if not mixed or mixed['sha']!=run['mixed_sha']:return None
        if pending_task(mixed,workflows,ordinal,creative=creative) or gate(workflows,ident,current['manifest_sha256'],ordinal):
            return None
        for task in mixed['tasks']:
            if early_window(task,ordinal) and not creative.status(task['id']) and native_route_available(run,task,mixed_roadmaps,workflows):
                return run,mixed,task,req,ordinal+1
    except (ValueError,OSError,KeyError,TypeError,sqlite3.Error):return None
    return None


class ProjectMidi:
    def __init__(self,runs,delegations):
        self.runs=runs
        self.delegations=delegations
        with runs.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS project_midi_v45(
                task_id TEXT PRIMARY KEY,request_id INTEGER NOT NULL,lease TEXT NOT NULL UNIQUE,
                contract TEXT NOT NULL,contract_sha TEXT NOT NULL,state TEXT NOT NULL,
                staged TEXT,review TEXT,receipt TEXT,detail TEXT NOT NULL DEFAULT '')""")

            db.execute("""CREATE TABLE IF NOT EXISTS creative_reports_v49(
                lease TEXT PRIMARY KEY,report TEXT NOT NULL,receipt_sha TEXT NOT NULL)""")
            from .worker_notices import ensure_schema
            ensure_schema(db)
            db.execute("""CREATE TABLE IF NOT EXISTS project_midi_prepare_v58(
                lease TEXT PRIMARY KEY,job_id INTEGER NOT NULL,approval_key TEXT NOT NULL,
                contract_sha TEXT NOT NULL)""")

    def record_notice(self,lease,contract,folder,receipt):
        """Only a current scoped native artifact may carry a production notice."""
        if 'notice' not in receipt:return False
        from .worker_notices import record
        from .worker_reports import creative_request
        self._staged(contract,folder,receipt)
        if not creative_request(self.runs.path.parent/'jobs.sqlite3',contract,states=('active',)):
            raise ValueError('Stale creative notice scope')
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,bound=self._row(db,contract['task']['id'])
            run=db.execute("SELECT * FROM roadmap_runs WHERE request_id=?",(contract['request_id'],)).fetchone()
            if (not row or row['lease']!=lease or row['state']!='assigned' or bound!=contract
                or not run or run['state']!='active' or run['creative_midi']!=1
                or run['mixed_sha']!=contract['plan_sha'] or run['manifest_sha256']!=contract['code_sha']):
                raise ValueError('Stale creative notice assignment')
            return record(db,lease,contract['request_id'],contract,receipt['notice'],receipt['sha256'],'multimedia')

    def report_dependency(self,lease,contract,report):
        from .worker_reports import parse_report,PREFIX,creative_request,creative_envelope
        report=parse_report(PREFIX+json.dumps(report))
        if not creative_request(self.runs.path.parent/'jobs.sqlite3',contract,states=('active',)):
            raise ValueError('Stale creative report scope')
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,bound=self._row(db,contract['task']['id'])
            run=db.execute("SELECT * FROM roadmap_runs WHERE request_id=?",(contract['request_id'],)).fetchone()
            if (not row or row['lease']!=lease or row['state']!='assigned' or bound!=contract
                    or not run or run['state']!='active' or run['creative_midi']!=1
                    or run['mixed_sha']!=contract['plan_sha'] or run['manifest_sha256']!=contract['code_sha']):
                raise ValueError('Stale creative report assignment')
            item=creative_envelope(lease,contract,report)
            db.execute("INSERT INTO creative_reports_v49 VALUES(?,?,?)",(lease,json.dumps(report,sort_keys=True),canonical_sha(item)))
            db.execute("UPDATE project_midi_v45 SET state='blocked',detail=? WHERE lease=?",
                       ('Gemma reported '+report['kind']+': '+report['need'],lease))
            if not db.execute("SELECT 1 FROM project_midi_prepare_v58 WHERE lease=?",(lease,)).fetchone():
                db.execute("UPDATE roadmap_runs SET state='blocked',detail=?,updated_at=CURRENT_TIMESTAMP WHERE request_id=?",
                           ('Gemma dependency claim awaiting coordination; not verified',contract['request_id']))
        return item

    def recover(self):
        with self.runs.db() as db:
            db.execute("UPDATE project_midi_v45 SET state='interrupted',detail='Inspect private staging and project output; no automatic replay' WHERE state IN ('assigned','reviewed','publishing')")

    def _row(self,db,task_id):
        row=db.execute('SELECT * FROM project_midi_v45 WHERE task_id=?',(task_id,)).fetchone()
        if row:
            bound=json.loads(row['contract'])
            if canonical_sha(bound)!=row['contract_sha']:raise ValueError('Project MIDI assignment identity changed')
            return row,bound
        return None,None

    def _identity(self,run,plan,task,request,before):
        if (not run or run['state']!='active' or run.get('creative_midi')!=1
            or run['request_id']!=request['id'] or run['chat_id']!=request['chat_id']
            or request['mode']!='draft_plan' or request['state']!='responded'
            or not same_workspace(run['project'],request['project'])
            or plan['request_id']!=request['id'] or plan['code_sha']!=run['manifest_sha256']
            or plan['sha']!=run['mixed_sha'] or digest({k:v for k,v in plan.items() if k!='sha'})!=plan['sha']
            or task not in plan['tasks'] or task['after']!=before-1 or not supports(task)):
            raise ValueError('No current approved native artifact boundary')
        if 'prepare_after' in task and not early_window(task,task['after']):
            raise ValueError('Invalid private preparation declaration')
        output,target=_safe_auto_path(Path(run['project']),task['output'])
        if output!=task['output']:raise ValueError('Artifact path changed')
        if task.get('acceptance'):validate(output,task['acceptance'])
        scope='roadmap-midi:'+canonical_sha([request['id'],plan['sha'],task['id'],sha(request['prompt'])])
        brief=task['goal']+'; required project output: '+output
        if task.get('acceptance'):brief+='; exact acceptance: '+json.dumps(task['acceptance'],sort_keys=True)
        packet=request_packet('janus',scope,brief)
        return {'schema':'project-midi-v45','request_id':request['id'],'project':str(Path(run['project']).resolve(strict=True)),
                'chat_id':request['chat_id'],'plan_sha':plan['sha'],'code_sha':plan['code_sha'],
                'original_sha':sha(request['prompt']),'task':task,'before':before,
                'scope':scope,'brief':brief,'assignment_sha':validate_creative_assignment(packet),
                'publication':'new exact file only, separate host authorization'}

    def begin(self,run,plan,task,request,before,*,enabled,early_job=None):
        if not enabled:raise PermissionError('Approved project work disabled')
        contract=self._identity(run,plan,task,request,before)
        _,target=_safe_auto_path(Path(contract['project']),task['output'])
        if target.exists():raise ValueError('Refusing to replace existing project artifact')
        lease=uuid.uuid4().hex
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT * FROM roadmap_runs WHERE request_id=?',(request['id'],)).fetchone()
            if not current or self._identity(dict(current),plan,task,request,before)!=contract:
                raise ValueError('Roadmap approval changed')
            if self._row(db,task['id'])[0]:raise ValueError('Prior artifact attempt exists; inspect before revising roadmap')
            if early_job is not None:
                key=early_job.get('approval_key') or ''
                expected=f"milestone:{request['id']}:{before-1}:{sha(request['prompt'])[:16]}"
                dispatch=db.execute("SELECT * FROM roadmap_dispatch WHERE approval_key=?",(key,)).fetchone()
                if (not early_window(task,before-1) or key!=expected or early_job['state']!='running'
                        or early_job['mode']!='build' or early_job['chat_id']!=request['chat_id']
                        or not same_workspace(early_job['project'],request['project'])
                        or not dispatch or dispatch['state']!='ready' or dispatch['job_id']!=early_job['id']
                        or dispatch['request_id']!=request['id'] or dispatch['ordinal']!=before-1):
                    raise ValueError('No exact approved private preparation window')
                db.execute("INSERT INTO project_midi_prepare_v58 VALUES(?,?,?,?)",
                           (lease,early_job['id'],key,canonical_sha(contract)))
            db.execute("INSERT INTO project_midi_v45(task_id,request_id,lease,contract,contract_sha,state) VALUES(?,?,?,?,?,'assigned')",
                       (task['id'],request['id'],lease,json.dumps(contract,ensure_ascii=False),canonical_sha(contract)))
        return lease,contract

    def status(self,task_id):
        with self.runs.db() as db:
            row,_=self._row(db,task_id)
            return row['state'] if row else None

    def live(self,lease):
        with self.runs.db() as db:
            row=db.execute("""SELECT 1 FROM project_midi_v45 m JOIN roadmap_runs r ON r.request_id=m.request_id
                WHERE m.lease=? AND m.state='assigned' AND r.state='active' AND r.creative_midi=1""",(lease,)).fetchone()
            return bool(row)

    def _staged(self,contract,folder,receipt):
        data=self.delegations._artifact(folder,receipt,{'requester':'janus','scope':contract['scope'],'brief':contract['brief']})
        raw=(Path(data['folder'])/'score.mid').read_bytes()
        score=inspect_midi(raw)
        if hashlib.sha256(raw).hexdigest()!=receipt['sha256'] or score['bpm']!=receipt['bpm'] or len(score['notes'])!=receipt['notes']:
            raise ValueError('Native score receipt disagrees with decoded notes')
        observed={'bpm':score['bpm'],'notes':len(score['notes'])}
        for key,wanted in contract['task'].get('acceptance',{}).items():
            if observed[key]!=wanted:raise ValueError('MIDI requirement mismatch: '+key)
        return data,raw,score

    def reviewed(self,lease,contract,folder,receipt,review):
        data,_,score=self._staged(contract,folder,receipt)
        proposal=review_text(contract,score)
        if (review.get('accepted') is not True or review.get('verified') is not False
            or review.get('original_sha')!=contract['original_sha']
            or review.get('proposal_sha')!=sha(proposal)
            or not isinstance(review.get('evidence_sha'),str) or len(review['evidence_sha'])!=64):
            raise ValueError('Independent Sentinel score review does not match assignment')
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,bound=self._row(db,contract['task']['id'])
            if not row or row['lease']!=lease or row['state']!='assigned' or bound!=contract:
                raise ValueError('Stale MIDI review')
            prep=db.execute("SELECT * FROM project_midi_prepare_v58 WHERE lease=?",(lease,)).fetchone()
            if prep and (prep['contract_sha']!=canonical_sha(contract) or not early_window(contract['task'],contract['before']-1)):
                raise ValueError('Private preparation binding changed')
            state='prepared' if prep else 'reviewed'
            db.execute("UPDATE project_midi_v45 SET state=?,staged=?,review=? WHERE lease=?",
                       (state,json.dumps(data),json.dumps(review),lease))

    def publish_prepared(self,run,plan,task,request,conversations,hierarchies,index,jobs,workflows,*,enabled):
        """Reopen the original publication gate; never replay generation or a write."""
        from .roadmap_runs import eligible_successor
        from .roadmap_tool_bridge import gate
        from .mixed_roadmap import pending_task
        if not enabled:raise PermissionError('Approved project work disabled')
        result=eligible_successor(run,request,conversations,hierarchies,index,jobs)
        if not result:raise ValueError('Private score awaits its original verified publication boundary')
        before=(hierarchies.status(index,request['id'],request['prompt'])['milestones_total']+1
                if result['complete'] else result['milestone']['ordinal'])
        current=self._identity(run,plan,task,request,before)
        if gate(workflows,request['id'],result['manifest_sha256'],before) or pending_task(plan,workflows,before,creative=self)!=task:
            raise ValueError('An earlier publication dependency remains unresolved')
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,bound=self._row(db,task['id'])
            now=db.execute("SELECT * FROM roadmap_runs WHERE request_id=?",(request['id'],)).fetchone()
            if (not row or row['state']!='prepared' or bound!=current or not now
                    or self._identity(dict(now),plan,task,request,before)!=current):
                raise ValueError('Prepared score scope changed')
            lease=row['lease']
            prep=db.execute("SELECT * FROM project_midi_prepare_v58 WHERE lease=?",(lease,)).fetchone()
            if not prep or prep['contract_sha']!=canonical_sha(current) or not early_window(task,before-1):
                raise ValueError('Missing exact private preparation receipt')
            dispatch=db.execute("SELECT * FROM roadmap_dispatch WHERE approval_key=?",(prep['approval_key'],)).fetchone()
            if (not dispatch or dispatch['state']!='ready' or dispatch['job_id']!=prep['job_id']
                    or dispatch['request_id']!=request['id'] or dispatch['ordinal']!=before-1):
                raise ValueError('Private preparation predecessor changed')
            db.execute("UPDATE project_midi_v45 SET state='reviewed' WHERE lease=?",(lease,))
        return self.publish(lease,run,plan,task,request,before,enabled=enabled)

    def publish(self,lease,run,plan,task,request,before,*,enabled):
        if not enabled:raise PermissionError('Approved project work disabled')
        current=self._identity(run,plan,task,request,before)
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row,contract=self._row(db,task['id'])
            now=db.execute('SELECT * FROM roadmap_runs WHERE request_id=?',(request['id'],)).fetchone()
            if (not row or row['lease']!=lease or row['state']!='reviewed' or contract!=current
                or not now or self._identity(dict(now),plan,task,request,before)!=contract):
                raise ValueError('Stale or changed project MIDI publication')
            data=json.loads(row['staged']);review=json.loads(row['review'])
            _,raw,score=self._staged(contract,data['folder'],data['receipt'])
            if (review.get('accepted') is not True or review.get('verified') is not False
                or review.get('original_sha')!=contract['original_sha'] or review.get('proposal_sha')!=sha(review_text(contract,score))
                or not isinstance(review.get('evidence_sha'),str) or len(review['evidence_sha'])!=64):
                raise ValueError('Score review receipt changed')
            _,target=_safe_auto_path(Path(contract['project']),task['output'])
            if target.exists():raise ValueError('Destination appeared after approval')
            db.execute("UPDATE project_midi_v45 SET state='publishing' WHERE lease=?",(lease,))
        # Durable publishing state first. An interrupted write cannot be retried.
        target.parent.mkdir(parents=True,exist_ok=True)
        _,again=_safe_auto_path(Path(contract['project']),task['output'])
        if again!=target or target.exists():raise ValueError('Destination changed before publication')
        fd,name=tempfile.mkstemp(prefix='.deepthort-midi-',suffix='.tmp',dir=target.parent)
        tmp=Path(name)
        try:
            with os.fdopen(fd,'wb') as out:
                out.write(raw);out.flush();os.fsync(out.fileno())
            # Exclusive atomic new-file publication; never replace existing bytes.
            os.link(tmp,target)
        finally:tmp.unlink(missing_ok=True)
        observed=artifact(contract['project'],task['output'])
        if observed['sha256']!=data['receipt']['sha256']:raise ValueError('Published MIDI changed')
        result={'artifact':observed,'score':score,'review_sha':review['evidence_sha'],'runtime_verified':False}
        with self.runs.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("UPDATE project_midi_v45 SET state='checked',receipt=? WHERE lease=? AND state='publishing'",
                          (json.dumps(result),lease)).rowcount!=1:raise ValueError('Lost artifact publication lease')
        return result

    def fail(self,lease,reason):
        with self.runs.db() as db:
            db.execute("""UPDATE project_midi_v45 SET state=CASE WHEN state='publishing' THEN 'interrupted' ELSE 'blocked' END,
                detail=? WHERE lease=? AND state IN ('assigned','prepared','reviewed','publishing')""",(str(reason)[:400],lease))

    def integration_records(self,job,request,plan,*,exclude=(),limit=3):
        """Checked, earlier native artifacts for an exact automatically approved
        code milestone. No inferred dependency, new permission or path search.
        Legacy/manual jobs without a matching dispatch retain their old path.
        """
        from .inspection_exclusions import normalized_relative
        key=job.get('approval_key') or ''
        parts=key.split(':')
        if len(parts)!=4 or parts[0]!='milestone' or parts[1]!=str(request['id']):return []
        ordinal=int(parts[2])
        if job.get('state')!='running' or job.get('chat_id')!=request['chat_id'] or not same_workspace(job['project'],request['project']):
            raise ValueError('Media integration belongs to another project or job')
        with self.runs.db() as db:
            dispatch=db.execute("SELECT * FROM roadmap_dispatch WHERE approval_key=?",(key,)).fetchone()
            if not dispatch:return []
            if (dispatch['state']!='ready' or dispatch['job_id']!=job['id']
                or dispatch['request_id']!=request['id'] or dispatch['ordinal']!=ordinal):
                raise ValueError('Media integration milestone dispatch changed')
            run=db.execute("SELECT * FROM roadmap_runs WHERE request_id=?",(request['id'],)).fetchone()
            if not run or run['state']!='active':raise ValueError('Media integration roadmap is not active')
            run=dict(run)
        if not run['mixed_sha'] or run['creative_midi']!=1:return []
        if (not plan or plan['sha']!=run['mixed_sha'] or plan['code_sha']!=run['manifest_sha256']
                or plan['request_id']!=request['id'] or digest({k:v for k,v in plan.items() if k!='sha'})!=plan['sha']):
            raise ValueError('Media integration approval changed')
        result=[]
        for task in plan['tasks']:
            if task['after']>=ordinal or normalized_relative(task['output']) in exclude:continue
            with self.runs.db() as db:
                row,contract=self._row(db,task['id'])
            if not row:continue  # existing external workflow route is unchanged
            if (contract!=self._identity(run,plan,task,request,task['after']+1)
                    or row['state']!='checked'):
                raise ValueError('Earlier native artifact is not current and checked')
            _,target=_safe_auto_path(Path(run['project']),task['output'])
            if not target.is_file() or target.stat().st_size>4096:raise ValueError('Earlier native MIDI is missing or outside its checked profile')
            if self.checked(plan,task) is not True:raise ValueError('Earlier native artifact receipt missing')
            receipt=json.loads(row['receipt'])
            score=receipt['score']
            record={'path':task['output'],'sha256':receipt['artifact']['sha256'],
                    'bytes':receipt['artifact']['bytes'],'bpm':score['bpm'],'notes':len(score['notes']),
                    'task_id':task['id'],'request_id':request['id'],'before':ordinal,
                    'plan_sha':plan['sha'],'code_sha':plan['code_sha']}
            if len(result)<max(0,min(3,limit)):result.append(record)
        return result

    def checked(self,plan,task):
        """None = external workflow path; False = native attempt not complete."""
        with self.runs.db() as db:
            row,contract=self._row(db,task['id'])
            if not row:return None
            if contract['plan_sha']!=plan['sha'] or contract['code_sha']!=plan['code_sha'] or contract['task']!=task:
                raise ValueError('Native artifact belongs to another approved roadmap')
            if row['state']!='checked':return False
            result=json.loads(row['receipt'])
            staged=json.loads(row['staged']);review=json.loads(row['review'])
        if (result['runtime_verified'] is not False or result['artifact']['sha256']!=staged['receipt']['sha256']
                or result['review_sha']!=review.get('evidence_sha') or review.get('accepted') is not True
                or review.get('verified') is not False or review.get('original_sha')!=contract['original_sha']
                or review.get('proposal_sha')!=sha(review_text(contract,result['score']))):
            raise ValueError('Published MIDI review evidence changed')
        actual=artifact(contract['project'],task['output'])
        if actual!=result['artifact']:raise ValueError('Published project MIDI receipt stale')
        _,target=_safe_auto_path(Path(contract['project']),task['output'])
        score=inspect_midi(target.read_bytes())
        if score!=result['score']:raise ValueError('Published MIDI score changed')
        measured={'bpm':score['bpm'],'notes':len(score['notes'])}
        if any(measured[k]!=v for k,v in task.get('acceptance',{}).items()):raise ValueError('Published score acceptance changed')
        return True
