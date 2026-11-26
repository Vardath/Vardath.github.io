"""JANUS's local execution worker, launched as a capped child of DeepThorT.exe.

No model/cloud calls; no shell execution. It observes persistent work and can run
only commands explicitly authorized in the GUI and saved in JanusStore.
"""
from __future__ import annotations
import argparse
import json
import shutil
import os
import signal
import subprocess
import sys
import time
import hashlib
import threading
from pathlib import Path

from deepthort_local.disk_gate import DiskGate
from deepthort_local.janus_engine import JanusStore
from deepthort_local.action_guards import verify_guards
from deepthort_local.state_health import MIN_FREE_BYTES
from deepthort_local.janus_counsel import LocalCounsel
from deepthort_local.job_queue import JobStore
from deepthort_local.flight_recorder import record,install_crash_hooks

# Hard stop for a forgotten or misbehaving approved process. Never assume that
# exit code 0 implies tested game behavior. These bounds do not change model
# inference timeouts; they apply only to JANUS child processes.
MAX_TOOL_SECONDS = 3600
MAX_VERIFICATION_SECONDS = 7200
MAX_ACTION_LOG_BYTES = 8_000_000


def stop_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:return
    if os.name=='nt':
        try:subprocess.run(['taskkill.exe','/T','/F','/PID',str(proc.pid)],timeout=8,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,
                           creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0)
        except (OSError,subprocess.TimeoutExpired):proc.terminate()
    else:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except (ProcessLookupError, PermissionError):proc.terminate()
    try:proc.wait(timeout=6)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait(timeout=4)


