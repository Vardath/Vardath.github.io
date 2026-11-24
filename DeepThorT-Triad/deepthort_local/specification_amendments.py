"""Append-only user amendments; older requirements and plans are never deleted.

A new amendment creates a new immutable planning request. It is NOT permission
to edit the previously approved job or to execute the newly proposed plan.
"""
from __future__ import annotations
import hashlib
import json
import re

from .specification_library import MAX_STORED_REQUEST_CHARS

PRECEDENCE=(
    'USER SPECIFICATION REVISION: The verbatim original and amendments below '
    'are all authoritative user input. Where they conflict, the newest explicit '
    'amendment wins ONLY for the affected requirement. Preserve every other '
    'original requirement and all compatible completed work. The earlier plan '
    'is historical evidence, not authority to ignore a newer instruction.\n'
)


# The brief checkpoint variant was already committed. Recognize it without
# rewriting any stored effective specification or its recorded digest.
PRECEDENCE_CHECKPOINT=PRECEDENCE.replace(
    'original requirement and all compatible completed work.',
    'original requirement and all compatible completed work, unless the user explicitly directs otherwise.')


def revision_matches(effective,original,amendments):
    expected=render_revision(original,amendments)
    return effective==expected or effective==expected.replace(PRECEDENCE,PRECEDENCE_CHECKPOINT,1)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def render_revision(original,amendments):
    if not amendments:raise ValueError('At least one explicit user amendment is required')
    blocks=[PRECEDENCE,'--- VERBATIM ORIGINAL SPECIFICATION ---\n',original,
            '\n--- END ORIGINAL SPECIFICATION ---\n']
    for n,text in enumerate(amendments,1):
        if not isinstance(text,str) or not text.strip():raise ValueError('Empty amendment')
        blocks.extend((f'\n--- USER AMENDMENT {n} (later amendments take precedence) ---\n',
                       text,f'\n--- END USER AMENDMENT {n} ---\n'))
    result=''.join(blocks)
    if len(result)>MAX_STORED_REQUEST_CHARS:
        raise ValueError('Amended specification exceeds the local storage ceiling; original retained')
    return result


def root_request_for_job(job,conversations):
    key=job.get('approval_key') or ''
    draft=re.fullmatch(r'draft:([1-9][0-9]*)',key)
    if draft:
        row=conversations.draft(int(draft[1]))
        return row['request_id'] if row else None
    milestone=re.fullmatch(r'milestone:([1-9][0-9]*):[1-9][0-9]*:[a-f0-9]{16}',key)
    return int(milestone[1]) if milestone else None


def job_is_superseded(job,conversations):
    if not job or job.get('mode')!='build':return False
    ident=root_request_for_job(job,conversations)
    return bool(ident and conversations.amendment_supersedes(
        ident,job['chat_id'],job['project']))
