"""Reviewed single-function local-variable rename, with exact AST comparison."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import keyword
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
SCHEMA='janus-code-refactoring-v1'
EXTRA=('document','.py')
MAX_SOURCE=120000
# Deliberately narrow initial scope. Reject nested scopes, exotic bindings,
# and reflective/dynamic calls rather than guess their name resolution.
BLOCKED=(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Lambda,ast.ListComp,
         ast.SetComp,ast.DictComp,ast.GeneratorExp,ast.Global,ast.Nonlocal,
         ast.Import,ast.ImportFrom,ast.ExceptHandler,ast.Match,ast.JoinedStr)
REFLECTIVE={'locals','globals','vars','eval','exec','compile','dir','getattr','setattr','delattr',
            '__import__','breakpoint','help'}
def identifier(v):
    if not isinstance(v,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',v) or keyword.iskeyword(v) or keyword.issoftkeyword(v):
        raise ValueError('Use a simple non-keyword ASCII identifier')
    return v
def checked(s):
    if not isinstance(s,dict) or set(s)!={'document','function','old_name','new_name'} or not isinstance(s['document'],str):
        raise ValueError('Expected Python source, top-level function and local rename')
    for k in ('function','old_name','new_name'):identifier(s[k])
    if s['old_name']==s['new_name']:raise ValueError('Choose a different name')
    return s
def target(tree,s):
    found=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==s['function']]
    if len(found)!=1:raise ValueError('Choose one unique top-level function')
    return found[0]
def parse(text):
    tree=ast.parse(text,type_comments=True)
    compile(tree,'<reviewed-source>','exec') # compile only, never execute
    return tree
def refactor(raw,s):
    checked(s)
    if not raw or len(raw)>MAX_SOURCE or raw.startswith(b'\xef\xbb\xbf') or b'\r' in raw:
        raise ValueError('Use bounded UTF-8 Python source with LF newlines and no BOM')
    text=raw.decode('utf-8');tree=parse(text);fn=target(tree,s)
    if fn.decorator_list:raise ValueError('Decorated target functions unsupported')
    old,new=s['old_name'],s['new_name']
    arguments={n.arg for n in ast.walk(fn.args) if isinstance(n,ast.arg)}
    if old in arguments or new in arguments:raise ValueError('Cannot rename a parameter or collide with one')
    # Exclude signature/default/annotation expressions from rewrite.
    nodes=[n for statement in fn.body for n in ast.walk(statement)]
    if len(nodes)>20000 or any(isinstance(n,BLOCKED) for n in nodes):
        raise ValueError('Function contains unsupported scope or binding constructs')
    if any(isinstance(n,ast.Name) and n.id in REFLECTIVE for n in nodes):
        raise ValueError('Reflective or dynamic name access unsupported')
    if any(isinstance(n,ast.Attribute) and n.attr in REFLECTIVE|{'f_locals','f_globals','__code__','co_varnames','currentframe','_getframe'} for n in nodes):
        raise ValueError('Reflective attributes unsupported')
    names=[n for n in nodes if isinstance(n,ast.Name)]
    if any(n.id==new for n in names):raise ValueError('New identifier already occurs in function')
    changes=[n for n in names if n.id==old]
    if not changes or not any(isinstance(n.ctx,ast.Store) for n in changes):
        raise ValueError('Old identifier must be locally assigned')
    # AST byte offsets refer to UTF-8, not Python Unicode code points.
    lines=raw.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    spans=[]
    for n in changes:
        if n.lineno!=n.end_lineno:raise ValueError('Unexpected identifier range')
        a=offsets[n.lineno-1]+n.col_offset;b=offsets[n.end_lineno-1]+n.end_col_offset
        if raw[a:b]!=old.encode('ascii'):raise ValueError('Exact identifier evidence mismatch')
        spans.append((a,b,n.lineno,n.col_offset))
    if len({(a,b) for a,b,_,_ in spans})!=len(spans):raise ValueError('Duplicate identifier range')
    output=raw
    for a,b,_,_ in sorted(spans,reverse=True):output=output[:a]+new.encode('ascii')+output[b:]
    # Independently parse resulting bytes and compare the entire module AST
    # with the original tree transformed only at selected local Name nodes.
    for n in changes:n.id=new
    actual=parse(output.decode('utf-8'))
    if ast.dump(actual,include_attributes=False)!=ast.dump(tree,include_attributes=False):
        raise ValueError('AST differs beyond reviewed rename')
    return output,{'source_sha256':hashlib.sha256(raw).hexdigest(),'function':s['function'],
        'old_name':old,'new_name':new,'changed_occurrences':len(spans),
        'source_locations':[{'line':l,'utf8_column':c} for a,b,l,c in sorted(spans)],
        'ast_comparison_verified':True,'runtime_equivalence_verified':False}
def validate(root,plan):return guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.py',extra=EXTRA)
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.py',extra=EXTRA)
    _,_,doc=validate(root,plan)
    _,receipt=refactor(guard.exact(doc,plan['guards'][1],MAX_SOURCE),s)
    return plan,dict(s,reviewed_rename=receipt,scope='Produce a new Python file; source unchanged. AST verification is not a runtime equivalence proof.')
def execute(root,plan):
    s,dst,doc=validate(root,plan);payload,r=refactor(guard.exact(doc,plan['guards'][1],MAX_SOURCE),s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'local_rename_ast_verified','output':plan['output'],'sha256':digest,'source_unchanged':True,**r}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:
        print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'Refactoring unavailable; inspect exact function and conservative scope rules'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
