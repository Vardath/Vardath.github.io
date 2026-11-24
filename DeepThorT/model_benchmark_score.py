"""Fixed independent scorer: generated Python is interpreted, never executed."""
import argparse
import ast
import json
import operator
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
CASES=json.loads((ROOT/'benchmarks/cases.json').read_text())
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
     ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,
     ast.Eq:operator.eq,ast.NotEq:operator.ne,ast.Lt:operator.lt,
     ast.LtE:operator.le,ast.Gt:operator.gt,ast.GtE:operator.ge}
BUILTINS={'min':min,'max':max,'sum':sum,'len':len,'abs':abs,'range':range,'enumerate':enumerate}
class Unsupported(ValueError):pass
class Returned(Exception):
    def __init__(self,value):self.value=value

def bounded(v):
    if type(v) is int and abs(v)>1000000:raise Unsupported('integer budget')
    if isinstance(v,(str,list,tuple,range)) and len(v)>256:raise Unsupported('value budget')
    return v

def code_result(source,name,args):
    if len(source)>8000:raise Unsupported('source size')
    source=source.strip()
    fence=re.fullmatch(r'\x60{3}(?:python)?\s*\n(.*?)\n\x60{3}',source,re.S)
    if fence:source=fence[1]
    try:tree=ast.parse(source)
    except SyntaxError as exc:raise Unsupported('syntax') from exc
    if sum(1 for _ in ast.walk(tree))>400 or len(tree.body)!=1:raise Unsupported('module shape')
    fn=tree.body[0]
    if (not isinstance(fn,ast.FunctionDef) or fn.name!=name or fn.decorator_list or
        fn.args.posonlyargs or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or
        fn.args.defaults or len(fn.args.args)!=len(args)):raise Unsupported('signature')
    # Reject unsupported code even in an unvisited branch.
    safe=(ast.Module,ast.FunctionDef,ast.arguments,ast.arg,ast.Return,ast.If,ast.Assign,
          ast.AugAssign,ast.For,ast.Expr,ast.Constant,ast.Name,ast.List,ast.Tuple,ast.BinOp,
          ast.UnaryOp,ast.Compare,ast.BoolOp,ast.IfExp,ast.Subscript,ast.Call,
          ast.Load,ast.Store,ast.And,ast.Or,ast.Not,ast.USub,*OPS.keys())
    if any(not isinstance(n,safe) or isinstance(n,ast.Call) and
           (not isinstance(n.func,ast.Name) or n.func.id not in BUILTINS or n.keywords)
           for n in ast.walk(tree)):raise Unsupported('unsupported syntax')
    values=dict(zip([a.arg for a in fn.args.args],args))
    steps=0
    def tick():
        nonlocal steps
        steps+=1
        if steps>2000:raise Unsupported('step budget')
    def expr(n):
        tick()
        if isinstance(n,ast.Constant) and type(n.value) in (int,bool,str,type(None)):return bounded(n.value)
        if isinstance(n,ast.Name) and n.id in values:return values[n.id]
        if isinstance(n,(ast.List,ast.Tuple)):return bounded([expr(x) for x in n.elts])
        if isinstance(n,ast.BinOp) and type(n.op) in OPS:
            a,b=expr(n.left),expr(n.right)
            if type(a) is not int or type(b) is not int:raise Unsupported('numeric operands')
            return bounded(OPS[type(n.op)](a,b))
        if isinstance(n,ast.UnaryOp):
            a=expr(n.operand)
            if isinstance(n.op,ast.Not):return not a
            if isinstance(n.op,ast.USub) and type(a) is int:return bounded(-a)
        if isinstance(n,ast.Compare):
            left=expr(n.left)
            for op,right_node in zip(n.ops,n.comparators):
                right=expr(right_node)
                if type(op) not in OPS:raise Unsupported('comparison')
                if not OPS[type(op)](left,right):return False
                left=right
            return True
        if isinstance(n,ast.BoolOp):
            for node in n.values:
                result=expr(node)
                if isinstance(n.op,ast.And) and not result:return result
                if isinstance(n.op,ast.Or) and result:return result
            return result
        if isinstance(n,ast.IfExp):return expr(n.body if expr(n.test) else n.orelse)
        if isinstance(n,ast.Subscript):return expr(n.value)[expr(n.slice)]
        if isinstance(n,ast.Call):
            name=n.func.id
            a=[expr(x) for x in n.args]
            if name=='range' and any(type(x) is not int or abs(x)>256 for x in a):raise Unsupported('range budget')
            result=BUILTINS[name](*a)
            if name=='enumerate':result=list(result)
            return bounded(result)
        raise Unsupported('expression '+type(n).__name__)
    def assign(target,value):
        if isinstance(target,ast.Name):values[target.id]=value
        elif isinstance(target,(ast.Tuple,ast.List)) and len(target.elts)==len(value):
            for t,v in zip(target.elts,value):assign(t,v)
        else:raise Unsupported('assignment')
    def body(nodes):
        for n in nodes:
            tick()
            if isinstance(n,ast.Return):raise Returned(expr(n.value) if n.value else None)
            if isinstance(n,ast.If):body(n.body if expr(n.test) else n.orelse)
            elif isinstance(n,ast.Assign):
                val=expr(n.value)
                for t in n.targets:assign(t,val)
            elif isinstance(n,ast.AugAssign) and isinstance(n.target,ast.Name) and type(n.op) in OPS:
                a,b=expr(n.target),expr(n.value)
                if type(a) is not int or type(b) is not int:raise Unsupported('numeric operands')
                assign(n.target,bounded(OPS[type(n.op)](a,b)))
            elif isinstance(n,ast.For):
                seq=expr(n.iter)
                if not isinstance(seq,(list,tuple,range,str)) or len(seq)>256:raise Unsupported('loop budget')
                for val in seq:
                    tick();assign(n.target,val);body(n.body)
                body(n.orelse)
            elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):pass
            else:raise Unsupported('statement '+type(n).__name__)
    try:body(fn.body)
    except Returned as result:return result.value
    return None

