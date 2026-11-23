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
MAX_UNPRODUCTIVE_CALLS = 8  # Stalled corrections should not burn days of CPU.


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
    """One validator goal per ONNX call; retain the verbatim original section.

    The v48 prompt listed every gap and every file while seeking one change.
    On the 1.5B local model this repeatedly produced tiny unrelated edits.
    Focus metadata is advisory; the exact source and all validated proposals
    stay in SQLite and only model-authored responses can change the roadmap.
    """
    row=rows[ordinal]
    words={w for w in re.findall(r'[a-z0-9]{3,}',focus.casefold())
           if w not in {'the','and','for','with','file','from','xml','specific','definition'}}
    ranked=sorted(steps,key=lambda entry:(
        -sum(word in (entry['path']+' '+entry['description']).casefold() for word in words),
        entry['path']))
    relevant=ranked[:3]
    existing='\n'.join(f'{item["path"]}: {item["description"][:170]}'
                       for item in relevant) or '(none)'
    header=(
        'X4 FILE ROADMAP: CORRECT ONE MISSING ACCEPTANCE CHECK.\n'
        f'CHECK TO CLOSE: {focus}\n'
        'The other original sections and saved model files are preserved. '
        'Do not repeat or rewrite unrelated files. '
        'Use the exact required relative path when the check names one '
        '(e.g. content.xml or index/macros.xml). Otherwise choose the '
        'necessary relative X4 XML file path yourself. '
        'For an existing file, improve its description WITHOUT dropping '
        'previously promised requirements. Do not invent verified IDs.\n'
        'Return ONLY one complete compact JSON object with ONE changed file, or TWO if an asset needs its registration index in the same change: '
        '{"files":[{"path":"relative/file.xml","description":"specific implementation"}]}. '
        'Close all brackets. No explanations or markdown.\n'
        f'RELEVANT SAVED MODEL FILES (out of {len(steps)}):\n{existing}\n'
        f'VERBATIM ORIGINAL SOURCE SECTION {ordinal+1}/{len(rows)} BEGIN\n'
    )
    tail='\nVERBATIM ORIGINAL SOURCE SECTION END.\n'
    prompt=header+original[row[1]:row[2]]+tail
    if len(prompt)>MAX_MODEL_INPUT:
        # Only optional advisory summaries may be dropped. Never truncate an
        # original source section or silently abbreviate a user requirement.
        header=header.split('RELEVANT SAVED MODEL FILES',1)[0]
        header+=f'VERBATIM ORIGINAL SOURCE SECTION {ordinal+1}/{len(rows)} BEGIN\n'
        prompt=header+original[row[1]:row[2]]+tail
    if len(prompt)>MAX_MODEL_INPUT:
        raise PlanError('Original indexed section and targeted correction '
                        'instructions exceed the ONNX input window; source remains saved')
    return prompt


def repair_indexed_roadmap(client, index, hierarchy, request_id: int, session: str,
                           original: str, project: str | Path, *, chat_id: str,
                           max_rounds: int, stage=None, cancelled=None,
                           continuous: bool = False):
    if max_rounds <= 0:
        raise PlanError('All 40 planning calls were consumed reviewing the source. '
                        'Retry to continue correcting the incomplete X4 roadmap.')
    previous_focus=''
    stagnation=0
    stalled_this_batch=0
    i=0
    batch_progress=False
    batch_number=1
    while True:
        if i >= max_rounds*batch_number:
            if not continuous or not batch_progress:
                break
            batch_number+=1
            batch_progress=False
            if stage:
                stage(f'X4 roadmap checkpoint saved; next 40-call batch '
                      f'{batch_number} permitted because an acceptance check closed')
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
            stage(f'Indexed roadmap correction {(i % max_rounds)+1}/{max_rounds} '
                  f'(batch {batch_number}; progress-based continuation): '
                  f'{len(gaps)} unmet X4 checks; '
                  f'original section {ordinal+1}/{len(rows)}; focus: {focus[:75]}')
        round_session=f'{session}-roadmap-revision-{serial}'
        lookup=getattr(client,'completed_exchange',None)
        reply=lookup(round_session,prompt) if callable(lookup) else None
        if reply is None:
            reply=client.chat(round_session,prompt,max_tokens=768 if stagnation else 640)
        if cancelled and cancelled():
            raise PlanError('Planning stopped; no pending model correction was saved')
        i+=1
        applied=False
        try:
            applied=index.merge_model_revision(request_id,original,ordinal,reply,project=project)
        except (ValueError,PlanError) as exc:
            if stage:stage('Rejected proposed X4 roadmap correction: '+str(exc)[:160])
        new_rows=index._verified_rows(request_id,original)
        new_steps,_=hierarchy._collect(new_rows,project)
        remaining=remaining_plan_gaps(new_steps,original)
        objective=index.record_revision_outcome(
            request_id,original,serial,gaps,remaining,
            file_count=len(new_steps),accepted=applied)
        closed=set(gaps)-set(remaining)
        opened=set(remaining)-set(gaps)
        progressed=bool(closed) and not opened
        record(index.path.parent,'planner','indexed_roadmap_revision',
            request_id=request_id, pass_number=i, gap_count=len(remaining),
            model_authored=True, source_section=ordinal,
            revised_files=len(new_steps), source_changed=False,
            accepted=applied, checks_closed=len(closed),
            checks_opened=len(opened), stalled_batch_calls=stalled_this_batch)
        if stage:
            stage(f'X4 roadmap acceptance: {len(closed)} checks closed this pass; '
                  f'{len(remaining)} still unmet; '
                  f'{0 if progressed else stalled_this_batch+1}/{MAX_UNPRODUCTIVE_CALLS} unproductive calls')
        if not remaining:
            return hierarchy.prepare(index,request_id,original,project,chat_id=chat_id)
        if progressed:
            batch_progress=True
            stagnation=0
            stalled_this_batch=0
            previous_focus=''
            continue
        stalled_this_batch+=1
        stagnation=stagnation+1 if previous_focus==focus else 1
        previous_focus=focus
        if stalled_this_batch>=MAX_UNPRODUCTIVE_CALLS:
            raise PlanError('Indexed X4 roadmap paused for lack of verified progress '
                            f'after {stalled_this_batch} consecutive correction calls. '
                            f'{len(remaining)} X4 acceptance checks are still unmet. '
                            'Saved proposed files and original requirements are intact. '
                            'Retry manually if desired, or change the model/strategy; '
                            'adding more idle passes will not build the mod.')
    rows=index._verified_rows(request_id,original)
    steps,_=hierarchy._collect(rows,project)
    gaps=remaining_plan_gaps(steps,original)
    raise PlanError('Indexed X4 roadmap remains incomplete after '
                    f'{max_rounds} correction attempts: {len(gaps)} unmet checks. '
                    'Completed original sections and valid model-authored corrections '
                    'are saved. Retry to continue; no files were queued or modified.')
