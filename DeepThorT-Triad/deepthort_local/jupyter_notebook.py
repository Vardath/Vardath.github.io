"""Reviewed portable Jupyter notebook authoring; no kernel execution."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.long_form_writing import ID
SCHEMA='janus-jupyter-notebook-v1'
MAX_CELLS=64
MAX_TEXT=120000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'cells'} or not isinstance(s['cells'],list) or not 1<=len(s['cells'])<=MAX_CELLS:
        raise ValueError('Expected 1–64 reviewed notebook cells')
    seen=set();total=0
    for cell in s['cells']:
        if not isinstance(cell,dict) or set(cell)!={'id','kind','source'} or not isinstance(cell['id'],str) or not ID.fullmatch(cell['id']) or cell['id'] in seen or cell['kind'] not in ('markdown','code'):
            raise ValueError('Invalid or duplicate notebook cell')
        seen.add(cell['id']);source=cell['source']
        if not isinstance(source,str) or not source.strip() or len(source)>20000 or any(ord(c)<32 and c not in '\n\t' or 0xd800<=ord(c)<=0xdfff for c in source):
            raise ValueError('Invalid bounded notebook cell source')
        total+=len(source)
        if cell['kind']=='code':
            try:ast.parse(source,mode='exec')
            except (SyntaxError,RecursionError) as exc:raise ValueError('Only syntactically valid Python code cells supported') from exc
    if total>MAX_TEXT:raise ValueError('Notebook text exceeds budget')
    return s
def notebook(s):
    checked(s);cells=[]
    for c in s['cells']:
        cell={'cell_type':c['kind'],'id':c['id'],'metadata':{},'source':c['source'].splitlines(keepends=True)}
        if c['kind']=='code':cell.update(execution_count=None,outputs=[])
        cells.append(cell)
    return {'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'cells':cells}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.ipynb')
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.ipynb')
    return plan,dict(s,scope='Export an unexecuted Python notebook. Code is data until separately executed by a user-approved kernel.')
def execute(root,plan):
    s,dst,_=validate(root,plan);n=notebook(s);payload=(json.dumps(n,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode()
    restored=json.loads(payload)
    if restored!=n or [''.join(c['source']) for c in restored['cells']]!=[c['source'] for c in s['cells']]:
        raise ValueError('Notebook roundtrip mismatch')
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'unexecuted_notebook_exported','output':plan['output'],'sha256':digest,
            'cells':len(n['cells']),'code_cells':sum(c['cell_type']=='code' for c in n['cells']),
            'kernel_started':False,'code_executed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Notebook export unavailable'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
