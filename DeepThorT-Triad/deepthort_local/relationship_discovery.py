"""Bounded automatic relationship candidates from local text.

Only exact same-line co-occurrence is observed. It is not a semantic predicate,
causal relationship, or authorization to create an asserted knowledge edge.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from itertools import combinations
import hashlib
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.knowledge_graph import EXTRA,build,checked as graph_checked,source_lines
from deepthort_local.document_knowledge import MAX_BYTES
from deepthort_local.long_form_writing import literal

SCHEMA='janus-relationship-discovery-v1'
MAX_MENTIONS=128
MAX_SPAN=500
MAX_EXAMPLES=3

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'document','nodes','max_candidates'}:
        raise ValueError('Expected document, reviewed nodes and candidate limit')
    if type(spec['max_candidates']) is not int or not 1<=spec['max_candidates']<=128:
        raise ValueError('Invalid candidate limit')
    if not isinstance(spec['nodes'],list) or not 2<=len(spec['nodes'])<=32:
        raise ValueError('Choose 2–32 reviewed entities')
    graph_checked({'document':spec['document'],'nodes':spec['nodes'],'edges':[]})
    return spec

def discover(spec,raw):
    checked(spec)
    graph=build({'document':spec['document'],'nodes':spec['nodes'],'edges':[]},raw)
    lines=source_lines(raw)
    patterns={n['id']:re.compile(r'(?<!\w)'+re.escape(n['label'])+r'(?!\w)',re.IGNORECASE)
              for n in graph['nodes']}
    pairs=defaultdict(lambda:{'supporting_lines':0,'examples':[]})
    skipped=0
    for line_no,line in enumerate(lines,1):
        mentions=[]
        for node,pattern in patterns.items():
            for match in pattern.finditer(line):
                mentions.append((match.start(),match.end(),node))
                if len(mentions)>MAX_MENTIONS:break
            if len(mentions)>MAX_MENTIONS:break
        if len(mentions)>MAX_MENTIONS:
            skipped+=1;continue
        found={}
        for a,b in combinations(sorted(mentions),2):
            if a[2]==b[2] or b[0]<a[1]:continue
            end=max(a[1],b[1]);length=end-a[0]
            if length>MAX_SPAN:continue
            quote=line[a[0]:end]
            try:literal(quote,MAX_SPAN)
            except ValueError:continue
            key=tuple(sorted((a[2],b[2])))
            choice=(length,a[0],quote)
            if key not in found or choice<found[key]:found[key]=choice
        for key,(_,start,quote) in found.items():
            entry=pairs[key];entry['supporting_lines']+=1
            if len(entry['examples'])<MAX_EXAMPLES:
                entry['examples'].append({'line':line_no,'start':start,'quote':quote})
    ranked=sorted(pairs.items(),key=lambda row:(-row[1]['supporting_lines'],row[0]))
    candidates=[{'id':'r'+str(i+1),'entities':list(key),'observed_relation':'same_line_cooccurrence',
                 'status':'candidate_not_semantically_verified','direction':None,**data}
                for i,(key,data) in enumerate(ranked[:spec['max_candidates']])]
    return {'schema':'janus-relationship-discovery-result-v1','document':spec['document'],
            'document_sha256':hashlib.sha256(raw).hexdigest(),'nodes':graph['nodes'],
            'candidates':candidates,'qualifying_pairs':len(ranked),'skipped_dense_lines':skipped,
            'omitted_pairs':len(ranked)-len(candidates),'claims_verified':False,'authority':False,
            'limitations':'Exact same-line co-occurrence within 500 characters; not a proven relationship, direction, or cause. Dense lines are skipped; at most three evidence examples per pair.'}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    raw=guard.exact(doc,plan['guards'][1],MAX_BYTES)
    build({'document':spec['document'],'nodes':spec['nodes'],'edges':[]},raw)
    return plan,dict(spec,scope='Discover exact textual co-occurrence candidates only. No semantic assertions or graph mutation.')
def execute(root,plan):
    spec,dst,doc=validate(root,plan);result=discover(spec,guard.exact(doc,plan['guards'][1],MAX_BYTES))
    payload=json.dumps(result,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'relationship_candidates_observed','output':plan['output'],'sha256':digest,
            'candidates':len(result['candidates']),'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Relationship evidence or reviewed source invalid'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
