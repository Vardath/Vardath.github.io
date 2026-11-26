"""Local JANUS 1|3|7 society processor, used independently by JANUS and Sentinel.

Contract based on the owner's JANUS topology.py / senses.py documents:
  every one of eleven OUTER cores has seven INNER Fano faculties;
  the seven specialist outer cores project to both hemispheres;
  Left and Right -> Front -> Interface, with no Interface->Front feedback.

This computes transparent, bounded task appraisals; it is NOT a neural
language model or the separate JANUS server implementation. New external
observations are required to establish progress or truth. The local language
model may be consulted separately for *suggestions* only.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from .interface_outbox import select,express,digest
from dataclasses import dataclass, field
from typing import Any

from .janus_recursive import recursive_readout

SPECIALISTS = ('Evidence','Safety','Counterpoint','Context','Logic','Novelty','Memory')
CORE_NAMES = (*SPECIALISTS,'Left','Right','Front','Interface')
FANO_LINES = ((1,2,3),(1,4,5),(1,6,7),(2,4,6),(2,5,7),(3,4,7),(3,5,6))
FACULTIES = {1:'truth',2:'valence',3:'significance',4:'pattern',5:'understanding',6:'possibility',7:'continuity'}
HOME_DIRECTIONS = dict(zip(SPECIALISTS,range(1,8)))
MODALITIES = {'text','image','audio','file','web','memory','runtime','peer','action_result'}
APPRAISAL_KEYS = ('confidence','valence','salience','uncertainty','novelty','urgency','familiarity','risk','opportunity','conflict')


def unit(number: float) -> float:
    return max(0.0,min(1.0,float(number)))


@dataclass(frozen=True)
class SenseFrame:
    modality: str
    source: str
    content: str
    salience: float=.5
    uncertainty: float=.5
    novelty: float=.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.modality not in MODALITIES:raise ValueError('Unsupported JANUS modality')
        if not self.source or len(self.source)>100:raise ValueError('Invalid sensory source')
        object.__setattr__(self,'content',str(self.content)[:2500])
        for key in ('salience','uncertainty','novelty'):
            object.__setattr__(self,key,unit(getattr(self,key)))

    def public(self):
        return {'modality':self.modality,'source':self.source,'content':self.content,
                'salience':self.salience,'uncertainty':self.uncertainty,'novelty':self.novelty}


def choose_response(appraisal: dict) -> str:
    if appraisal['risk']>=.8 and appraisal['urgency']>=.6:return 'interrupt_or_warn'
    if appraisal['conflict']>=.7 or appraisal['uncertainty']>=.75:return 'clarify_or_preserve_uncertainty'
    if appraisal['opportunity']>=.7 and appraisal['risk']<=.4:return 'explore_or_act'
    if appraisal['salience']<=.25:return 'defer_or_observe'
    return 'respond_normally'


def process_society(*, society: str, observation: dict, frames: list[SenseFrame],
                    previous_front: dict | None=None, previous_observation: dict | None=None,
                    previous_cores: dict | None=None,
                    focus: str, decision: str, goal: str='', alternatives: list[str] | None=None,
                    findings: list[dict] | None=None, neural: dict | None=None) -> dict:
    if society not in ('janus','sentinel'):raise ValueError('Unknown society identity')
    if not frames:frames=[SenseFrame('runtime',society,'No new external evidence',salience=.1)]
    frames=frames[:16]
    previous_front=previous_front or {}
    previous_observation=previous_observation or {}
    previous_cores=previous_cores or {}
    alternatives=list(dict.fromkeys(str(x)[:200] for x in (alternatives or []) if x))[:6]
    # Only the observed environment produces the factual signals below.
    states=observation.get('counts',{}) if isinstance(observation.get('counts'),dict) else {}
    stalled=bool(observation.get('stalled') or observation.get('drift'))
    bad=bool(stalled or observation.get('failed') or states.get('failed') or states.get('needs_input') or observation.get('unverified_actions'))
    blocked=bool(observation.get('waiting_approval') or observation.get('requires_user'))
    gaming=bool(observation.get('game_detected'))
    conflict=bool(observation.get('conflict') or (bad and observation.get('reported_success')))
    actual_change=(observation != previous_observation)
    salient=max(x.salience for x in frames)
    uncertain=max(x.uncertainty for x in frames)
    novel=max(x.novelty for x in frames) if actual_change else .05
    goal=goal[:300]
    findings=(findings or [])[:8]
    neural=neural or {}
    # Stable external material, not previous core output, drives wake/revision.
    # A heartbeat is not another thought. An old Interface message is never
    # recursively injected as a new stimulus.
    material={'society':society,'obs':observation,'focus':focus,'decision':decision,
              'goal':goal,'alternatives':alternatives,'frames':[f.public() for f in frames],
              'findings':findings,'neural':neural}
    fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True,default=str).encode()).hexdigest()[:24]
    base_material={k:v for k,v in material.items() if k!='findings'}
    base_material['frames']=[f.public() for f in frames if f.source not in ('janus_findings','sentinel_findings')]
    base_fingerprint=hashlib.sha256(json.dumps(base_material,sort_keys=True,default=str).encode()).hexdigest()[:24]
    if (set(previous_cores)==set(CORE_NAMES) and
            (previous_front.get('material_fingerprint')==fingerprint or
             (not findings and previous_front.get('base_fingerprint')==base_fingerprint))):
        cores=deepcopy(previous_cores)
        for c in cores.values():
            c['quiescent_count']=int(c.get('quiescent_count',0))+1
            c['changed']=False
        cores['Memory'].update(previous_front=previous_front,previous_observation=previous_observation,
                               continuity_cycle=int(previous_front.get('cycle',0) or 0))
        cores['Front'].update(cycle=int(previous_front.get('cycle',0) or 0)+1,
            changed_from_prior=False,evidence_changed=False,outward_finding=None)
        cores['Interface']['message']=None
        return {'society':society,'cores':cores,'appraisal':dict(cores['Front']['appraisal']),
                'fingerprint':previous_front['material_fingerprint'],'focus':focus,'decision':decision,'goal':goal,
                'alternatives':alternatives,'frames':[f.public() for f in frames],
                'flow':'7->2->1->1','peer_exchange':{'changed':False,'links':0,'model_calls':0}}
    base={1:unit(.8 if observation else .25),
          2:unit(.95 if gaming or blocked or bad else .45),
          3:unit(.9 if bad or conflict else .2),
          4:unit(.75 if goal or frames else .25),
          5:unit(.7 if decision else .3),
          6:unit(.9 if bad and alternatives else .35 if alternatives else .1),
          7:unit(.85 if previous_front or previous_observation else .2)}
    appraisal={
        'confidence':unit(.8 if observation and not bad else .45),
        'valence': max(-1.,min(1., -.65 if bad else .3)),
        'salience':unit(max(salient,.85 if bad else .2)),
        'uncertainty':unit(max(uncertain,.8 if stalled else .55 if bad else .2)),
        'novelty':unit(novel),
        'urgency':unit(.95 if gaming or stalled else .75 if bad else .2),
        'familiarity':unit(.8 if previous_front else .2),
        'risk':unit(.9 if gaming and observation.get('active_actions') else .7 if bad else .1),
        'opportunity':unit(.8 if alternatives and not gaming else .2),
        'conflict':unit(.85 if conflict else .2),
    }
    # New evidence and bounded advisory counsel are registered to all outer
    # cores, but only the specialists consume raw material in their readouts.
    stimulus_refs=[{'id':item['id'],'mode':item['mode'],'characters':item['characters']}
                   for item in observation.get('stimuli',{}).get('events',[])][:8]
    finding_text=' | '.join(f"Finding: {f['finding'][:200]}; proposed: {f['proposal'][:240]}" for f in findings)
    sensory_content=f'{goal}; {focus}; {decision}; '+finding_text[:850]+' | '+ ' | '.join(f.content for f in frames[:4])
    def outer_core(name: str, sources: list[str], projection: int=0):
        # Every core is a complete 7-faculty recursive processor, not one value.
        faculties={str(direction):{'faculty':FACULTIES[direction],
                    'activation':unit(base[direction]*(1.0 if projection==direction else .82)),
                    'evidence':frames[0].source if name in SPECIALISTS else '+'.join(sources), 'influences':[
                    list(line) for line in FANO_LINES if direction in line]}
                    for direction in range(1,8)}
        # Only specialists sense raw frames. Each downstream core receives
        # bounded actual conclusions from its declared predecessors.
        peers=[(src,cores[src].get('last_conclusion','')) for src in sources if src in CORE_NAMES and src in cores]
        if name in SPECIALISTS:
            content=sensory_content
        else:
            content=' | '.join(f'{src}: {summary[:260]}' for src,summary in peers)
            if name=='Interface':
                content+=' | Integrated outward finding: '+json.dumps(cores['Front'].get('outward_finding'),ensure_ascii=False)[:900]
        reading=recursive_readout(name,content,appraisal,previous_cores.get(name),peers)
        for d in range(1,8):
            faculties[str(d)]['score']=int(reading['scores'].get(str(d),0))
        return {'outer_role':name,'home_direction':projection,
                'internal_fano_faculties':faculties,'recursive_janus':True,
                'appraisal':dict(appraisal),'input_sources':sources,
                'intent':decision,'goal':goal,
                'retained_front':str(previous_front.get('focus',''))[:200],
                'peer_sources':[src for src,_ in peers],
                'registered_stimuli':stimulus_refs,
                **reading}
    cores={}
    for name in SPECIALISTS:
        cores[name]=outer_core(name,[f.source for f in frames],HOME_DIRECTIONS[name])
    # JANUS peer revision: six other specialist readouts re-enter the SAME
    # core's internal Fano processor, before hemisphere integration.
    first={name:cores[name]['last_conclusion'] for name in SPECIALISTS}
    for name in SPECIALISTS:
        peers=[(other,summary) for other,summary in first.items() if other!=name]
        revised=recursive_readout(name,
               sensory_content,
               appraisal,cores[name],peers)
        cores[name].update(revised)
        cores[name]['peer_sources']=[other for other,_ in peers]
        # Each specialist registers advisory evidence with its own readout.
        # No role is authorized to send an outward message on its own.
        cores[name]['finding_refs']=[digest(f) for f in findings]
        for d in range(1,8):
            cores[name]['internal_fano_faculties'][str(d)]['score']=int(revised['scores'].get(str(d),0))
    cores['Evidence']['observations']=observation
    cores['Evidence']['uncertainty']='Unknown external state is not inferred'
    cores['Safety'].update(game_priority=gaming,requires_user_confirmation=blocked,external_installs_allowed=False,unapproved_commands_allowed=False)
    cores['Counterpoint']['conflict']='Observed stall/conflict requiring review' if bad else 'No verified conflict'
    cores['Context'].update(job_focus=focus,last_focus=previous_front.get('focus',''))
    cores['Logic'].update(selected_next_step=decision,cannot_claim_success_without_tests=True)
    cores['Novelty']['available_next_steps']=alternatives
    cores['Memory'].update(previous_front=previous_front,previous_observation=previous_observation,
                           continuity_cycle=int(previous_front.get('cycle',0) or 0))
    # The hemispheres independently receive ALL seven specialist streams.
    cores['Left']=outer_core('Left',list(SPECIALISTS))
    cores['Left'].update(source_roles=list(SPECIALISTS),constraint_checked=True,decision=decision,
                         finding_refs=sorted(set.intersection(*(set(cores[n]['finding_refs']) for n in SPECIALISTS))))
    cores['Right']=outer_core('Right',list(SPECIALISTS))
    cores['Right'].update(source_roles=list(SPECIALISTS),alternatives=alternatives,
                          finding_refs=list(dict.fromkeys(ref for n in SPECIALISTS for ref in cores[n]['finding_refs'])))
    # Front receives only the two hemisphere interpretations, not Interface.
    cores['Front']=outer_core('Front',['Left','Right'])
    reviewed_refs=set(cores['Left']['finding_refs']) & set(cores['Right']['finding_refs'])
    reviewed_findings=[f for f in findings if digest(f) in reviewed_refs]
    cores['Front'].update(focus=focus,priority=decision,goal=goal,cycle=int(previous_front.get('cycle',0) or 0)+1,
                          posture=choose_response(appraisal),
                          changed_from_prior=focus!=previous_front.get('focus') or decision!=previous_front.get('priority'),
                          evidence_changed=actual_change,
                          disagreement=bool(conflict or bad),
                          alternatives_to_review=alternatives,material_fingerprint=fingerprint,base_fingerprint=base_fingerprint,
                          outward_finding=select(reviewed_findings,appraisal,observation))
    # Interface receives Front only. Results can return *next cycle* as new frames.
    cores['Interface']=outer_core('Interface',['Front'])
    cores['Interface'].update(action=decision,selected_posture=cores['Front']['posture'],
                              autonomous_install=False,autonomous_file_modification=False,
                              may_execute_without_approval=False,
                              message=express(cores['Front']))
    # The resumable neural phase is the same society's separately retained
    # interpretations, not additional external observations or authority.
    for name,reading in neural.get('cores',{}).items():
        if name in cores:cores[name]['neural_readout']=reading
    if neural:cores['Front']['neural_progress']={k:v for k,v in neural.items() if k!='cores'}
    # These are actual directed recursive-readout inputs, not a nominal topology.
    for core in cores.values():
        weights=core['weights']
        core['projection_1_3_4']={'origin':weights[0],'line':sum(weights[1:4]),'off_line':sum(weights[4:8])}
    return {'society':society,'cores':cores,'appraisal':appraisal,'fingerprint':fingerprint,
            'focus':focus,'decision':decision,'goal':goal,'alternatives':alternatives,
            'frames':[f.public() for f in frames], 'flow':'7->2->1->1',
            'peer_exchange':{'changed':True,'links':sum(len(c['peer_sources']) for c in cores.values()),'model_calls':0}}
