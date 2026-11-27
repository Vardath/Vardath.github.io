"""Deterministic advisory routing on fixed permanent local operatives.

This changes scheduling preference only, not role doctrine, permissions,
model weights, resident placement, independent verification or Memory duty.
"""
import re
from .agent_doctrine import fingerprint
from .agent_contract import canonical_sha

ROLES=('janus','sentinel','implementation')
VOCAB={
    'janus':frozenset('plan planning design architecture coordinate priorities scope requirements roadmap decompose strategy dependencies'.split()),
    'sentinel':frozenset('verify verification validate validation audit acceptance security risk regression review compliance inspect correctness safety'.split()),
    'implementation':frozenset('implement implementation code coding build compile bug fix debug repair refactor tests test function interface module repository'.split()),
}

def rank(prompt,available,*,preferred=None):
    if not isinstance(prompt,str) or len(prompt)>2400:raise ValueError('Invalid advisory routing prompt')
    allowed=[r for r in ROLES if r in available]
    terms=set(re.findall(r'[a-z]+',prompt.casefold()))
    scores={r:len(terms&VOCAB[r]) for r in allowed}
    ordered=sorted(allowed,key=lambda r:(r!=preferred,-scores[r],ROLES.index(r)))
    return ordered,scores

def receipt(prompt,available,selected,identity,*,preferred=None):
    order,scores=rank(prompt,available,preferred=preferred)
    if selected not in order:raise ValueError('Unadmitted route')
    return {'schema':'triad-advisory-route-v1','task_identity':identity,'selected':selected,
            'available':list(order),'scores':scores,'preferred':preferred if preferred in order else None,
            'role_sha256':fingerprint(selected),'authority':False,'model_replaced':False,
            'scope':'advisory routing preference only'}
