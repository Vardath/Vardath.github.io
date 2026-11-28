"""Host-owned bounded behavioral regression for one recurring-fault hypothesis.

Interpret a tiny expression subset over fixed JSON-like fixture rows; never
compile/execute model-generated functions, import their modules or install them.
"""
import ast
from pathlib import Path
from .agent_contract import canonical_sha
from .self_investigation import _candidate,sha
from .source_security import linked
from .typed_project_tool import read_bound

TARGET='deepthort_local/conversation_memory.py'
FUNCTION='_cross_allowed'
CASES=(
    ({'mode':'draft_plan','project':'example'},True),
    ({'mode':'chat','project':'example'},False),
    ({'mode':'draft_plan','project':'(general)'},False),
    ({'mode':'draft_plan','project':''},False),
    ({'mode':'draft_plan','project':None},False),
    ({'project':'example'},False),
    ({'mode':'draft_plan'},False),
    ({},False),
)

def evaluate(node,row):
    if isinstance(node,ast.Constant) and (node.value is None or type(node.value) in (str,bool)):return node.value
    if isinstance(node,ast.Name) and node.id=='row':return row
    if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Name) and node.value.id=='row':
        key=evaluate(node.slice,row)
        if type(key) is str:return row[key]
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='row' and node.func.attr=='get' and not node.keywords and 1<=len(node.args)<=2:
        args=[evaluate(n,row) for n in node.args]
        if type(args[0]) is str:return row.get(*args)
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='bool' and len(node.args)==1 and not node.keywords:
        return bool(evaluate(node.args[0],row))
    if isinstance(node,ast.BoolOp) and isinstance(node.op,(ast.And,ast.Or)):
        for value in node.values:
            result=evaluate(value,row)
            if isinstance(node.op,ast.And) and not result:return result
            if isinstance(node.op,ast.Or) and result:return result
        return result
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not):return not evaluate(node.operand,row)
    if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.ops[0],(ast.Eq,ast.NotEq,ast.Is,ast.IsNot)):
        a,b=evaluate(node.left,row),evaluate(node.comparators[0],row)
        op=node.ops[0]
        if isinstance(op,ast.Eq):return a==b
        if isinstance(op,ast.NotEq):return a!=b
        if isinstance(op,ast.Is):return a is b
        return a is not b
    raise ValueError('Unsupported expression in fixed regression interpreter')

def expression(source):
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==FUNCTION]
    if len(nodes)!=1:raise ValueError('Expected exact predicate')
    fn=nodes[0]
    if fn.decorator_list or len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return) or fn.body[0].value is None or len(list(ast.walk(fn)))>100:
        raise ValueError('Only bounded single-return predicate is supported')
    if ast.dump(fn.args)!=ast.dump(ast.parse('def f(row): pass').body[0].args):
        raise ValueError('Predicate interface changed')
    expr=fn.body[0].value
    # Traverse every branch, including unreachable branches, before evaluating fixtures.
    allowed=(ast.Constant,ast.Name,ast.Load,ast.Subscript,ast.Call,ast.Attribute,ast.BoolOp,ast.And,ast.Or,
             ast.UnaryOp,ast.Not,ast.Compare,ast.Eq,ast.NotEq,ast.Is,ast.IsNot)
    if any(not isinstance(n,allowed) for n in ast.walk(expr)):raise ValueError('Unsupported predicate syntax')
    for n in ast.walk(expr):
        if isinstance(n,ast.Name) and n.id not in ('row','bool'):raise ValueError('Unsupported name')
        if isinstance(n,ast.Attribute) and not (n.attr=='get' and isinstance(n.value,ast.Name) and n.value.id=='row'):
            raise ValueError('Unsupported attribute')
        if isinstance(n,ast.Call):
            valid=(isinstance(n.func,ast.Name) and n.func.id=='bool' and len(n.args)==1) or (isinstance(n.func,ast.Attribute) and n.func.attr=='get' and 1<=len(n.args)<=2)
            if not valid or n.keywords:raise ValueError('Unsupported call')
    return expr

def outcomes(source):
    expr=expression(source);result=[]
    for i,(row,expected) in enumerate(CASES):
        try:
            value=evaluate(expr,row);passed=type(value) is bool and value==expected
            result.append({'case':i,'passed':passed,'raised_key_error':False})
        except KeyError:result.append({'case':i,'passed':False,'raised_key_error':True})
    return result

def verify(root,state,case,body):
    if case['evidence']['target']!=TARGET or body['plan']['function']!=FUNCTION:return None
    if body['state']!='investigation_staged' or body['authority'] is not False or body['review']['accepted'] is not True:
        raise ValueError('Independent staged review required')
    candidate=_candidate(case,body['plan'],__import__('json').dumps({'function_source':body['candidate']['function_source']}))
    if candidate['candidate_sha']!=body['candidate']['candidate_sha'] or body['review']['candidate_sha']!=candidate['candidate_sha']:
        raise ValueError('Reviewed candidate mismatch')
    folder=Path(state)/'self-development'/case['key']
    paths=[folder/'baseline.py.txt',folder/'candidate.py.txt',folder/'manifest.json']
    if any(linked(p) for p in (folder,folder.parent,*paths)):raise ValueError('Linked staged evidence')
    baseline,new,manifest=map(lambda p:read_bound(p,64000),paths)
    if baseline.decode('utf8')!=case['source'] or new.decode('utf8')!=candidate['source']:
        raise ValueError('Staged bytes mismatch')
    record=__import__('json').loads(manifest)
    if any(record.get(k)!=v for k,v in body.items()) or record.get('installation_authorized') is not False:
        raise ValueError('Staged manifest mismatch')
    before=outcomes(case['source'])
    try:after=outcomes(candidate['source']);status='passed' if all(x['passed'] for x in after) and not all(x['passed'] for x in before) else 'failed'
    except ValueError:after=[];status='unsupported'
    return {'schema':'triad-fixed-predicate-regression-v1','scope_sha':case['key'],
            'baseline_sha':sha(case['source']),'candidate_sha':candidate['candidate_sha'],
            'fixture_sha':canonical_sha(CASES),'baseline':before,'candidate':after,'status':status,
            'generated_python_executed':False,'native_runtime_verified':False,'installation_authorized':False}
