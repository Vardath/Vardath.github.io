"""Reviewed, exact staged-tree Git commits for the existing JANUS action queue.

No staging, checkout, reset, push or remote operation. Git commit-tree and
compare-and-swap update-ref avoid ordinary commit hooks and unrelated changes.
Trusted local repository and Git executable required; not an OS sandbox.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

MAX_DIFF=64000
MAX_OUTPUT=128000
MAX_SECONDS=20
OID=re.compile(r'^[0-9a-f]{40}$|^[0-9a-f]{64}$')

def _git(executable,root,args,*,limit=MAX_OUTPUT):
    executable=Path(executable).resolve(strict=True)
    if not executable.is_file():raise ValueError('Git executable unavailable')
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
    with tempfile.TemporaryDirectory(prefix='janus-git-hooks-') as hooks, tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        command=[str(executable),'--no-pager','-c','core.hooksPath='+hooks,'-c','core.fsmonitor=false',
                 '-c','commit.gpgSign=false','-c','color.ui=false','-C',str(root),*args]
        proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,env=env,shell=False,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        deadline=time.monotonic()+MAX_SECONDS
        try:
            while proc.poll() is None:
                if time.monotonic()>deadline or os.fstat(out.fileno()).st_size>limit or os.fstat(err.fileno()).st_size>MAX_OUTPUT:
                    proc.kill();proc.wait(timeout=5)
                    raise ValueError('Git command exceeded bounded output or runtime')
                time.sleep(.04)
            if proc.returncode:
                err.seek(0)
                raise ValueError('Git refused operation: '+err.read(1800).decode('utf-8','replace').strip())
            out.seek(0);data=out.read(limit+1)
            if len(data)>limit:raise ValueError('Staged changes exceed review size; split into smaller commits')
            return data
        finally:
            if proc.poll() is None:proc.kill();proc.wait(timeout=5)

def _text(executable,root,args):
    return _git(executable,root,args).decode('utf-8','strict').strip()

def _identity(executable,root):
    root=Path(root).resolve(strict=True)
    actual=Path(_text(executable,root,['rev-parse','--show-toplevel'])).resolve(strict=True)
    if actual!=root:raise ValueError('Select the exact Git repository root, not a parent or subdirectory')
    for name in ('MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-apply','rebase-merge','sequencer','BISECT_LOG'):
        location=Path(_text(executable,root,['rev-parse','--git-path',name]))
        if not location.is_absolute():location=root/location
        if location.exists():raise ValueError('Finish the current merge, rebase or other Git operation first')
    ref=_text(executable,root,['symbolic-ref','HEAD'])
    if not ref.startswith('refs/heads/') or any(ord(c)<32 for c in ref):raise ValueError('A checked-out local branch is required')
    head=_text(executable,root,['rev-parse','--verify','HEAD^{commit}'])
    tree=_text(executable,root,['write-tree'])
    if not OID.fullmatch(head) or not OID.fullmatch(tree):raise ValueError('Invalid Git object identity')
    return {'root':str(root),'ref':ref,'head':head,'tree':tree}

def _snapshot(executable,root):
    identity=_identity(executable,root)
    old_tree=_text(executable,root,['rev-parse',identity['head']+'^{tree}'])
    if old_tree==identity['tree']:raise ValueError('No staged changes; stage intended files in Git first')
    diff=_git(executable,root,['diff','--no-ext-diff','--no-textconv','--no-renames','--binary','--full-index',
                              identity['head'],identity['tree'],'--'],limit=MAX_DIFF)
    if not diff:raise ValueError('No reviewable staged diff')
    if _identity(executable,root)!=identity:raise ValueError('Repository changed during review')
    return {**identity,'diff_sha':hashlib.sha256(diff).hexdigest()},diff

def preview(executable,root):
    identity,diff=_snapshot(executable,root)
    # Reject undecodable diffs instead of hiding bytes in a supposedly exact review.
    return {'identity':identity,'diff':diff.decode('utf-8','strict')}

def approved_plan(review,message):
    if not isinstance(message,str) or not 1<=len(message.strip())<=240 or any(ord(c)<32 for c in message):
        raise ValueError('Commit message must be a single nonempty line, at most 240 characters')
    identity=review['identity']
    if hashlib.sha256(review['diff'].encode('utf-8')).hexdigest()!=identity['diff_sha']:
        raise ValueError('Displayed diff changed')
    return {'schema':'janus-git-commit-v1','identity':identity,'message':message.strip(),
            'expires_at':int(time.time())+1800}

def apply(executable,root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','identity','message','expires_at'} or plan['schema']!='janus-git-commit-v1':
        raise ValueError('Invalid approved commit plan')
    if type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Commit review expired; review again')
    msg=plan['message']
    if not isinstance(msg,str) or not 1<=len(msg.strip())<=240 or any(ord(c)<32 for c in msg):raise ValueError('Invalid approved message')
    actual,diff=_snapshot(executable,root)
    if actual!=plan['identity']:raise ValueError('Branch, parent or staged tree changed since approval')
    # Write an immutable commit for the reviewed tree. No working file changes,
    # no hooks, no signing or model-supplied command flags.
    new=_text(executable,root,['commit-tree',actual['tree'],'-p',actual['head'],'-m',msg])
    if not OID.fullmatch(new):raise ValueError('Git did not return a commit object')
    if _identity(executable,root)!={k:v for k,v in actual.items() if k!='diff_sha'}:
        raise ValueError('Repository changed before branch update; commit object not published to branch')
    _git(executable,root,['update-ref','-m','JANUS reviewed local commit',actual['ref'],new,actual['head']])
    if _text(executable,root,['rev-parse','--verify',actual['ref']])!=new:
        raise ValueError('Branch changed after commit; inspect Git state before retry')
    return {'commit':new,'parent':actual['head'],'tree':actual['tree'],'branch':actual['ref'],
            'remote_published':False,'tests_verified':False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--git',required=True);parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        result=apply(args.git,args.root,json.loads(args.plan))
        print(json.dumps(result,sort_keys=True))
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError) as exc:
        parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
