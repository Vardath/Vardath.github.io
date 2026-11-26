"""JANUS Sentinel: independent, local-only observer of the JANUS worker.

One authority: JANUS worker owns approved actions. Sentinel never submits,
modifies, or automatically retries jobs. It may start/restart only the JANUS
worker after a confirmed process exit, with bounded backoff and durable logs.
A live-but-unresponsive worker is *not* killed automatically; user review is
required because an approved tool process might still be executing.
"""
from __future__ import annotations

import json
import hashlib
import os
import sqlite3
import subprocess
import sys
import time
import threading
from datetime import timedelta
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from . import interface_outbox
from .janus_cognition import SenseFrame, process_society
from .janus_counsel import LocalCounsel


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class SentinelStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sentinel_status (
              singleton INTEGER PRIMARY KEY CHECK (singleton=1),
              state TEXT NOT NULL DEFAULT 'starting',
              detail TEXT NOT NULL DEFAULT 'Sentinel initializing',
              updated_at TEXT NOT NULL,
              sentinel_pid INTEGER,
              janus_pid INTEGER,
              restart_count INTEGER NOT NULL DEFAULT 0,
              last_janus_cycle INTEGER NOT NULL DEFAULT 0,
              janus_updated_at TEXT,
              gui_updated_at TEXT);
            CREATE TABLE IF NOT EXISTS sentinel_recommendations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              evidence_key TEXT UNIQUE NOT NULL,
              recorded_at TEXT NOT NULL,
              origin TEXT NOT NULL,
              finding TEXT NOT NULL,
              proposal TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS sentinel_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              stamp TEXT NOT NULL, level TEXT NOT NULL,
              description TEXT NOT NULL);
            ''')
            db.execute('INSERT OR IGNORE INTO sentinel_status(singleton,updated_at) VALUES (1,?)',(utc_now(),))
            interface_outbox.ensure_schema(db,'sentinel')
            # Additive schema migration. Existing v9 recovery history is retained.
            cols={row[1] for row in db.execute('PRAGMA table_info(sentinel_status)')}
            for name,ddl in (
                 ('cycle','INTEGER NOT NULL DEFAULT 0'),
                 ('focus',"TEXT NOT NULL DEFAULT 'startup'"),
                 ('decision',"TEXT NOT NULL DEFAULT 'observe'"),
                 ('goal',"TEXT NOT NULL DEFAULT ''"),
                 ('society_json',"TEXT NOT NULL DEFAULT '{}'"),
                 ('observation_json',"TEXT NOT NULL DEFAULT '{}'"),
                 ('last_fingerprint',"TEXT NOT NULL DEFAULT ''"),
                 ('society_updated_at',"TEXT NOT NULL DEFAULT ''")):
                if name not in cols:db.execute(f'ALTER TABLE sentinel_status ADD COLUMN {name} {ddl}')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            db.execute('PRAGMA busy_timeout=10000')
            with db:yield db
        finally:db.close()

    def interface_messages(self,limit=20,*,unread_first=False):
        with self.connect() as db:return interface_outbox.messages(db,limit,unread_first=unread_first)

    def interface_unread(self):
        with self.connect() as db:return interface_outbox.unread(db)

    def acknowledge_interface(self,ids):
        with self.connect() as db:return interface_outbox.mark_read(db,ids,utc_now())

    def update(self, *, state: str, detail: str, sentinel_pid: int | None,
               janus_pid: int | None, restart_count: int,
               last_janus_cycle: int=0, janus_updated_at: str | None=None,
               gui_updated_at: str | None=None):
        with self.connect() as db:
            db.execute('''UPDATE sentinel_status SET state=?,detail=?,updated_at=?,
              sentinel_pid=?,janus_pid=?,restart_count=?,last_janus_cycle=?,
              janus_updated_at=?,gui_updated_at=? WHERE singleton=1''',
              (state,detail[:500],utc_now(),sentinel_pid,janus_pid,restart_count,
               last_janus_cycle,janus_updated_at,gui_updated_at))

    def reflect(self, *, observation: dict, focus: str, decision: str,
                goal: str, alternatives: list[str], neural=None) -> dict:
        """Independent 11×7 supervisory readout, never action authority.

        Sentinel evaluates evidence about work and health. It cannot queue
        approved commands, modify project files, or overwrite JANUS state.
        """
        old=self.snapshot()
        prev=json.loads(old.get('society_json') or '{}')
        previous_front=(prev.get('cores') or {}).get('Front',{})
        prior_observation=json.loads(old.get('observation_json') or '{}')
        frames=[SenseFrame('runtime','watchdog',
             f'JANUS health={observation.get("worker_state")}; goal={goal}; '
             f'work={observation.get("counts")}; warning={observation.get("warning")}',
             salience=.9 if observation.get('warning') else .4,
             uncertainty=.65 if observation.get('warning') else .2),
            SenseFrame('peer','janus_public_front',
             f'Observed JANUS: {observation.get("janus_focus")}; decision={observation.get("janus_decision")}',
             salience=.8 if observation.get('drift') else .4)]
        if observation.get('delegation',{}).get('available'):
            frames.append(SenseFrame('runtime','delegation_graph',
                 json.dumps(observation['delegation'],sort_keys=True),
                 salience=.9 if observation.get('conflict') else .65,
                 uncertainty=.65 if observation.get('conflict') or observation['delegation']['failed'] else .2))
        assignments=observation.get('project_assignments',{})
        if assignments.get('available') and (assignments.get('active') or assignments.get('recent')):
            frames.insert(1,SenseFrame('runtime','project_role_assignments',json.dumps(assignments,sort_keys=True),salience=.7,uncertainty=.3))
        creative=observation.get('project_midi',{})
        if creative.get('active') or creative.get('recent'):
            frames.insert(1,SenseFrame('runtime','project_creative_assignments',json.dumps(creative,sort_keys=True),salience=.75,uncertainty=.3))
        reports=observation.get('worker_reports',{}).get('reports',[])
        if reports:
            frames.insert(1,SenseFrame('peer','production_worker_dependency_report',json.dumps(reports[:2],sort_keys=True),salience=.85,uncertainty=.7))
        notices=observation.get('worker_reports',{}).get('notices',[])
        if notices:
            frames.insert(1,SenseFrame('peer','production_worker_nonblocking_notice',json.dumps(notices[:2],sort_keys=True),salience=.65,uncertainty=.7))
        memory=observation.get('memory_duties',{})
        if memory.get('reports'):
            frames.insert(1,SenseFrame('memory','fifth_worker_findings',json.dumps(memory['reports'],sort_keys=True),salience=.8,uncertainty=.5))
        # Worker cycles are proof of heartbeat, but are NOT a new finding on
        # each poll. Keep them out of the issue signature to avoid log spam.
        material={k:v for k,v in observation.items() if k!='janus_cycle'}
        from .society_stimuli import stimulus_frame
        stimulus=stimulus_frame(material.get('stimuli',{}))
        if stimulus:frames.insert(0,stimulus)
        with self.connect() as db:
            findings=interface_outbox.pending(db,'sentinel')
        if findings:
            frames.append(SenseFrame('runtime','sentinel_findings',
                f'{len(findings)} new recorded supervisory findings await independent outward appraisal.',
                salience=.75,uncertainty=.5))
        society=process_society(society='sentinel',observation=material,frames=frames,neural=neural,
            previous_front=previous_front,previous_observation=prior_observation,
            previous_cores=prev.get('cores',{}),
            focus=focus,decision=decision,goal=goal,alternatives=alternatives,findings=findings)
        fresh=(society['fingerprint']!=(prev.get('fingerprint') or ''))
        stamp=old.get('society_updated_at') or ''
        try:
            due=(datetime.now(timezone.utc)-datetime.fromisoformat(stamp)).total_seconds()>60
        except (TypeError,ValueError):due=True
        if not fresh and not due:return prev
        with self.connect() as db:
            db.execute("""UPDATE sentinel_status SET cycle=?,focus=?,decision=?,goal=?,
              society_json=?,observation_json=?,society_updated_at=? WHERE singleton=1""",
              (old['cycle']+1,focus,decision,goal,json.dumps(society),json.dumps(material),utc_now()))
            interface_outbox.publish(db,'sentinel',society,old['cycle']+1,utc_now())
            issue_signature=hashlib.sha256((str(observation.get('warning') or '')+'|'+goal).encode()).hexdigest()[:24]
            if (observation.get('warning') and
                (observation.get('drift') or observation.get('failed') or observation.get('requires_user'))
                and issue_signature!=old['last_fingerprint']):
                db.execute('UPDATE sentinel_status SET last_fingerprint=? WHERE singleton=1',
                           (issue_signature,))
                db.execute('INSERT INTO sentinel_events(stamp,level,description) VALUES (?,?,?)',
                           (utc_now(),'warning',str(observation['warning'])[:1200]))
        return society

    def recommend(self, evidence_key: str, finding: str, proposal: str,
                  origin: str='sentinel') -> bool:
        if origin not in ('sentinel','local_model'):
            raise ValueError('Unsupported advisory source')
        if not evidence_key or not finding or not proposal:raise ValueError('Missing advisory evidence')
        with self.connect() as db:
            changed=db.execute("""INSERT OR IGNORE INTO sentinel_recommendations(
                evidence_key,recorded_at,origin,finding,proposal) VALUES(?,?,?,?,?)""",
                (evidence_key[:100],utc_now(),origin,finding[:800],proposal[:1800])).rowcount
        if changed:
            with self.connect() as db:
                db.execute('DELETE FROM sentinel_recommendations WHERE id NOT IN '
                           '(SELECT id FROM sentinel_recommendations ORDER BY id DESC LIMIT 500)')
        return bool(changed)

    def recommendations(self, limit: int=10) -> list[dict]:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute('SELECT * FROM sentinel_recommendations ORDER BY id DESC LIMIT ?',
                                                 (max(1,min(limit,30)),))]

    def event(self, level: str, description: str):
        if level not in ('info','warning','error'):
            raise ValueError('Unknown sentinel event level')
        with self.connect() as db:
            db.execute('INSERT INTO sentinel_events(stamp,level,description) VALUES (?,?,?)',
                       (utc_now(),level,description[:1200]))
            db.execute('DELETE FROM sentinel_events WHERE id NOT IN (SELECT id FROM sentinel_events ORDER BY id DESC LIMIT 400)')

    def snapshot(self) -> dict:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            return dict(db.execute('SELECT * FROM sentinel_status WHERE singleton=1').fetchone())

    def events(self, limit: int = 12) -> list[dict]:
        with self.connect() as db:
            db.row_factory=sqlite3.Row
            return [dict(x) for x in db.execute('SELECT * FROM sentinel_events ORDER BY id DESC LIMIT ?',
                                                (min(100,max(1,limit)),))]


def janus_health(db_path: str | Path) -> dict:
    from .janus_engine import JanusStore
    # Query state only; JanusStore creates tables if not present, safely.
    try:return JanusStore(db_path).status()
    except (sqlite3.Error,OSError,ValueError):return {}


def gui_health(path: str | Path) -> dict:
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict):return {}
        return data
    except (OSError,ValueError,TypeError):return {}


class JanusSentinel:
    def __init__(self, *, sentinel_db: str | Path, janus_db: str | Path,
                 jobs_db: str | Path, games_file: str | Path,
                 gui_heartbeat: str | Path, worker_command: list[str] | None=None,
                 max_restarts: int=3, restart_window: float=600,
                 loop_interval: float=3, stall_after: float=90,
                 work_stall_after: float=1800):
        self.store=SentinelStore(sentinel_db)
        self.janus_db=Path(janus_db)
        self.jobs_db=Path(jobs_db)
        self.games_file=Path(games_file)
        self.gui_heartbeat=Path(gui_heartbeat)
        self.worker_command=worker_command or [sys.executable,str(Path(__file__).resolve().parent.parent/'janus_worker.py'),
                      '--state',str(self.janus_db),'--jobs',str(self.jobs_db),
                      '--games',str(self.games_file),'--interval','10']
        if not 1<=max_restarts<=10 or loop_interval<=0:
            raise ValueError('Unsafe Sentinel settings')
        self.max_restarts=max_restarts
        self.restart_window=restart_window
        self.loop_interval=loop_interval
        self.stall_after=stall_after
        self.work_stall_after=work_stall_after
        self.restarts=deque()
        self.worker=None
        self.stopping=False
        self.last_healthy_cycle=0
        self.last_healthy_monotonic=time.monotonic()
        self.last_exit_reported=False
        self.warned_stale=False
        self.gui_missing_since=time.monotonic()
        self.gui_pause_logged=False
        self._counsel=LocalCounsel(Path(sentinel_db).parent/'janus-counsel.sqlite3')
        self._counsel_thread=None
        self._last_counsel_attempt=0.0

    def launch_worker(self) -> bool:
        now=time.monotonic()
        while self.restarts and self.restarts[0]<now-self.restart_window:self.restarts.popleft()
        if len(self.restarts)>=self.max_restarts:
            self.store.event('error','JANUS restart limit reached; manual intervention required. No approved commands retried.')
            return False
        self.restarts.append(now)
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
        try:
            self.worker=subprocess.Popen(self.worker_command,stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                     cwd=str(Path(__file__).resolve().parent.parent),
                     creationflags=flags)
            self.last_healthy_monotonic=time.monotonic()
            self.last_healthy_cycle=0
            self.warned_stale=False
            self.store.event('info',f'JANUS worker started PID {self.worker.pid}; run {len(self.restarts)}/{self.max_restarts} in restart window')
            return True
        except OSError as exc:
            self.store.event('error',f'JANUS could not start: {type(exc).__name__}: {exc}')
            self.worker=None
            return False

    def step(self) -> dict:
        j=janus_health(self.janus_db)
        gui=gui_health(self.gui_heartbeat)
        now=time.monotonic()
        cycle=int(j.get('cycle') or 0)
        if cycle!=self.last_healthy_cycle:
            self.last_healthy_cycle=cycle
            self.last_healthy_monotonic=now
            self.warned_stale=False
        # If the UI has stopped reporting life, do not continue launching new
        # approved commands in an unattended system. This safety pause is
        # intentionally NOT automatically cleared; the user must resume JANUS.
        from .janus_engine import JanusStore
        heartbeat_stamp=gui.get('stamp')
        heartbeat_fresh=False
        if heartbeat_stamp:
            try:
                seen=datetime.fromisoformat(heartbeat_stamp)
                seconds=(datetime.now()-seen).total_seconds()
                heartbeat_fresh=(-20<=seconds<=30)
            except (ValueError,TypeError):
                heartbeat_fresh=False
        if heartbeat_fresh:
            self.gui_missing_since=now
        elif now-self.gui_missing_since>40 and not self.gui_pause_logged:
            JanusStore(self.janus_db).set_paused(True)
            self.store.event('warning','Desktop heartbeat missing/stale; JANUS paused for safety. User must resume after checking GUI. Running tool actions are not automatically replayed.')
            self.gui_pause_logged=True
        worker_alive=self.worker is not None and self.worker.poll() is None
        status='running' if worker_alive else 'stopped'
        detail=f'JANUS cycle {cycle}' if worker_alive else 'JANUS worker unavailable'
        if not worker_alive and not self.stopping:
            if self.worker is not None and not self.last_exit_reported:
                self.store.event('warning',f'JANUS worker exited with code {self.worker.returncode}; inspecting interrupted work before recovery')
                self.last_exit_reported=True
            # A crashed worker might have left an approved tool running.
            # Never launch another worker while the previous instance's process
            # is marked running; close/reopen the desktop to kill the capped job
            # process tree, then inspect the durable needs_attention entry.
            active_actions=[]
            if self.worker is not None and self.worker.poll() is not None:
                from .janus_engine import JanusStore
                active_actions=[a for a in JanusStore(self.janus_db).actions(limit=80)
                                if a['status']=='running']
            if active_actions:
                status='needs_attention'
                detail=f'JANUS exited with {len(active_actions)} unverified active tool(s); restart blocked until safe review'
                if not getattr(self,'orphan_warning_reported',False):
                    self.store.event('error',detail+'; close DeepThorT to terminate capped processes, reopen and inspect logs. No automatic replay.')
                    self.orphan_warning_reported=True
            elif self.launch_worker():
                status='restarting' if self.last_exit_reported else 'starting'
                detail='JANUS launched; awaiting first cycle'
            else:
                status='needs_attention';detail='JANUS restart limit or launch error; inspect Sentinel events'
        elif worker_alive and bool(j.get('paused')):
            # JANUS intentionally pauses after lost desktop heartbeats or an explicit
            # Pause JANUS action. A frozen cycle is EXPECTED while paused: do not
            # misdiagnose it as a worker hang or restart an approved process.
            status='paused'
            detail='JANUS is paused; resume explicitly in JANUS & Sentinel when safe'
            self.warned_stale=False
            self.last_healthy_monotonic=now
        elif worker_alive and now-self.last_healthy_monotonic>self.stall_after:
            status='needs_attention'
            detail=f'JANUS cycle unchanged for {int(now-self.last_healthy_monotonic)}s; process alive, NOT killed automatically'
            if not self.warned_stale:
                self.store.event('warning',detail)
                self.warned_stale=True
        if gui.get('model_loading') and gui.get('model_loading_seconds',0)>240:
            if status=='running':
                status='warning'
                detail='Local AI model still loading beyond 240s; no automatic restart during load; check Processes for elapsed time'
        # Second complete eleven-core society. Sentinel owns only supervisory
        # recommendations; JANUS remains the sole executor of approved work.
        js=JanusStore(self.janus_db)
        jobs=js.observe_jobs(self.jobs_db)
        from .planning_recovery import observe_planning
        plans=observe_planning(self.jobs_db)
        from .delegation_senses import observe_delegation,active_work,conflict,observe_project_assignments,observe_project_midi
        delegation=observe_delegation(self.jobs_db)
        project_assignments=observe_project_assignments(self.jobs_db)
        project_midi=observe_project_midi(self.jobs_db)
        from .memory_duty import observe_memory_duties
        memory_duties=observe_memory_duties(self.jobs_db)
        from .worker_reports import observe_worker_reports
        worker_reports=observe_worker_reports(self.jobs_db)
        from .corrective_coordination import observe as observe_corrections
        corrective_assignments=observe_corrections(self.jobs_db)
        team_active=active_work(delegation)
        team_conflict=conflict(delegation)
        active_plans=[p for p in plans if p['state'] in ('pending','running')]
        failed_plans=[p for p in plans if p['state']=='failed']
        jobcounts={state:sum(job['state']==state for job in jobs) for state in
                   ('queued','running','needs_input','waiting_approval','waiting_verification','waiting_repair','failed','complete')}
        goal=js.goal() or 'Monitor user-directed work and verify completion'
        janus_focus=str(j.get('last_focus') or '')
        janus_decision=str(j.get('last_action') or '')
        off_task=bool(not j.get('paused') and (jobcounts['queued'] or jobcounts['running'] or active_plans or team_active or project_midi['active']) and
                       janus_focus in ('idle','startup') and cycle>=2)
        # A running model at 20% CPU may legitimately need many minutes; detect
        # prolonged lack of evidence, never terminate an active process on age alone.
        stalled_jobs=[]
        for job in jobs:
            if job['state']!='running':continue
            try:
                changed=datetime.fromisoformat(job['updated_at'])
                if changed.tzinfo is None:changed=changed.replace(tzinfo=timezone.utc)
                age=(datetime.now(timezone.utc)-changed).total_seconds()
                if age>self.work_stall_after:stalled_jobs.append(job['id'])
            except (ValueError,TypeError):pass
        warning=''
        if off_task:
            warning='JANUS appears off-task: queued/running work exists but its Front reports idle; inspect the queue and model.'
        elif team_conflict:
            warning='Delegation lease and conversation disagree; inspect current task identity and cancellation; no automatic replay.'
        elif stalled_jobs:
            warning=f'Jobs {stalled_jobs[:8]} have no recorded progress for over {int(self.work_stall_after/60)} minutes; inspect the model and logs. No automatic restart.'
            if status=='running':status='warning';detail=warning
        elif failed_plans and not active_plans:
            warning=f"Draft #{failed_plans[0]['id']} is incomplete; check JANUS retranslation and recorded recovery evidence."
        elif status in ('needs_attention','warning'):
            warning=detail
        elif delegation['failed']:
            warning='Delegated work failed or was interrupted; inspect scoped receipts and explicit retry requirements.'
        elif jobcounts['failed'] or jobcounts['needs_input']:
            warning='Blocked or failed work requires verified diagnosis and user guidance; do not claim completion.'
        try:
            janus_observation=json.loads(j.get('last_observation') or '{}')
        except (TypeError,ValueError):janus_observation={}
        from .society_stimuli import observe_stimuli
        try:prior_stimuli=json.loads(self.store.snapshot().get('observation_json') or '{}').get('stimuli')
        except (ValueError,TypeError,AttributeError):prior_stimuli=None
        stimuli=observe_stimuli(self.jobs_db,prior_stimuli)
        observation={'stimuli':stimuli,'worker_state':status,'janus_cycle':cycle,'janus_focus':janus_focus,
            'janus_decision':janus_decision,'counts':jobcounts,'drift':off_task,
            'stalled':bool(stalled_jobs) or status=='needs_attention',
            'failed':bool(jobcounts['failed'] or failed_plans or delegation['failed']),
            'delegation':delegation,'conflict':team_conflict,'project_assignments':project_assignments,'project_midi':project_midi,'memory_duties':memory_duties,'worker_reports':worker_reports,'corrective_assignments':corrective_assignments,
            'planning_counts':{state:sum(p['state']==state for p in plans)
                              for state in ('pending','running','waiting_sources','failed')},
            'requires_user':bool(jobcounts['needs_input']),
            'warning':warning,
            'active_actions':sum(a['status']=='running' for a in js.actions(40)),
            'game_detected':bool(janus_observation.get('game_detected'))}
        focus='task_drift' if off_task else 'delegation_review' if team_conflict or delegation['failed'] else ('worker_health' if status!='running' else
               'failed_work' if jobcounts['failed'] or jobcounts['needs_input'] or failed_plans else 'task_adherence')
        decision='report_and_request_guidance' if warning else 'monitor_and_verify'
        alternatives=(['Inspect verified logs','Ask for guidance before retrying',
                       'Preserve existing task and approved-action state'] if warning else
                      ['Check that JANUS Front tracks a real active goal','Check outcomes against job evidence'])
        from .core_deliberation import snapshot as neural_snapshot
        reflection=self.store.reflect(observation=observation,focus=focus,decision=decision,
                                      goal=goal,alternatives=alternatives,neural=neural_snapshot(self.jobs_db,'sentinel'))
        # Review exact pending JANUS corrections before general advisory work.
        # Sentinel never substitutes its own proposal or grants authority.
        pending_report=None
        if not self.stopping and not observation['game_detected'] and not j.get('paused'):
            from .corrective_coordination import pending_review,review,invalidate_review
            from .worker_reports import still_current,counsel_fields
            correction=pending_review(self.jobs_db)
            seen={r['evidence_key'] for r in self.store.recommendations(40)}
            pending_report=(correction[0] if correction else
                next((r for r in worker_reports['reports']+worker_reports['notices'] if 'worker-'+r['receipt_sha'] not in seen),None))
            if (pending_report and (self._counsel_thread is None or not self._counsel_thread.is_alive())
                    and time.monotonic()-self._last_counsel_attempt>=60):
                self._last_counsel_attempt=time.monotonic()
                report_id=pending_report['receipt_sha']
                def challenge():
                    if not still_current(self.jobs_db,report_id):return
                    try:problem,evidence=counsel_fields(pending_report,self.jobs_db)
                    except (ValueError,OSError):return
                    if correction:
                        row=correction[1]
                        evidence='EXACT JANUS CORRECTIVE PROPOSAL: '+row['proposal']+'\n'+evidence
                    answer=self._counsel.request(society='sentinel',goal=pending_report['focus'],
                        problem=problem,evidence=evidence,worker_report=True,coordination='review' if correction else '')
                    if answer and not self.stopping and not JanusStore(self.janus_db).status()['paused'] and still_current(self.jobs_db,report_id):
                        if correction:
                            try:review(self.jobs_db,pending_report,row,answer)
                            except ValueError:invalidate_review(self.jobs_db,row)
                            except (OSError,sqlite3.Error):return
                            self.store.recommend('coordination-review-'+report_id,problem,answer,'local_model')
                        self.store.recommend('worker-'+report_id,problem,answer,'local_model')
                self._counsel_thread=threading.Thread(target=challenge,name='Sentinel-worker-challenge',daemon=True)
                self._counsel_thread.start()
        if (not pending_report and not self.stopping and not observation['game_detected']
                and not j.get('paused') and heartbeat_fresh
                and (self._counsel_thread is None or not self._counsel_thread.is_alive())
                and time.monotonic()-self._last_counsel_attempt>=60):
            from .workflow_attention import choose,run_once
            from .core_deliberation import choose as choose_core,step as core_step,select_lane
            ordinary=choose(self.jobs_db,'sentinel')
            core_packet=choose_core(self.jobs_db,'sentinel')
            lane=select_lane(ordinary,core_packet,getattr(self,'_last_attention_lane',''))
            if lane:
                self._last_attention_lane=lane
                if lane!='core':core_packet=None
                self._last_counsel_attempt=time.monotonic()
                def supervise():
                    def stopped():
                        state=JanusStore(self.janus_db).status()
                        try:gaming=bool(json.loads(state.get('last_observation') or '{}').get('game_detected'))
                        except (ValueError,TypeError):gaming=True
                        return self.stopping or state['paused'] or gaming
                    if core_packet:
                        item=core_step(self.jobs_db,'sentinel',self._counsel,stopped,core_packet)
                        if item and not stopped():
                            self.store.recommend('core-'+item['round_sha'],item['result']['finding'],item['result']['guidance'],'local_model')
                    else:
                        item=run_once(self.jobs_db,'sentinel',self._counsel,stopped)
                        if item and item['result']['kind']=='advice' and not stopped():
                            self.store.recommend('attention-'+item['key'],item['result']['finding'],item['result']['guidance'],'local_model')
                self._counsel_thread=threading.Thread(target=supervise,name='Sentinel-independent-attention',daemon=True)
                self._counsel_thread.start()
        if warning:
            case_key=hashlib.sha256((warning+'|'+goal+'|'+str(jobcounts)).encode()).hexdigest()[:24]
            self.store.recommend('sentinel-'+case_key,warning,
                                 '; '.join(alternatives))
            if (not pending_report and not self.stopping and not observation['game_detected'] and
                not j.get('paused') and heartbeat_fresh and
                (self._counsel_thread is None or not self._counsel_thread.is_alive()) and
                time.monotonic()-self._last_counsel_attempt>=600):
                key='model-'+case_key
                if not any(r['evidence_key']==key for r in self.store.recommendations(20)):
                    self._last_counsel_attempt=time.monotonic()
                    def suggest():
                        answer=self._counsel.request(society='sentinel',goal=goal,problem=warning,
                            evidence=janus_focus+' | '+janus_decision+' | '+str(jobcounts))
                        if answer:self.store.recommend(key,warning,answer,'local_model')
                    self._counsel_thread=threading.Thread(target=suggest,name='Sentinel-local-advice',daemon=True)
                    self._counsel_thread.start()
        self.store.update(state=status,detail=detail,sentinel_pid=os.getpid(),
             janus_pid=self.worker.pid if self.worker and self.worker.poll() is None else None,
             restart_count=len(self.restarts),last_janus_cycle=cycle,
             janus_updated_at=j.get('updated_at'),gui_updated_at=gui.get('stamp'))
        return self.store.snapshot()

    def shutdown(self):
        self.stopping=True
        if self.worker and self.worker.poll() is None:
            # Never automatically re-run unfinished approved commands after shutdown.
            self.worker.terminate()
            try:self.worker.wait(timeout=6)
            except subprocess.TimeoutExpired:
                self.worker.kill();self.worker.wait(timeout=4)
        self.store.update(state='stopped',detail='Sentinel stopped; durable state preserved',
             sentinel_pid=None,janus_pid=None,restart_count=len(self.restarts),
             last_janus_cycle=self.last_healthy_cycle)
        self.store.event('info','Sentinel stopped')

    def run(self):
        import signal
        def stopping(*_):self.stopping=True
        signal.signal(signal.SIGTERM,stopping)
        if hasattr(signal,'SIGINT'):signal.signal(signal.SIGINT,stopping)
        self.store.event('info','Sentinel online: observing JANUS without independent work authority')
        try:
            while not self.stopping:
                self.step()
                deadline=time.monotonic()+self.loop_interval
                while time.monotonic()<deadline and not self.stopping:
                    time.sleep(min(.2,max(0,deadline-time.monotonic())))
        finally:self.shutdown()
