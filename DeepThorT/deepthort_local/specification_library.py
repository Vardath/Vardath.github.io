"""Durable, exact-content index for specifications exceeding the model context.

The original is owned by ConversationStore. This index stores offsets, hashes
and scoped model proposals, not a silently truncated substitute for user text.
A long specification is NEVER approved until every indexed section has been
processed and the accumulated model-authored proposal passes validation.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
import sqlite3
from pathlib import Path, PurePosixPath
from contextlib import contextmanager
from .agent_plan import (PlanError, VanillaSourceCollision, parse_build_plan, validate_project_plan,
                         incompatible_x4_path, project_kind, remaining_plan_gaps)
from .x4_variant import VariantSource

# A practical local storage ceiling, not an inference-context limit. Millions
# of ordinary-language words fit, subject to available memory and disk space.
MAX_STORED_REQUEST_CHARS = 120_000_000
SECTION_CHARS = 3_200


def sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sections(text: str, limit: int = SECTION_CHARS) -> list[tuple[int,int]]:
    """Deterministic, complete non-overlapping UTF-8-safe character ranges."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Specification must contain text')
    if not 256 <= limit <= 7000:
        raise ValueError('Invalid section size')
    spans=[]
    start=0
    while start<len(text):
        end=min(start+limit,len(text))
        if end<len(text):
            # Prefer paragraph / line boundaries near the end, without leaving
            # fragments behind or dropping even a single character.
            split=text.rfind('\n',start+limit//2,end)
            if split>start:
                end=split+1
        spans.append((start,end))
        start=end
    assert spans[0][0]==0 and spans[-1][1]==len(text)
    return spans


class SpecificationIndex:
    def __init__(self, path: str | Path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS specification_index (
                  request_id INTEGER PRIMARY KEY, source_sha256 TEXT NOT NULL,
                  character_count INTEGER NOT NULL, section_count INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS specification_sections (
                  request_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                  start_char INTEGER NOT NULL, end_char INTEGER NOT NULL,
                  section_sha256 TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                  steps_json TEXT NOT NULL DEFAULT '',
                  PRIMARY KEY(request_id,ordinal));
                CREATE TABLE IF NOT EXISTS specification_revision_attempts (
                  request_id INTEGER NOT NULL, serial INTEGER NOT NULL,
                  section_ordinal INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
                  prompt_sha256 TEXT NOT NULL,
                  PRIMARY KEY(request_id,serial));
                CREATE TABLE IF NOT EXISTS specification_revision_outcomes (
                  request_id INTEGER NOT NULL, serial INTEGER NOT NULL,
                  source_sha256 TEXT NOT NULL, before_gaps INTEGER NOT NULL,
                  after_gaps INTEGER NOT NULL, checks_closed INTEGER NOT NULL,
                  checks_opened INTEGER NOT NULL, total_files INTEGER NOT NULL,
                  accepted INTEGER NOT NULL, made_progress INTEGER NOT NULL,
                  PRIMARY KEY(request_id,serial));
                CREATE TABLE IF NOT EXISTS retired_section_proposals (
                  request_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                  section_sha256 TEXT NOT NULL, steps_json TEXT NOT NULL,
                  PRIMARY KEY(request_id,ordinal,section_sha256,steps_json));
                CREATE TABLE IF NOT EXISTS variant_collisions (
                  request_id INTEGER NOT NULL, ordinal INTEGER NOT NULL,
                  source_path TEXT NOT NULL, source_digest TEXT NOT NULL,
                  failed_attempt INTEGER NOT NULL, PRIMARY KEY(request_id,ordinal));
                CREATE TABLE IF NOT EXISTS variant_bindings (
                  project TEXT NOT NULL, package TEXT NOT NULL, source_path TEXT NOT NULL,
                  source_digest TEXT NOT NULL, macro_name TEXT NOT NULL,
                  PRIMARY KEY(project,package,source_path,source_digest,macro_name));
            ''')

    @contextmanager
    def _db(self):
        con=sqlite3.connect(self.path,timeout=30)
        try:
            with con:
                yield con
        finally:
            con.close()

    def index(self, request_id: int, original: str) -> dict:
        if not isinstance(request_id,int) or request_id<=0:
            raise ValueError('Valid durable conversation request ID required')
        if len(original)>MAX_STORED_REQUEST_CHARS:
            raise ValueError(f'Specification exceeds practical local storage ceiling of {MAX_STORED_REQUEST_CHARS:,} characters')
        fingerprint=sha(original)
        with self._db() as db:
            existing=db.execute('SELECT source_sha256,section_count FROM specification_index WHERE request_id=?', (request_id,)).fetchone()
            if existing:
                if existing[0]!=fingerprint:
                    raise ValueError('Source specification changed: never reuse indexed progress against different instructions')
                return self.status(request_id, original)
            spans=sections(original)
            db.execute('INSERT INTO specification_index VALUES (?,?,?,?)',
                       (request_id,fingerprint,len(original),len(spans)))
            db.executemany('''INSERT INTO specification_sections
              (request_id,ordinal,start_char,end_char,section_sha256)
              VALUES (?,?,?,?,?)''',[(request_id,i,start,end,sha(original[start:end]))
                                    for i,(start,end) in enumerate(spans)])
        return self.status(request_id,original)

    def inherit_exact_progress(self, request_id: int, original: str,
                               project: str | Path, chat_id: str) -> int:
        """Recover old indexed sections only from the exact original workspace.

        A diagnostic ZIP deliberately omits user instructions and model outputs,
        so it cannot be used for reconstruction. This uses the existing local
        SQLite state, with source-section hashes and current path validation.
        No approval or executable action is inherited.
        """
        conversations_path = self.path.parent / 'conversations.sqlite3'
        if not chat_id or not conversations_path.is_file():
            return 0
        self.index(request_id, original)
        with closing(sqlite3.connect(conversations_path, timeout=20)) as db, db:
            candidates = [int(ident) for ident, saved_project in db.execute(
                'SELECT id,project FROM conversation_requests '
                'WHERE id<>? AND chat_id=? AND mode=? AND prompt=? AND attachments=? '
                'ORDER BY id DESC',
                (request_id,chat_id,'draft_plan',original,'[]'))
                if str(Path(saved_project).resolve()).casefold() ==
                   str(Path(project).resolve()).casefold()]
        if not candidates:
            return 0
        dest = self._verified_rows(request_id, original)
        if any(row[5] for row in dest):
            return 0
        for old_id in candidates:
            try:
                source = self._verified_rows(old_id, original)
            except ValueError:
                continue
            if len(source) != len(dest):
                continue
            valid = []
            for row in source:
                if not row[5]:
                    continue
                try:
                    steps = json.loads(row[5])
                    checked = parse_build_plan(json.dumps({'files':steps}),project,fragment=True)
                    if checked != steps:
                        continue
                    if project_kind(original) == 'x4':
                        checked = [step for step in checked if not incompatible_x4_path(step['path'],original)]
                        if not checked:
                            continue
                except (ValueError,PlanError):
                    continue
                if row[0] != dest[row[0]][0] or row[3] != dest[row[0]][3]:
                    continue
                valid.append((json.dumps(checked, ensure_ascii=False),request_id,row[0]))
            if valid:
                with self._db() as db:
                    db.executemany('UPDATE specification_sections SET steps_json=? '
                                   'WHERE request_id=? AND ordinal=? AND steps_json=\'\'', valid)
                return len(valid)
        return 0

    def _verified_rows(self, request_id: int, original: str):
        with self._db() as db:
            meta=db.execute('SELECT source_sha256,character_count,section_count FROM specification_index WHERE request_id=?',(request_id,)).fetchone()
            if not meta or meta[0]!=sha(original) or meta[1]!=len(original):
                raise ValueError('Specification index unavailable or source content changed')
            rows=db.execute('''SELECT ordinal,start_char,end_char,section_sha256,attempts,steps_json
               FROM specification_sections WHERE request_id=? ORDER BY ordinal''',(request_id,)).fetchall()
        if len(rows)!=meta[2]:
            raise ValueError('Specification index is incomplete')
        if any(sha(original[a:b])!=digest for _,a,b,digest,_,_ in rows):
            raise ValueError('Indexed specification section differs from stored original')
        return rows

    def status(self, request_id: int, original: str) -> dict:
        rows=self._verified_rows(request_id,original)
        done=sum(bool(row[5]) for row in rows)
        return {'sections':len(rows),'reviewed':done,'pending':len(rows)-done,
                'characters':len(original),'sha256':sha(original),
                'model_attempts':sum(row[4] for row in rows)}

    def reserve_revision_attempt(self, request_id: int, original: str,
                                 ordinal: int, prompt: str) -> int:
        """Number a scoped model call durably; invalid answers are not replayed forever."""
        rows = self._verified_rows(request_id, original)
        if not 0 <= ordinal < len(rows) or not rows[ordinal][5]:
            raise ValueError('Only fully indexed, already reviewed sections can be revised')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            serial = db.execute('SELECT COALESCE(MAX(serial),0)+1 FROM '
                'specification_revision_attempts WHERE request_id=?',(request_id,)).fetchone()[0]
            db.execute('INSERT INTO specification_revision_attempts VALUES (?,?,?,?,?)',
                (request_id,serial,ordinal,sha(original),sha(prompt)))
        return serial

    def record_revision_outcome(self, request_id: int, original: str, serial: int,
                                before: list[str], after: list[str], *,
                                file_count: int, accepted: bool) -> dict:
        """Persist objective validator progress, not merely model activity.

        A changed description or extra proposed file does not count as
        acceptance progress until an actual previously unmet check closes.
        Review history is retained across a manual retry or application restart.
        """
        self._verified_rows(request_id, original)
        before_set, after_set = set(before), set(after)
        closed, opened = before_set-after_set, after_set-before_set
        with self._db() as db:
            attempt = db.execute('SELECT source_sha256 FROM specification_revision_attempts '
                                 'WHERE request_id=? AND serial=?',
                                 (request_id,serial)).fetchone()
            if not attempt or attempt[0] != sha(original):
                raise ValueError('Revision attempt is not part of this exact specification')
            db.execute("""INSERT INTO specification_revision_outcomes
                (request_id,serial,source_sha256,before_gaps,after_gaps,
                 checks_closed,checks_opened,total_files,accepted,made_progress)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (request_id,serial,sha(original),len(before_set),len(after_set),
                 len(closed),len(opened),file_count,int(accepted),
                 int(bool(closed) and not opened)))
        return self.roadmap_stall_status(request_id, original)

    def roadmap_stall_status(self, request_id: int, original: str) -> dict:
        self._verified_rows(request_id,original)
        with self._db() as db:
            history = db.execute("""SELECT serial,made_progress,checks_closed,
                checks_opened,after_gaps,total_files FROM specification_revision_outcomes
                WHERE request_id=? AND source_sha256=? ORDER BY serial DESC""",
                (request_id,sha(original))).fetchall()
        consecutive=0
        for _,progress,*_ in history:
            if progress: break
            consecutive+=1
        return {'recorded_attempts':len(history),
                'unproductive_in_a_row':consecutive,
                'last_gap_count':history[0][4] if history else None,
                'last_file_count':history[0][5] if history else None,
                'checks_closed_total':sum(row[2] for row in history if row[1])}

    def merge_model_revision(self, request_id: int, original: str, ordinal: int,
                             answer: str, *, project: str | Path, inspected_evidence: str='') -> bool:
        """Persist ONLY a structurally valid model correction to one exact section.

        The original section text and its digest never change. Existing model
        proposals survive unless the model explicitly revises the same path,
        and a rewrite cannot erase coverage already present. No authorization.
        """
        rows = self._verified_rows(request_id, original)
        if not rows or any(not row[5] for row in rows) or not 0 <= ordinal < len(rows):
            raise ValueError('Every section must be indexed before correcting the roadmap')
        proposal = parse_build_plan(answer, project, request=original, fragment=True, inspected_evidence=inspected_evidence)
        own = {item['path'].casefold(): item for item in json.loads(rows[ordinal][5])}
        others = {}
        for row in rows:
            if row[0]==ordinal:continue
            for item in json.loads(row[5]):
                others.setdefault(item['path'].casefold(),item)
        new = dict(own)
        for step in proposal:
            key=step['path'].casefold()
            if key in others:
                if others[key] != step:
                    raise PlanError('Corrected file conflicts with a proposal in another reviewed section: '+step['path'])
                # Do not attach one file to multiple 3,200-character scopes
                # merely because the model repeats a previously accepted step.
                continue
            new[key]=step
        if len(new)>24:
            raise PlanError('Corrected section exceeds 24 model-authored file entries')
        if new==own:return False
        def combined(own_steps):
            merged={}
            for row in rows:
                for item in (own_steps if row[0]==ordinal else json.loads(row[5])):
                    merged[item['path'].casefold()]=item
            return list(merged.values())
        before = set(remaining_plan_gaps(combined(own.values()),original))
        after = set(remaining_plan_gaps(combined(new.values()),original))
        new_paths = set(new)-set(own)
        if after-before:
            # New paths must not be used to excuse replacing already accepted
            # descriptions with regressions. This guards against oscillating
            # coverage during many hours of low-resource ONNX revisions. A
            # newly required index must be proposed in the SAME correction as
            # the asset that introduced it.
            raise PlanError('Correction would introduce unmet X4 requirements: '+
                            '; '.join(sorted(after-before)))
        with self._db() as db:
            cursor=db.execute('UPDATE specification_sections SET steps_json=? '
                'WHERE request_id=? AND ordinal=? AND steps_json=?',
                (json.dumps(list(new.values()),ensure_ascii=False),request_id,
                 ordinal,rows[ordinal][5]))
            if cursor.rowcount!=1:
                raise ValueError('Section changed during model correction; retry with current state')
        return True

    def next_section(self, request_id: int, original: str):
        rows=self._verified_rows(request_id,original)
        for ordinal,start,end,digest,attempts,steps in rows:
            if not steps:
                return {'ordinal':ordinal,'start':start,'end':end,'sha256':digest,
                        'attempts':attempts,'total':len(rows),'text':original[start:end]}
        return None

    def x4_draft_probe(self, project: str) -> dict:
        """Inspect the latest indexed draft in the selected workspace without changing its state."""
        conversations = self.path.parent/'conversations.sqlite3'
        if conversations.is_file():
            with closing(sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
                db.execute('ATTACH DATABASE ? AS history', (conversations.resolve().as_uri()+'?mode=ro',))
                row = db.execute("SELECT c.id,c.prompt FROM history.conversation_requests c "
                                 "JOIN specification_index s ON s.request_id=c.id "
                                 "WHERE c.mode='draft_plan' AND c.project=? COLLATE NOCASE ORDER BY c.id DESC LIMIT 1",
                                 (str(Path(project).resolve()),)).fetchone()
        else:
            row = None
        if not row or project_kind(row[1]) != 'x4':
            return {'status':'inconclusive','detail':'No current indexed X4 draft in this workspace.'}
        ident, original = row
        status = self.status(ident, original)
        steps = self.merged_steps(ident, original)
        foreign = sum(incompatible_x4_path(step['path'],original) for step in steps)
        gaps = remaining_plan_gaps(steps, original)
        with self._db() as db:
            bindings = db.execute('SELECT package,source_path,source_digest,macro_name FROM variant_bindings '
                                  'WHERE project=?', (str(Path(project).resolve()),)).fetchall()
        pairs = sum(all(step in steps for step in VariantSource(package,PurePosixPath(path),digest).steps(name))
                    for package,path,digest,name in bindings)
        return {'status':'blocked' if foreign or gaps or status['pending'] else 'passed',
                'detail':f"Draft #{ident}: {status['reviewed']}/{status['sections']} sections reviewed, "
                         f"{foreign} incompatible paths, {len(gaps)} open planning checks, {pairs} source-backed ship/index pairs planned. "
                         "Build and playtest require separate evidence."}

    def recover_x4_draft(self, request_id: int, original: str) -> int:
        """Retain each prior draft verbatim before removing foreign paths from active planning."""
        self._verified_rows(request_id, original)
        retired = 0
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute('SELECT ordinal,section_sha256,steps_json FROM specification_sections '
                              "WHERE request_id=? AND steps_json!=''", (request_id,)).fetchall()
            for ordinal, digest, raw in rows:
                steps = json.loads(raw)
                kept = [step for step in steps if not incompatible_x4_path(step['path'],original)]
                if len(kept) == len(steps):
                    continue
                db.execute('INSERT OR IGNORE INTO retired_section_proposals VALUES (?,?,?,?)',
                           (request_id, ordinal, digest, raw))
                db.execute('UPDATE specification_sections SET steps_json=? WHERE request_id=? AND ordinal=?',
                           (json.dumps(kept, ensure_ascii=False) if kept else '', request_id, ordinal))
                retired += len(steps) - len(kept)
        return retired

    def model_prompt(self, request_id: int, original: str, *, max_chars: int=7500,
                     inspected_evidence: str='') -> str:
        row=self.next_section(request_id,original)
        if row is None:
            raise ValueError('Every section is already reviewed')
        context=(f'PROJECT SPECIFICATION INCREMENTAL REVIEW; section {row["ordinal"]+1}/{row["total"]}. '
          f'Original {len(original):,} characters stored exactly as supplied, SHA-256 {sha(original)[:20]}. '
          'This section is NOT the entire project. All sections must be reviewed before approval. '
          'Propose 1 or 2 concrete source files relevant to ONLY the supplied section. '
          'Return exactly {"files":[{"path":"relative/path.ext","description":"what this file implements"}]}. '
          'If a file has a SPECIFIED, exact dependency on another source file, you may append '
          '"; depends-on: relative/other.ext" to its description; never invent dependencies. '
          'When a user requirement is explicitly labelled REQ-N and you propose a genuine test file, '
          'append "; verifies: REQ-N"; for Python API files use "; provides: Symbol" or '
          '"; uses: path/to/provider.py::Symbol" only when this is a real intended contract. '
          'These declarations require source inspection later and never prove acceptance. '
          'No markdown, no invented game IDs, no claims of execution. Do not modify the original specification.\n'
          f'UNMODIFIED SPECIFICATION SECTION {row["ordinal"]+1} (chars {row["start"]}:{row["end"]}):\n')
        prompt=context+row['text']+'\nEND OF SPECIFICATION SECTION.\n'
        if project_kind(original) == 'x4':
            from .indexed_roadmap_repair import x4_section_prompt
            proposals = self.merged_steps(request_id, original)
            prompt = x4_section_prompt(row, inspected_evidence, max_chars,
                                       [step['path'] for step in proposals],
                                       remaining_plan_gaps(proposals, original))
        if len(prompt)>max_chars:
            raise ValueError('Section and instructions exceed inference limit; source preserved')
        return prompt

    def pending_variant(self, request_id, row, original, evidence):
        with self._db() as db:
            record = db.execute('SELECT source_path,source_digest,failed_attempt FROM variant_collisions '
                                'WHERE request_id=? AND ordinal=?', (request_id,row['ordinal'])).fetchone()
        if record and 0 <= row['attempts'] - record[2] < 2:
            source = VariantSource.inspected(original, evidence, record[0])
            if source and source.digest == record[1]:
                return source
        return None

    def save_response(self, request_id: int, original: str, ordinal: int, response: str,
                      *, project: str | Path, inspected_evidence: str='', variant=None) -> list[dict]:
        # Model-authored data only. Invalid format increments attempts but does
        # not mark the section reviewed, and can be retried safely.
        row=self.next_section(request_id,original)
        if row is None or row['ordinal']!=ordinal:
            raise ValueError('Only next unreviewed section may be completed')
        parsed=None
        collision=None
        try:
            if variant is not None:
                response = variant.proposal(response, inspected_evidence)
            parsed=parse_build_plan(response,project,request=original,fragment=True,inspected_evidence=inspected_evidence)
        except VanillaSourceCollision as exc:
            collision=VariantSource.inspected(original, inspected_evidence, exc.path)
            raise
        finally:
            with self._db() as db:
                db.execute('UPDATE specification_sections SET attempts=attempts+1 WHERE request_id=? AND ordinal=?',
                           (request_id,ordinal))
                if collision:
                    db.execute('INSERT OR REPLACE INTO variant_collisions SELECT request_id,ordinal,?,?,attempts '
                               'FROM specification_sections WHERE request_id=? AND ordinal=? AND steps_json=?',
                               (str(collision.path),collision.digest,request_id,ordinal,''))
        if parsed is not None:
            with self._db() as db:
                db.execute('BEGIN IMMEDIATE')
                if project_kind(original) == 'x4':
                    siblings = db.execute("SELECT steps_json FROM specification_sections WHERE request_id=? "
                                          "AND ordinal<>? AND steps_json<>''", (request_id,ordinal))
                    assigned = {step['path'].casefold(): step for (raw,) in siblings for step in json.loads(raw)}
                    for step in parsed:
                        other = assigned.get(step['path'].casefold())
                        if other is not None and other != step:
                            raise PlanError('Another section already owns a different proposal for '+step['path'])
                changed = db.execute('UPDATE specification_sections SET steps_json=? WHERE request_id=? AND ordinal=? AND steps_json=?',
                                     (json.dumps(parsed),request_id,ordinal,'')).rowcount
                if not changed:
                    raise PlanError('Another reviewer already completed this section')
                if variant:
                    db.execute('INSERT OR IGNORE INTO variant_bindings VALUES (?,?,?,?,?)',
                               (str(Path(project).resolve()),variant.package,str(variant.path),variant.digest,
                                PurePosixPath(parsed[0]['path']).stem))
        return parsed

    def render_planned_variant(self, project, relative, steps, reference_dir):
        """Supply a new file to the normal Build approval path only for the exact recorded pair."""
        if not reference_dir or not (relative=='index/macros.xml' or '/macros/' in relative):
            return None
        approved = {step['path']:step['description'] for step in steps}
        with self._db() as db:
            bindings = db.execute('SELECT package,source_path,source_digest,macro_name FROM variant_bindings '
                                  'WHERE project=?', (str(Path(project).resolve()),)).fetchall()
        for package, source, digest, name in bindings:
            variant = VariantSource(package,PurePosixPath(source),digest)
            pair = variant.steps(name)
            if relative not in (pair[0]['path'], pair[1]['path']):
                continue
            if any(approved.get(step['path'])!=step['description'] for step in pair):
                continue
            if relative=='index/macros.xml' and any('/macros/' in p and p!=pair[0]['path'] for p in approved):
                continue
            return variant.render(name,relative,reference_dir)
        return None

    def merged_steps(self, request_id: int, original: str) -> list[dict]:
        rows=self._verified_rows(request_id,original)
        merged={}
        for row in rows:
            if row[5]:
                for step in json.loads(row[5]):
                    key=step['path'].casefold()
                    if key in merged and merged[key]!=step:
                        # Conflicts need model reconciliation before approval;
                        # do not overwrite earlier user-scoped intentions.
                        raise PlanError('Conflicting definitions for '+step['path']+' in separate specification sections')
                    merged[key]=step
        return list(merged.values())


def generate_indexed_plan(client, index: SpecificationIndex, request_id: int, session: str,
                          original: str, project: str | Path, *, max_rounds: int=40,
                          stage=None, cancelled=None, hierarchy=None, chat_id: str = '',
                          continuous: bool = False,
                          neural_council: bool = False, inspected_evidence: str = '',
                          guidance_getter=None, checkpoint=None, council_provider=None) -> tuple[str,list[dict]]:
    """Consume exact sections; never substitute partial coverage for full approval.

    Each invocation remains bounded; successful sections resume from SQLite on
    retry. The project-level plan stays unapproved until all sections reviewed.
    """
    if not 1<=max_rounds<=40:
        raise ValueError('Planning attempts must be 1..40')
    index.index(request_id,original)
    if chat_id:
        inherited=index.inherit_exact_progress(request_id,original,project,chat_id)
        if inherited and stage:
            stage(f'Recovered {inherited} already reviewed large-document sections '
                  'from exact matching local historical state; not a build approval')
    x4 = project_kind(original) == 'x4'
    if x4 and (hierarchy is None or not hierarchy.has_roadmap(request_id)):
        retired = index.recover_x4_draft(request_id, original)
        if retired and stage:
            stage(f'Retained {retired} incompatible old file proposals in draft history; resuming X4 review')
    section_calls=0
    section_batch=0
    reviewed_this_batch=0
    consecutive_invalid=0
    last_rejection=''
    while True:
        if cancelled and cancelled():
            raise PlanError('Planning stopped by user; indexed specification remains saved')
        row=index.next_section(request_id,original)
        if row is None:
            break
        if section_calls >= (section_batch+1)*max_rounds:
            if not continuous or not reviewed_this_batch:
                break
            section_batch += 1
            reviewed_this_batch = 0
            if stage:
                stage(f'Indexed source checkpoint saved after {section_calls} model calls; '
                      'starting another 40-call batch because reviewed sections advanced')
        if stage:
            stage(f'Large-document review: section {row["ordinal"]+1}/{row["total"]}; '
                  f'model call {(section_calls % max_rounds)+1}/{max_rounds} in batch '
                  f'{section_batch+1} (not a file count or total-project limit)')
        variant = index.pending_variant(request_id,row,original,inspected_evidence) if x4 else None
        if variant:
            prompt = variant.prompt()
        elif x4:
            prompt = index.model_prompt(request_id,original,inspected_evidence=inspected_evidence)
        else:
            prompt = index.model_prompt(request_id,original)
        if x4 and last_rejection and not variant:
            note = '\nPrevious proposal rejected: ' + last_rejection[:240]
            if len(prompt+note) <= 7500:
                prompt += note
        # A new user message may arrive while the first ONNX inference runs.
        # JANUS/Sentinel advice joins ONLY this NEW planning pass. Never
        # mutate the indexed original or the approved build-stage contract.
        if guidance_getter and len(prompt)<5800:
            advice=guidance_getter()
            if advice and len(prompt)+len(advice)+2<=7900:
                prompt+='\n\n'+advice
        exchange=f'{session}-spec-{row["ordinal"]}-{row["attempts"]}'
        if checkpoint:
            prompt, instruction = checkpoint.attach(prompt, 7500)
        lookup=getattr(client,'completed_exchange',None)
        response=lookup(exchange,prompt) if callable(lookup) else None
        if response is None:
            response=client.chat(exchange,prompt,max_tokens=64 if variant else (224 if x4 else 640))
        if checkpoint:
            checkpoint.received(instruction, exchange, prompt, response)
        section_calls+=1
        if cancelled and cancelled():
            raise PlanError('Planning stopped by user; no additional sections marked complete')
        try:
            options = {'variant':variant} if variant else {}
            index.save_response(request_id,original,row['ordinal'],response,project=project,
                                inspected_evidence=inspected_evidence,**options)
            reviewed_this_batch+=1
            consecutive_invalid=0
            last_rejection=''
        except PlanError as exc:
            consecutive_invalid+=1
            last_rejection=str(exc)
            if stage:stage(f'Large specification section {row["ordinal"]+1} rejected: {exc}')
            if continuous and consecutive_invalid>=8:
                raise PlanError('Large-document review paused after 8 invalid model replies '
                    'without a reviewed section. Original sections and saved proposals '
                    'remain intact; further identical inference is not productive.') from exc
    progress=index.status(request_id,original)
    if progress['pending']:
        raise PlanError(f'Large specification stored without truncation: {progress["reviewed"]}/{progress["sections"]} '
                        f'sections reviewed; {progress["pending"]} still require model inspection. '
                        'No complete plan or executable work approved. Retry to continue saved progress.')
    # The indexed source is now a master specification, not a file-stage plan.
    # A hierarchy must be explicitly reviewed and approved one milestone at a
    # time; never bypass the old 24-stage queue by submitting one giant job.
    if hierarchy is not None:
        if not chat_id:
            raise ValueError('Hierarchical planning requires a durable chat identifier')
        try:
            summary=hierarchy.prepare(index,request_id,original,project,chat_id=chat_id)
        except PlanError as exc:
            # A v46 indexed X4 plan could have all sections "reviewed" but none
            # of the required extension files. Retrying immediately raised the
            # SAME error without calling the model. Correct the saved plan
            # using additional scoped, model-authored revisions instead.
            if (project_kind(original)!='x4' or
                    not str(exc).startswith('Plan does not cover the X4 specification: ')):
                raise
            from .indexed_roadmap_repair import repair_indexed_roadmap
            summary=repair_indexed_roadmap(
                client,index,hierarchy,request_id,session,original,project,
                chat_id=chat_id,
                max_rounds=(max_rounds if continuous else max_rounds-section_calls),
                stage=stage,cancelled=cancelled,continuous=continuous,
                neural_council=neural_council,inspected_evidence=inspected_evidence,
                guidance_getter=guidance_getter, checkpoint=checkpoint, council_provider=council_provider)
        return json.dumps({'hierarchy_ready':summary},ensure_ascii=False), []
    steps=index.merged_steps(request_id,original)
    if len(steps)>24:
        raise PlanError(f'All {progress["sections"]} specification sections reviewed, but the model proposed '
                        f'{len(steps)} file stages and the current single-plan executor accepts 24. '
                        'A hierarchical milestone planner is required before execution; source preserved.')
    validated=validate_project_plan(steps,original)
    return json.dumps({'files':validated},ensure_ascii=False),validated
