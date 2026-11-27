"""Local, inspectable JANUS coordinator and durable approved-process ledger.

Seven perspectives -> two hemispheres -> Front -> Interface (11 roles).
A cycle reads observed facts and *its own previous state*, not an unbounded
LLM-generated monologue. This deterministic metacognition costs no model tokens.
Executable actions require an explicit desktop user approval and are never
inferred from a model response. No networking or cloud model integration.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .janus_cognition import CORE_NAMES, SenseFrame, process_society
from . import interface_outbox
from .action_guards import validate_guards
APPROVED_KINDS = frozenset({'verification', 'tool'})
ACTION_STATES = frozenset({'approved', 'running', 'succeeded', 'failed', 'cancelled', 'paused', 'needs_attention'})


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class JanusStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
              CREATE TABLE IF NOT EXISTS janus_status (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                cycle INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                paused INTEGER NOT NULL DEFAULT 0,
                last_focus TEXT NOT NULL DEFAULT 'startup',
                last_action TEXT NOT NULL DEFAULT 'observe',
                last_observation TEXT NOT NULL DEFAULT '{}',
                cores_json TEXT NOT NULL DEFAULT '{}');
              CREATE TABLE IF NOT EXISTS janus_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stamp TEXT NOT NULL, cycle INTEGER NOT NULL,
                focus TEXT NOT NULL, decision TEXT NOT NULL, snapshot_json TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS janus_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER, kind TEXT NOT NULL,
                label TEXT NOT NULL, cwd TEXT NOT NULL, argv_json TEXT NOT NULL,
                approved_at TEXT NOT NULL, approval_source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'approved',
                output_file TEXT NOT NULL DEFAULT '',
                pid INTEGER, returncode INTEGER, cancel_requested INTEGER NOT NULL DEFAULT 0,
                started_at TEXT, finished_at TEXT,
                detail TEXT NOT NULL DEFAULT 'Waiting for engine',
                input_guards_json TEXT NOT NULL DEFAULT '[]');
              CREATE INDEX IF NOT EXISTS janus_action_status ON janus_actions(status,id);
              CREATE TABLE IF NOT EXISTS janus_goals (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                goal TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS janus_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evidence_key TEXT NOT NULL UNIQUE,
                job_id INTEGER, recorded_at TEXT NOT NULL,
                origin TEXT NOT NULL CHECK(origin IN ('janus','local_model')),
                status TEXT NOT NULL DEFAULT 'awaiting_review',
                problem TEXT NOT NULL, proposal TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS janus_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stamp TEXT NOT NULL, message TEXT NOT NULL);
            ''')
            interface_outbox.ensure_schema(db,'janus')
            # Preserve every historical action when upgrading an existing database.
            columns={row[1] for row in db.execute('PRAGMA table_info(janus_actions)')}
            if 'input_guards_json' not in columns:
                db.execute("ALTER TABLE janus_actions ADD COLUMN input_guards_json TEXT NOT NULL DEFAULT '[]'")
            db.execute("INSERT OR IGNORE INTO janus_status(singleton,updated_at) VALUES(1,?)", (utc_now(),))
            db.execute("INSERT OR IGNORE INTO janus_goals(singleton,updated_at) VALUES(1,?)", (utc_now(),))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.execute('PRAGMA busy_timeout=15000')
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        finally:
            db.close()

    def interface_messages(self,limit=20,*,unread_first=False):
        with self.connect() as db:return interface_outbox.messages(db,limit,unread_first=unread_first)

    def interface_unread(self):
        with self.connect() as db:return interface_outbox.unread(db)

    def acknowledge_interface(self,ids):
        with self.connect() as db:return interface_outbox.mark_read(db,ids,utc_now())

    def status(self) -> dict:
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            row = db.execute('SELECT * FROM janus_status WHERE singleton=1').fetchone()
            return dict(row)

    def history(self, limit: int = 12) -> list[dict]:
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(
                'SELECT stamp,cycle,focus,decision FROM janus_cycles ORDER BY id DESC LIMIT ?',
                (min(100,max(1,limit)),))]

    def append_event(self, message: str) -> None:
        with self.connect() as db:
            db.execute('INSERT INTO janus_events(stamp,message) VALUES(?,?)', (utc_now(),str(message)[:1000]))
            db.execute('DELETE FROM janus_events WHERE id NOT IN (SELECT id FROM janus_events ORDER BY id DESC LIMIT 500)')

    def events(self, limit: int = 15) -> list[dict]:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute(
                'SELECT stamp,message FROM janus_events ORDER BY id DESC LIMIT ?', (max(1,min(limit,100)),))]

    def goal(self) -> str:
        with self.connect() as db:
            return str(db.execute('SELECT goal FROM janus_goals WHERE singleton=1').fetchone()[0])

    def set_goal(self, goal: str) -> None:
        if not isinstance(goal,str) or len(goal)>1000:raise ValueError('Goal must be at most 1000 characters')
        with self.connect() as db:
            db.execute('UPDATE janus_goals SET goal=?,updated_at=? WHERE singleton=1',
                       (goal.strip(),utc_now()))
        self.append_event('JANUS primary goal updated by user' if goal.strip() else 'JANUS primary goal unpinned')

    def recommend(self, *, evidence_key: str, problem: str, proposal: str,
                  job_id: int | None=None, origin: str='janus') -> bool:
        if origin not in ('janus','local_model'):raise ValueError('Untrusted recommendation origin')
        if not evidence_key or not problem.strip() or not proposal.strip():raise ValueError('Missing evidence or suggestion')
        with self.connect() as db:
            changed=db.execute("""INSERT OR IGNORE INTO janus_recommendations(
              evidence_key,job_id,recorded_at,origin,problem,proposal) VALUES(?,?,?,?,?,?)""",
              (evidence_key[:120],job_id,utc_now(),origin,problem[:700],proposal[:2000])).rowcount
        if changed:
            self.append_event(f'JANUS {origin} proposed alternative for review: {problem[:180]}')
            with self.connect() as db:
                db.execute('DELETE FROM janus_recommendations WHERE id NOT IN '
                           '(SELECT id FROM janus_recommendations ORDER BY id DESC LIMIT 500)')
        return bool(changed)

    def recommendations(self, limit: int=10) -> list[dict]:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute("""SELECT * FROM janus_recommendations
                ORDER BY id DESC LIMIT ?""",(max(1,min(limit,50)),))]

    def set_paused(self, value: bool) -> None:
        with self.connect() as db:
            db.execute('UPDATE janus_status SET paused=?,updated_at=? WHERE singleton=1',
                       (int(value),utc_now()))
        self.append_event('JANUS paused by user' if value else 'JANUS resumed by user')

    def add_approved_action(self, *, argv: Sequence[str], cwd: str | Path,
                            label: str, kind: str, job_id: int | None = None,
                            user_approved: bool = False,
                            input_guards: list[dict] | None = None) -> int:
        """The GUI must call this only *after* an affirmative user confirmation.

        This is not callable by a free-form model/tool plan without an approval.
        """
        if not user_approved:
            raise PermissionError('Explicit local user approval is required to queue a process')
        if kind not in APPROVED_KINDS:
            raise ValueError('Unsupported JANUS process kind')
        if not argv or len(argv)>24 or not all(isinstance(x,str) and 0<len(x)<4096 for x in argv):
            raise ValueError('Command requires a bounded argument vector')
        if not label or len(label)>180:
            raise ValueError('Invalid process label')
        guards = validate_guards(input_guards)
        working = Path(cwd).resolve(strict=True)
        if not working.is_dir():
            raise ValueError('Working directory must be an existing folder')
        with self.connect() as db:
            ident=db.execute('''INSERT INTO janus_actions(
                job_id,kind,label,cwd,argv_json,approved_at,approval_source,input_guards_json)
                VALUES (?,?,?,?,?,?,?,?)''',
                (job_id,kind,label,str(working),json.dumps(list(argv)),utc_now(),
                 'desktop-user-confirmation',json.dumps(guards))).lastrowid
        self.append_event(f'Approved process #{ident}: {label}')
        return ident

    def pending_git_action(self):
        # Hold desktop project dispatch while a reviewed Git action owns the repository.
        with self.connect() as db:
            return db.execute("SELECT 1 FROM janus_actions WHERE (label LIKE 'Git: reviewed %' OR label IN ('Integration: reviewed Python suite','Coverage: reviewed Python suite','Profile: reviewed Python suite','Security: reviewed dependency audit','Security: reviewed source scan','Document: reviewed PDF page edit','Document: reviewed PDF production','Document: reviewed PDF table extraction','Document: reviewed conversion','Document: reviewed comparison','Spreadsheet: reviewed cell edit','Database: reviewed schema','Spreadsheet: reviewed creation','Spreadsheet: reviewed formulas','Data: reviewed CSV processing','Database: reviewed query','Data: reviewed cleaning','Data: reviewed transformation','Presentation: reviewed edit','Presentation: reviewed creation','Presentation: reviewed template','Document: reviewed manuscript','Document: reviewed Word production','Document: reviewed bibliography','Data: reviewed interactive table','Data: reviewed chart','Data: reviewed interactive chart','Data: reviewed mathematics','Data: reviewed statistics','Data: reviewed exploration','Data: reviewed analytical report','Audio: reviewed tempo','Audio: reviewed metadata','Audio: reviewed key','Audio: reviewed noise reduction','Audio: reviewed conversion','Texture: reviewed normal map','Texture: reviewed height map','Mesh: reviewed UV atlas','Mesh: reviewed simplification','Mesh: reviewed conversion','Image: reviewed composition','Image: reviewed enhancement','Image: reviewed logo','Image: reviewed infographic','Image: reviewed batch','Video: reviewed sequence','Image: reviewed background removal','Image: reviewed background replacement','Image: reviewed OCR','Research: reviewed search evidence','Research: reviewed webpage','Research: reviewed image discovery','Research: reviewed citation check','Research: reviewed academic discovery','Research: reviewed website crawl','Research: reviewed multi-source evidence','Research: reviewed source credibility','Research: reviewed source comparison','Research: reviewed report','Research: reviewed latent vectors','Research: reviewed knowledge graph','Research: reviewed relationship discovery','Research: reviewed PDF diagrams','Document: reviewed layout inspection','Document: reviewed clause evidence','Document: reviewed raster checks','Data: reviewed predictive model','Data: reviewed scientific calculation','Data: reviewed anomaly candidates','Data: reviewed time-series forecast','Data: reviewed notebook export','Database: reviewed live read','Development: reviewed API contract','Development: reviewed API tests')) AND status IN ('approved','running') LIMIT 1").fetchone() is not None

    def actions(self, limit: int = 25) -> list[dict]:
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(x) for x in db.execute('SELECT * FROM janus_actions ORDER BY id DESC LIMIT ?', (limit,))]

    def action(self, ident: int) -> dict | None:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            row=db.execute('SELECT * FROM janus_actions WHERE id=?',(ident,)).fetchone()
            return dict(row) if row else None

    def cancel_action(self, ident: int) -> bool:
        with self.connect() as db:
            changed=db.execute('''UPDATE janus_actions SET
                    cancel_requested=1,status=CASE WHEN status='approved' THEN 'cancelled' ELSE status END,
                    detail=CASE WHEN status='approved' THEN 'Cancelled before execution' ELSE 'Cancellation requested' END
                    WHERE id=? AND status IN ('approved','running')''',(ident,)).rowcount
        if changed:self.append_event(f'Cancellation requested for approved process #{ident}')
        return bool(changed)

    def claim_next_action(self) -> dict | None:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            row=db.execute("SELECT * FROM janus_actions WHERE status='approved' AND cancel_requested=0 ORDER BY id LIMIT 1").fetchone()
            if row is None:return None
            # A workflow designed against a stored specification must not start
            # an obsolete queued process after a user amendment or restart.
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tool_workflow_stages'").fetchone()
            if exists:
                wf=db.execute('SELECT w.id,w.state,w.manifest FROM tool_workflow_stages s JOIN tool_workflows w ON w.id=s.workflow_id WHERE s.action_id=?',(row['id'],)).fetchone()
                if wf:
                    manifest=json.loads(wf['manifest'])
                    binding=manifest.get('specification')
                    valid=wf['state']=='active'
                    if binding and valid:
                        try:
                            from .workflow_design import current_source_file
                            source_path=self.path.parent/'conversations.sqlite3'
                            valid=source_path.is_file() and current_source_file(binding,source_path)
                        except (ValueError,OSError,sqlite3.Error,KeyError):valid=False
                    if not valid:
                        db.execute("UPDATE janus_actions SET status='cancelled',cancel_requested=1,detail='Workflow consent superseded' WHERE id=? AND status='approved'",(row['id'],))
                        db.execute("UPDATE tool_workflows SET state='cancelled',detail='Workflow consent superseded' WHERE id=? AND state='active'",(wf['id'],))
                        return None
            probe_table=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='asset_probe_runs'").fetchone()
            if probe_table:
                probe=db.execute('SELECT plan,plan_sha FROM asset_probe_runs WHERE action_id=?',(row['id'],)).fetchone()
                if probe:
                    try:
                        from .tool_workflows import digest
                        from .workflow_design import current_source_file
                        plan=json.loads(probe['plan'])
                        binding=plan.get('specification')
                        valid=(digest(plan)==probe['plan_sha'] and json.loads(row['argv_json'])==plan['argv']
                               and json.loads(row['input_guards_json'])==plan['guards'] and row['cwd']==plan['project'])
                        if binding and valid:
                            valid=current_source_file(binding,self.path.parent/'conversations.sqlite3')
                        if valid and plan.get('automatic_authority'):
                            from .asset_import_probe import claim_auto_authority
                            if not claim_auto_authority(self,plan,plan['automatic_authority']):
                                return None
                    except (ValueError,OSError,sqlite3.Error,KeyError,TypeError):valid=False
                    if not valid:
                        db.execute("UPDATE janus_actions SET status='cancelled',cancel_requested=1,detail='Asset probe approval changed or superseded' WHERE id=?",(row['id'],))
                        return None
            updated=db.execute("UPDATE janus_actions SET status='running', started_at=?, detail='Engine starting approved process' WHERE id=? AND status='approved'",(utc_now(),row['id']))
            return dict(row) if updated.rowcount else None

    def update_action(self, ident: int, status: str, *, detail: str,
                      returncode: int | None = None, pid: int | None = None,
                      output_file: str | None = None) -> None:
        if status not in ACTION_STATES:
            raise ValueError('Unknown action status')
        with self.connect() as db:
            db.execute('''UPDATE janus_actions SET status=?,detail=?,returncode=COALESCE(?,returncode),
                       pid=COALESCE(?,pid),output_file=COALESCE(?,output_file),
                       finished_at=CASE WHEN ? IN ('succeeded','failed','cancelled','paused','needs_attention')
                       THEN ? ELSE finished_at END WHERE id=?''',
                       (status,detail,returncode,pid,output_file,status,utc_now(),ident))
        if status in ('succeeded','failed','cancelled','paused','needs_attention'):
            self.append_event(f'Process #{ident} {status}: {detail}')

    def recover_interrupted_actions(self) -> int:
        """Only call once when a freshly launched *sole* JANUS worker starts.

        Never automatically re-run partial file-writing commands after a crash.
        """
        with self.connect() as db:
            count=db.execute("UPDATE janus_actions SET status='needs_attention',detail='Previous engine shut down mid-process; inspect logs before retry',finished_at=? WHERE status='running'",(utc_now(),)).rowcount
        if count:self.append_event(f'Recovered {count} interrupted process(es) as needs_attention')
        return count

    def observe_jobs(self, job_db: str | Path) -> list[dict]:
        p=Path(job_db)
        if not p.is_file():return []
        db=sqlite3.connect(f'file:{p.resolve().as_posix()}?mode=ro', uri=True,timeout=10)
        try:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute('''SELECT id,project,mode,state,detail,
                 updated_at FROM jobs ORDER BY id DESC LIMIT 120''')]
        except sqlite3.Error:return []
        finally:db.close()

    def tick(self, job_db: str | Path, *, gaming: bool = False,
             observed_processes: list[str] | None = None) -> dict:
        """Run canonical 11 outer cores × 7 inner faculties, preserving prior Front.

        Observed job/action results drive new sensory frames; no worker uses
        unverified model prose to declare code successfully built.
        """
        old=self.status()
        if old['paused']:
            return {'paused':True,'cycle':old['cycle'],'focus':old['last_focus'],
                    'decision':'user_paused'}
        jobs=self.observe_jobs(job_db)
        from .planning_recovery import observe_planning
        plans=observe_planning(job_db)
        from .delegation_senses import observe_delegation,active_work,conflict,observe_project_assignments,observe_project_midi
        delegation=observe_delegation(job_db)
        project_assignments=observe_project_assignments(job_db)
        project_midi=observe_project_midi(job_db)
        from .memory_duty import observe_memory_duties
        memory_duties=observe_memory_duties(job_db)
        from .conversation_memory import observations as conversation_memory_observations
        memory_duties['conversation_reports']=conversation_memory_observations(job_db)
        from .worker_reports import observe_worker_reports
        worker_reports=observe_worker_reports(job_db)
        from .corrective_coordination import observe as observe_corrections
        corrective_assignments=observe_corrections(job_db)
        team_active=active_work(delegation)
        team_conflict=conflict(delegation)
        active_plans=[p for p in plans if p['state'] in ('pending','running')]
        failed_plans=[p for p in plans if p['state']=='failed']
        source_wait=[p for p in plans if p['state']=='waiting_sources']
        actions=self.actions(limit=100)
        counts={state:sum(j['state']==state for j in jobs) for state in (
            'queued','running','paused','needs_input','waiting_approval','waiting_verification','failed','complete')}
        awaiting=[j for j in jobs if j['state'] in ('needs_input','waiting_approval','waiting_verification')]
        failures=[j for j in jobs if j['state']=='failed']
        action_failed=[a for a in actions if a['status'] in ('failed','needs_attention')]
        active=[a for a in actions if a['status']=='running']
        approved=[a for a in actions if a['status']=='approved']
        in_progress=[j for j in jobs if j['state'] in ('running','queued')]
        # Keep a concrete user goal; choosing a new job does not overwrite it.
        pinned_goal=self.goal()
        current=in_progress[0] if in_progress else awaiting[0] if awaiting else failures[0] if failures else None
        plan=next(iter(active_plans or source_wait or failed_plans),None)
        goal=pinned_goal or (f"Finish draft #{plan['id']} for {plan['project']}" if plan and (active_plans or not current)
             else f"Finish job #{current['id']}: {current['mode']} for {current['project']}" if current else 'Await user-directed work')
        alerts=[]
        if gaming and (in_progress or active or approved or team_active):
            focus='gaming_priority'; decision='defer_disk_heavy_work'
            alternatives=['Preserve job state and defer work while a game is active']
        elif active:
            focus=f"approved_process_{active[0]['id']}";decision='monitor_process_and_verify_exit'
            alternatives=['Wait for verifiable exit status','Check log for errors']
        elif team_active and not team_conflict:
            focus='delegated_team_work';decision='coordinate_dependency_ready_assignments'
            alternatives=['Observe role leases and accepted dependency receipts','Keep independent work progressing under existing authority','Use Sentinel review before integrating staged outputs']
        elif project_midi['active']:
            focus='project_creative_production';decision='coordinate_native_artifact_review'
            alternatives=['Observe Gemma generation and exact Sentinel review','Wait for host publication receipt','Preserve project boundary and current specification']
        elif active_plans:
            focus=f"draft_{active_plans[0]['id']}_planning";decision='monitor_requirements_and_reframe_failed_steps'
            alternatives=['Observe indexed progress','Retranslate failed objectives against original requirements','Use Sentinel review before changing strategy']
        elif worker_reports['reports']:
            focus='worker_dependency_coordination';decision='appraise_worker_dependency'
            alternatives=['Inspect exact scoped worker claim','Determine whether missing evidence or an actual dependency prevents progress','Coordinate existing authorized resources; request new authority only if necessary']
        elif awaiting:
            focus=f"job_{awaiting[0]['id']}_requires_user";decision='request_approval_or_guidance'
            alternatives=['Report the exact blocked step','Ask user to review the proposed action or revise the specification']
        elif approved:
            focus=f"approved_process_{approved[0]['id']}";decision='execute_approved_process'
            alternatives=['Run only the exact approved executable with its recorded arguments']
        elif counts['running'] and project_assignments['active']:
            focus='project_role_production';decision='coordinate_reviewed_project_assignment'
            alternatives=['Observe scoped production and Sentinel receipts','Retain approved dependency evidence','Require host save and actual test evidence']
        elif counts['running']:
            focus='model_work_in_progress';decision='monitor_and_record_outcome'
            alternatives=['Check response against specification','Record independent test outcome']
        elif counts['queued']:
            focus='queued_work';decision='wait_for_local_model_and_dispatch'
            alternatives=['Confirm local model is ready','Retain queued request without pretending it ran']
        elif action_failed:
            focus=f"approved_process_{action_failed[0]['id']}_failed";decision='inspect_failure_and_propose_repair'
            alternatives=['Inspect the captured process output','Identify the failing tool and propose a scoped repair','Ask for approval before rerunning']
        elif failures:
            focus=f"job_{failures[0]['id']}_failed";decision='diagnose_failure_and_propose_alternatives'
            alternatives=['Identify the failure from the queue detail','Propose an alternative implementation','Request approval for any new tool or file write']
        elif team_conflict or delegation['failed']:
            focus='delegated_team_review';decision='inspect_delegation_failure'
            alternatives=['Check interrupted or stale task receipts','Preserve completed artifacts; require explicit retry where necessary']
        elif source_wait:
            focus=f"draft_{source_wait[0]['id']}_waiting_sources";decision='inspect_missing_source_evidence'
            alternatives=['Preserve original requirements','Wait for required source inspection']
        elif failed_plans:
            focus=f"draft_{failed_plans[0]['id']}_failed";decision='diagnose_and_reframe_incomplete_plan'
            alternatives=['Review durable planning failures','Resume only eligible bounded recovery','Keep unresolved acceptance checks visible']
        else:
            focus='idle';decision='sleep_until_new_evidence';alternatives=['Monitor for new evidence']
        if team_conflict or delegation['failed']:alerts.append('Delegated work requires evidence-based review; no automatic replay')
        if failed_plans:alerts.append('Unfinished draft planning requires evidence-based recovery')
        if failures or action_failed:
            alerts.append('Prioritize documented failure and verification before advancing')
        if awaiting:alerts.append('User decision required')
        previous=json.loads(old['cores_json'] or '{}')
        previous_front=previous.get('Front',{})
        previous_observation=json.loads(old['last_observation'] or '{}')
        from .society_stimuli import observe_stimuli,stimulus_frame
        stimuli=observe_stimuli(job_db,previous_observation.get('stimuli'))
        # Stable snapshots ignore volatile PID/time fields so cycles can tell
        # whether meaningful evidence changed.
        observation={'counts':counts,'failed':bool(failures or action_failed or failed_plans or delegation['failed']),
            'delegation':delegation,'conflict':team_conflict,'project_assignments':project_assignments,'project_midi':project_midi,'memory_duties':memory_duties,'worker_reports':worker_reports,'corrective_assignments':corrective_assignments,'stimuli':stimuli,
            'planning_counts':{state:sum(p['state']==state for p in plans)
                              for state in ('pending','running','waiting_sources','failed')},
            'current_draft':{k:plan[k] for k in ('id','state','detail')} if plan else None,
            'waiting_approval':bool(awaiting),'requires_user':bool(awaiting),
            'pending_approved_actions':len(approved),'active_actions':len(active),
            'game_detected':bool(gaming),
            'current_job':{k:current.get(k) for k in ('id','mode','state','detail') } if current else None,
            'latest_actions':[{'id':a['id'],'status':a['status'],'returncode':a['returncode']}
                              for a in actions[:8]],'alerts':alerts}
        frames=[SenseFrame('runtime','job_queue',
                f'Goal: {goal}; focus: {focus}; decision: {decision}; evidence: {counts}',
                salience=.85 if alerts else .4, uncertainty=.6 if alerts else .15)]
        if delegation['available'] and (team_active or delegation['failed'] or delegation['recent']):
            frames.append(SenseFrame('runtime','delegation_graph',
                json.dumps(delegation,sort_keys=True),salience=.9 if team_conflict else .65,
                uncertainty=.65 if team_conflict or delegation['failed'] else .2))
        if project_assignments['available'] and (project_assignments['active'] or project_assignments['recent']):
            frames.insert(1,SenseFrame('runtime','project_role_assignments',json.dumps(project_assignments,sort_keys=True),salience=.7,uncertainty=.3))
        if project_midi['active'] or project_midi['recent']:
            frames.insert(1,SenseFrame('runtime','project_creative_assignments',json.dumps(project_midi,sort_keys=True),salience=.75,uncertainty=.3))
        if worker_reports['reports']:
            frames.insert(1,SenseFrame('peer','production_worker_dependency_report',json.dumps(worker_reports['reports'][:2],sort_keys=True),salience=.85,uncertainty=.7))
        if worker_reports['notices']:
            frames.insert(1,SenseFrame('peer','production_worker_nonblocking_notice',json.dumps(worker_reports['notices'][:2],sort_keys=True),salience=.65,uncertainty=.7))
        if memory_duties['reports']:
            frames.insert(1,SenseFrame('memory','fifth_worker_findings',json.dumps(memory_duties['reports'],sort_keys=True),salience=.8,uncertainty=.5))
        for action in actions[:3]:
            if action['status'] in ('succeeded','failed','needs_attention','cancelled'):
                frames.append(SenseFrame('action_result',f"approved_process_{action['id']}",
                    f"{action['status']}; exit={action['returncode']}; {action['detail'][:300]}",
                    salience=.9 if action['status']!='succeeded' else .6,
                    uncertainty=.65 if action['status']=='needs_attention' else .2))
        stimulus=stimulus_frame(stimuli)
        if stimulus:frames.insert(0,stimulus)
        with self.connect() as db:
            findings=interface_outbox.pending(db,'janus')
        if findings:
            frames.append(SenseFrame('runtime','janus_findings',
                f'{len(findings)} new recorded advisory findings await independent outward appraisal.',
                salience=.75,uncertainty=.5))
        from .core_deliberation import snapshot as neural_snapshot
        society=process_society(society='janus',observation=observation,frames=frames,
            neural=neural_snapshot(job_db,'janus'),
            previous_front=previous_front,previous_observation=previous_observation,
            previous_cores=previous,
            focus=focus,decision=decision,goal=goal,alternatives=alternatives,findings=findings)
        cycle=old['cycle']+1
        society['cycle']=cycle;society['stamp']=utc_now()
        with self.connect() as db:
            db.execute("""UPDATE janus_status SET cycle=?,updated_at=?,last_focus=?,
                last_action=?,last_observation=?,cores_json=? WHERE singleton=1""",
                (cycle,society['stamp'],focus,decision,json.dumps(observation),json.dumps(society['cores'])))
            interface_outbox.publish(db,'janus',society,cycle,society['stamp'])
            if society['cores']['Front']['changed_from_prior'] or society['peer_exchange']['changed'] or cycle==1 or cycle%6==0:
                db.execute('INSERT INTO janus_cycles(stamp,cycle,focus,decision,snapshot_json) VALUES(?,?,?,?,?)',
                           (society['stamp'],cycle,focus,decision,json.dumps(society)))
            db.execute('DELETE FROM janus_cycles WHERE id NOT IN (SELECT id FROM janus_cycles ORDER BY id DESC LIMIT 1000)')
        # Alternate remedies are durable and bound to observed failures, not
        # injected into the execution queue. No unauthorized retries.
        if failures or action_failed:
            target=action_failed[0] if action_failed else failures[0]
            ident=f"action-{target['id']}" if action_failed else f"job-{target['id']}"
            msg=str(target.get('detail') or 'Failed operation')
            key=f'{ident}-{__import__("hashlib").sha256(msg.encode()).hexdigest()[:24]}'
            self.recommend(evidence_key=key,job_id=None if action_failed else target['id'],
                problem=msg,proposal='; '.join(alternatives))
        return society
