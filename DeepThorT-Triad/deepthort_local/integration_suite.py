"""Reviewed local Python unittest integration suites with exact source receipts.

Suite designation is chosen by the user, not a claim about test semantics.
Tests run with ordinary user rights inside the existing capped JANUS process.
This is not a sandbox. No automatic installation, generated shell commands,
or claim of complete project acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
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
def fingerprint(root):
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
            files[p.relative_to(root).as_posix()]=sha(raw);total+=len(raw)
    if not files:raise ValueError('No eligible project source')
    return {'sha':sha(json.dumps(files,sort_keys=True,separators=(',',':')).encode()),
            'files':len(files),'bytes':total}
def review(root,suite):
    root=root_for(root);suite_path(root,suite)
    observed=fingerprint(root)
    return {'schema':'janus-integration-suite-v1','project':str(root),'suite':suite,
            'fingerprint':observed,'expires_at':int(time.time())+1800}
def validate(root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','project','suite','fingerprint','expires_at'} or plan['schema']!='janus-integration-suite-v1':
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
def run(root,plan):
    root,suite=validate(root,plan)
    # Explicit trusted project execution after review; no model-authored argv.
    sys.path.insert(0,str(root))
    try:
        tests=unittest.TestLoader().discover(str(suite),pattern='test_*.py')
        result=unittest.TextTestRunner(verbosity=2,resultclass=CountedResult).run(tests)
    finally:
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
    return {'schema':'janus-integration-result-v1','suite':plan['suite'],'source':plan['fingerprint'],
            'source_stable':stable,'counts':counts,'status':status,'full_application_verified':False,
            'security_sandbox':False}
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
