"""Bounded per-job test execution trace; no inferred semantic coverage.

Only exact named unittest results count as observed execution. A file-level
verifies declaration links a requirement to a test file, not to a proved
individual assertion. Historical summary-only tests stay unconfirmed.
"""
from __future__ import annotations
import re
import json
import hashlib
from pathlib import Path
from collections import Counter
from .behavior_tests import test_kind,validate
from .workspace import safe_target
from .acceptance_contracts import explicit_requirement_labels
from .requirements_intelligence import requirement_candidates
from .specification_library import sections

RESULT=re.compile(r'^test_\w+ \(([\w.]+\.test_\w+)\) \.\.\. (ok|FAIL|ERROR|skipped(?: .*)?|expected failure|unexpected success)$')
SUMMARY=re.compile(r'^Ran (\d+) tests? in ')

def named_results(lines):
    observed={}
    ambiguous=set()
    for raw in lines:
        match=RESULT.fullmatch(raw.strip())
        if not match:continue
        ident,status=match.groups()
        if ident in observed:ambiguous.add(ident)
        observed[ident]={'ok':'passed','FAIL':'failed','ERROR':'failed'}.get(status,'not_passed')
    for ident in ambiguous:observed.pop(ident,None)
    return observed

def build_trace(job,steps,original,output,exit_code):
    project=Path(job['project']).resolve(strict=True)
    before=output['regression_before'];after=output['regression_after']
    if before!=after:raise ValueError('Changed test inputs')
    argv=output['argv']
    lines=output.get('lines',[])
    verbose=argv[1:]==['-m','unittest','discover','-v']
    observed=named_results(lines) if verbose and not output.get('truncated') else {}
    # A truncated tail is not a complete run. Positive claims require a
    # matching nonempty summary and exact unique names.
    counts=[int(m[1]) for line in lines if (m:=SUMMARY.match(line.strip()))]
    complete=bool(verbose and len(counts)==1 and counts[0]>0 and counts[0]==len(observed) and not output.get('truncated'))
    rows=[]
    links={}
    candidates=requirement_candidates(original,[(i,start,end) for i,(start,end) in enumerate(sections(original))])
    labels=explicit_requirement_labels(original,candidates)
    for step in steps:
        path=step['path']
        kind=test_kind(path)
        if not kind:continue
        file=safe_target(project,path,must_exist=True)
        if file.stat().st_size>220000:raise ValueError('Test source exceeds trace bound')
        data=file.read_bytes();fingerprint=hashlib.sha256(data).hexdigest()
        if before.get(path)!=fingerprint:raise ValueError('Test source not pinned in regression baseline')
        try:names=validate(path,data.decode('utf-8'))
        except ValueError:names=[]
        module=Path(path).with_suffix('').as_posix().replace('/','.')
        ids=[module+'.'+name if kind=='python' else name for name in names]
        status=[]
        for ident in ids:
            result=observed.get(ident,'not_observed') if kind=='python' else 'not_observed'
            if result=='passed' and (exit_code!=0 or not complete):result='pass_observed_in_unconfirmed_run'
            status.append({'test':ident,'status':result})
        row={'path':path,'sha256':fingerprint,'tests':status,'state':'written' if names else 'no_supported_tests'}
        rows.append(row)
        for group in re.findall(r'(?:^|[;\n])\s*verifies\s*:\s*([^;\n]+)',step['description'],re.I):
            for token in group.split(','):
                match=re.fullmatch(r'REQ[-_ ](\d+)',token.strip(),re.I)
                if match:
                    key='REQ-'+str(int(match[1]))
                    if key in labels:links.setdefault(key,[]).append(row)
    requirements=[]
    for key,anchor in labels.items():
        files=links.get(key,[])
        states=[t['status'] for f in files for t in f['tests']]
        status=('no_linked_test' if not files else 'failed' if 'failed' in states else
                'linked_tests_passed' if states and all(s=='passed' for s in states) and all(f['tests'] for f in files)
                else 'written_not_confirmed')
        requirements.append({'label':key,'anchor':anchor,'test_files':[f['path'] for f in files],'status':status})
    return {'schema':'deepthort-test-execution-v1','job_id':job['id'],'project':str(project),
            'spec_sha256':hashlib.sha256(original.encode()).hexdigest(),'source_hashes':before,
            'argv_sha256':hashlib.sha256(json.dumps(argv).encode()).hexdigest(),
            'output_sha256':hashlib.sha256('\n'.join(lines).encode()).hexdigest(),
            'exit_code':exit_code,'complete_named_run':complete,'files':rows,'requirements':requirements,
            'unlabelled_candidates':len(candidates)-len(labels),
            'counts':dict(Counter(t['status'] for f in rows for t in f['tests'])),
            'requirement_counts':dict(Counter(r['status'] for r in requirements)),
            'scope':'Exact observed unittest names; file-level declared links only, no proof of semantic coverage'}


