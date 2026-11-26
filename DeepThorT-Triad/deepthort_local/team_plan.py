"""Bounded model-authored task graph for explicitly staged team requests.

The exact conversation remains authoritative. Nodes are proposals until
Sentinel reviews the graph. Only registered read-only/staged adapters run;
neither a model nor a task graph grants project write or tool authority.
"""
import json
import re
from .agent_contract import canonical_sha

TEAM_STAGES=(('plan','janus',()),('review_plan','sentinel',('plan',)))
KINDS={'design':'implementation','midi':'multimedia'}
MAX_TASKS=4

def is_team_request(brief):
    return isinstance(brief,str) and brief.strip().lower().startswith('/delegate ') and 11<len(brief.strip())<=1000

def parse_plan(answer,original):
    if not is_team_request(original) or not isinstance(answer,str) or len(answer)>6000:
        raise ValueError('Invalid team request or plan')
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('Duplicate plan key')
            result[k]=v
        return result
    plan=json.loads(answer,object_pairs_hook=pairs)
    if not isinstance(plan,dict) or set(plan)!={'tasks'} or not isinstance(plan['tasks'],list) or not 1<=len(plan['tasks'])<=MAX_TASKS:
        raise ValueError('Expected 1–4 typed tasks')
    seen=set()
    midi_requested=bool(re.search(r'\bMIDI\b',original,re.I))
    midi_count=0
    for t in plan['tasks']:
        if not isinstance(t,dict) or set(t)!={'id','kind','brief','depends_on'}:
            raise ValueError('Unexpected task fields')
        ident=t['id'];kind=t['kind'];brief=t['brief'];deps=t['depends_on']
        if not isinstance(ident,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,15}',ident) or ident in seen:
            raise ValueError('Invalid task identifier')
        if not isinstance(kind,str) or kind not in KINDS or not isinstance(brief,str) or not brief.strip() or len(brief)>240:
            raise ValueError('Unsupported task kind or brief')
        if not isinstance(deps,list) or any(not isinstance(d,str) or d not in seen for d in deps) or len(set(deps))!=len(deps):
            raise ValueError('Unknown, duplicate or cyclic dependency')
        if kind=='midi':
            midi_count+=1
            if not midi_requested or midi_count>1:
                raise ValueError('Only one explicitly requested staged MIDI is authorized')
        seen.add(ident)
    if midi_requested and midi_count!=1:
        raise ValueError('Requested MIDI adapter omitted')
    return plan

def plan_prompt(original):
    return ('JANUS: propose a dependency graph for this explicit staged team request. '
            'Only design (Granite read-only design/asset specification) and midi (Gemma short staged MIDI) '
            'are available. No project edits, commands, installs or publication. '
            'Use 1–4 nodes, unique lowercase ids, briefs <=240 chars, dependencies only on earlier ids. '
            'Use midi only if user explicitly requests MIDI; never claim other artifacts can be made by this route. '
            'Return exactly one JSON object, e.g. {"tasks":[{"id":"design","kind":"design",'
            '"brief":"Specify interface","depends_on":[]}]}. EXACT USER REQUEST:\n'+original)

def task_name(ident):
    return 'task:'+ident

def contract(original,scope,plan,node,dependencies):
    return {'schema':'triad-team-task-v1','scope':scope,'original_sha256':canonical_sha(original),
            'plan_sha256':canonical_sha(plan),'id':node['id'],'kind':node['kind'],
            'role':KINDS[node['kind']],'brief':node['brief'],'dependencies':dependencies,
            'publication_authorized':False}

def acceptance(text):
    return isinstance(text,str) and text.strip()=='ACCEPT'
