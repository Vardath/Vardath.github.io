"""Reviewed local Python unittest integration suites with exact source receipts.

Suite designation is chosen by the user, not a claim about test semantics.
Tests run with ordinary user rights inside the existing capped JANUS process.
This is not a sandbox. No automatic installation, generated shell commands,
or claim of complete project acceptance.
"""
from __future__ import annotations
import argparse
import cProfile
import dis
import math
import pstats
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import types
import unittest

MAX_ENTRIES=12000
MAX_FILES=4000
MAX_FILE=8_000_000
MAX_BYTES=128_000_000
SKIP={'.git','.venv','venv','node_modules','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache'}
SUFFIXES={'.py','.pyi','.json','.toml','.ini','.cfg','.yaml','.yml','.xml','.csv','.sql','.txt','.md','.html','.css','.js','.ts','.env','.lock','.db','.sqlite','.sqlite3'}
SUITES=('tests/integration','integration_tests','tests')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def linked(p):
    if p.is_symlink() or getattr(p,'is_junction',lambda:False)():return True
    # Reparse point fallback for older Python on Windows.
    return bool(getattr(p.lstat(),'st_file_attributes',0)&0x400)
def root_for(root):
    p=Path(root).resolve(strict=True)
    if not p.is_dir():raise ValueError('Project folder required')
    return p
def suite_path(root,suite):
    if suite not in SUITES:raise ValueError('Unsupported integration suite directory')
    p=root
    for part in suite.split('/'):
        p=p/part
        if linked(p):raise ValueError('Linked suite paths are not eligible')
    if not p.is_dir():raise ValueError('Integration suite directory is missing')
    return p
def fingerprint(root,*,observe=None):
    root=root_for(root)
    files={};entries=0;total=0
    def failed(error):raise error
    for directory,dirs,names in os.walk(root,followlinks=False,onerror=failed):
        base=Path(directory)
        entries+=len(dirs)+len(names)
        if entries>MAX_ENTRIES:raise ValueError('Project exceeds bounded integration inventory')
        for name in sorted(dirs):
            p=base/name
            if name not in SKIP and linked(p):raise ValueError('Linked source directory in test scope')
        dirs[:]=sorted(n for n in dirs if n not in SKIP)
        for name in sorted(names):
            p=base/name
            if p.suffix.casefold() not in SUFFIXES and name not in ('Dockerfile','Makefile'):continue
            if linked(p) or not p.is_file():raise ValueError('Unsafe source in integration scope')
            st=p.stat()
            if st.st_size>MAX_FILE or len(files)>=MAX_FILES or total+st.st_size>MAX_BYTES:
                raise ValueError('Integration source fingerprint exceeds bound')
            with p.open('rb') as stream:raw=stream.read(MAX_FILE+1)
            if len(raw)!=st.st_size or p.stat().st_mtime_ns!=st.st_mtime_ns:
                raise ValueError('Source changed during fingerprint')
            relative=p.relative_to(root).as_posix()
            files[relative]=sha(raw);total+=len(raw)
            if observe is not None:observe(relative,raw)
    if not files:raise ValueError('No eligible project source')
    return {'sha':sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
            'files':len(files),'bytes':total}
def review(root,suite,*,coverage=False,profile=False):
    if coverage and profile:raise ValueError('Choose separate coverage or profiling runs')
    root=root_for(root);suite_path(root,suite)
    observed=fingerprint(root)
    return {'schema':'janus-integration-coverage-v1' if coverage else ('janus-integration-profile-v1' if profile else 'janus-integration-suite-v1'),'project':str(root),'suite':suite,
            'fingerprint':observed,'expires_at':int(time.time())+1800}
def validate(root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','project','suite','fingerprint','expires_at'} or plan['schema'] not in ('janus-integration-suite-v1','janus-integration-coverage-v1','janus-integration-profile-v1'):
        raise ValueError('Invalid integration review')
    if type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Integration review expired')
    root=root_for(root)
    if str(root)!=plan['project']:raise ValueError('Reviewed workspace changed')
    suite=suite_path(root,plan['suite'])
    if fingerprint(root)!=plan['fingerprint']:raise ValueError('Reviewed source or tests changed')
    return root,suite
class CountedResult(unittest.TextTestResult):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw);self.passed=0
    def addSuccess(self,test):
        super().addSuccess(test);self.passed+=1
COVERAGE_MAX_FILE=1_000_000
COVERAGE_MAX_BYTES=24_000_000
COVERAGE_MAX_FILES=1000
COVERAGE_MAX_DETAILS=100
COVERAGE_TEST_DIRS={'tests','integration_tests','test','testing'}
COVERAGE_SKIP_DIRS={'vendor','site-packages','state','backups','dist','build','models','runtime','env'}
NON_LINE_OPS={'RESUME','RETURN_GENERATOR','COPY_FREE_VARS','MAKE_CELL','CACHE','EXTENDED_ARG'}

