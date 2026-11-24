"""Bounded correction of semantically rejected generated work.

Neither rejected text nor a changed project specification may reach the write
path. The caller retains its normal approval, source and testing safeguards.
"""
from __future__ import annotations
from .specification_guard import SpecificationRejected
from .reasoning_council import sha


def generate_reviewed(client,session,prompt,review,*,max_chars=7500,
                      max_tokens=768,attempts=3,transform=None,cancelled=None,stage=None):
    """Generate, review, and retry with specific feedback in fresh sessions."""
    if not 1<=attempts<=3 or len(prompt)>max_chars:
        raise ValueError('Invalid bounded reviewed generation')
    original=prompt
    seen=set()
    feedback=''
    for n in range(attempts):
        if cancelled and cancelled():raise SpecificationRejected('Reviewed generation cancelled')
        request=original
        if feedback:
            note='\n\nSENTINEL REJECTION AND CORRECTIVE ADVICE (not a scope change):\n'
            room=max_chars-len(original)-len(note)
            if room<80:
                raise SpecificationRejected('No context space for safe correction; split the approved task')
            request+=note+feedback[:room]
        call_id=f'{session}-reviewed-{n+1}-{sha(request)[:16]}'
        lookup=getattr(client,'completed_exchange',None)
        answer=lookup(call_id,request) if callable(lookup) else None
        if answer is None:answer=client.chat(call_id,request,max_tokens=max_tokens)
        if cancelled and cancelled():raise SpecificationRejected('Reviewed generation cancelled')
        try:
            candidate=transform(answer) if transform else answer
            if not isinstance(candidate,str) or not candidate.strip():
                raise ValueError('Empty or invalid generated source')
        except ValueError as exc:
            feedback='Output format rejected: '+str(exc)
            if stage:stage(f'Candidate {n+1}/{attempts} format rejected; retrying with correction')
            continue
        fingerprint=sha(candidate)
        if fingerprint in seen:
            feedback='The previous rejected proposal was repeated unchanged. Use a different implementation preserving the exact original requirements. '+feedback
            continue
        seen.add(fingerprint)
        try:
            review(candidate)
        except SpecificationRejected as exc:
            feedback=str(exc)
            if stage:stage(f'Sentinel refused candidate {n+1}/{attempts}; JANUS correction requested')
            continue
        if cancelled and cancelled():raise SpecificationRejected('Reviewed generation cancelled')
        return candidate
    raise SpecificationRejected('No aligned proposal after bounded correction attempts. '+feedback[:600])
