"""Reviewed, source-located directed knowledge graph from local text.

Edges are reviewer assertions supported by exact quotations, not independent
verification that the asserted predicate is true. No external calls or writes
to the knowledge index; publication uses the existing reviewed tool framework.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import ID,literal
from deepthort_local.document_knowledge import MAX_BYTES

SCHEMA='janus-knowledge-graph-v1'
EXTRA=('document',('.txt','.md','.rst','.adoc'))

def locator(evidence):
    if not isinstance(evidence,dict) or set(evidence)!={'line','start','quote'}:
        raise ValueError('Expected exact line, zero-based start and quote')
    if type(evidence['line']) is not int or not 1<=evidence['line']<=MAX_BYTES:
        raise ValueError('Invalid line locator')
    if type(evidence['start']) is not int or not 0<=evidence['start']<MAX_BYTES:
        raise ValueError('Invalid source offset')
    literal(evidence['quote'],500)

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'document','nodes','edges'} or not isinstance(spec['document'],str):
        raise ValueError('Expected document, nodes and directed edges')
    nodes=spec['nodes'];edges=spec['edges']
    if not isinstance(nodes,list) or not 1<=len(nodes)<=64 or not isinstance(edges,list) or len(edges)>128:
        raise ValueError('Choose 1–64 nodes and at most 128 edges')
    ids=set();labels=set()
    for n in nodes:
        if not isinstance(n,dict) or set(n)!={'id','label','kind','evidence'} or not isinstance(n['id'],str) or not ID.fullmatch(n['id']) or n['id'] in ids:
            raise ValueError('Invalid or duplicate node ID')
        literal(n['label'],120);literal(n['kind'],80);locator(n['evidence'])
        label=n['label'].casefold()
        if label in labels:raise ValueError('Duplicate node label')
        ids.add(n['id']);labels.add(label)
    seen=set()
    for e in edges:
        if not isinstance(e,dict) or set(e)!={'from','to','predicate','evidence'} or not isinstance(e['from'],str) or not isinstance(e['to'],str):
            raise ValueError('Invalid edge')
        if e['from'] not in ids or e['to'] not in ids:raise ValueError('Unknown edge endpoint')
        literal(e['predicate'],120);locator(e['evidence'])
        key=(e['from'],e['to'],e['predicate'].casefold())
        if key in seen:raise ValueError('Duplicate edge')
        seen.add(key)
    return spec

def source_lines(raw):
    if not raw or len(raw)>MAX_BYTES or b'\x00' in raw:raise ValueError('Invalid bounded text source')
    return raw.decode('utf-8-sig').splitlines()

def exact_quote(lines,evidence):
    i=evidence['line']-1;start=evidence['start'];quote=evidence['quote']
    if i>=len(lines) or lines[i][start:start+len(quote)]!=quote:
        raise ValueError('Graph evidence does not match exact source')
    return quote

def build(spec,raw):
    checked(spec);lines=source_lines(raw)
    nodes={n['id']:n for n in spec['nodes']}
    adjacency={key:{'outgoing':[],'incoming':[]} for key in nodes}
    for n in nodes.values():
        if n['label'].casefold() not in exact_quote(lines,n['evidence']).casefold():
            raise ValueError('Node label absent from its evidence')
    edges=[]
    for index,e in enumerate(spec['edges']):
        quote=exact_quote(lines,e['evidence']).casefold()
        if any(nodes[key]['label'].casefold() not in quote for key in (e['from'],e['to'])):
            raise ValueError('Both endpoint labels must occur in edge evidence')
        ident='e'+str(index+1)
        edges.append(dict(e,id=ident,status='reviewed_assertion_not_verified'))
        adjacency[e['from']]['outgoing'].append(ident)
        adjacency[e['to']]['incoming'].append(ident)
    return {'schema':'janus-knowledge-graph-result-v1','document':spec['document'],
            'document_sha256':hashlib.sha256(raw).hexdigest(),'nodes':list(nodes.values()),
            'edges':edges,'adjacency':adjacency,'claims_verified':False,'authority':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.json',extra=EXTRA)
    _,_,doc=validate(root,plan)
    graph=build(spec,guard.exact(doc,plan['guards'][1],MAX_BYTES))
    return plan,graph
def execute(root,plan):
    spec,dst,doc=validate(root,plan);graph=build(spec,guard.exact(doc,plan['guards'][1],MAX_BYTES))
    payload=json.dumps(graph,ensure_ascii=True,allow_nan=False,sort_keys=True,indent=2).encode()
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'knowledge_graph_structure_verified','output':plan['output'],'sha256':digest,
            'nodes':len(graph['nodes']),'edges':len(graph['edges']),'claims_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Graph evidence or reviewed source invalid'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
