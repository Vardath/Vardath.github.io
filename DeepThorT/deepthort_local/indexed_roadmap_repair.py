"""Model-driven corrections for an already indexed, incomplete X4 roadmap.

Every original specification character is retained in the unchanged index.
Only one exact original section is supplied per ONNX call; no substitute plan
or game file is manufactured, and no source file is written or approved here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .agent_plan import PlanError, remaining_plan_gaps
from .flight_recorder import record

MAX_MODEL_INPUT = 7500


def _choose_section(rows, original: str, focus: str, turn: int) -> int:
    """Prefer the most relevant *original* section, rotate on tied scores."""
    words = {w for w in re.findall(r'[a-z]{3,}', focus.casefold())
             if w not in {'the','and','for','with','file','from','xml','specific'}}
    graded=[]
    for row in rows:
        text=original[row[1]:row[2]].casefold()
        score=sum(3 if word in text else 0 for word in words)
        score+=2 if 'x4' in text else 0
        score+=2 if 'xenon' in text else 0
        graded.append((score,row[0]))
    best=max(item[0] for item in graded)
    ties=[ordinal for score,ordinal in graded if score==best]
    return ties[turn%len(ties)]


def _prompt(rows, original: str, ordinal: int, focus: str,
            gaps: list[str], steps: list[dict]) -> str:
    row=rows[ordinal]
    header=(
        'REPAIR AN INCOMPLETE X4 EXTENSION FILE ROADMAP. The full original '
        f'{len(original):,}-character specification remains preserved in local '
        'SQLite and was already reviewed section by section. No files have '
        'been built or approved. This input contains ONE exact source section; '
        'do NOT interpret it as the complete specification. All other source '
        'sections and existing model-proposed files remain saved.\n'
        f'UNSATISFIED ACCEPTANCE CRITERION: {focus}\n'
        'Return ONLY one complete JSON object: '
        '{"files":[{"path":"relative/file.xml","description":"concrete implementation details"}]}. '
        'Propose 1-2 necessary X4 XML files OR substantive revisions of existing '
        'file descriptions; never invent unverified X4 IDs, installed game '
        'evidence or working code. Keep descriptions under 400 characters. '
        'No Python application entrypoints. No markdown or explanatory text.\n'
        f'CURRENT GAPS ({len(gaps)}): {"; ".join(gaps[:12])}\n'
        'CURRENT MODEL-PROPOSED PATHS: '
        + ', '.join(step['path'] for step in steps[:24])[:900] + '\n'
        f'VERBATIM ORIGINAL SOURCE SECTION {ordinal+1}/{len(rows)} BEGIN\n'
    )
    tail='\nVERBATIM ORIGINAL SOURCE SECTION END.\n'
    prompt=header+original[row[1]:row[2]]+tail
    if len(prompt)>MAX_MODEL_INPUT:
        # Do not truncate or modify the source section. Reduce only advisory
        # path/gap metadata, never the original user requirements.
        header=header.split('CURRENT GAPS (',1)[0]
        header+=f'CURRENT FOCUS: {focus}\n'
        header+=f'VERBATIM ORIGINAL SOURCE SECTION {ordinal+1}/{len(rows)} BEGIN\n'
        prompt=header+original[row[1]:row[2]]+tail
    if len(prompt)>MAX_MODEL_INPUT:
        raise PlanError('Original indexed section and safe correction instructions exceed the ONNX input window; source remains saved')
    return prompt


def repair_indexed_roadmap(client, index, hierarchy, request_id: int, session: str,
                           original: str, project: str | Path, *, chat_id: str,
                           max_rounds: int, stage=None, cancelled=None):
    if max_rounds <= 0:
        raise PlanError('All 40 planning calls were consumed reviewing the source. '
                        'Retry to continue correcting the incomplete X4 roadmap.')
    previous_focus=''
    stagnation=0
    for i in range(max_rounds):
        if cancelled and cancelled():
            raise PlanError('Planning stopped; indexed roadmap corrections remain saved for retry')
        rows=index._verified_rows(request_id,original)
        steps,_=hierarchy._collect(rows,project)
        gaps=remaining_plan_gaps(steps,original)
        if not gaps:
            return hierarchy.prepare(index,request_id,original,project,chat_id=chat_id)
        # Keep a focus for two attempts; rotate when the model fails to improve.
        if previous_focus in gaps and stagnation < 2:
            focus=previous_focus
        else:
            focus=gaps[(i//2)%len(gaps)]
        ordinal=_choose_section(rows,original,focus,i)
        prompt=_prompt(rows,original,ordinal,focus,gaps,steps)
        serial=index.reserve_revision_attempt(request_id,original,ordinal,prompt)
        if stage:
            stage(f'Indexed roadmap correction {i+1}/{max_rounds} '
                  f'(total planning budget 40): {len(gaps)} unmet X4 checks; '
                  f'original section {ordinal+1}/{len(rows)}; focus: {focus[:75]}')
        round_session=f'{session}-roadmap-revision-{serial}'
        lookup=getattr(client,'completed_exchange',None)
        reply=lookup(round_session,prompt) if callable(lookup) else None
        if reply is None:
            reply=client.chat(round_session,prompt,max_tokens=768 if stagnation else 640)
        if cancelled and cancelled():
            raise PlanError('Planning stopped; no pending model correction was saved')
        applied=False
        try:
            applied=index.merge_model_revision(request_id,original,ordinal,reply,project=project)
        except (ValueError,PlanError) as exc:
            if stage:stage('Rejected proposed X4 roadmap correction: '+str(exc)[:160])
        if applied:
            new_rows=index._verified_rows(request_id,original)
            new_steps,_=hierarchy._collect(new_rows,project)
            remaining=remaining_plan_gaps(new_steps,original)
            record(index.path.parent,'planner','indexed_roadmap_revision',
                request_id=request_id, pass_number=i+1, gap_count=len(remaining),
                model_authored=True, source_section=ordinal,
                revised_files=len(new_steps), source_changed=False)
            if stage:stage(f'Saved model-authored X4 roadmap correction; '
                           f'{len(remaining)} acceptance gaps remain')
            if not remaining:
                return hierarchy.prepare(index,request_id,original,project,chat_id=chat_id)
            if len(remaining)<len(gaps):
                stagnation=0
                previous_focus=''
                continue
        stagnation=stagnation+1 if previous_focus==focus else 1
        previous_focus=focus
    rows=index._verified_rows(request_id,original)
    steps,_=hierarchy._collect(rows,project)
    gaps=remaining_plan_gaps(steps,original)
    raise PlanError('Indexed X4 roadmap remains incomplete after '
                    f'{max_rounds} correction attempts: {len(gaps)} unmet checks. '
                    'Completed original sections and valid model-authored corrections '
                    'are saved. Retry to continue; no files were queued or modified.')