def fingerprint(trace):
    return hashlib.sha256(json.dumps(trace,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def current_sources(project,hashes):
    try:
        if not isinstance(hashes,dict) or not 1<=len(hashes)<=10000:return False
        root=Path(project).resolve(strict=True)
        for rel,expected in hashes.items():
            target=safe_target(root,rel,must_exist=True)
            if target.stat().st_size>220000 or hashlib.sha256(target.read_bytes()).hexdigest()!=expected:return False
        return True
    except (OSError,ValueError,TypeError):return False

def receipt(trace,assessment,command):
    if (command[1:]!=['-m','unittest','discover','-v'] or not assessment.get('accepted')
        or assessment.get('assurance')!='python_tests_passed' or not trace.get('complete_named_run')
        or trace['exit_code']!=0
        or trace['argv_sha256']!=hashlib.sha256(json.dumps(command).encode()).hexdigest()):
        raise ValueError('Named test execution receipt is incomplete')
    if any(t['status']!='passed' for f in trace['files'] for t in f['tests']):
        raise ValueError('Approved behavioral tests lack passing named execution evidence')
    if any(f['state']!='written' for f in trace['files'] if test_kind(f['path'])=='python'):
        raise ValueError('Approved Python test file has no discoverable validated cases')
    return {'trace_sha256':fingerprint(trace),'spec_sha256':trace['spec_sha256'],
            'source_hashes':trace['source_hashes'],'counts':trace['counts'],
            'requirement_counts':trace['requirement_counts']}

def describe(trace,job,original):
    if (trace['job_id']!=job['id'] or trace['project']!=str(Path(job['project']).resolve())
        or trace['spec_sha256']!=hashlib.sha256(original.encode()).hexdigest()
        or not current_sources(job['project'],trace['source_hashes'])):
        return 'STALE — source or specification changed; rerun verification.'
    lines=['Current named test observations (not semantic coverage):']
    if job['state']=='complete':
        try:
            proof=json.loads(job['result'])['verification']['named_tests']
            if proof['trace_sha256']!=fingerprint(trace):raise ValueError('Trace differs')
            lines.append('Bound to completed verification receipt.')
        except (ValueError,KeyError,TypeError):lines.append('Diagnostic only; not bound to current accepted verification.')
    else:lines.append('Diagnostic only; job not complete.')
    lines.append('Test results: '+json.dumps(trace['counts'],sort_keys=True))
    lines.append('Requirement links: '+json.dumps(trace['requirement_counts'],sort_keys=True))
    for row in trace['requirements'][:50]:
        lines.append(row['label']+': '+row['status']+' — '+', '.join(row['test_files']))
    for f in trace['files'][:24]:
        for t in f['tests'][:30]:lines.append(t['test']+': '+t['status'])
    lines.append('Unlabelled requirement candidates: '+str(trace['unlabelled_candidates']))
    return '\n'.join(lines)
