"""Roadmap-bound Gemma MIDI assignments. No arbitrary tools or overwrite rights.

The existing explicit roadmap approval includes an opt-in for this exact adapter.
Private staging, independent review and host publication are separate steps.
A lost generation or publication lease is never silently replayed.
"""
import json
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

def review_text(contract,score):
    return json.dumps({'task':contract['task'],'scope':contract['scope'],
        'score':score,'assurance':'bounded single-track MIDI; no audio playback or aesthetic verification'},
        ensure_ascii=False,sort_keys=True)

class ProjectMidi:
    def __init__(self,runs,delegations):
        self.runs=runs
        self.delegations=delegations
        with runs.db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS project_midi_v45(
                task_id TEXT PRIMARY KEY,request_id INTEGER NOT NULL,lease TEXT NOT NULL UNIQUE,
                contract TEXT NOT NULL,contract_sha TEXT NOT NULL,state TEXT NOT NULL,
                staged TEXT,review TEXT,receipt TEXT,detail TEXT NOT NULL DEFAULT '')""")

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

    def begin(self,run,plan,task,request,before,*,enabled):
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
            db.execute("UPDATE project_midi_v45 SET state='reviewed',staged=?,review=? WHERE lease=?",
                       (json.dumps(data),json.dumps(review),lease))

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
                detail=? WHERE lease=? AND state IN ('assigned','reviewed','publishing')""",(str(reason)[:400],lease))

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
