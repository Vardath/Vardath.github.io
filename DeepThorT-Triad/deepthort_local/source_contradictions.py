"""Compare quote-bound claims, preserving reviewer interpretation and uncertainty."""
from __future__ import annotations
import argparse
from itertools import combinations
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import literal
from deepthort_local.source_credibility import load_report,MAX_REPORT

SCHEMA='janus-source-contradictions-v1'
EXTRA=('research','.json')
ID=re.compile(r'[a-z][a-z0-9_-]{0,39}\Z')
POSITIONS=('supports','opposes','qualifies','unclear')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'research','claims'} or not isinstance(s['research'],str):
        raise ValueError('Expected research report and explicit claims')
    claims=s['claims']
    if not isinstance(claims,list) or not 1<=len(claims)<=12:raise ValueError('Choose 1–12 claims')
    ids=set()
    for c in claims:
        if (not isinstance(c,dict) or set(c)!={'id','claim','context','observations'}
                or not isinstance(c['id'],str) or not ID.fullmatch(c['id']) or c['id'] in ids):
            raise ValueError('Invalid or duplicate claim identifier')
        ids.add(c['id']);literal(c['claim'],600);literal(c['context'],600)
        obs=c['observations']
        if not isinstance(obs,list) or not 2<=len(obs)<=5:raise ValueError('Choose 2–5 observations per claim')
        seen=set()
        for o in obs:
            if (not isinstance(o,dict) or set(o)!={'source_id','position','line','start','quote','reason'}
                    or not isinstance(o['source_id'],str) or not re.fullmatch(r'S[1-5]',o['source_id'])
                    or o['source_id'] in seen or o['position'] not in POSITIONS
                    or type(o['line']) is not int or not 1<=o['line']<=100000
                    or type(o['start']) is not int or not 0<=o['start']<=100000):
                raise ValueError('Invalid or repeated source observation')
            seen.add(o['source_id']);literal(o['quote'],480);literal(o['reason'],600)
    return s

def compare(s,raw):
    checked(s);report=load_report(raw);sources={r['id']:r for r in report['sources']};claims=[]
    for c in s['claims']:
        observations=[]
        for o in c['observations']:
            source=sources.get(o['source_id'])
            if not source or source['status']!='retrieved':raise ValueError('Observation needs retrieved evidence')
            page=source['evidence'];lines=page['text'].split('\n');i=o['line']-1
            if i>=len(lines) or lines[i][o['start']:o['start']+len(o['quote'])]!=o['quote']:
                raise ValueError('Exact claim quote and offset do not match evidence')
            observations.append(dict(o,url=source['url'],text_sha256=page['text_sha256'],
                                     duplicate_text_of=source['duplicate_text_of']))
        pairs=[]
        for a,b in combinations(observations,2):
            positions={a['position'],b['position']}
            if a['text_sha256']==b['text_sha256']:
                status='duplicate_evidence'
            elif positions=={'supports','opposes'}:status='reported_disagreement'
            elif 'unclear' in positions:status='unclear'
            elif 'qualifies' in positions:status='qualification'
            else:status='same_reported_position'
            pairs.append({'source_ids':[a['source_id'],b['source_id']],'status':status,
                          'interpretation_verified':False})
        disagreements=sum(p['status']=='reported_disagreement' for p in pairs)
        claims.append({'id':c['id'],'claim':c['claim'],'context':c['context'],'observations':observations,
                       'pairs':pairs,'reported_disagreement_count':disagreements,
                       'resolution':'unresolved' if disagreements else 'no_opposing_positions_recorded',
                       'truth_determined':False})
    return {'schema':'janus-source-contradiction-result-v1','question':report['question'],
            'research_report_sha256':hashlib.sha256(raw).hexdigest(),'claims':claims,
            'reported_disagreement_count':sum(c['reported_disagreement_count'] for c in claims),
            'semantic_contradictions_verified':False,'claims_verified':False,'network_performed':False,
            'reference_only':True,
            'limitations':'Positions and context are supplied reviewer interpretations, not independently inferred facts. Exact quotes are checked; semantic comparability, scope, chronology, independence and scientific truth are not. Identical text is not corroboration or contradiction. No majority vote resolves a disagreement.'}
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,path=validate(root,plan);r=compare(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    return plan,{'research':s['research'],'claims':s['claims'],'comparison':r['claims'],'scope':r['limitations']}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def execute(root,plan):
    s,dst,path=validate(root,plan);r=compare(s,guard.exact(path,plan['guards'][1],MAX_REPORT))
    payload=json.dumps(r,ensure_ascii=True,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'source_positions_compared','output':plan['output'],'sha256':digest,
            'claims':len(r['claims']),'reported_disagreement_count':r['reported_disagreement_count'],
            'semantic_contradictions_verified':False,'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Comparison unavailable; inspect exact evidence and claim positions'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
