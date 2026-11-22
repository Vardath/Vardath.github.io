"""Durable multi-milestone plans traced to exact indexed specification sections.

The local model proposes every file. This module groups existing proposals into
small, sequential, independently approvable milestones; it does not invent
files, requirements, tool results, or approvals. `verified` only follows the
existing approved build-verification queue's successful exit record.

A milestone is an *implementation scope*, not proof of correct dependency
analysis or complete semantic understanding of the source specification.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path

from .agent_plan import PlanError, validate_project_plan
from .specification_library import sha
from .requirements_intelligence import (requirement_candidates, dependency_order,
                                       declared_dependencies, check_dependency_schedule)
from .workspace import safe_target
from .acceptance_contracts import inspect_model_contracts, source_ambiguities
from .semantic_reconciliation import (reconcile_explicit_requirements,
    acceptance_candidates, audit_python_interfaces, verified_sources_current,
    declared_requirement_dependencies)

MAX_MILESTONE_FILES = 12       # comfortably below the existing 24-file queue limit
MAX_SCOPE_SOURCE_CHARS = 4400 # exact excerpts, no truncation
MAX_MILESTONE_PROMPT_CHARS = 6500 # leave space for file-stage guidance


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


class HierarchicalPlanStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS hierarchy_roots (
                  request_id INTEGER PRIMARY KEY, chat_id TEXT NOT NULL,
                  project TEXT NOT NULL, source_sha256 TEXT NOT NULL,
                  model_steps_sha256 TEXT NOT NULL, section_count INTEGER NOT NULL,
                  milestone_count INTEGER NOT NULL,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                CREATE INDEX IF NOT EXISTS hierarchy_by_chat
                  ON hierarchy_roots(chat_id,project,request_id);
                CREATE TABLE IF NOT EXISTS hierarchy_milestones (
                  request_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                  title TEXT NOT NULL, steps_json TEXT NOT NULL,
                  section_ordinals_json TEXT NOT NULL,
                  scope_sha256 TEXT NOT NULL,
                  state TEXT NOT NULL DEFAULT 'planned', job_id INTEGER,
                  PRIMARY KEY(request_id,ordinal));
                CREATE TABLE IF NOT EXISTS hierarchy_requirements (
                  request_id INTEGER NOT NULL, requirement_id TEXT NOT NULL,
                  section_ordinal INTEGER NOT NULL, start_char INTEGER NOT NULL,
                  end_char INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
                  kind TEXT NOT NULL,
                  PRIMARY KEY(request_id,requirement_id));
                CREATE INDEX IF NOT EXISTS hierarchy_req_section
                  ON hierarchy_requirements(request_id,section_ordinal);
                CREATE TABLE IF NOT EXISTS hierarchy_dependencies (
                  request_id INTEGER NOT NULL, file_path TEXT NOT NULL,
                  requires_path TEXT NOT NULL,
                  PRIMARY KEY(request_id,file_path,requires_path));
                CREATE TABLE IF NOT EXISTS hierarchy_trace (
                  request_id INTEGER NOT NULL, section_ordinal INTEGER NOT NULL,
                  section_sha256 TEXT NOT NULL,
                  path TEXT NOT NULL, milestone_ordinal INTEGER NOT NULL,
                  PRIMARY KEY(request_id,section_ordinal,path));
            ''')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _source_rows(index, request_id: int, original: str):
        rows = index._verified_rows(request_id, original)
        if any(not row[5] for row in rows):
            raise PlanError('Some original specification sections have not been reviewed by the model')
        return rows

    @staticmethod
    def _collect(rows, project: str | Path):
        """No inferred file intentions. Duplicate files must agree exactly."""
        merged = OrderedDict()
        refs = {}
        for ordinal, start, end, fingerprint, attempts, plan_json in rows:
            steps = json.loads(plan_json)
            if not isinstance(steps, list) or not steps:
                raise PlanError(f'Specification section {ordinal+1} has no model-proposed files')
            for step in steps:
                if not isinstance(step, dict) or set(step) != {'path', 'description'}:
                    raise PlanError('Stored model file step has an invalid schema')
                rel = safe_target(Path(project), step['path']).relative_to(Path(project).resolve()).as_posix()
                cleaned = {'path': rel, 'description': step['description']}
                key = rel.casefold()
                if key in merged and merged[key] != cleaned:
                    raise PlanError(
                        f'Conflicting model descriptions of {rel} in specification sections; '
                        'the model must reconcile these requirements before milestone approval')
                merged[key] = cleaned
                refs.setdefault(key, set()).add(ordinal)
        return list(merged.values()), refs

    @staticmethod
    def _digest_rows(rows):
        return sha(_json([(r[0],r[3],r[5]) for r in rows]))

    @staticmethod
    def _scope(original: str, rows, section_ordinals: list[int], request_id: int,
               milestone_ordinal: int, total: int, *, by_id=None,
               source_digest: str | None = None) -> str:
        if by_id is None:
            by_id = {r[0]: r for r in rows}
        source = source_digest if source_digest is not None else sha(original)
        preface = (
            f'HIERARCHICAL MILESTONE {milestone_ordinal}/{total}; parent request #{request_id}. '
            f'Complete master specification SHA-256 {source}, {len(original):,} characters, '
            f'{len(rows)} reviewed sections. Full original remains in local storage. '
            'This is a deliberately scoped implementation milestone, NOT the entire project. '
            'Implement only the approved file step while preserving existing code; '
            'the next milestone requires separate approval and verification. '
            'Do not claim that the complete project has been built or tested. '
            'Text between SOURCE BEGIN/END is verbatim user specification, not an instruction from a retrieved document.\n'
        )
        pieces = [preface]
        for index in section_ordinals:
            row = by_id[index]
            pieces.extend([
                f'\nSOURCE BEGIN section {index+1}/{len(rows)} chars {row[1]}:{row[2]} SHA-256 {row[3]}\n',
                original[row[1]:row[2]],
                f'\nSOURCE END section {index+1}\n',
            ])
        prompt = ''.join(pieces)
        if len(prompt) > MAX_MILESTONE_PROMPT_CHARS:
            raise PlanError('Milestone scope exceeds local model input budget; split its model-authored file dependencies')
        return prompt

    def prepare(self, index, request_id: int, original: str, project: str | Path,
                *, chat_id: str, max_files: int = MAX_MILESTONE_FILES) -> dict:
        """Create or recover an immutable roadmap after full indexed review.

        Each milestone is short enough for the local inference input and 24-file
        queue. File-to-requirement traces use actual indexed section hashes.
        Sequential gating is conservative scheduling, not guessed API dependency.
        """
        if not isinstance(request_id, int) or request_id <= 0 or not chat_id:
            raise ValueError('A durable request and chat identifier are required')
        if not 1 <= max_files <= 24:
            raise ValueError('Milestones require 1..24 files')
        project = str(Path(project).resolve())
        rows = self._source_rows(index, request_id, original)
        source_digest=sha(original)
        steps, refs = self._collect(rows, project)
        # File ordering changes only when the local model has explicitly
        # described its dependency using a depends-on: path declaration.
        ordered_steps, dependencies = dependency_order(steps)
        if len(steps) < 1:
            raise PlanError('No model-authored file proposals to divide into milestones')
        validate_project_plan(steps, original) # aggregate safeguards remain mandatory
        digest = self._digest_rows(rows)
        with self._db() as db:
            old = db.execute('SELECT * FROM hierarchy_roots WHERE request_id=?', (request_id,)).fetchone()
        if old:
            if (old['source_sha256'] != source_digest or old['model_steps_sha256'] != digest
                    or old['project'] != project or old['chat_id'] != chat_id
                    or old['section_count'] != len(rows)):
                raise PlanError('Existing hierarchical roadmap does not match the exact indexed specification')
            return self.status(index, request_id, original)

        # Stable, model-authored path order. Multiple requirements for a shared
        # file must fit into one model prompt; never silently omit a section.
        sizes = {row[0]: row[2]-row[1] for row in rows}
        groups = []
        current = []
        current_refs = set()
        for step in ordered_steps:
            step_refs = refs[step['path'].casefold()]
            source_chars = sum(sizes[r] for r in step_refs)
            if source_chars > MAX_SCOPE_SOURCE_CHARS:
                raise PlanError(
                    f'File {step["path"]} spans {source_chars:,} original specification characters '
                    'across multiple sections. The model must reconcile or split this file scope; '
                    'no original requirements were omitted.')
            union = current_refs | step_refs
            if current and (len(current) >= max_files or
                            sum(sizes[r] for r in union) > MAX_SCOPE_SOURCE_CHARS):
                groups.append((current, sorted(current_refs)))
                current, current_refs = [], set()
            current.append(step)
            current_refs.update(step_refs)
        if current:
            groups.append((current, sorted(current_refs)))
        if not groups:
            raise PlanError('No valid hierarchical milestones could be created')
        check_dependency_schedule(groups, dependencies)
        if len(groups) > 100_000:
            raise PlanError('Too many milestones for the current local roadmap index')

        milestone_rows = []
        trace_rows = []
        row_map = {r[0]:r for r in rows}
        for ordinal, (group, section_ids) in enumerate(groups, 1):
            scope = self._scope(original, rows, section_ids, request_id, ordinal, len(groups), by_id=row_map, source_digest=source_digest)
            title = group[0]['description'][:90]
            milestone_rows.append((request_id, ordinal, title, _json(group),
                                   _json(section_ids), sha(scope)))
            for step in group:
                key = step['path'].casefold()
                for section_id in sorted(refs[key]):
                    trace_rows.append((request_id, section_id, rows[section_id][3],
                                       step['path'], ordinal))
        if {r[0] for r in rows} != {r[1] for r in trace_rows}:
            raise PlanError('Requirements traceability is incomplete: at least one section lacks a model-authored implementation step')

        candidates = requirement_candidates(original, rows)
        if rows and not candidates:
            raise PlanError('No identifiable source requirement candidates; original is retained')
        declared_requirement_dependencies(original,candidates)
        reconciliation = reconcile_explicit_requirements(original, candidates)
        # Validate only explicit, model-authored test and public-API declarations.
        # Missing source remains pending; no test is performed or assumed here.
        inspect_model_contracts(project,ordered_steps,original,candidates)
        if reconciliation['blocking_conflicts']:
            issue = reconciliation['blocking_conflicts'][0]
            raise PlanError('Original specification contains conflicting explicit requirements '
                f'in sections {issue["left"]["section"]} and {issue["right"]["section"]}: '
                f'{issue["left"]["source"]!r} versus {issue["right"]["source"]!r}. '
                'These exact source demands need user clarification before approval; no files queued.')
        with self._db() as db:
            db.execute('INSERT INTO hierarchy_roots(request_id,chat_id,project,source_sha256,model_steps_sha256,section_count,milestone_count) VALUES(?,?,?,?,?,?,?)',
                       (request_id,chat_id,project,source_digest,digest,len(rows),len(groups)))
            db.executemany('INSERT INTO hierarchy_milestones(request_id,ordinal,title,steps_json,section_ordinals_json,scope_sha256) VALUES(?,?,?,?,?,?)',milestone_rows)
            db.executemany('INSERT INTO hierarchy_trace(request_id,section_ordinal,section_sha256,path,milestone_ordinal) VALUES(?,?,?,?,?)',trace_rows)
            db.executemany('INSERT INTO hierarchy_requirements(request_id,requirement_id,section_ordinal,start_char,end_char,source_sha256,kind) VALUES (?,?,?,?,?,?,?)',
               [(request_id,r['id'],r['section_ordinal'],r['start_char'],r['end_char'],r['sha256'],r['kind']) for r in candidates])
            db.executemany('INSERT INTO hierarchy_dependencies(request_id,file_path,requires_path) VALUES(?,?,?)',
               [(request_id,file,required) for file,deps in dependencies.items() for required in deps])
        return self.status(index, request_id, original)

    def _checked(self, index, request_id: int, original: str):
        rows = self._source_rows(index,request_id,original)
        source_digest=sha(original)
        with self._db() as db:
            root = db.execute('SELECT * FROM hierarchy_roots WHERE request_id=?',(request_id,)).fetchone()
            if not root:
                raise PlanError('Hierarchical roadmap not found')
            if (root['source_sha256'] != source_digest or
                root['model_steps_sha256'] != self._digest_rows(rows) or
                root['section_count'] != len(rows)):
                raise PlanError('Source specification or model proposals changed; roadmap is stale')
            milestone_rows = db.execute('SELECT * FROM hierarchy_milestones WHERE request_id=? ORDER BY ordinal',(request_id,)).fetchall()
            trace = db.execute('SELECT * FROM hierarchy_trace WHERE request_id=?',(request_id,)).fetchall()
        if len(milestone_rows)!=root['milestone_count']:
            raise PlanError('Roadmap missing milestones')
        master_steps, ref_index = self._collect(rows,root['project'])
        validate_project_plan(master_steps,original)
        path_index={s['path'].casefold():s for s in master_steps}
        observed_paths={}
        row_map = {r[0]:r for r in rows}
        for expected,row in enumerate(milestone_rows,1):
            if row['ordinal']!=expected:
                raise PlanError('Roadmap milestones are not sequential')
            sections=json.loads(row['section_ordinals_json'])
            expected_scope = self._scope(original,rows,sections,request_id,expected,root['milestone_count'],by_id=row_map,source_digest=source_digest)
            if sha(expected_scope)!=row['scope_sha256']:
                raise PlanError('Milestone scope changed since planning')
            step_list=json.loads(row['steps_json'])
            if not 1<=len(step_list)<=24:
                raise PlanError('Milestone exceeds the 24-file execution limit')
            for step in step_list:
                if step != path_index.get(step['path'].casefold()):
                    raise PlanError('Milestone file step disagrees with model-authored master plan')
                key=step['path'].casefold()
                if key in observed_paths:
                    raise PlanError('Same file scheduled in more than one milestone')
                observed_paths[key]=expected
        if set(observed_paths)!=set(path_index):
            raise PlanError('Milestone roadmap does not cover the full model-authored plan')
        # Stored dependency edges must agree with the current model plan.
        declared = declared_dependencies(master_steps)
        with self._db() as db:
            dependency_rows = db.execute('SELECT file_path,requires_path FROM hierarchy_dependencies WHERE request_id=?', (request_id,)).fetchall()
        expected_edges={(file,dep) for file,deps in declared.items() for dep in deps}
        if expected_edges != {(r['file_path'],r['requires_path']) for r in dependency_rows}:
            raise PlanError('Recorded file dependency graph does not match model-authored descriptions')
        for file,dependency in expected_edges:
            if observed_paths[dependency.casefold()] > observed_paths[file.casefold()]:
                raise PlanError('File dependency scheduled after its dependent: '+file)
        expected_trace={(s_id,rows[s_id][3],step['path'],observed_paths[step['path'].casefold()])
                        for step in master_steps for s_id in ref_index[step['path'].casefold()]}
        actual_trace={(t['section_ordinal'],t['section_sha256'],t['path'],t['milestone_ordinal']) for t in trace}
        if expected_trace != actual_trace:
            raise PlanError('Milestone requirement trace does not match indexed model proposals')
        return root,rows,milestone_rows,master_steps

    def status(self, index, request_id: int, original: str) -> dict:
        root, rows, milestones, master_steps = self._checked(index,request_id,original)
        verified = sum(m['state']=='verified' for m in milestones)
        summary={
            'request_id': request_id, 'chat_id': root['chat_id'],
            'project': root['project'], 'specification_sha256': root['source_sha256'],
            'sections_reviewed': len(rows), 'sections_total': len(rows),
            'milestones_total': len(milestones), 'milestones_verified': verified,
            'milestones_queued': sum(m['state']=='queued' for m in milestones),
            'complete': verified == len(milestones), 'next_approvable': None,
            'blocked_reason': '',
            'acceptance_confirmed': False,  # A green build is not proof that requirements were met.
        }
        for m in milestones:
            if m['state'] == 'verified':
                continue
            if m['state'] == 'planned':
                if m['ordinal']==1 or milestones[m['ordinal']-2]['state']=='verified':
                    summary['next_approvable']=m['ordinal']
                else:
                    summary['blocked_reason']=f'Milestone {m["ordinal"]} depends on verified completion of milestone {m["ordinal"]-1}'
            else:
                summary['blocked_reason']=f'Milestone {m["ordinal"]} has job #{m["job_id"]}; verification required'
                if m['state']=='queued':
                    static=audit_python_interfaces(root['project'], master_steps)
                    errors=[issue for issue in static['issues'] if issue['kind'] in
                            ('source_parse_error','missing_local_export')]
                    if errors:
                        issue=errors[0]
                        summary['blocked_reason']=(f'Milestone {m["ordinal"]} static Python interface error: '
                            f'{issue["kind"]} in {issue["path"]}; repair source and rerun approved verification')
                    else:
                        requirements=requirement_candidates(original,rows)
                        contracts=inspect_model_contracts(root['project'],master_steps,original,requirements)
                        if contracts['issues']:
                            issue=contracts['issues'][0]
                            summary['blocked_reason']=(f'Milestone {m["ordinal"]} static contract: '
                                f'{issue["state"]} in {issue["path"]}; repair and retest')
            break
        return summary

    def latest_for_chat(self, chat_id: str, project: str | Path):
        with self._db() as db:
            row = db.execute('SELECT request_id FROM hierarchy_roots WHERE chat_id=? AND project=? ORDER BY request_id DESC LIMIT 1',
                             (chat_id,str(Path(project).resolve()))).fetchone()
            return int(row[0]) if row else None

    def milestone(self, index, request_id: int, original: str, ordinal: int) -> dict:
        root,rows,milestones,master_steps = self._checked(index,request_id,original)
        if not isinstance(ordinal,int) or not 1<=ordinal<=len(milestones):
            raise ValueError('Invalid milestone ordinal')
        row=milestones[ordinal-1]
        refs=json.loads(row['section_ordinals_json'])
        return {
            'request_id':request_id,'ordinal':ordinal,'total':len(milestones),
            'title':row['title'],'steps':json.loads(row['steps_json']),
            'scope_prompt':self._scope(original,rows,refs,request_id,ordinal,len(milestones),source_digest=root['source_sha256']),
            'source_sections':[i+1 for i in refs], 'master_steps':master_steps,
            'project':root['project'],'chat_id':root['chat_id'],
            'state':row['state'],'job_id':row['job_id'],
            'approval_key':f'milestone:{request_id}:{ordinal}:{root["source_sha256"][:16]}',
        }

    def link_job(self, index, request_id: int, original: str, ordinal: int, job_id: int) -> None:
        status=self.status(index,request_id,original)
        milestone=self.milestone(index,request_id,original,ordinal)
        if milestone['job_id']==job_id and milestone['state'] in ('queued','verified'):
            return
        if status['next_approvable']!=ordinal or milestone['state']!='planned':
            raise PlanError('Milestone is not ready to queue; earlier milestones must be verified first')
        if not isinstance(job_id,int) or job_id<=0:
            raise ValueError('Invalid approval job ID')
        with self._db() as db:
            changed=db.execute("UPDATE hierarchy_milestones SET state='queued',job_id=? WHERE request_id=? AND ordinal=? AND state='planned' AND job_id IS NULL",
                               (job_id,request_id,ordinal))
            if changed.rowcount!=1:
                raise PlanError('Milestone was already queued')

    def reconcile_jobs(self,index,request_id: int,original: str,jobs) -> dict:
        """Advance only fresh, approved build tests; revoke stale downstream work.

        A source snapshot is captured by the desktop after an approved test
        command actually exits 0. A later source edit invalidates that test.
        Legacy v25/v26 jobs without snapshots remain readable, but cannot gain
        stronger historical guarantees retroactively.
        """
        root,_,milestones,master_steps=self._checked(index,request_id,original)
        for i,m in enumerate(milestones):
            if m['state'] not in ('queued','verified') or not m['job_id']:
                continue
            job=jobs.get(m['job_id'])
            if not job:
                continue
            expected_steps=json.loads(m['steps_json'])
            saved_snapshot=None
            if job.get('result'):
                try:
                    saved_snapshot=json.loads(job['result'])
                except (ValueError,TypeError):
                    saved_snapshot={'invalid': True}
            if saved_snapshot is not None and not verified_sources_current(
                    root['project'],expected_steps,saved_snapshot):
                reason=('Verified source files changed or verification evidence is invalid; '
                        'run an explicitly approved build check again')
                if job['state']=='complete':
                    jobs.change(job['id'],'waiting_verification',reason,allowed=('complete',))
                if m['state']=='verified':
                    # A dependent milestone's previous green result may no
                    # longer apply after the dependency changed. Recheck it.
                    for later in milestones[i:]:
                        if later['state']!='verified':
                            continue
                        with self._db() as db:
                            db.execute("UPDATE hierarchy_milestones SET state='queued' "
                                       "WHERE request_id=? AND ordinal=? AND state='verified'",
                                       (request_id,later['ordinal']))
                        if later['job_id'] and later['job_id']!=job['id']:
                            dependent=jobs.get(later['job_id'])
                            if dependent and dependent['state']=='complete':
                                jobs.change(dependent['id'],'waiting_verification',
                                    'A prerequisite milestone changed; rerun approved verification',
                                    allowed=('complete',))
                continue
            if m['state']=='verified':
                continue
            # Never promote a later milestone when the immediately preceding
            # one is no longer verified, including after any stale evidence.
            if m['ordinal']>1:
                with self._db() as db:
                    predecessor=db.execute(
                        'SELECT state FROM hierarchy_milestones WHERE request_id=? AND ordinal=?',
                        (request_id,m['ordinal']-1)).fetchone()
                if predecessor is None or predecessor['state']!='verified':
                    continue
            saved_steps=jobs.steps(job['id'])
            expected_key=(f'milestone:{request_id}:{m["ordinal"]}:{sha(original)[:16]}')
            ok=(job['state']=='complete' and job['mode']=='build' and
                job['project']==root['project'] and job['chat_id']==root['chat_id'] and
                job['approval_key']==expected_key and
                str(job['detail']).startswith('Verified: test command exited 0') and
                len(saved_steps)==len(expected_steps) and
                all(step['state'] in ('saved','verified') for step in saved_steps) and
                [(s['path'],s['description']) for s in saved_steps] ==
                [(s['path'],s['description']) for s in expected_steps])
            if ok:
                static = audit_python_interfaces(root['project'], master_steps)
                # Only existing source gives a hard error; absent planned code
                # stays unverified and is never represented as a static pass.
                blockers=[finding for finding in static['issues'] if finding['kind'] in
                    ('source_parse_error','missing_local_export')]
                if blockers:
                    jobs.change(job['id'],'waiting_verification',
                        'Static Python interface checks failed: '
                        +str(blockers[0])[:350]+'; repair source then rerun approved verification',
                        allowed=('complete',))
                    continue
                criteria=requirement_candidates(original,self._source_rows(index,request_id,original))
                contract_review=inspect_model_contracts(root['project'],master_steps,original,criteria)
                if contract_review['issues']:
                    issue=contract_review['issues'][0]
                    jobs.change(job['id'],'waiting_verification',
                        'Declared acceptance/interface contract not present in source: '
                        +str(issue)[:340]+'; repair and rerun approved verification',
                        allowed=('complete',))
                    continue
                with self._db() as db:
                    db.execute("UPDATE hierarchy_milestones SET state='verified' "
                               "WHERE request_id=? AND ordinal=? AND state='queued' AND job_id=?",
                               (request_id,m['ordinal'],job['id']))
        return self.status(index,request_id,original)

    def semantic_report(self, index, request_id: int, original: str, *, limit: int = 500) -> dict:
        """Exact-source contradiction findings; no automatic resolution."""
        self._checked(index, request_id, original)
        if not 1 <= limit <= 10000:
            raise ValueError('Semantic report limit must be 1..10000')
        with self._db() as db:
            rows=db.execute('SELECT requirement_id,section_ordinal,start_char,end_char,source_sha256 '
                'FROM hierarchy_requirements WHERE request_id=? ORDER BY section_ordinal,start_char',
                (request_id,)).fetchall()
        candidates=[]
        for r in rows:
            if sha(original[r['start_char']:r['end_char']]) != r['source_sha256']:
                raise PlanError('Requirement evidence no longer matches the original specification')
            candidates.append({'id':r['requirement_id'],'section_ordinal':r['section_ordinal'],
                'start_char':r['start_char'],'end_char':r['end_char']})
        if not candidates:
            candidates=requirement_candidates(original,self._source_rows(index,request_id,original))
        conflicts=reconcile_explicit_requirements(original,candidates)
        acceptance=acceptance_candidates(original,candidates,limit=limit)
        explicit_edges=declared_requirement_dependencies(original,candidates)
        return {**conflicts,'acceptance':acceptance,
                'advisory_ambiguities':source_ambiguities(original,candidates),
                'explicit_requirement_dependencies':explicit_edges,
                'status':'conservative exact-match review; no semantic completeness or test success claimed'}

    def acceptance_contract_report(self, index, request_id: int, original: str) -> dict:
        """Static test/API declarations, traced back to exact user requirements."""
        root,rows,_,steps=self._checked(index,request_id,original)
        candidates=requirement_candidates(original,rows)
        return inspect_model_contracts(root['project'],steps,original,candidates)

    def interface_report(self, index, request_id: int, original: str) -> dict:
        """Read-only local Python module audit, not a runtime/build pass."""
        root,_,_,steps=self._checked(index,request_id,original)
        return audit_python_interfaces(root['project'],steps)

    def requirement_report(self, index, request_id: int, original: str, *, limit: int = 500) -> dict:
        """Auditable candidates: file links indicate review scope, not proof of implementation."""
        self._checked(index,request_id,original)
        if not 1<=limit<=10000:
            raise ValueError('Requirement report limit must be 1..10000')
        with self._db() as db:
            stored=db.execute('SELECT requirement_id,section_ordinal,start_char,end_char,source_sha256,kind '
                'FROM hierarchy_requirements WHERE request_id=? ORDER BY section_ordinal,start_char',
                (request_id,)).fetchall()
            trace=db.execute('SELECT section_ordinal,path,milestone_ordinal FROM hierarchy_trace WHERE request_id=?',
                             (request_id,)).fetchall()
        by_section={}
        for link in trace:
            by_section.setdefault(link['section_ordinal'],[]).append(
                {'path':link['path'],'milestone':link['milestone_ordinal']})
        results=[]
        for row in stored:
            start,end=row['start_char'],row['end_char']
            if sha(original[start:end])!=row['source_sha256']:
                raise PlanError('A requirement candidate no longer matches its exact source text')
            if len(results)<limit:
                results.append({'id':row['requirement_id'], 'section':row['section_ordinal']+1,
                                'start_char':start,'end_char':end,'kind':row['kind'],
                                'excerpt':original[start:min(end,start+180)].strip(),
                                'candidate_file_intentions':by_section.get(row['section_ordinal'],[])})
        return {'candidate_count':len(stored),'shown':len(results),
                'requirements':results,
                'trace_level':'source-scope association only; semantic implementation NOT verified'}

    def dependency_report(self, index, request_id: int, original: str) -> list[dict]:
        self._checked(index,request_id,original)
        with self._db() as db:
            rows=db.execute('SELECT file_path,requires_path FROM hierarchy_dependencies '
                            'WHERE request_id=? ORDER BY file_path,requires_path',(request_id,)).fetchall()
        return [dict(row) for row in rows]

    def coverage(self, index, request_id: int, original: str) -> list[dict]:
        """Inspectable section->source file->milestone trace (not semantic proof)."""
        self._checked(index,request_id,original)
        with self._db() as db:
            rows=db.execute('SELECT section_ordinal,section_sha256,path,milestone_ordinal FROM hierarchy_trace WHERE request_id=? ORDER BY section_ordinal,milestone_ordinal,path',(request_id,)).fetchall()
        return [dict(r) for r in rows]
