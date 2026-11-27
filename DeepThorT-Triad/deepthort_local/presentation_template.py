"""Populate explicit, whole-run placeholders in a reviewed existing PPTX template."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.presentation_edit import package,slide_parts,xml,NS,literal,apply

SCHEMA='janus-presentation-template-v1'
EXTRA=('template','.pptx')
TOKEN=re.compile(r'\{\{([A-Z][A-Z0-9_]{0,39})\}\}')
def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'template','values'} or not isinstance(spec['template'],str) or not isinstance(spec['values'],dict) or not 1<=len(spec['values'])<=100:
        raise ValueError('Expected template and explicit placeholder values')
    for key,value in spec['values'].items():
        if not isinstance(key,str) or not TOKEN.fullmatch('{{'+key+'}}'):
            raise ValueError('Invalid placeholder name')
        literal(value)
        if TOKEN.search(value):raise ValueError('Replacement must not introduce a placeholder')
    return spec

def operations(raw,spec):
    parts=package(raw);names=slide_parts(parts);edits=[];used=set()
    for i,name in enumerate(names,1):
        root=xml(parts[name])
        all_text=root.xpath('.//a:t',namespaces=NS)
        editable=root.xpath('.//p:sp/p:txBody/a:p/a:r/a:t',namespaces=NS)
        counts={}
        for node in all_text:
            value=node.text or ''
            if not TOKEN.search(value):
                if '{{' in value or '}}' in value:raise ValueError('Malformed or split placeholder')
                continue
            match=TOKEN.fullmatch(value)
            if not match or node not in editable:raise ValueError('Placeholder must occupy a whole ordinary shape text run')
            key=match.group(1)
            if key not in spec['values']:raise ValueError('Missing explicit placeholder value: '+key)
            counts[key]=counts.get(key,0)+1
            if counts[key]>1:raise ValueError('Repeated placeholder on one slide is ambiguous')
            used.add(key)
            edits.append({'slide':i,'before':value,'after':spec['values'][key]})
            if len(edits)>100:raise ValueError('Template placeholder count exceeds bound')
    if used!=set(spec['values']) or not edits:
        raise ValueError('Unused supplied value or no supported placeholders')
    return edits

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.pptx',extra=EXTRA)
    _,_,path=validate(root,plan)
    raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    return plan,dict(spec,resolved_replacements=operations(raw,spec))
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.pptx',extra=EXTRA)
def execute(root,plan):
    spec,dst,path=validate(root,plan);raw=guard.exact(path,plan['guards'][1],guard.MAX_INPUT)
    edits=operations(raw,spec)
    payload,count,changed=apply(raw,{'presentation':spec['template'],'edits':edits})
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-presentation-template-result-v1','status':'template_structure_verified','output':plan['output'],
            'sha256':sha,'slides':count,'placeholders_filled':len(edits),'changed_slide_parts':changed,
            'source_unchanged':True,'untouched_part_bytes_verified':True,'visual_render_verified':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2);resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Template application unavailable; inspect whole-run placeholders and reviewed values'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
