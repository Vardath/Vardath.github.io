"""Portable offline implementation of JANUS RecursiveCoreProcessor mechanics.

Adapted from the user's JANUS server_v2/recursive_core.py and intuition.py
without OpenAI, account/server code or dependencies. Every OUTER role runs a
complete seven-faculty accumulator with peer revision and labelled hunches.
This processor is deterministic: findings are prompts for testing, not proof.
"""
from __future__ import annotations
import hashlib
import re
from typing import Any

ROLE_BIASES={
 'Evidence':{1:5,5:2,3:1}, 'Safety':{2:5,3:2,7:1},
 'Counterpoint':{3:5,1:2,2:2,5:1},'Context':{4:5,6:2,7:1},
 'Logic':{5:5,1:2,4:2,3:1},'Novelty':{6:5,4:2,2:2,5:1},
 'Memory':{7:5,1:1,2:1,4:1,5:1},'Left':{5:5,1:3,3:2,7:1},
 'Right':{6:5,4:4,7:2,2:1},'Front':{3:4,2:3,7:3,5:2,6:1},
 'Interface':{3:3,2:3,5:2,6:2,1:2,7:1},
}
CUES={
 1:('evidence','source','fact','true','false','claim','support','verify','confidence'),
 2:('want','prefer','good','bad','harm','benefit','safe','unsafe','privacy','boundary','goal'),
 3:('important','urgent','risk','conflict','contradict','however','but','failure','consequence'),
 4:('pattern','context','relationship','similar','structure','system','environment','analogy'),
 5:('because','cause','logic','model','therefore','constraint','explain','predict','consistent'),
 6:('could','might','possible','idea','alternative','imagine','create','explore','option','future'),
 7:('remember','before','again','history','previous','continuity','memory','learned','past'),
}


def recursive_readout(name: str, content: str, appraisal: dict, previous: dict | None=None,
                      peers: list[tuple[str,str]] | None=None) -> dict[str,Any]:
    if name not in ROLE_BIASES:raise ValueError('Unknown JANUS core')
    previous=previous or {};peers=(peers or [])[:10]
    text=' '.join(str(content).split())[:2200]
    peer_text=' '.join(str(p[1])[:220] for p in peers if p[0]!=name)
    material=text+'\n'+'\n'.join(f'{n}:{summary[:220]}' for n,summary in peers if n!=name)
    signature=hashlib.sha256(material.encode('utf-8',errors='ignore')).hexdigest()[:24]
    weights=list(previous.get('weights') or [8,1,1,1,1,1,1,1])
    if len(weights)!=8 or any(not isinstance(v,int) or v<0 for v in weights):weights=[8,1,1,1,1,1,1,1]
    if signature==previous.get('last_signature'):
        return {'weights':weights,'active_direction':previous.get('active_direction',0),
            'revision_count':int(previous.get('revision_count',0)),
            'peer_turn_count':int(previous.get('peer_turn_count',0)),
            'quiescent_count':int(previous.get('quiescent_count',0))+1,
            'last_signature':signature,'intuition':previous.get('intuition',{}),
            'last_conclusion':previous.get('last_conclusion',''),
            'scores':previous.get('scores',{}),'changed':False}
    low=text.lower();peer_low=peer_text.lower()
    words=set(re.findall(r'[a-z0-9][a-z0-9_-]{2,}',low))
    peer_words=set(re.findall(r'[a-z0-9][a-z0-9_-]{2,}',peer_low))
    p=appraisal
    scores={}
    for d in range(1,8):
        cue_hits=sum(cue in low for cue in CUES[d]); peer_hits=sum(cue in peer_low for cue in CUES[d])
        score=2+cue_hits*2+min(4,peer_hits)+ROLE_BIASES[name].get(d,0)
        if d==1:score+=round(p['confidence']*3)
        elif d==2:score+=round((abs(p['valence'])+p['risk'])*2)
        elif d==3:score+=round((p['salience']+p['conflict']+p['urgency'])*2)
        elif d==4:score+=min(3,len(words & peer_words))
        elif d==5:score+=round((p['confidence']+(1-p['uncertainty']))*2)
        elif d==6:score+=round((p['novelty']+p['opportunity'])*2)
        elif d==7:score+=round(p['familiarity']*4)
        scores[d]=int(score);weights[d]+=max(1,int(score))
    weights[0]+=1
    if max(weights)>5000:weights=[max(1,w//2) for w in weights]
    active=max(scores,key=scores.get)
    strongest=max(scores.values(),default=1)
    coalition=sum(scores.get(x,0) for x in (4,6,7))/(3*max(1,strongest))
    grounding=sum(scores.get(x,0) for x in (1,5))/(2*max(1,strongest))
    tension=min(1,.55*p['conflict']+.45*p['uncertainty'])
    strength=min(1,.30*coalition+.22*grounding+.18*p['novelty']+.12*(1-tension))
    basis=sorted(scores,key=lambda k:scores[k],reverse=True)[:3]
    hunch={'basis':basis,'strength':round(strength,3),'tension':round(tension,3),
           'needs_check':bool(strength>=.28 or tension>=.35),
           'epistemic_status':'hunch_not_evidence'}
    peer_clause=f' reconsidered {len(peers)} peer reports' if peers else ''
    return {'weights':weights,'active_direction':active,
        'revision_count':int(previous.get('revision_count',0))+(1 if peers else 0),
        'peer_turn_count':int(previous.get('peer_turn_count',0))+len(peers),
        'quiescent_count':0,'last_signature':signature,'intuition':hunch,
        'last_conclusion':f'{name}: d{active} active;{peer_clause}; focus {text[:250]}',
        'scores':{str(k):v for k,v in scores.items()},'changed':True}
