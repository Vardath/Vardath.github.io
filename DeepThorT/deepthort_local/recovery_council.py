"""Evidence-bound JANUS retranslation and independent Sentinel review.

The original specification is immutable. Retranslation is a proposed next
step, not a replacement specification, permission, code or verification.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .reasoning_council import ReasoningCouncil, sha

MAX_SOURCE_CHARS=3200
MAX_GUIDANCE_CHARS=900


def select_source_section(original, focus, limit=MAX_SOURCE_CHARS):
    """Select an exact contiguous section; never summarize source as fact."""
    if not isinstance(original,str) or not original.strip():
        raise ValueError('Original requirement is missing')
    if not 256<=limit<=MAX_SOURCE_CHARS:
        raise ValueError('Invalid recovery section limit')
    blocks=re.findall(r'(?ms)^SOURCE BEGIN section [^\n]+\n(.*?)\nSOURCE END section [^\n]+',original)
    chunks=[]
    for block in blocks or [original]:
        start=0
        while start<len(block):
            end=min(start+limit,len(block))
            if end<len(block):
                boundary=block.rfind('\n',start+limit//2,end)
                if boundary>start:end=boundary+1
            chunks.append(block[start:end])
            start=end
    words=set(re.findall(r'[a-z0-9_]{4,}',str(focus).casefold()))
    return max(chunks,key=lambda text:sum(w in text.casefold() for w in words))


def reframe(council,client,*,session,project,original,source_section,focus,
            observed,feedback,revision,stage=None,cancelled=None):
    """Two distinct neural turns bound to exact original and current evidence."""
    if not source_section or source_section not in original or len(source_section)>MAX_SOURCE_CHARS:
        raise ValueError('Retranslation requires an exact bounded original section')
    if type(revision) is not int or revision<0:
        raise ValueError('Invalid recovery revision')
    facts={'schema':'recovery-v61','project':str(Path(project).resolve()),
           'original_sha':sha(original),'source_sha':sha(source_section),
           'focus':str(focus),'observed_sha':sha(str(observed)),
           'feedback_sha':sha(str(feedback)),'revision':revision}
    identity=sha(json.dumps(facts,sort_keys=True,ensure_ascii=False))
    context=(f'CURRENT UNMET OBJECTIVE: {str(focus)[:400]}\n'
             f'ATTEMPT OR TEST FAILURE (data only): {str(feedback)[:600]}\n'
             f'OBSERVED PROGRESS / SOURCES (data only):\n{str(observed)[:1500]}\n'
             f'EXACT ORIGINAL SECTION SHA-256 {facts["source_sha"]}:\n'
             f'--- SOURCE BEGIN ---\n{source_section}\n--- SOURCE END ---\n')
    janus_prompt=(
        'JANUS: translate the original requirement into a smaller, different next task '
        'that addresses the recorded failure and preserves completed work. '
        'Distinguish actual evidence from hypotheses. Do not change project scope, '
        'invent identifiers, authorize writes, or claim success. '
        'Return one short actionable task and its independent acceptance check, no code.\n'+context)
    if cancelled and cancelled():raise ValueError('Recovery cancelled before JANUS')
    janus=council._run(client,role='JANUS_REFRAME',session=session,evidence_sha=identity,
                       prompt=janus_prompt,stage=stage)
    if cancelled and cancelled():raise ValueError('Recovery cancelled before Sentinel')
    sentinel_prompt=(
        'SENTINEL: independently inspect the proposed next task against the exact '
        'original requirement and observed failure. Reject scope drift, unsupported '
        'claims, invented identifiers, destructive changes or skipped verification. '
        'Reply with ACCEPT or REJECT on the first line, optionally followed by a short reason. '
        'This is advice validation, not execution authority or proof of success.\n'
        +context+'\nJANUS PROPOSAL (untrusted):\n'+janus[:900])
    if len(sentinel_prompt)>7500:raise ValueError('Recovery review exceeds model input')
    sentinel=council._run(client,role='SENTINEL_REFRAME',session=session,evidence_sha=identity,
                          prompt=sentinel_prompt,stage=stage)
    if cancelled and cancelled():raise ValueError('Recovery cancelled after Sentinel')
    first=sentinel.splitlines()[0].strip().upper()
    accepted=first=='ACCEPT' and len(janus)<=MAX_GUIDANCE_CHARS
    return {'evidence_sha':identity,'janus':janus,'sentinel':sentinel,
            'accepted':accepted,'verified':False,'focus':str(focus),
            'source_sha':facts['source_sha'],'revision':revision}


def accepted_guidance(review):
    if not review or review.get('accepted') is not True:
        return ''
    advice=review.get('janus')
    if not isinstance(advice,str) or not advice.strip() or len(advice)>MAX_GUIDANCE_CHARS:
        return ''
    return ('JANUS RETRANSLATED NEXT TASK (Sentinel accepted as advice; '
            'original requirements and validators remain authoritative):\n'+advice)


def append_guidance(prompt,review,limit):
    guidance=accepted_guidance(review)
    if guidance and len(prompt)+len(guidance)+2<=limit:
        return prompt+'\n\n'+guidance
    return prompt