class JanusWorker:
    def __init__(self, state_db: str | Path, jobs_db: str | Path, games_file: str | Path,
                 *, game_probe=None):
        install_crash_hooks(Path(state_db).parent,'janus_worker')
        record(Path(state_db).parent,'janus_worker','worker_initialized',pid=os.getpid())
        self.store=JanusStore(state_db)
        self.jobs_db=Path(jobs_db)
        self.game_gate=DiskGate(game_names_path=games_file,
                                game_flag=Path(state_db).parent/'game-active.flag',
                                game_probe=game_probe)
        self.logs=Path(state_db).parent/'janus-process-logs'
        self.logs.mkdir(parents=True,exist_ok=True)
        self._stopping=False
        self._counsel=LocalCounsel(Path(state_db).parent/'janus-counsel.sqlite3')
        self._counsel_thread=None
        self._last_counsel_attempt=time.monotonic()-300.0

    def observe_once(self) -> dict:
        # Full deterministic 11x7 society cycles continue while the ONNX
        # model is offline. Optional advice never gains execution authority.
        gaming=self.game_gate.gaming()
        state=self.store.tick(self.jobs_db,gaming=gaming)
        if not gaming and not self._stopping and not state.get('paused'):
            if not self._consider_worker_reports():
                if not self._consider_live_work():self._consider_local_alternatives(state)
        return state

    def _consider_worker_reports(self):
        from deepthort_local.worker_reports import observe_worker_reports,still_current,counsel_fields
        from deepthort_local.corrective_coordination import eligible,propose
        observed=observe_worker_reports(self.jobs_db)
        reports=observed['reports']+observed['notices']
        if not reports:return False
        seen={r['evidence_key'] for r in self.store.recommendations(40)}
        structured_report=next((r for r in reports if eligible(self.jobs_db,r) and 'coordination-propose-'+r['receipt_sha'] not in seen),None)
        pending=structured_report or next((r for r in reports if 'worker-'+r['receipt_sha'] not in seen),None)
        if not pending:return False
        if self._counsel_thread is not None and self._counsel_thread.is_alive():return True
        if time.monotonic()-self._last_counsel_attempt<60:return True
        self._last_counsel_attempt=time.monotonic()
        ident=pending['receipt_sha'];key='worker-'+ident
        def coordinate():
            if not still_current(self.jobs_db,ident):return
            try:problem,evidence=counsel_fields(pending,self.jobs_db)
            except (ValueError,OSError):return
            structured=structured_report is not None and eligible(self.jobs_db,pending)
            answer=self._counsel.request(society='janus',goal=pending['focus'],problem=problem,
                                         evidence=evidence,worker_report=True,coordination='propose' if structured else '')
            if answer and not self._stopping and not self.store.status()['paused'] and not self.game_gate.gaming() and still_current(self.jobs_db,ident):
                if structured:
                    import sqlite3
                    try:propose(self.jobs_db,pending,answer)
                    except (ValueError,OSError,sqlite3.Error):pass # Malformed advice never becomes an action.
                    self.store.recommend(evidence_key='coordination-propose-'+ident,job_id=pending.get('job_id'),
                        problem=problem,proposal=answer,origin='local_model')
                self.store.recommend(evidence_key=key,job_id=pending.get('job_id'),
                     problem=problem,proposal=answer,origin='local_model')
        self._counsel_thread=threading.Thread(target=coordinate,name='JANUS-worker-coordination',daemon=True)
        self._counsel_thread.start()
        return True

    def _consider_live_work(self):
        """Independent executive reasoning while production is active."""
        if self._counsel_thread is not None and self._counsel_thread.is_alive():return True
        if time.monotonic()-self._last_counsel_attempt<60:return False
        from deepthort_local.workflow_attention import choose,run_once
        from deepthort_local.core_deliberation import choose as choose_core,step as core_step
        ordinary=choose(self.jobs_db,'janus')
        core_packet=choose_core(self.jobs_db,'janus') if not ordinary else None
        if not ordinary and not core_packet:return False
        self._last_counsel_attempt=time.monotonic()
        def work():
            stopped=lambda:self._stopping or self.store.status()['paused'] or self.game_gate.gaming()
            if core_packet:
                item=core_step(self.jobs_db,'janus',self._counsel,stopped,core_packet)
                if item and not stopped():
                    self.store.recommend(evidence_key='core-'+item['round_sha'],job_id=item['job_id'],
                        problem=item['result']['finding'],proposal=item['result']['guidance'],origin='local_model')
            else:
                item=run_once(self.jobs_db,'janus',self._counsel,stopped)
                if item and item['result']['kind']=='advice' and not stopped():
                    self.store.recommend(evidence_key='attention-'+item['key'],job_id=item['identity']['scope']['job_id'],
                        problem=item['result']['finding'],proposal=item['result']['guidance'],origin='local_model')
        self._counsel_thread=threading.Thread(target=work,name='JANUS-independent-attention',daemon=True)
        self._counsel_thread.start()
        return True

    def _consider_local_alternatives(self, state: dict) -> None:
        if state.get('decision') not in (
              'inspect_failure_and_propose_repair','diagnose_failure_and_propose_alternatives',
              'request_approval_or_guidance'):
            return
        if self._counsel_thread is not None and self._counsel_thread.is_alive():return
        if time.monotonic()-self._last_counsel_attempt<300:return
        # The resident broker, not the presence of another worker's job,
        # determines whether executive neural reasoning can proceed.
        candidates=self.store.recommendations(10)
        current=candidates[0] if candidates else None
        if not current:return
        key='model-'+current['evidence_key']
        if any(a['evidence_key']==key for a in candidates):return
        self._last_counsel_attempt=time.monotonic()
        def work():
            text=self._counsel.request(society='janus',goal=state.get('goal',''),
                 problem=current['problem'],evidence=current['proposal'])
            if text:
                self.store.recommend(evidence_key=key,job_id=current['job_id'],
                     problem=current['problem'],proposal=text,origin='local_model')
        self._counsel_thread=threading.Thread(target=work,name='JANUS-local-reasoning',daemon=True)
        self._counsel_thread.start()

    def _observe_active_process(self):
        # Continue scoped live cognition during a long approved subprocess.
        # Do not run the old generic failure fallback or recursively dispatch.
        try:
            gaming=self.game_gate.gaming()
            state=self.store.tick(self.jobs_db,gaming=gaming)
            if not gaming and not self._stopping and not state.get('paused'):
                if not self._consider_worker_reports():self._consider_live_work()
        except Exception as exc:
            record(self.jobs_db.parent,'janus_worker','active_process_observation_failed',
                   level='WARNING',error_type=type(exc).__name__)

    def execute_next_approved(self) -> int | None:
        if self.store.status()['paused'] or self.game_gate.gaming():
            return None
        action=self.store.claim_next_action()
        if action is None:return None
        ident=action['id']
        record(self.jobs_db.parent,'janus_worker','approved_action_claimed',action_id=ident,kind=action['kind'])
        cmd=json.loads(action['argv_json'])
        log_path=self.logs/f'action-{ident}.log'
        try:
            # Recheck approved executable/script/input/output snapshots at the
            # last responsible moment, not only when the user clicked Approve.
            # Old actions contain the default [] and retain historic behavior.
            verify_guards(json.loads(action.get('input_guards_json') or '[]'))
            if shutil.disk_usage(self.logs).free < MIN_FREE_BYTES:
                raise ValueError('Less than 150 MB disk space; approved process not launched')
        except (ValueError, OSError, TypeError, json.JSONDecodeError) as exc:
            reason=f'Approved input changed; process NOT started: {exc}'
            self.store.update_action(ident,'needs_attention',detail=reason)
            self._update_parent_job(action,'needs_input',reason)
            record(self.jobs_db.parent,'janus_worker','approved_preflight_blocked',
                   level='WARNING',action_id=ident,reason=str(exc)[:250])
            return ident
        try:
            with open(log_path,'xb',buffering=0) as logfile:
                flags=getattr(subprocess,'CREATE_NO_WINDOW',0) if os.name=='nt' else 0
                started=time.monotonic()
                deadline=MAX_VERIFICATION_SECONDS if action['kind']=='verification' else MAX_TOOL_SECONDS
                proc=subprocess.Popen(cmd,cwd=action['cwd'],stdin=subprocess.DEVNULL,
                    stdout=logfile,stderr=subprocess.STDOUT,shell=False,
                    creationflags=flags,start_new_session=(os.name!='nt'))
                self.store.update_action(ident,'running',detail='Approved process running',
                                         pid=proc.pid,output_file=str(log_path))
                next_observation=started+10.0
                while proc.poll() is None:
                    fresh=self.store.action(ident)
                    if fresh is None or fresh['cancel_requested'] or self._stopping:
                        stop_tree(proc)
                        self.store.update_action(ident,'cancelled',detail='User cancellation or engine shutdown',returncode=proc.returncode)
                        return ident
                    if time.monotonic()-started>deadline:
                        stop_tree(proc)
                        reason=f'Approved process exceeded {deadline}s runtime; inspect partial changes before retry'
                        self.store.update_action(ident,'needs_attention',detail=reason,returncode=proc.returncode)
                        self._update_parent_job(action,'needs_input',reason)
                        return ident
                    if log_path.stat().st_size>MAX_ACTION_LOG_BYTES:
                        stop_tree(proc)
                        reason='Approved process exceeded 8 MB output log; inspect partial changes before retry'
                        self.store.update_action(ident,'needs_attention',detail=reason,returncode=proc.returncode)
                        self._update_parent_job(action,'needs_input',reason)
                        return ident
                    if self.game_gate.gaming():
                        stop_tree(proc)
                        self.store.update_action(ident,'paused',detail='Game detected; stopped process to protect responsiveness. Inspect partial changes before rerun.',returncode=proc.returncode)
                        self._update_parent_job(action,'needs_input','Verification interrupted for gaming; inspect partial effects')
                        return ident
                    if time.monotonic()>=next_observation:
                        self._observe_active_process()
                        next_observation=time.monotonic()+10.0
                    time.sleep(.25)
                code=proc.returncode
            if log_path.stat().st_size>MAX_ACTION_LOG_BYTES:
                reason='Approved process produced more than 8 MB output; execution NOT verified'
                self.store.update_action(ident,'needs_attention',detail=reason,returncode=code)
                self._update_parent_job(action,'needs_input',reason)
                return ident
            status='succeeded' if code==0 else 'failed'
            record(self.jobs_db.parent,'janus_worker','approved_action_finished',action_id=ident,exit_code=code,status=status)
            self.store.update_action(ident,status,detail=f'Approved process exited {code}; read log for evidence',returncode=code)
            if action['kind']=='verification':
                if code==0:
                    self._update_parent_job(action,'complete','Verified: JANUS approved process exited 0; see process log')
                else:
                    self._update_parent_job(action,'needs_input',f'Build verification exited {code}; inspect JANUS process log')
        except Exception as exc:
            record(self.jobs_db.parent,'janus_worker','approved_action_failed',level='ERROR',action_id=ident,
                   error_type=type(exc).__name__,error=str(exc))
            self.store.update_action(ident,'failed',detail=f'Failed to start/run process: {type(exc).__name__}: {exc}')
            self._update_parent_job(action,'needs_input',f'JANUS engine failed: {type(exc).__name__}: {exc}')
        return ident

    def _update_parent_job(self, action: dict, state: str, detail: str) -> None:
        if action['job_id'] is not None:
            JobStore(self.jobs_db).change(int(action['job_id']),state,detail,allowed=('running',))

    def run(self, interval: float = 10.0, *, once: bool = False):
        if not 1 <= interval <= 60:raise ValueError('Interval must be between 1 and 60 seconds')
        self.store.recover_interrupted_actions()
        self.store.append_event('JANUS engine started; local-only cognition and approved process runner')
        def shutdown(*_):self._stopping=True
        signal.signal(signal.SIGTERM,shutdown)
        if hasattr(signal,'SIGINT'):signal.signal(signal.SIGINT,shutdown)
        while not self._stopping:
            self.observe_once()
            self.execute_next_approved()
            if once:break
            # During a game, reduce wakeups and SQLite writes. Keep a bounded
            # heartbeat so Sentinel can distinguish sleep from a dead worker.
            end=time.monotonic()+(max(interval,45.0) if self.game_gate.gaming() else interval)
            while not self._stopping:
                # Read the deadline clock once: it can cross the deadline between
                # two reads, otherwise time.sleep() receives a negative value.
                remaining=end-time.monotonic()
                if remaining<=0:break
                time.sleep(min(.25,remaining))
        self.store.append_event('JANUS engine stopped; durable state preserved')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--state',required=True)
    p.add_argument('--jobs',required=True)
    p.add_argument('--games',required=True)
    p.add_argument('--interval',type=float,default=10.0)
    p.add_argument('--once',action='store_true')
    a=p.parse_args()
    JanusWorker(a.state,a.jobs,a.games).run(a.interval,once=a.once)

if __name__=='__main__':main()