def pairs(items):
    out={}
    for k,v in items:
        if k in out:raise ValueError('duplicate key')
        out[k]=v
    return out

def equal(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b

def score_case(case,result):
    if 'error' in result:return 'inference_error'
    answer=result.get('answer','').strip()
    if case['kind']=='exact':return 'pass' if answer==case['expected'] else 'fail'
    if case['kind']=='json':
        try:actual=json.loads(answer,object_pairs_hook=pairs)
        except (ValueError,RecursionError):return 'fail'
        return 'pass' if equal(actual,case['expected']) else 'fail'
    try:
        for args,wanted in case['tests']:
            if not equal(code_result(answer,case['name'],args),wanted):return 'fail'
        return 'pass'
    except Unsupported:return 'unsupported'
    except (TypeError,ValueError,IndexError,KeyError,ArithmeticError,RecursionError):return 'fail'

def score(report):
    observed={r['id']:r for r in report['results']}
    rows=[{'id':c['id'],'category':c['category'],'status':score_case(c,observed[c['id']]) if c['id'] in observed else 'not_run'} for c in CASES]
    return {'profile':report['profile'],'complete':report.get('complete',False),
            'passed':sum(r['status']=='pass' for r in rows),'total':len(rows),
            'startup_ms':report.get('startup_ms'),'peak_rss_bytes':report.get('peak_rss_bytes'),
            'failure':report.get('failure'),'cases':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('report',type=Path);args=p.parse_args()
    report=json.loads(args.report.read_text(encoding='utf-8')); scored=score(report)
    output=args.report.with_name(args.report.stem+'-score.json')
    output.write_text(json.dumps(scored,indent=2),encoding='utf-8')
    print('BENCHMARK_SCORE '+json.dumps(scored,separators=(',',':')),flush=True)

if __name__=='__main__':main()
