"""Reviewed X4 attribute diff construction against exact extracted asset XML."""
from __future__ import annotations
import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard

SCHEMA='janus-x4-attribute-diff-v1'
EXTRA=('asset','.xml')
MAX_XML=2_000_000
IDENT=r'[A-Za-z_][A-Za-z0-9_.-]{0,159}'
TAG=r'[A-Za-z_][A-Za-z0-9_-]{0,63}'
NUMBER=r'-?[0-9]{1,14}(?:\.[0-9]{1,8})?'

def match(value,pattern):
    return isinstance(value,str) and re.fullmatch(pattern,value) is not None

def checked(s):
    if not isinstance(s,dict) or set(s)!={'asset','kind','name','edits'} or not isinstance(s['asset'],str) or not s['asset'].startswith('assets/') or s['kind'] not in ('macro','component') or not match(s['name'],IDENT):
        raise ValueError('Choose an extracted asset macro or component and exact identity')
    edits=s['edits']
    if not isinstance(edits,list) or not 1<=len(edits)<=32:raise ValueError('Choose 1–32 reviewed numeric attribute replacements')
    selectors=set()
    for e in edits:
        if not isinstance(e,dict) or set(e)!={'path','attribute','expected','value'} or not match(e['attribute'],TAG) or not match(e['expected'],NUMBER) or not match(e['value'],NUMBER):
            raise ValueError('Expected exact attribute and bounded numeric strings')
        if Decimal(e['expected'])==Decimal(e['value']):raise ValueError('Replacement must change numeric value')
        steps=e['path']
        if not isinstance(steps,list) or not 1<=len(steps)<=8:raise ValueError('Choose 1–8 child steps')
        for step in steps:
            if not isinstance(step,dict) or set(step) not in ({'tag'},{'tag','key','value'}) or not match(step['tag'],TAG):
                raise ValueError('Invalid selector step')
            if 'key' in step and (step['key'] not in ('name','ref','id','class','type') or not match(step['value'],IDENT)):
                raise ValueError('Use a literal identity predicate only')
        sel=selector(s,e)
        if sel in selectors:raise ValueError('Repeated target attribute')
        selectors.add(sel)
    return s

def selector(s,e):
    kind=s['kind']
    path='/'+kind+'s/'+kind+"[@name='"+s['name']+"']"
    for step in e['path']:
        path+='/'+step['tag']
        if 'key' in step:path+="[@"+step['key']+"='"+step['value']+"']"
    return path+'/@'+e['attribute']

def parse(raw):
    if not isinstance(raw,bytes) or not 1<=len(raw)<=MAX_XML:raise ValueError('XML exceeds audit bound')
    text=raw.decode('utf-8-sig')
    if re.search(r'<!\s*(?:DOCTYPE|ENTITY)\b',text,re.I):raise ValueError('DTD/entity declarations refused')
    tree=ET.fromstring(text)
    if sum(1 for _ in tree.iter())>20000:raise ValueError('XML node count exceeds bound')
    return tree

def resolve(tree,s,e):
    if tree.tag!=s['kind']+'s':raise ValueError('Asset root does not match selected kind')
    nodes=[n for n in tree.findall(s['kind']) if n.get('name')==s['name']]
    if len(nodes)!=1:raise ValueError('Asset identity missing or ambiguous')
    node=nodes[0]
    for step in e['path']:
        nodes=[n for n in node.findall(step['tag']) if 'key' not in step or n.get(step['key'])==step['value']]
        if len(nodes)!=1:raise ValueError('Selector missing or ambiguous')
        node=nodes[0]
    if e['attribute'] not in node.attrib:raise ValueError('Existing attribute required')
    return node

def generate(raw,s):
    checked(s);tree=parse(raw);targets=[];seen=set()
    # Resolve every target against original bytes before performing any edits.
    for e in s['edits']:
        n=resolve(tree,s,e);key=(id(n),e['attribute'])
        if key in seen or n.get(e['attribute'])!=e['expected']:raise ValueError('Duplicate target or expected value mismatch')
        seen.add(key);targets.append((n,e))
    diff=ET.Element('diff')
    for n,e in targets:
        ET.SubElement(diff,'replace',sel=selector(s,e)).text=e['value']
        n.set(e['attribute'],e['value'])
    ET.indent(diff,space='  ')
    payload=ET.tostring(diff,encoding='utf-8',xml_declaration=True)+b'\n'
    # Reparse output, resolve each emitted selector against an independent source tree,
    # and compare the complete resulting tree, including unaffected attributes/children.
    replay=parse(raw);out=parse(payload);ops=list(out)
    if out.tag!='diff' or len(ops)!=len(targets):raise ValueError('Patch structure changed')
    for op,(_,e) in zip(ops,targets):
        if op.tag!='replace' or op.attrib!={'sel':selector(s,e)} or op.text!=e['value'] or len(op):
            raise ValueError('Patch operation roundtrip failed')
        n=resolve(replay,s,e)
        if n.get(e['attribute'])!=e['expected']:raise ValueError('Patch replay source mismatch')
        n.set(e['attribute'],op.text)
    if ET.tostring(replay)!=ET.tostring(tree):raise ValueError('Patch replay diverged')
    return payload,{'source_sha256':hashlib.sha256(raw).hexdigest(),'asset':s['asset'],
        'operations':[{'selector':selector(s,e),'before':e['expected'],'after':e['value']} for e in s['edits']],
        'local_replay_verified':True,'game_schema_verified':False,'gameplay_verified':False}

def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.xml',extra=EXTRA)

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.xml',extra=EXTRA)
    _,_,src=validate(root,plan)
    _,r=generate(guard.exact(src,plan['guards'][1],MAX_XML),s)
    return plan,dict(s,observations=r,scope='New X4 diff artifact only; numeric existing attributes, no game install or schema acceptance.')

def execute(root,plan):
    s,dst,src=validate(root,plan)
    payload,r=generate(guard.exact(src,plan['guards'][1],MAX_XML),s)
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-x4-attribute-diff-result-v1','status':'x4_diff_locally_replayed','output':plan['output'],
        'sha256':sha,'source_unchanged':True,**r}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Invalid reviewed X4 source or numeric attribute selector'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