def executable_lines(code):
    """Conservative bytecode line-table denominator, not coverage.py semantics."""
    lines=set();stack=[code]
    while stack:
        current=stack.pop()
        lines.update(ins.starts_line for ins in dis.get_instructions(current)
                     if ins.starts_line is not None and ins.starts_line>0 and ins.opname not in NON_LINE_OPS)
        stack.extend(c for c in current.co_consts if isinstance(c,types.CodeType))
    return lines

class LineCoverage:
    def __init__(self,root):
        self.root=root
        self.files={};self.hits={};self.lookup={};self.omitted=0;self.bytes=0
        self.skipped=0
    def observe(self,relative,raw):
        path=Path(relative)
        if path.suffix.casefold()!='.py':return
        parts=[part.casefold() for part in path.parts]
        if (any(x.startswith('.') or x in COVERAGE_TEST_DIRS or x in COVERAGE_SKIP_DIRS for x in parts[:-1])
                or parts[-1].startswith('test_') or parts[-1].endswith('_test.py')):
            self.skipped+=1;return
        if (len(raw)>COVERAGE_MAX_FILE or len(self.files)>=COVERAGE_MAX_FILES
                or self.bytes+len(raw)>COVERAGE_MAX_BYTES):
            self.omitted+=1;return
        self.bytes+=len(raw)
        absolute=str(self.root/path)
        try:lines=executable_lines(compile(raw,absolute,'exec',dont_inherit=True,optimize=sys.flags.optimize))
        except (SyntaxError,ValueError,UnicodeError,RecursionError):
            self.omitted+=1;return
        if not lines:return
        self.files[relative]=lines;self.hits[relative]=set()
        self.lookup[os.path.normcase(os.path.abspath(absolute))]=relative
    def trace(self,frame,event,arg):
        # Do not trace library/test code, other threads or child processes.
        if event!='call':return None
        filename=frame.f_code.co_filename
        if not os.path.isabs(filename):return None
        relative=self.lookup.get(os.path.normcase(os.path.abspath(filename)))
        if relative is None:return None
        eligible=self.files[relative];hits=self.hits[relative]
        def local(frame,event,arg):
            if event=='line' and frame.f_lineno in eligible:hits.add(frame.f_lineno)
            return local
        return local
    def report(self,*,valid,trace_intact):
        total=sum(len(x) for x in self.files.values())
        hit=sum(len(x) for x in self.hits.values())
        details=[]
        for path,lines in self.files.items():
            missing=sorted(lines-self.hits[path])
            details.append({'path':path,'executable_lines':len(lines),'covered_lines':len(self.hits[path]),
                            'missing_lines':missing[:40],'missing_line_count':len(missing)})
        details.sort(key=lambda r:(-r['missing_line_count'],r['path']))
        reliable=valid and trace_intact and total>0
        return {'method':'Python bytecode line-table / current-thread trace; approximate statement-line coverage',
                'status':'measured' if reliable and not self.omitted else ('partial' if reliable else 'inconclusive'),
                'covered_lines':hit,'executable_lines':total,
                'percent':round(100*hit/total,2) if reliable else None,
                'source_files':len(self.files),'omitted_source_files':self.omitted,'excluded_python_files':self.skipped,
                'details':details[:COVERAGE_MAX_DETAILS],'details_truncated':len(details)>COVERAGE_MAX_DETAILS,
                'branch_coverage':False,'child_process_coverage':False,'other_thread_coverage':False,
                'trace_intact':trace_intact,'complete_application_verified':False}

PROFILE_MAX_FUNCTIONS=50
PROFILE_MAX_FILES=4000

def profile_report(profiler,root,eligible,elapsed,cpu,*,valid,intact):
    """Observed deterministic profiler times, not production benchmark timings."""
    rows=[]
    for (filename,line,name),(primitive,calls,self_time,cumulative,_) in pstats.Stats(profiler).stats.items():
        if not os.path.isabs(filename):continue
        rel=eligible.get(os.path.normcase(os.path.abspath(filename)))
        if rel is None:continue
        if not all(math.isfinite(v) and v>=0 for v in (self_time,cumulative)):continue
        rows.append({'path':rel,'line':line,'function':name[:160],
                     'calls':calls,'primitive_calls':primitive,
                     'self_seconds':round(self_time,9),'cumulative_seconds':round(cumulative,9)})
    rows.sort(key=lambda r:(-r['self_seconds'],-r['cumulative_seconds'],r['path'],r['line'],r['function']))
    reliable=bool(valid and intact and rows)
    return {'method':'cProfile deterministic current-thread function profiling (instrumented wall time)',
            'status':'measured' if reliable else 'inconclusive',
            'elapsed_seconds':round(elapsed,6),'process_cpu_seconds':round(cpu,6),
            'observed_project_functions':len(rows),'eligible_source_files':len(eligible),
            'hotspots':rows[:PROFILE_MAX_FUNCTIONS],'details_truncated':len(rows)>PROFILE_MAX_FUNCTIONS,
            'profile_intact':intact,'other_thread_function_profile':False,'child_process_profile':False,
            'production_benchmark':False,'complete_application_verified':False,
            'timing_scope':'test discovery plus execution; process CPU includes other threads; profiler overhead and resource caps affect measurements'}

