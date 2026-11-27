"""Generate explicit, bounded same-sheet formulas; do not evaluate them."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.spreadsheet_edit import coordinate,load,serialize,snapshot,scalar

SCHEMA='janus-spreadsheet-formula-v1'
INFIX={'ADD':'+','SUB':'-','MUL':'*','DIV':'/','EQ':'=','NE':'<>','GT':'>','LT':'<','GE':'>=','LE':'<='}
AGG={'SUM','AVERAGE','MIN','MAX','COUNT','COUNTA'}
FIXED={'ROUND':2,'ABS':1,'IF':3}
MAX_NODES=64
MAX_RANGE_CELLS=50000

def box(ref):
    from openpyxl.utils.cell import coordinate_to_tuple
    parts=ref.split(':')
    if len(parts) not in (1,2):raise ValueError('Invalid same-sheet reference')
    points=[coordinate_to_tuple(coordinate(x)) for x in parts]
    r1,c1=points[0];r2,c2=points[-1]
    if r2<r1 or c2<c1 or (r2-r1+1)*(c2-c1+1)>MAX_RANGE_CELLS:raise ValueError('Reversed or oversized formula range')
    return (r1,c1,r2,c2)

def expression(node,*,depth=0,budget=None,refs=None,allow_range=False):
    if budget is None:budget=[0]
    if refs is None:refs=[]
    budget[0]+=1
    if depth>8 or budget[0]>MAX_NODES or not isinstance(node,dict):raise ValueError('Formula expression exceeds typed bounds')
    if set(node)=={'cell'}:
        value=coordinate(node['cell']);refs.append(box(value));return value
    if set(node)=={'range'}:
        value=node['range']
        if not allow_range or not isinstance(value,str) or ':' not in value:raise ValueError('Range requires an aggregate argument')
        refs.append(box(value));return value
    if set(node)=={'literal'}:
        value=scalar(node['literal'])
        if value is None:raise ValueError('Formula literal cannot be null')
        if type(value) is bool:return 'TRUE' if value else 'FALSE'
        if type(value) in (int,float):return str(value)
        if any(ord(c)<32 for c in value) or len(value)>200:raise ValueError('Invalid formula text literal')
        return '"'+value.replace('"','""')+'"'
    if set(node)!={'op','args'} or not isinstance(node['op'],str) or not isinstance(node['args'],list):
        raise ValueError('Expected typed formula expression')
    op=node['op'];args=node['args']
    if op in INFIX:
        if len(args)!=2:raise ValueError('Binary operator requires two arguments')
    elif op in AGG:
        if not 1<=len(args)<=16:raise ValueError('Invalid aggregate argument count')
    elif op in FIXED:
        if len(args)!=FIXED[op]:raise ValueError('Invalid function arity')
    else:raise ValueError('Formula function is outside the local allowlist')
    values=[expression(x,depth=depth+1,budget=budget,refs=refs,allow_range=op in AGG) for x in args]
    if op in INFIX:return '('+values[0]+INFIX[op]+values[1]+')'
    return op+'('+','.join(values)+')'

def compile_formula(node):
    if not isinstance(node,dict) or 'op' not in node:raise ValueError('Root expression requires a supported operation')
    refs=[];formula='='+expression(node,refs=refs)
    if len(formula)>4000:raise ValueError('Formula exceeds length bound')
    return formula,refs

def checked(spec):
    if not isinstance(spec,dict) or set(spec)!={'workbook','formulas'} or not isinstance(spec['workbook'],str):
        raise ValueError('Expected workbook and formulas')
    if not isinstance(spec['formulas'],list) or not 1<=len(spec['formulas'])<=200:raise ValueError('Invalid formula count')
    output=[];seen=set()
    for f in spec['formulas']:
        if not isinstance(f,dict) or set(f)!={'sheet','cell','expression','replace'} or not isinstance(f['sheet'],str) or not 1<=len(f['sheet'])<=31 or type(f['replace']) is not bool:
            raise ValueError('Invalid formula target')
        key=(f['sheet'].casefold(),coordinate(f['cell']))
        if key in seen:raise ValueError('Duplicate formula target')
        seen.add(key);compile_formula(f['expression']);output.append(f)
    # Reject cycles introduced among the newly authored formulas, including
    # a direct range reference that contains the target. Existing formulas
    # are not evaluated or parsed for transitive dependency claims.
    locations={key:box(key[1])[:2] for key in seen}
    dependencies={}
    for f in output:
        key=(f['sheet'].casefold(),f['cell']);_,refs=compile_formula(f['expression'])
        dependencies[key]={other for other,(r,c) in locations.items() if other[0]==key[0]
                           and any(r1<=r<=r2 and c1<=c<=c2 for r1,c1,r2,c2 in refs)}
    pending=set(dependencies)
    while pending:
        ready={key for key in pending if not dependencies[key]&pending}
        if not ready:raise ValueError('New formulas contain a dependency cycle')
        pending-=ready
    return {'workbook':spec['workbook'],'formulas':output}

def review(root,source,output,exclude=()):
    plan,spec=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.xlsx',extra=('workbook','.xlsx'))
    # Display generated formula strings as well as the exact typed inputs.
    preview={'workbook':spec['workbook'],'formulas':[dict(f,generated_formula=compile_formula(f['expression'])[0]) for f in spec['formulas']]}
    return plan,preview
def validate(root,plan):
    return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.xlsx',extra=('workbook','.xlsx'))
def execute(root,plan):
    spec,dst,source=validate(root,plan);wb=load(guard.exact(source,plan['guards'][1],guard.MAX_INPUT))
    try:
        for f in spec['formulas']:
            if f['sheet'] not in wb.sheetnames:raise ValueError('Formula sheet missing')
            cell=wb[f['sheet']][f['cell']]
            if cell.value is not None and not f['replace']:raise ValueError('Formula target occupied; explicit replacement required')
            cell.value=compile_formula(f['expression'])[0]
            if cell.data_type!='f':raise ValueError('Formula type not stored')
        payload=serialize(wb,snapshot(wb))
    finally:wb.close()
    sha=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'schema':'janus-spreadsheet-formula-result-v1','status':'formula_text_verified','output':plan['output'],
            'sha256':sha,'formulas':len(spec['formulas']),'source_unchanged':True,
            'formula_values_recalculated':False,'existing_formula_dependencies_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True);args=parser.parse_args()
    try:
        if sys.platform!='win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS,(768*1024*1024,)*2)
            resource.setrlimit(resource.RLIMIT_CPU,(30,30))
        print(json.dumps(execute(args.root,json.loads(args.plan)),sort_keys=True),flush=True);return 0
    except Exception as exc:
        print(json.dumps({'status':'blocked','error_type':type(exc).__name__,'reason':'Formula generation unavailable; inspect typed specification and installed tools'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
