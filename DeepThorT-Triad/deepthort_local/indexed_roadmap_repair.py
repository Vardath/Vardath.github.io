"""Model-driven corrections for an already indexed, incomplete X4 roadmap.

Every original specification character is retained in the unchanged index.
Only one exact original section is supplied per ONNX call; no substitute plan
or game file is manufactured, and no source file is written or approved here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .agent_plan import PlanError, VanillaSourceCollision, remaining_plan_gaps
from .x4_variant import VariantSource
from .flight_recorder import record
from .reasoning_council import ReasoningCouncil, limited_guidance
from .recovery_council import reframe, accepted_guidance

MAX_MODEL_INPUT = 7500
MAX_UNPRODUCTIVE_CALLS = 8  # Stalled corrections should not burn days of CPU.

def _evidence_lines(evidence: str, focus: str, limit: int) -> str:
    """Fit whole inspection records; prefer matching terms and diverse asset types."""
    terms = set(re.findall(r'[a-z0-9]{3,}', focus.casefold()))
    lines = list(dict.fromkeys(line.strip() for line in evidence.splitlines() if line.strip()))
    def relevance(line):
        return len(terms.intersection(re.findall(r'[a-z0-9]{3,}', line.casefold())))
    ranked = sorted(lines, key=relevance, reverse=True)
    representatives = {}
    for line in ranked:
        representatives.setdefault(line.partition(':')[0], line)
    selected = []
    used = 0
    for line in dict.fromkeys([*representatives.values(), *ranked]):
        if used + len(line) + 1 <= limit:
            selected.append(line)
            used += len(line) + 1
    return '\n'.join(selected)


def x4_section_prompt(row: dict, evidence: str, max_chars: int, existing=(), gaps=()) -> str:
    text = row['text']
    header = (f"X4: Foundations extension draft. Original section {row['ordinal']+1}/{row['total']}.\n"
              "VERBATIM ORIGINAL SOURCE SECTION BEGIN\n" + text + "\nEND OF SECTION.\n")
    task = ('Plan one installable file for a requirement in this section. Paths start INSIDE the extension: '
            'content.xml at its root, md/ for mission XML, assets/ for models/macros, libraries/ for game data. '
            'The root content.xml declares extension metadata only. Omit content/x4/extensions/ and src/. '
            'Use an independent output name for a custom asset. '
            'Describe what this file will implement and how to verify it. '
            'Return only {"files":[{"path":"...","description":"..."}]}.')
    visible = []
    used = 0
    for path in existing:
        if used + len(path) + 2 <= 600:
            visible.append(path)
            used += len(path) + 2
    occupied = ('Files already assigned to other sections: ' + ', '.join(visible) + '\n') if visible else ''
    label = 'INSPECTED GAME REFERENCES (inputs only):\n'
    # Pick one unmet check supported by the current section. Avoid generic
    # file-count findings or prompting with an unrelated section's goals.
    words = set(re.findall(r'[a-z]{4,}', text.casefold())) - {
        'game','ship','files','file','specific','under','installed','original','extension','with','from'}
    matching = [(len(words.intersection(re.findall(r'[a-z]{4,}', gap.casefold()))),gap)
                for gap in gaps if not gap.startswith('at least four')]
    ranked = sorted((item for item in matching if item[0]),key=lambda item:-item[0])
    if ranked:
        # A repeated rejection should change the question asked of the small
        # model. The section attempt counter survives an interrupted session.
        focus = ranked[row.get('attempts',0) % len(ranked)][1]
        task += '\nYour ONE planning target: ' + focus + '. Name the actual game file and its role.'
    else:
        focus = text
    refs = _evidence_lines(evidence, focus, min(950, max_chars-len(header+task+occupied+label)-1))
    return header + (label + refs + '\n' if refs else '') + occupied + task


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
            gaps: list[str], steps: list[dict], *, neural_review: dict | None = None,
            new_instruction: str = '', inspected_evidence: str = '', feedback: str = '') -> str:
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
    guidance=(accepted_guidance(neural_review) if neural_review and 'accepted' in neural_review
              else limited_guidance(neural_review))
    advisory=('\n' + guidance + '\n') if guidance else ''
    if new_instruction:
        advisory+='\nJANUS PLANNING CHECKPOINT (advisory only):\n'+new_instruction[:1300]+'\n'
    # Keep all generated guidance outside the verbatim source boundary.
    prompt=header+original[row[1]:row[2]]+tail+advisory
    if len(prompt)>MAX_MODEL_INPUT:
        # Only optional advisory summaries may be dropped. Never truncate an
        # original source section or silently abbreviate a user requirement.
        header=header.split('RELEVANT SAVED MODEL FILES',1)[0]
        header+=f'VERBATIM ORIGINAL SOURCE SECTION {ordinal+1}/{len(rows)} BEGIN\n'
        prompt=header+original[row[1]:row[2]]+tail
    if len(prompt)>MAX_MODEL_INPUT:
        raise PlanError('Original indexed section and targeted correction '
                        'instructions exceed the ONNX input window; source remains saved')
    # Put the active requirement after the long source. Small models otherwise
    # frequently answer the last user paragraph instead of fixing this check.
    task = ('\nPlan the missing check now: ' + focus +
            '\nUse a path relative to the extension root; no src/main or project-name prefix. '
            'Return only the JSON files object.')
    correction = ('\nPrevious attempt: ' + feedback[:210]) if feedback else ''
    label = '\nINSPECTED GAME REFERENCES (inputs only):\n'
    room = MAX_MODEL_INPUT - len(prompt + task + correction + label)
    refs = _evidence_lines(inspected_evidence, focus, min(room, 1200))
    if refs:
        prompt += label + refs
    if len(prompt + correction + task) <= MAX_MODEL_INPUT:
        prompt += correction + task
    return prompt


def repair_indexed_roadmap(client, index, hierarchy, request_id: int, session: str,
                           original: str, project: str | Path, *, chat_id: str,
                           max_rounds: int, stage=None, cancelled=None,
                           continuous: bool = False,
                           neural_council: bool = False,
                           inspected_evidence: str = '', guidance_getter=None, checkpoint=None,
                           council_provider=None, after_variant=None, reviewer=None,operation_memory=None):
    if max_rounds <= 0:
        raise PlanError('All 40 planning calls were consumed reviewing the source. '
                        'Retry to continue correcting the incomplete X4 roadmap.')
    resume_cursor=index.revision_cursor(request_id,original)
    previous_focus=''
    stagnation=0
    stalled_this_batch=0
    i=0
    batch_progress=False
    batch_number=1
    review=None
    consulted_at=-1
    feedback=''
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
        geometry_gap='scaled asteroid mesh and ship geometry under assets/'
        if i==0 and geometry_gap in gaps and inspected_evidence.startswith('Native visual mesh:'):
            focus=geometry_gap
        elif previous_focus in gaps and stagnation < 2:
            focus=previous_focus
        else:
            focus=gaps[((resume_cursor+i)//2)%len(gaps)]
        ordinal=_choose_section(rows,original,focus,resume_cursor+i)
        pending=index.pending_roadmap_variant(request_id,original,inspected_evidence)
        variant=None
        if pending and index.reserve_variant_recovery(request_id):
            ordinal,variant=pending
            focus='independent source-backed ship identity and registration'
        # Dynamic guidance can arrive between ONNX model requests. The
        # source specification remains unchanged, and correction validator
        # still decides whether the proposed X4 file is valid.
        options = dict(neural_review=review if review and review.get('focus',focus)==focus else None,
                       inspected_evidence=inspected_evidence, feedback=feedback)
        prompt=_prompt(rows,original,ordinal,focus,gaps,steps,**options)
        # Do NOT mark an instruction delivered if the model input cannot fit
        # it alongside the exact original section and mandatory X4 evidence.
        if guidance_getter and len(prompt)<MAX_MODEL_INPUT-1700:
            extra=guidance_getter()
            if extra:
                prompt=_prompt(rows,original,ordinal,focus,gaps,steps,
                               new_instruction=extra,**options)
        instruction=None
        if variant is not None:
            prompt=variant.prompt()
        elif checkpoint:
            prompt, instruction = checkpoint.attach(prompt, MAX_MODEL_INPUT)
        if operation_memory:
            from .indexed_memory import append,sha
            exact=original[rows[ordinal][1]:rows[ordinal][2]]
            prompt=append(prompt,operation_memory,phase='indexed_roadmap_correction',
                          identity=(request_id,ordinal,resume_cursor+i,sha(prompt)),
                          focus=focus,section=exact,limit=MAX_MODEL_INPUT,cancelled=cancelled)
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
            reply=client.chat(round_session,prompt,max_tokens=64 if variant is not None else (768 if stagnation else 640))
        if checkpoint and instruction is not None:
            checkpoint.received(instruction, round_session, prompt, reply)
        if cancelled and cancelled():
            raise PlanError('Planning stopped; no pending model correction was saved')
        i+=1
        applied=False
        feedback=''
        try:
            options={'variant':variant} if variant is not None else {}
            if reviewer:options['reviewer']=reviewer
            applied=index.merge_model_revision(request_id,original,ordinal,reply,project=project,inspected_evidence=inspected_evidence,**options)
        except VanillaSourceCollision as exc:
            feedback=str(exc)
            source=VariantSource.inspected(original,inspected_evidence,exc.path)
            if source is not None:
                index.remember_roadmap_collision(request_id,original,ordinal,source)
                if stage:stage('Vanilla source collision saved; next correction can choose an independent identity.')
        except (ValueError,PlanError) as exc:
            feedback=str(exc)
            if stage:stage('Rejected proposed X4 roadmap correction: '+str(exc)[:160])
        if applied and variant is not None and after_variant and i<max_rounds*batch_number:
            note,used=after_variant()
            i+=used
            if note:
                inspected_evidence=note+'\n'+inspected_evidence
                if stage:stage(note)
        new_rows=index._verified_rows(request_id,original)
        new_steps,_=hierarchy._collect(new_rows,project)
        remaining=remaining_plan_gaps(new_steps,original)
        objective=index.record_revision_outcome(
            request_id,original,serial,gaps,remaining,
            file_count=len(new_steps),accepted=applied)
        closed=set(gaps)-set(remaining)
        opened=set(remaining)-set(gaps)
        progressed=bool(closed) and not opened
        if not progressed and not feedback:
            feedback = 'No validator check closed. Use an installable file that directly implements the named requirement.'
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
            review=None
            consulted_at=-1
            continue
        stalled_this_batch+=1
        stagnation=stagnation+1 if previous_focus==focus else 1
        previous_focus=focus
        # Two actual neural reasoning turns (JANUS hypothesis, Sentinel critique)
        # after evidenced stagnation. Same already-supervised ONNX worker, one
        # request at a time. No second model process, external tool or authority.
        # Advice only informs the *next* validated correction, never marks success.
        wants_review = (neural_council and stalled_this_batch>=3
                        and (consulted_at<0 or stalled_this_batch-consulted_at>=3)
                        and i<max_rounds*batch_number)
        advisor = (council_provider() if council_provider else client) if wants_review else None
        if wants_review and advisor is None and stage:
            stage('Council worker unavailable or handling another instruction. Planning can continue.')
        if advisor is not None:
            consulted_at=stalled_this_batch
            target=focus if focus in remaining else remaining[0]
            selected=_choose_section(new_rows,original,target,resume_cursor+i)
            context_section=original[new_rows[selected][1]:new_rows[selected][2]]
            council=ReasoningCouncil(index.path.parent/'reasoning-council-v50.sqlite3')
            observed=json.dumps({'unmet':remaining,'inspection':inspected_evidence[:700],
                                  'proposals':new_steps},ensure_ascii=False)
            recovery_feedback=feedback
            if review and review.get('accepted') is False:
                recovery_feedback+='\nPrior Sentinel rejection: '+review.get('sentinel','')[:240]
            try:
                from .indexed_memory import recall
                memory=recall(operation_memory,phase='indexed_roadmap_recovery',
                              identity=(request_id,serial,target),focus=target,section=context_section,
                              cancelled=cancelled,client=advisor)
                review=reframe(council,advisor,session=session,original=original,
                    project=project,source_section=context_section,focus=target,
                    observed=observed,feedback=recovery_feedback,revision=serial,
                    stage=stage,cancelled=cancelled,memory=memory)
                if stage:
                    stage('Sentinel accepted retranslation as advice' if review['accepted']
                          else 'Sentinel rejected retranslation; preserving original requirements')
                if review['accepted']:
                    previous_focus=target
                    stagnation=0
            except (OSError,ValueError) as error:
                if stage:
                    stage('Council recovery unavailable: '+type(error).__name__)
                review=None
            finally:
                release=getattr(advisor,'release',None)
                if callable(release):release()
        if advisor is not None and review:
            record(index.path.parent,'planner','janus_sentinel_neural_review',
                   request_id=request_id,evidence_hash=review['evidence_sha'][:20],
                   roles_reviewed=2,verified=False,files_written=0,
                   retranslation_accepted=review.get('accepted',False),
                   advisor='supervised local ONNX')
            # Publish their distinct neural analyses to the existing JANUS &
            # Sentinel tab. These are hypotheses, not approvals or test results.
            from .janus_engine import JanusStore
            from .watchdog import SentinelStore
            key=review['evidence_sha'][:40]
            JanusStore(index.path.parent/'janus.sqlite3').recommend(
                evidence_key='neural-'+key,origin='local_model',
                problem=review.get('focus',remaining[0]),proposal=review['janus'])
            SentinelStore(index.path.parent/'sentinel.sqlite3').recommend(
                evidence_key='neural-'+key,origin='local_model',
                finding=review.get('focus',remaining[0]),proposal=review['sentinel'])
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