def run(root,plan):
    root,suite=validate(root,plan)
    coverage=None
    if plan['schema']=='janus-integration-coverage-v1':
        coverage=LineCoverage(root)
        if fingerprint(root,observe=coverage.observe)!=plan['fingerprint']:
            raise ValueError('Reviewed source changed during coverage preparation')
        if not coverage.files:raise ValueError('No eligible application Python bytecode lines for coverage')
    profiler=None;profile_paths={}
    if plan['schema']=='janus-integration-profile-v1':
        def profile_source(relative,raw):
            parts=Path(relative).parts
            if (Path(relative).suffix.casefold()=='.py' and not any(x.startswith('.') or x.casefold() in COVERAGE_TEST_DIRS|COVERAGE_SKIP_DIRS for x in parts[:-1])
                    and not parts[-1].casefold().startswith('test_') and not parts[-1].casefold().endswith('_test.py')):
                if len(profile_paths)>=PROFILE_MAX_FILES:raise ValueError('Profiler source inventory exceeds bound')
                profile_paths[os.path.normcase(os.path.abspath(root/relative))]=relative
        if fingerprint(root,observe=profile_source)!=plan['fingerprint']:
            raise ValueError('Reviewed source changed during profiler preparation')
        if not profile_paths:raise ValueError('No eligible application Python source for profiling')
        profiler=cProfile.Profile()
    # Explicit trusted project execution after review; no model-authored argv.
    sys.path.insert(0,str(root))
    previous_trace=sys.gettrace()
    trace_hook=coverage.trace if coverage else None
    trace_intact=True;profile_intact=True
    previous_profile=sys.getprofile();elapsed=cpu=0.0
    start_wall=time.perf_counter();start_cpu=time.process_time()
    try:
        if profiler is not None:profiler.enable()
        if trace_hook is not None:sys.settrace(trace_hook)
        tests=unittest.TestLoader().discover(str(suite),pattern='test_*.py')
        result=unittest.TextTestRunner(verbosity=2,resultclass=CountedResult).run(tests)
    finally:
        if profiler is not None:
            profile_intact=sys.getprofile() is profiler
            profiler.disable()
            sys.setprofile(previous_profile)
        elapsed=max(0.0,time.perf_counter()-start_wall);cpu=max(0.0,time.process_time()-start_cpu)
        if trace_hook is not None:
            trace_intact=sys.gettrace() is trace_hook
            sys.settrace(previous_trace)
        try:sys.path.remove(str(root))
        except ValueError:pass
    stable=False
    try:stable=fingerprint(root)==plan['fingerprint']
    except (OSError,ValueError):pass
    counts={'run':result.testsRun,'passed':result.passed,'failed':len(result.failures),'errors':len(result.errors),
            'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),
            'unexpected_successes':len(result.unexpectedSuccesses)}
    ok=(stable and result.wasSuccessful() and result.testsRun>0 and result.passed==result.testsRun)
    status='passed' if ok else ('failed' if not result.wasSuccessful() else 'inconclusive')
    output={'schema':'janus-integration-result-v1','suite':plan['suite'],'source':plan['fingerprint'],
            'source_stable':stable,'counts':counts,'status':status,'full_application_verified':False,
            'security_sandbox':False}
    if coverage:
        output['coverage']=coverage.report(valid=ok,trace_intact=trace_intact)
        if ok and output['coverage']['status']=='inconclusive':output['status']='inconclusive'
    if profiler is not None:
        output['profile']=profile_report(profiler,root,profile_paths,elapsed,cpu,valid=ok,intact=profile_intact)
        if ok and output['profile']['status']=='inconclusive':output['status']='inconclusive'
    return output
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        result=run(args.root,json.loads(args.plan));print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='passed' else 1
    except (OSError,ValueError,ImportError) as exc:
        print(json.dumps({'schema':'janus-integration-result-v1','status':'blocked','reason':str(exc)[:500]}),flush=True)
        return 1
if __name__=='__main__':sys.exit(main())
