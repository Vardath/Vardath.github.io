"""Durable, exact-content index for specifications exceeding the model context.

The original is owned by ConversationStore. This index stores offsets, hashes
and scoped model proposals, not a silently truncated substitute for user text.
A long specification is NEVER approved until every indexed section has been
processed and the accumulated model-authored proposal passes validation.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .agent_plan import PlanError, parse_build_plan, validate_project_plan, project_kind

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

    def next_section(self, request_id: int, original: str):
        rows=self._verified_rows(request_id,original)
        for ordinal,start,end,digest,attempts,steps in rows:
            if not steps:
                return {'ordinal':ordinal,'start':start,'end':end,'sha256':digest,
                        'attempts':attempts,'total':len(rows),'text':original[start:end]}
        return None

    def model_prompt(self, request_id: int, original: str, *, max_chars: int=7500) -> str:
        row=self.next_section(request_id,original)
        if row is None:
            raise ValueError('Every section is already reviewed')
        context=(f'PROJECT SPECIFICATION INCREMENTAL REVIEW; section {row["ordinal"]+1}/{row["total"]}. '
          f'Original {len(original):,} characters stored exactly as supplied, SHA-256 {sha(original)[:20]}. '
          'This section is NOT the entire project. All sections must be reviewed before approval. '
          'Propose 1 or 2 concrete source files relevant to ONLY the supplied section. '
          'Return exactly {"files":[{"path":"relative/path.ext","description":"what this file implements"}]}. '
          'No markdown, no invented game IDs, no claims of execution. Do not modify the original specification.\n'
          f'UNMODIFIED SPECIFICATION SECTION {row["ordinal"]+1} (chars {row["start"]}:{row["end"]}):\n')
        prompt=context+row['text']+'\nEND OF SPECIFICATION SECTION.\n'
        if len(prompt)>max_chars:
            raise ValueError('Section and instructions exceed inference limit; source preserved')
        return prompt

    def save_response(self, request_id: int, original: str, ordinal: int, response: str,
                      *, project: str | Path) -> list[dict]:
        # Model-authored data only. Invalid format increments attempts but does
        # not mark the section reviewed, and can be retried safely.
        row=self.next_section(request_id,original)
        if row is None or row['ordinal']!=ordinal:
            raise ValueError('Only next unreviewed section may be completed')
        parsed=None
        try:
            parsed=parse_build_plan(response,project,fragment=True)
            if project_kind(row['text'])=='x4' and any(e['path'].lower().endswith('.py') for e in parsed):
                raise PlanError('X4 extension cannot be built from generic Python app files')
        finally:
            with self._db() as db:
                db.execute('UPDATE specification_sections SET attempts=attempts+1 WHERE request_id=? AND ordinal=?',
                           (request_id,ordinal))
        if parsed is not None:
            with self._db() as db:
                db.execute('UPDATE specification_sections SET steps_json=? WHERE request_id=? AND ordinal=? AND steps_json=?',
                           (json.dumps(parsed),request_id,ordinal,''))
        return parsed

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
                          stage=None, cancelled=None) -> tuple[str,list[dict]]:
    """Consume exact sections; never substitute partial coverage for full approval.

    Each invocation remains bounded; successful sections resume from SQLite on
    retry. The project-level plan stays unapproved until all sections reviewed.
    """
    if not 1<=max_rounds<=40:
        raise ValueError('Planning attempts must be 1..40')
    index.index(request_id,original)
    for attempt in range(max_rounds):
        if cancelled and cancelled():
            raise PlanError('Planning stopped by user; indexed specification remains saved')
        row=index.next_section(request_id,original)
        if row is None:
            break
        if stage:
            stage(f'Large specification section {row["ordinal"]+1}/{row["total"]}; '
                  f'local inference pass {attempt+1}/{max_rounds}')
        prompt=index.model_prompt(request_id,original)
        exchange=f'{session}-spec-{row["ordinal"]}-{row["attempts"]}'
        lookup=getattr(client,'completed_exchange',None)
        response=lookup(exchange,prompt) if callable(lookup) else None
        if response is None:
            response=client.chat(exchange,prompt,max_tokens=640)
        if cancelled and cancelled():
            raise PlanError('Planning stopped by user; no additional sections marked complete')
        try:
            index.save_response(request_id,original,row['ordinal'],response,project=project)
        except PlanError as exc:
            if stage:stage(f'Large specification section {row["ordinal"]+1} rejected: {exc}')
    progress=index.status(request_id,original)
    if progress['pending']:
        raise PlanError(f'Large specification stored without truncation: {progress["reviewed"]}/{progress["sections"]} '
                        f'sections reviewed; {progress["pending"]} still require model inspection. '
                        'No complete plan or executable work approved. Retry to continue saved progress.')
    steps=index.merged_steps(request_id,original)
    if len(steps)>24:
        raise PlanError(f'All {progress["sections"]} specification sections reviewed, but the model proposed '
                        f'{len(steps)} file stages and the current single-plan executor accepts 24. '
                        'A hierarchical milestone planner is required before execution; source preserved.')
    validated=validate_project_plan(steps,original)
    return json.dumps({'files':validated},ensure_ascii=False),validated
