"""Fixed, isolated regression for the V70 diagnostic-only source boundary.

No generated command or arbitrary test script. Execute only the trusted
baseline formatter and its structurally identical string-only variant.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

def sha(raw):return hashlib.sha256(raw).hexdigest()

def formatter(tree):
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='format_diagnostic']
    if len(nodes)!=1 or nodes[0].decorator_list:raise ValueError('Expected one undecorated diagnostic formatter')
    node=nodes[0]
    allowed={'bool':bool,'int':int,'str':str,'dict':dict,'list':list,'max':max}
    namespace={'__builtins__':allowed}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<isolated diagnostic formatter>','exec'),namespace)
    return namespace['format_diagnostic']

def check(baseline,candidate,old,new,caps):
    if not all(str(v)+'%' in new for v in caps.values()) or not new.startswith('System resource protection:'):
        raise ValueError('Diagnostic cap values not preserved')
    original=ast.parse(baseline.decode('utf-8'))
    modified=ast.parse(candidate.decode('utf-8'))
    old_nodes=[n for n in ast.walk(original) if isinstance(n,ast.Constant) and n.value==old]
    if len(old_nodes)!=1:raise ValueError('Baseline literal mismatch')
    old_nodes[0].value=new
    if ast.dump(original,include_attributes=False)!=ast.dump(modified,include_attributes=False):
        raise ValueError('Candidate is not a literal-only change')
    before=formatter(ast.parse(baseline.decode('utf-8')))
    after=formatter(modified)
    info={'issues':[],'components':{'node':True,'transformers':True,'server':True},'model_size_bytes':3000000000}
    count=0
    for running,ready,loading in ((False,False,False),(True,False,True),(True,False,False),(True,True,False)):
        for issues in ([],['Observed test issue']):
            data={**info,'issues':issues}
            kw=dict(model_running=running,model_ready=ready,model_loading=loading,queued=2,
                    recent_logs=['fixture log'],loading_seconds=62)
            a=before(data,**kw);b=after(data,**kw)
            if not isinstance(a,str) or a.count(old)!=1 or b!=a.replace(old,new,1):
                raise ValueError('Diagnostic behavior differs beyond reviewed text')
            count+=1
    return {'schema':'diagnostic-probe-v1','baseline_sha':sha(baseline),'candidate_sha':sha(candidate),
            'cases_passed':count,'assurance':'isolated_formatter_runtime_only'}

def main():
    if len(sys.argv)!=2:raise ValueError('Exact isolated fixture folder required')
    root=Path(sys.argv[1]).resolve(strict=True)
    request=json.loads((root/'probe.json').read_text('utf-8'))
    if set(request)!={'old','new','caps','baseline_sha','candidate_sha'}:raise ValueError('Invalid probe request')
    baseline=(root/'baseline.py.txt').read_bytes();candidate=(root/'candidate.py.txt').read_bytes()
    if len(baseline)>32000 or len(candidate)>32000 or sha(baseline)!=request['baseline_sha'] or sha(candidate)!=request['candidate_sha']:
        raise ValueError('Isolated fixture bytes changed')
    result=check(baseline,candidate,request['old'],request['new'],request['caps'])
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
