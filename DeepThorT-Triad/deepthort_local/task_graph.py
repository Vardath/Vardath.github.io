"""v42: evidence-backed dependency graph for one already-approved local build.

This is a durable representation of observed work, not a task planner or a
source of authority. A graph never permits a file write or command by itself:
project_authority remains mandatory. Unfinished leases must be reconciled by
human inspection after restart; they are NOT auto-replayed.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path

from .project_authority import _plan_digest, _safe_auto_path, _sha, recognized_test_command

MAX_STEPS = 24

class GraphError(ValueError):
    pass


def same_workspace(indexed,approved):
    """Compare existing absolute directory identities, including Windows short paths."""
    if not isinstance(indexed,str) or not isinstance(approved,str) or not indexed or not approved:
        return False
    try:
        a,b=Path(indexed),Path(approved)
        return a.is_absolute() and b.is_absolute() and a.is_dir() and b.is_dir() and a.samefile(b)
    except (OSError,ValueError,RuntimeError):
        return False


def independent_workspaces(first,second):
    """Prove two existing roots are distinct and not nested, including aliases.

    This is an overlap admission check, not a change to same_workspace's
    exact approval-identity semantics. Unknown identity fails closed.
    """
    if not isinstance(first,str) or not isinstance(second,str):return False
    try:
        a,b=Path(first),Path(second)
        if not a.is_absolute() or not b.is_absolute():return False
        a,b=a.resolve(strict=True),b.resolve(strict=True)
        if not a.is_dir() or not b.is_dir():return False
        return not (any(a.samefile(p) for p in (b,*b.parents))
                    or any(b.samefile(p) for p in (a,*a.parents)))
    except (OSError,ValueError,RuntimeError):return False


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()


def _executable_available(command):
    """Read-only executable presence, NOT installation or capability proof."""
    if not command or not command[0]:
        return False
    first = command[0]
    if first == sys.executable:
        return Path(first).is_file()
    if Path(first).is_absolute():
        return Path(first).is_file()
    return bool(shutil.which(first))


class TaskGraphStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS graphs(
                    job_id INTEGER PRIMARY KEY, project TEXT NOT NULL,
                    plan_sha256 TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS nodes(
                    job_id INTEGER NOT NULL, node TEXT NOT NULL, kind TEXT NOT NULL,
                    title TEXT NOT NULL, state TEXT NOT NULL,
                    evidence_sha256 TEXT NOT NULL DEFAULT '',
                    note TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(job_id,node));
                CREATE TABLE IF NOT EXISTS edges(
                    job_id INTEGER NOT NULL, node TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    PRIMARY KEY(job_id,node,depends_on));
                CREATE TABLE IF NOT EXISTS leases(
                    lease_id TEXT PRIMARY KEY, job_id INTEGER NOT NULL,
                    kind TEXT NOT NULL, node TEXT NOT NULL,
                    status TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT);
                CREATE INDEX IF NOT EXISTS leases_job ON leases(job_id,status);
                CREATE TABLE IF NOT EXISTS graph_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER NOT NULL, event TEXT NOT NULL,
                    note TEXT NOT NULL, stamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS graph_events_job ON graph_events(job_id,id);
                CREATE TABLE IF NOT EXISTS explicit_graph_v60(
                    job_id INTEGER PRIMARY KEY,plan_sha TEXT NOT NULL,edges_sha TEXT NOT NULL);
            ''')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            db.execute('PRAGMA busy_timeout=15000')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _binding(job, steps):
        if job.get('mode') != 'build' or not isinstance(job.get('id'), int):
            raise GraphError('Graph requires a real approved build job')
        if not str(job.get('approval_key') or '').startswith(('draft:', 'milestone:')):
            raise GraphError('A graph cannot be created from unapproved chat or arbitrary work')
        if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
            raise GraphError('Graph is bounded to 1..24 approved file stages')
        project = Path(job['project']).resolve(strict=True)
        seen = set()
        for step in steps:
            path, _ = _safe_auto_path(project, step['path'])
            if path.casefold() in seen:
                raise GraphError('Duplicate path in approved build')
            seen.add(path.casefold())
        contract = {'approved_plan': _plan_digest(job, steps),
                    'original_requirement_sha256': hashlib.sha256(
                        str(job.get('prompt') or '').encode('utf-8')).hexdigest()}
        return str(project), _hash(contract)

    def _assert_bound(self, db, job, steps):
        project, plan = self._binding(job, steps)
        row = db.execute('SELECT project,plan_sha256,state FROM graphs WHERE job_id=?',
                         (job['id'],)).fetchone()
        if not row:
            raise GraphError('No v42 graph for this job; no unattended graph action')
        if row[0] != project or row[1] != plan or row[2] != 'active':
            raise GraphError('Approved graph changed, was invalidated or belongs to another project')
        marker=db.execute("SELECT plan_sha,edges_sha FROM explicit_graph_v60 WHERE job_id=?",(job['id'],)).fetchone()
        if marker:
            expected=self._explicit_edges(job['id'],steps)
            actual=db.execute("""SELECT job_id,node,depends_on FROM edges WHERE job_id=?
                AND depends_on NOT LIKE 'req:%' ORDER BY node,depends_on""",(job['id'],)).fetchall()
            if expected is None or marker!=(plan,_hash(sorted(expected))) or sorted(actual)!=sorted(expected):
                raise GraphError('Explicit approved dependency graph changed')

    @staticmethod
    def _explicit_edges(jobid,steps):
        from .requirements_intelligence import complete_dependencies
        deps=complete_dependencies(steps)
        if deps is None:return None
        paths={s['path']:f"file:{s['id']}" for s in steps}
        result=[(jobid,'tool:verify','approval'),(jobid,'verify','tool:verify'),(jobid,'evidence','verify')]
        for path,required in deps.items():
            node=paths[path]
            result.append((jobid,'verify',node))
            result.append((jobid,node,'approval'))
            result.extend((jobid,node,paths[dependency]) for dependency in required)
        return result

    def explicit(self,jobid):
        with self._db() as db:
            return bool(db.execute("SELECT 1 FROM explicit_graph_v60 WHERE job_id=?",(jobid,)).fetchone())

    def ready_step(self,job,steps,*,preferred=None,exclude=()):
        candidates=self.ready_candidates(job,steps,preferred=preferred,exclude=exclude)
        return candidates[0] if candidates else None

    def ready_candidates(self,job,steps,*,preferred=None,exclude=()):
        """Expose only genuinely dependency-ready work, not arbitrary sequence position.

        Rank ready stages by the number of remaining direct consumers, with
        approved order as deterministic tie-break. A reviewed retry can pin
        its exact stage. All actual dependency hashes are checked here and
        again by the production contract before publication.
        """
        with self._db() as db:
            self._assert_bound(db,job,steps)
            explicit=db.execute("SELECT 1 FROM explicit_graph_v60 WHERE job_id=?",(job['id'],)).fetchone()
            planned=[s for s in steps if s['state']=='planned' and s['id'] not in exclude]
            if not planned:return []
            if not explicit:
                if preferred is not None and preferred!=planned[0]['id']:return []
                return [planned[0]]
            available=[]
            pending={f"file:{s['id']}" for s in planned}
            project=Path(job['project']).resolve(strict=True)
            for step in planned:
                if preferred is not None and step['id']!=preferred:continue
                node=f"file:{step['id']}"
                exact=db.execute("SELECT kind,title,state FROM nodes WHERE job_id=? AND node=?",(job['id'],node)).fetchone()
                if exact!=('artifact',step['path'],'waiting'):continue
                deps=db.execute("""SELECT n.kind,n.title,n.state,n.evidence_sha256 FROM edges e
                    LEFT JOIN nodes n ON n.job_id=e.job_id AND n.node=e.depends_on
                    WHERE e.job_id=? AND e.node=?""",(job['id'],node)).fetchall()
                if not deps or any(d[2] not in ('approved','saved','available','passed','linked') for d in deps):continue
                try:
                    if any(kind=='artifact' and (state!='saved' or not evidence or
                        _sha(_safe_auto_path(project,title)[1])!=evidence) for kind,title,state,evidence in deps):continue
                except (OSError,ValueError):continue
                consumers=db.execute("SELECT node FROM edges WHERE job_id=? AND depends_on=?",(job['id'],node)).fetchall()
                impact=sum(x[0] in pending for x in consumers)
                available.append((-impact,step['sequence'],step))
            return [item[2] for item in sorted(available,key=lambda x:(x[0],x[1]))]

    @staticmethod
    def _event(db, jobid, event, note):
        db.execute('INSERT INTO graph_events(job_id,event,note) VALUES(?,?,?)',
                   (jobid, str(event)[:60], str(note)[:460]))

    def create(self, job: dict, steps: list[dict]) -> None:
        if job.get('state') != 'queued':
            raise GraphError('Initial task graph needs a newly queued approved build')
        project, plan = self._binding(job, steps)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            prior = db.execute('SELECT plan_sha256,project FROM graphs WHERE job_id=?',
                               (job['id'],)).fetchone()
            if prior:
                if prior != (plan, project):
                    raise GraphError('Cannot silently replace an existing graph')
                return
            jobid = job['id']
            db.execute('INSERT INTO graphs(job_id,project,plan_sha256) VALUES(?,?,?)',
                       (jobid,project,plan))
            nodes = [('approval','requirement','Approved bounded project plan','approved'),
                     ('tool:verify','tool','Observed fixed verification executable','unknown'),
                     ('verify','verification','Run actual approved project check','waiting'),
                     ('evidence','acceptance','Capture test and source acceptance evidence','waiting')]
            for step in steps:
                nodes.append((f"file:{step['id']}",'artifact',step['path'],'waiting'))
            db.executemany('INSERT INTO nodes(job_id,node,kind,title,state) VALUES(?,?,?,?,?)',
                           [(jobid,*x) for x in nodes])
            edges=[(jobid,'tool:verify','approval'),(jobid,'verify','tool:verify'),
                   (jobid,'evidence','verify')]
            explicit=self._explicit_edges(jobid,steps)
            if explicit is not None:
                edges=explicit
                db.execute("INSERT INTO explicit_graph_v60 VALUES(?,?,?)",(jobid,plan,_hash(sorted(edges))))
            else:
                previous = 'approval'
                for step in steps:
                    node = f"file:{step['id']}"
                    edges.append((jobid,node,previous))
                    edges.append((jobid,'verify',node))
                    previous=node
            db.executemany('INSERT INTO edges(job_id,node,depends_on) VALUES(?,?,?)',edges)
            self._event(db,jobid,'created',f'{len(steps)} exact approved artifacts; '+('explicit dependencies' if explicit is not None else 'conservative legacy order')+'; tool verification pending')

    def attach_hierarchy(self,job,steps,provenance:dict):
        """Attach only existing persisted requirement/file links to the job DAG.

        File order remains the approved plan order. An explicit dependency from
        a LATER stage is refused (and never silently reordered). Cross-milestone
        dependencies remain governed by the hierarchy's existing verification
        gate and are not invented as completed local edges.
        """
        if not isinstance(provenance,dict) or not isinstance(provenance.get('requirements'),list):
            raise GraphError('No persisted requirement provenance supplied')
        if not same_workspace(provenance.get('root_project'),job['project']):
            raise GraphError('Requirements were indexed for another workspace')
        if len(provenance['requirements'])>128:
            raise GraphError('Requirement graph provenance exceeds bounded cap')
        local={step['path'].casefold():step for step in steps}
        order={step['path'].casefold():idx for idx,step in enumerate(steps)}
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            if db.execute("SELECT 1 FROM nodes WHERE job_id=? AND node LIKE 'req:%' LIMIT 1",
                          (job['id'],)).fetchone():
                raise GraphError('Persisted requirement links cannot be overwritten')
            for requirement in provenance['requirements']:
                key=str(requirement.get('id') or '')
                source=str(requirement.get('source_sha256') or '')
                if not key or len(key)>150 or len(source)!=64 or any(c not in '0123456789abcdef' for c in source):
                    raise GraphError('Invalid persisted requirement identifier or source checksum')
                files=requirement.get('files')
                if not isinstance(files,list) or not files:
                    raise GraphError('No exact approved file intention for requirement')
                node='req:'+hashlib.sha256(key.encode('utf-8')).hexdigest()[:24]
                db.execute('INSERT INTO nodes(job_id,node,kind,title,state,evidence_sha256,note) '
                           'VALUES(?,?,?,?,?,?,?)',
                           (job['id'],node,'requirement',key[:120],'linked',source,
                            'Exact original source reference; file intention, not implementation'))
                for path in files:
                    if str(path).casefold() not in local:
                        raise GraphError('Requirement points outside this approved milestone')
                    target=f"file:{local[str(path).casefold()]['id']}"
                    db.execute('INSERT OR IGNORE INTO edges(job_id,node,depends_on) VALUES(?,?,?)',
                               (job['id'],target,node))
            for item in provenance.get('declared_file_dependencies') or []:
                path=str(item.get('file_path') or '').casefold()
                dependency=str(item.get('requires_path') or '').casefold()
                if path not in local or dependency not in local:
                    continue # another milestone remains under existing hierarchy gate
                if order[dependency]>=order[path]:
                    raise GraphError('Declared file dependency is later than approved plan order')
                db.execute('INSERT OR IGNORE INTO edges(job_id,node,depends_on) VALUES(?,?,?)',
                           (job['id'],f"file:{local[path]['id']}",f"file:{local[dependency]['id']}"))
            self._event(db,job['id'],'requirement_trace',
                f"{len(provenance['requirements'])}/{provenance.get('total_linked_requirements',0)} "
                'persisted requirements linked; no semantic acceptance claimed')

    def exists(self, job_id: int) -> bool:
        with self._db() as db:
            return bool(db.execute('SELECT 1 FROM graphs WHERE job_id=?',(job_id,)).fetchone())

    def _update_node(self,db,jobid,node,state,note='',evidence=''):
        if db.execute('UPDATE nodes SET state=?,note=?,evidence_sha256=?,updated_at=CURRENT_TIMESTAMP '
                      'WHERE job_id=? AND node=?',(state,str(note)[:450],evidence,jobid,node)).rowcount != 1:
            raise GraphError('Graph node missing; cannot claim progress')
        self._event(db,jobid,f'{node}:{state}',note)

    def _dependencies(self,db,jobid,node):
        return db.execute('SELECT e.depends_on,n.state FROM edges e '
                          'LEFT JOIN nodes n ON n.job_id=e.job_id AND n.node=e.depends_on '
                          'WHERE e.job_id=? AND e.node=?',(jobid,node)).fetchall()

    def _ensure_deps(self,db,jobid,node,allow=('approved','saved','available','passed','linked')):
        not_ready=[f'{p}: {state}' for p,state in self._dependencies(db,jobid,node)
                   if state not in allow]
        if not_ready:
            raise GraphError('Waiting for prerequisites: '+', '.join(not_ready)[:250])

    def record_artifact(self,job,steps,step,sha256):
        if not isinstance(sha256,str) or len(sha256)!=64:
            raise GraphError('Missing SHA-256 evidence of saved file')
        node=f"file:{step['id']}"
        project=Path(job['project']).resolve(strict=True)
        path,target=_safe_auto_path(project,step['path'])
        if _sha(target)!=sha256:
            raise GraphError('Recorded artifact differs from its actual project file')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            if not any(x['id']==step['id'] and x['path']==step['path'] for x in steps):
                raise GraphError('Artifact is not part of the exact approved plan')
            self._ensure_deps(db,job['id'],node)
            old=db.execute('SELECT state FROM nodes WHERE job_id=? AND node=?',
                           (job['id'],node)).fetchone()
            if old is None or old[0] not in ('waiting','saved'):
                raise GraphError('Artifact is already outside its planned state')
            self._update_node(db,job['id'],node,'saved',f'Saved {path}, source hash checked',sha256)

    def record_repaired_artifact(self,job,steps,step,sha256):
        project=Path(job['project']).resolve(strict=True)
        _,target=_safe_auto_path(project,step['path'])
        if _sha(target)!=sha256:
            raise GraphError('Repaired source does not match saved SHA-256')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            node=f"file:{step['id']}"
            old=db.execute('SELECT state FROM nodes WHERE job_id=? AND node=?',
                           (job['id'],node)).fetchone()
            if not old or old[0]!='saved':
                raise GraphError('Only an existing approved saved artifact may be repaired')
            self._update_node(db,job['id'],node,'saved','Bounded ONNX repair saved, awaiting new test',sha256)
            self._update_node(db,job['id'],'verify','waiting','Reverification required')
            self._update_node(db,job['id'],'evidence','waiting','Existing acceptance evidence invalidated')

    def observe_tool(self,job,steps,command):
        project=Path(job['project']).resolve(strict=True)
        if not recognized_test_command(command,project):
            raise GraphError('Verification command not in the fixed supported profiles')
        ready=_executable_available(command)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            self._update_node(db,job['id'],'tool:verify','available' if ready else 'blocked',
                              'Executable located; capability NOT established' if ready else 'Verification executable not found',
                              _hash(command) if ready else '')
        return ready

    def ready_to_test(self,job,steps,command):
        if job.get('state')!='waiting_verification':
            raise GraphError('Job is not awaiting verification')
        if not self.observe_tool(job,steps,command):
            raise GraphError('Verification executable is missing; install/probe manually')
        project=Path(job['project']).resolve(strict=True)
        with self._db() as db:
            self._assert_bound(db,job,steps)
            self._ensure_deps(db,job['id'],'verify')
            for step in steps:
                sha=db.execute('SELECT evidence_sha256,state FROM nodes WHERE job_id=? AND node=?',
                               (job['id'],f"file:{step['id']}")).fetchone()
                if not sha or sha[1]!='saved':
                    raise GraphError('Unfinished approved artifact')
                _,target=_safe_auto_path(project,step['path'])
                if _sha(target)!=sha[0]:
                    raise GraphError('An approved source changed since graph evidence was recorded')
        return True

    def begin_action(self,job,steps,kind,node):
        if kind not in ('test','repair','write','retain'):
            raise GraphError('Unknown executable graph operation')
        lease=uuid.uuid4().hex
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            if db.execute("SELECT 1 FROM leases WHERE job_id=? AND status='running'",
                          (job['id'],)).fetchone():
                raise GraphError('An unfinished action lease exists; inspect instead of replay')
            if not db.execute('SELECT 1 FROM nodes WHERE job_id=? AND node=?',
                              (job['id'],node)).fetchone():
                raise GraphError('Action target does not exist in approved graph')
            if kind in ('write','retain') and db.execute("SELECT 1 FROM explicit_graph_v60 WHERE job_id=?",(job['id'],)).fetchone():
                self._ensure_deps(db,job['id'],node)
            db.execute('INSERT INTO leases(lease_id,job_id,kind,node,status) '
                       'VALUES(?,?,?,?,?)',(lease,job['id'],kind,node,'running'))
            self._event(db,job['id'],'lease:started',f'{kind} on {node}, lease {lease[:10]}')
        return lease

    def finish_action(self,lease,jobid,result):
        if result not in ('saved','passed','failed','blocked','interrupted'):
            raise GraphError('Unrecognized action completion state')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT kind,node FROM leases WHERE lease_id=? AND job_id=? AND status='running'",
                           (lease,jobid)).fetchone()
            if not row:
                raise GraphError('Missing or previously closed lease')
            db.execute('UPDATE leases SET status=?,note=?,finished_at=CURRENT_TIMESTAMP '
                       'WHERE lease_id=?',(result,result,lease))
            self._event(db,jobid,'lease:'+result,f'{row[0]} on {row[1]}, lease {lease[:10]}')
            if result=='interrupted':
                self._update_node(db,jobid,row[1],'needs_attention','Interrupted operation: human reconciliation required')
            elif row[0]=='test' and result=='failed':
                self._update_node(db,jobid,'verify','failed','Observed test failure; repair not yet proven')

    def test_finished(self,job,steps,successful,source_evidence=None,assurance=''):
        if successful and not isinstance(source_evidence,dict):
            raise GraphError('A passing test needs source-backed acceptance evidence')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            self._assert_bound(db,job,steps)
            if successful:
                digest=_hash(source_evidence)
                self._update_node(db,job['id'],'verify','passed','Verified test exit 0 and accepted evidence',digest)
                self._update_node(db,job['id'],'evidence','recorded',
                                  'Source-hash/test acceptance receipt; NOT gameplay validation. '+str(assurance)[:180],digest)
            else:
                self._update_node(db,job['id'],'verify','failed','Actual verification failed or lacked accepted evidence')
                self._update_node(db,job['id'],'evidence','waiting','No passing acceptance receipt')

    def invalidate(self,jobid,reason):
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT state FROM graphs WHERE job_id=?',(jobid,)).fetchone()
            if not row:return False
            if row[0]!='invalidated':
                db.execute("UPDATE graphs SET state='invalidated',updated_at=CURRENT_TIMESTAMP WHERE job_id=?",
                           (jobid,))
                self._event(db,jobid,'invalidated',str(reason)[:440])
                db.execute("UPDATE nodes SET state='invalidated',updated_at=CURRENT_TIMESTAMP WHERE job_id=?",
                           (jobid,))
            return True

    def interrupted(self):
        """Crash recovery: interrupt all outstanding leases without replaying work."""
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            rows=db.execute("SELECT lease_id,job_id,node FROM leases WHERE status='running'").fetchall()
            for lease,job,node in rows:
                db.execute("UPDATE leases SET status='interrupted',note='Restart before result',"
                           "finished_at=CURRENT_TIMESTAMP WHERE lease_id=?",(lease,))
                self._update_node(db,job,node,'needs_attention',
                                  'Prior process/write may have survived interruption; manual inspection required')
            return [j for _,j,_ in rows]

    def recovery_snapshot(self,job,steps):
        """Validate the sealed graph's job/plan binding before restart recovery."""
        with self._db() as db:
            self._assert_bound(db,job,steps)
            if db.execute("SELECT 1 FROM leases WHERE job_id=? AND status IN ('running','interrupted')",
                          (job['id'],)).fetchone():
                raise GraphError('Prior graph action is uncertain; recovery cannot replay it')
        return self.status(job['id'])

    def status(self,jobid):
        with self._db() as db:
            row=db.execute('SELECT state FROM graphs WHERE job_id=?',(jobid,)).fetchone()
            if not row:return None
            db.row_factory=sqlite3.Row
            nodes=[dict(r) for r in db.execute('SELECT node,kind,title,state,evidence_sha256,note '
                  'FROM nodes WHERE job_id=? ORDER BY CASE kind WHEN \'requirement\' THEN 0 '
                  'WHEN \'artifact\' THEN 1 WHEN \'tool\' THEN 2 WHEN \'verification\' THEN 3 ELSE 4 END,node',
                  (jobid,))]
            edges=[dict(r) for r in db.execute('SELECT node,depends_on FROM edges WHERE job_id=? ORDER BY node',
                  (jobid,))]
            active=db.execute("SELECT kind,node FROM leases WHERE job_id=? AND status='running'",
                              (jobid,)).fetchone()
            return {'state':row[0],'nodes':nodes,'edges':edges,
                    'active_action':dict(active) if active else None}

    def summary(self,project=None,limit=40):
        with self._db() as db:
            db.row_factory=sqlite3.Row
            if project is None:
                rows=db.execute('SELECT job_id,state FROM graphs ORDER BY job_id DESC LIMIT ?',
                                (min(limit,80),)).fetchall()
            else:
                rows=db.execute('SELECT job_id,state FROM graphs WHERE project=? ORDER BY job_id DESC LIMIT ?',
                                (str(Path(project).resolve()),min(limit,80))).fetchall()
            return {'graphs':[dict(x) for x in rows],
                    'meaning':'Observed dependencies only, not independent requirement or gameplay satisfaction'}
