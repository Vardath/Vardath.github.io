"""Typed, durable creative handoff. A contract is never a grant or command."""
import hashlib
import json
from .agent_doctrine import fingerprint

REQUESTERS=frozenset({'user','janus','implementation','sentinel','acceptance'})

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('utf-8')).hexdigest()

def creative_assignment(requester,scope,brief):
    if requester not in REQUESTERS or not isinstance(scope,str) or not 1<=len(scope)<=200:
        raise ValueError('Invalid assignment identity')
    if not isinstance(brief,str) or not brief.strip() or len(brief)>1400:
        raise ValueError('Invalid assignment brief')
    return {'schema':'triad-agent-assignment-v1','requester':requester,
            'assignee':'multimedia','scope':scope,
            'brief_sha256':hashlib.sha256(brief.encode('utf-8')).hexdigest(),
            'role_sha256':fingerprint('multimedia'),
            'task_type':'compose_midi','expected_artifact':'score.mid',
            'acceptance':['strict_score_schema','verified_midi_bytes','request_specific_checks_if_supplied'],
            'publication_authorized':False}

def validate_creative_assignment(packet):
    if not isinstance(packet,dict) or set(packet)!={'requester','scope','brief','kind','prompt','assignment'} or packet['kind']!='midi':
        raise ValueError('Unsupported creative task envelope')
    expected=creative_assignment(packet['requester'],packet['scope'],packet['brief'])
    if packet['assignment']!=expected:raise ValueError('Creative assignment identity mismatch')
    return canonical_sha(expected)
