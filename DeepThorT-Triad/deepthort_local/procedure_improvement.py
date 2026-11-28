"""Stage bounded, evidence-driven improvements to the acceptance procedure.

Never install a generated manifest or change the existing test order in use.
A historical earlier failure position is a scheduling proxy, not runtime proof.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from .latest_acceptance import load_test
from .self_evaluation import assess
from .source_security import linked
from .disk_gate import require_storage

SCHEMA='janus-acceptance-procedure-candidate-v1'
# Only existing audited checks, with conservative prerequisites.
# Unknown probes are not moved. Preserve all nonselected checks in original order.
DEPENDENCIES={
    'triad_residency':('shared_cap',),
    'triad_inference':('shared_cap','triad_residency'),
    'concurrent_status':('triad_inference',),
    'triad_collaboration':('triad_inference','concurrent_status'),
    'production_review':('triad_inference','concurrent_status','triad_collaboration'),
    'live_memory':('shared_cap','triad_residency'),
    'memory_core':('live_memory',),
    'multimedia_core':('shared_cap','triad_residency'),
    'five_model_acceptance':('shared_cap','triad_residency','live_memory','memory_core','multimedia_core'),
    'workflow_doctrine':('shared_cap','triad_residency'),
}
# Only probes whose actual preconditions are explicitly represented here can move.
MOVABLE={'triad_residency','triad_inference','concurrent_status','triad_collaboration',
         'production_review','live_memory','memory_core','multimedia_core','five_model_acceptance','workflow_doctrine'}

def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def propose(manifest,evaluation):
    if manifest['id']!=evaluation['test_id']:return None
    order=manifest['checks'];positions={name:i for i,name in enumerate(order)}
    if len(positions)!=len(order) or not order or order[0]!='shared_cap':return None
    # Check baseline dependency order; missing conditional probes may be absent,
    # but required dependencies for the chosen focus are not silently inserted.
    def closure(check,seen):
        if check in seen:return
        if check not in positions:raise ValueError('Missing explicit prerequisite')
        seen.add(check)
        for dep in DEPENDENCIES.get(check,()):closure(dep,seen)
    for finding in evaluation['findings']:
        target=finding['check']
        if target not in MOVABLE or finding['status']!='failed' or not (finding['regression'] or finding['consecutive_observations']>=2):continue
        selected=set()
        try:closure(target,selected)
        except ValueError:continue
        first=[x for x in order if x in selected]
        revised=first+[x for x in order if x not in selected]
        if revised.index(target)>=order.index(target):continue
        if revised[0]!='shared_cap' or len(revised)!=len(order) or set(revised)!=set(order):raise ValueError('Procedure lost checks')
        for name,deps in DEPENDENCIES.items():
            if name in positions:
                for dep in deps:
                    if dep in positions and revised.index(dep)>=revised.index(name):
                        raise ValueError('Candidate dependency order invalid')
        body={'schema':SCHEMA,'source_manifest_sha':digest(manifest),'source_report_sha':evaluation['latest_sha'],
              'test_id':manifest['id'],'focus':target,'baseline_order':order,'candidate_order':revised,
              'historical_checks_before_failure':order.index(target),
              'candidate_checks_before_failure':revised.index(target),
              'all_checks_preserved':True,'runtime_improvement_verified':False,
              'execution_authorized':False,'installation_authorized':False}
        return {**body,'candidate_sha':digest(body)}
    return None

def stage_once(root,state,store):
    root=Path(root).resolve(strict=True);state=Path(state).resolve(strict=True)
    source=root/'LATEST_TEST.json'
    if not source.is_file() or linked(source):return False
    manifest=load_test(source);evaluation=assess(state)
    if not evaluation:return False
    candidate=propose(manifest,evaluation)
    if candidate is None:return False
    folder=state/'procedure-improvements'
    if folder.exists() and linked(folder):raise ValueError('Linked procedure staging refused')
    folder.mkdir(exist_ok=True)
    name=candidate['candidate_sha'];dst=folder/(name+'.json')
    payload=(json.dumps(candidate,indent=2,sort_keys=True)+'\n').encode()
    if dst.exists():
        if linked(dst) or dst.stat().st_size!=len(payload) or dst.read_bytes()!=payload:
            raise ValueError('Existing procedure candidate changed')
    else:
        with os.scandir(folder) as entries:
            if sum(1 for _ in entries)>=128:raise ValueError('Procedure staging full; owner review required')
        require_storage(folder)
        fd,tmp=tempfile.mkstemp(prefix='.candidate-',dir=folder)
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
            if load_test(source)!=manifest or assess(state)!=evaluation:raise ValueError('Procedure evidence changed')
            os.link(tmp,dst)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return store.recommend(evidence_key='procedure-improvement-'+name,
        problem='Procedure improvement candidate: earlier detection of '+candidate['focus'],
        proposal=f"Staged {name}.json; all checks preserved. Historical failure position {candidate['historical_checks_before_failure']+1} becomes {candidate['candidate_checks_before_failure']+1}. Scheduling proxy only; owner review and prospective native acceptance required. No execution or installation authorized.")
