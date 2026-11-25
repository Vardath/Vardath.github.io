"""Two actual local-model reasoning turns, coordinated by JANUS and Sentinel.

JANUS proposes testable alternatives; Sentinel challenges them against observed
source/acceptance evidence. Both use the SAME single-flight ONNX model, not
independent neural weights, separate model servers, or uncontrolled processes.
The outputs are untrusted *advice*, never executable authority or proof.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path


def sha(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class ReasoningCouncil:
    def __init__(self, db_path: str | Path):
        self.db_path=Path(db_path)
        self.db_path.parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS deliberations (
                evidence_sha TEXT NOT NULL, role TEXT NOT NULL,
                prompt_sha TEXT NOT NULL, answer TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY(evidence_sha,role))''')

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.db_path,timeout=6)
        try:
            with db:
                yield db
        finally:
            db.close()

    def _run(self, client, *, role, session, evidence_sha, prompt, stage=None) -> str:
        with self._db() as db:
            row=db.execute('SELECT answer,prompt_sha FROM deliberations WHERE evidence_sha=? AND role=?',
                           (evidence_sha,role)).fetchone()
        if row:
            if row[1]!=sha(prompt):
                raise ValueError('Reasoning evidence changed; previous advice cannot be reused')
            return row[0]
        if stage:
            stage(f'{role} neural reasoning: consulting the assigned capped local Triad model; no files changed')
        # Completed identical responses from local durable client history can
        # be reused after a restart; no second server and no concurrent model.
        call_id=f'{session}-council-{role.casefold()}-{evidence_sha[:18]}'
        lookup=getattr(client,'completed_exchange',None)
        result=lookup(call_id,prompt) if callable(lookup) else None
        if result is None:
            from .triad_profiles import role_for_council
            if callable(getattr(type(client),'chat_as',None)):
                result=client.chat_as(role_for_council(role),call_id,prompt,max_tokens=240)
            else:result=client.chat(call_id,prompt,max_tokens=240)
        if not isinstance(result,str) or not result.strip():
            raise ValueError(f'{role} model did not supply a reasoning response')
        result=result.strip()[:1800]
        with self._db() as db:
            db.execute('''INSERT OR IGNORE INTO deliberations
                (evidence_sha,role,prompt_sha,answer,recorded_at) VALUES(?,?,?,?,?)''',
                (evidence_sha,role,sha(prompt),result,datetime.now(timezone.utc).isoformat()))
        return result

    def deliberate(self, client, *, session: str, original: str, project: str | Path,
                   gaps: list[str], saved_steps: list[dict], source_section: str,
                   inspected_evidence: str = '', stage=None, cancelled=None) -> dict:
        if not gaps:
            raise ValueError('Deliberation requires a concrete unsatisfied requirement')
        # Key by actual task/evidence, never by wall clock. A changed specification,
        # source, or file-plan invalidates previous counsel. The reference summary
        # is explicitly marked as inspection evidence, not tested compatibility.
        facts={'original_sha':sha(original),'project':str(Path(project).resolve()),
               'gaps':gaps[:20], 'saved':saved_steps[:24],
               'section_sha':sha(source_section),'inspected_evidence':inspected_evidence[:1800]}
        identity=sha(json.dumps(facts,sort_keys=True,ensure_ascii=False))
        focus=gaps[0]
        context=(f'UNMET VALIDATOR REQUIREMENTS: {json.dumps(gaps[:9],ensure_ascii=False)}\n'
                 f'SAVED MODEL INTENTIONS: {json.dumps(saved_steps[:5],ensure_ascii=False)[:900]}\n'
                 f'EXACT SOURCE EXCERPT (not a completed plan): {source_section[:1300]}\n'
                 f'INSPECTED VANILLA EVIDENCE (candidate IDs do not prove compatibility): '
                 f'{inspected_evidence[:1400] or "no source evidence supplied"}')
        janus_prompt=(
            'JANUS / ACTIVE REASONING. As the assigned local Triad planning role, '
            'think through a concrete failing X4 planning constraint. '
            'Propose TWO materially different testable explanations or approaches for the FIRST unmet check: '
            f'{focus}. For each: what evidence would confirm it, and what smallest X4 XML file '
            'intention could address it? Distinguish VERIFIED facts from hypotheses. '
            'Do not invent installed game IDs; do not propose shell commands or claim files were written. '
            'Return a concise analysis, not JSON.\n'+context)
        if len(janus_prompt)>7200:
            raise ValueError('Reasoning prompt exceeded bounded ONNX input')
        if cancelled and cancelled():raise ValueError('Neural council cancelled before JANUS turn')
        janus=self._run(client,role='JANUS',session=session,evidence_sha=identity,
                        prompt=janus_prompt,stage=stage)
        if cancelled and cancelled():raise ValueError('Neural council cancelled before Sentinel turn')
        sentinel_prompt=(
            'SENTINEL / INDEPENDENT NEURAL CRITIQUE. Use your assigned independent Triad verification role. '
            'Challenge the JANUS hypotheses using ONLY recorded evidence; identify invented identifiers, '
            'unproven compatibility, safety risks, and the exact missing acceptance criterion. '
            'Choose ONE smallest testable alternative or report that verified XML is missing. '
            'No tools, file writes, shell commands or unsupported claims. Return concise reasoning.\n'
            +context[:3800]+'\nJANUS PROPOSAL (UNTRUSTED): '+janus[:900])
        if len(sentinel_prompt)>7200:raise ValueError('Sentinel prompt exceeded bounded ONNX input')
        sentinel=self._run(client,role='SENTINEL',session=session,evidence_sha=identity,
                           prompt=sentinel_prompt,stage=stage)
        return {'evidence_sha':identity,'janus':janus,'sentinel':sentinel,
                'verified':False,'model':'assigned local Triad roles'}


def limited_guidance(review: dict | None, *, max_chars: int = 1000) -> str:
    """Model prose can guide the next proposal, but is never an accepted file."""
    if not review:
        return ''
    return ('UNVERIFIED JANUS HYPOTHESES (do not treat as source facts): '
            +str(review.get('janus',''))[:390]+'\n'
            'SENTINEL CRITIQUE (also unverified): '
            +str(review.get('sentinel',''))[:390])[:max_chars]
