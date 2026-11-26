"""Reviewed, exact staged-tree Git commits for the existing JANUS action queue.

Only explicit selected-file staging and reviewed non-force local branch operations; no reset, push or remote operation. Git commit-tree and
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

def _git(executable,root,args,*,limit=MAX_OUTPUT,index=None):
    executable=Path(executable).resolve(strict=True)
    if not executable.is_file():raise ValueError('Git executable unavailable')
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_LITERAL_PATHSPECS='1')
    if index is not None:env['GIT_INDEX_FILE']=str(index)
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

def _text(executable,root,args,*,index=None):
    return _git(executable,root,args,index=index).decode('utf-8','strict').strip()

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

def _selected_paths(root,paths):
    if not isinstance(paths,list) or not 1<=len(paths)<=12 or len(set(paths))!=len(paths):
        raise ValueError('Select one to twelve distinct project files')
    result=[]
    for name in paths:
        if not isinstance(name,str) or not 1<=len(name)<=200 or any(ord(c)<32 for c in name) or '\\' in name or ':' in name:
            raise ValueError('Invalid selected path')
        parts=name.split('/')
        if any(not x or x in ('.','..') or x.startswith('.') for x in parts):
            raise ValueError('Hidden or outside-project paths are not eligible')
        if any(x.casefold() in ('state','models','runtime','node_modules','__pycache__','backups') for x in parts):
            raise ValueError('Protected project path')
        path=Path(root)
        for part in parts:
            path=path/part
            if path.is_symlink():raise ValueError('Linked file is not eligible')
        if not path.is_file() or path.stat().st_size>MAX_DIFF:
            raise ValueError('Select existing bounded regular files')
        result.append(name)
    return sorted(result)

def _selected_snapshot(executable,root,paths):
    base=_identity(executable,root)
    old=_text(executable,root,['rev-parse',base['head']+'^{tree}'])
    if base['tree']!=old:raise ValueError('Index already contains staged changes; use staged commit review')
    paths=_selected_paths(Path(base['root']),paths)
    with tempfile.TemporaryDirectory(prefix='janus-git-index-') as tmp:
        index=Path(tmp)/'index'
        _git(executable,root,['read-tree',base['head']],index=index)
        _git(executable,root,['add','--',*paths],index=index)
        tree=_text(executable,root,['write-tree'],index=index)
        if not OID.fullmatch(tree) or tree==old:raise ValueError('No selected file changes')
        diff=_git(executable,root,['diff','--no-ext-diff','--no-textconv','--no-renames','--binary','--full-index',
                                  base['head'],tree,'--'],limit=MAX_DIFF)
        changed=_git(executable,root,['diff','--no-ext-diff','--no-renames','--name-only','-z',base['head'],tree,'--']).decode('utf-8','strict').split('\0')
        if not set(x for x in changed if x).issubset(paths):raise ValueError('Temporary index includes unselected paths')
    if _identity(executable,root)!=base:raise ValueError('Repository changed during selected-file review')
    return {**base,'selected_tree':tree,'paths':paths,'diff_sha':hashlib.sha256(diff).hexdigest()},diff

def preview_selected(executable,root,paths):
    identity,diff=_selected_snapshot(executable,root,paths)
    return {'identity':identity,'diff':diff.decode('utf-8','strict')}

def apply_selected(executable,root,plan):
    identity=plan['identity']
    actual,_=_selected_snapshot(executable,root,identity['paths'])
    if actual!=identity:raise ValueError('Selected files or repository changed since approval')
    base={k:v for k,v in actual.items() if k in ('root','head','ref','tree')}
    # Stage ONLY the reviewed existing files, against the clean original index.
    # Git's index lock protects its own write. Re-read exact tree before commit.
    _git(executable,root,['add','--',*actual['paths']])
    staged=_identity(executable,root)
    if staged!={**base,'tree':actual['selected_tree']}:
        raise ValueError('Index or files changed during staging; no commit made. Inspect staged changes.')
    reviewed={'schema':'janus-git-commit-v1','identity':{**staged,'diff_sha':actual['diff_sha']},
              'message':plan['message'],'expires_at':plan['expires_at']}
    return apply(executable,root,reviewed)

def branch_inventory(executable,root):
    identity=_identity(executable,root)
    raw=_git(executable,root,['for-each-ref','--format=%(refname)%00%(objectname)','refs/heads/'])
    branches=[]
    for line in raw.decode('utf-8','strict').splitlines():
        ref,oid=line.split('\0')
        if not ref.startswith('refs/heads/') or not OID.fullmatch(oid):raise ValueError('Invalid branch inventory')
        branches.append({'ref':ref,'commit':oid})
    if len(branches)>128:raise ValueError('Branch inventory exceeds review bound')
    if _identity(executable,root)!=identity:raise ValueError('Repository changed during branch inspection')
    return {'identity':identity,'branches':branches}

def branch_plan(executable,root,review,name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,79}',name):
        raise ValueError('Use a local branch name of up to 80 characters')
    ref='refs/heads/'+name
    _git(executable,root,['check-ref-format',ref])
    if branch_inventory(executable,root)!=review:raise ValueError('Branch inventory changed; review again')
    if ref in [x['ref'] for x in review['branches']]:raise ValueError('Branch already exists')
    return {'schema':'janus-git-branch-create-v1','identity':review['identity'],'ref':ref,
            'expires_at':int(time.time())+1800}

def apply_branch(executable,root,plan):
    if set(plan)!={'schema','identity','ref','expires_at'} or plan['schema']!='janus-git-branch-create-v1':
        raise ValueError('Invalid branch plan')
    if type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:raise ValueError('Branch review expired')
    actual=_identity(executable,root)
    if actual!=plan['identity']:raise ValueError('Repository changed since branch approval')
    ref=plan['ref']
    if not isinstance(ref,str) or not re.fullmatch(r'refs/heads/[A-Za-z0-9][A-Za-z0-9_./-]{0,79}',ref):
        raise ValueError('Only a named local branch may be created')
    _git(executable,root,['check-ref-format',ref])
    _git(executable,root,['update-ref','-m','JANUS reviewed branch creation',ref,actual['head'],'0'*len(actual['head'])])
    if _text(executable,root,['rev-parse','--verify',ref])!=actual['head']:
        raise ValueError('New branch changed after creation; inspect repository')
    return {'branch':ref,'commit':actual['head'],'checked_out':False,'remote_published':False}

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
    if 'selected_tree' in plan['identity']:
        return apply_selected(executable,root,plan)
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

def _local_ref(executable,root,name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./-]{0,79}',name):
        raise ValueError('Use an exact local branch name of up to 80 characters')
    ref='refs/heads/'+name
    _git(executable,root,['check-ref-format',ref])
    return ref

def _worktrees(executable,root):
    raw=_git(executable,root,['worktree','list','--porcelain','-z'])
    refs=[]
    for field in raw.decode('utf-8','strict').split('\0'):
        if field.startswith('branch '):
            ref=field[7:]
            if not ref.startswith('refs/heads/'):raise ValueError('Invalid worktree branch')
            refs.append(ref)
    return {'sha':hashlib.sha256(raw).hexdigest(),'refs':sorted(refs)}

def _clean(executable,root):
    return not _git(executable,root,['status','--porcelain=v1','-z','--untracked-files=all','--ignore-submodules=none'])

def _branch_snapshot(executable,root):
    review=branch_inventory(executable,root)
    return {'identity':review['identity'],'branches_sha':hashlib.sha256(json.dumps(review['branches'],sort_keys=True).encode()).hexdigest(),
            'branches':review['branches'],'worktrees':_worktrees(executable,root),'clean':_clean(executable,root)}

def _validate_operation(executable,root,review,operation,name,new_name):
    if operation not in ('switch','rename','delete'):raise ValueError('Unsupported local branch action')
    ref=_local_ref(executable,root,name)
    refs={row['ref']:row['commit'] for row in review['branches']}
    if ref not in refs:raise ValueError('Branch does not exist in reviewed local inventory')
    if ref==review['identity']['ref'] or ref in review['worktrees']['refs']:
        raise ValueError('Target is checked out in this or another worktree')
    new_ref=None
    if operation=='switch':
        if not review['clean']:raise ValueError('Switch requires clean tracked, staged and untracked workspace')
    elif operation=='rename':
        new_ref=_local_ref(executable,root,new_name)
        if new_ref in refs:raise ValueError('Destination branch already exists')
    else:
        # Never force-delete an unmerged branch. Require ancestry of exact HEAD,
        # then let native branch -d enforce its own additional protections.
        _git(executable,root,['merge-base','--is-ancestor',refs[ref],review['identity']['head']])
    return ref,refs[ref],new_ref

def branch_operation_plan(executable,root,review,operation,name,new_name=None):
    current=_branch_snapshot(executable,root)
    if current['identity']!=review['identity'] or current['branches']!=review['branches']:
        raise ValueError('Branch inventory changed; review again')
    ref,oid,new_ref=_validate_operation(executable,root,current,operation,name,new_name)
    return {'schema':'janus-git-branch-operation-v1','operation':operation,
            'identity':current['identity'],'branches_sha':current['branches_sha'],'worktrees':current['worktrees'],
            'clean':current['clean'],'ref':ref,'commit':oid,'new_ref':new_ref,
            'expires_at':int(time.time())+1800}

def apply_branch_operation(executable,root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','operation','identity','branches_sha','worktrees','clean','ref','commit','new_ref','expires_at'} or plan['schema']!='janus-git-branch-operation-v1':
        raise ValueError('Invalid branch operation plan')
    if type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:raise ValueError('Branch review expired')
    actual=_branch_snapshot(executable,root)
    if any(actual[k]!=plan[k] for k in ('identity','branches_sha','worktrees','clean')):
        raise ValueError('Repository, branches, worktrees or clean state changed since approval')
    operation=plan['operation']
    if not isinstance(plan['ref'],str) or not plan['ref'].startswith('refs/heads/'):raise ValueError('Invalid local branch')
    name=plan['ref'][11:]
    new_name=plan['new_ref'][11:] if isinstance(plan['new_ref'],str) and plan['new_ref'].startswith('refs/heads/') else None
    ref,oid,new_ref=_validate_operation(executable,root,actual,operation,name,new_name)
    if (ref,oid,new_ref)!=(plan['ref'],plan['commit'],plan['new_ref']):raise ValueError('Reviewed branch identity changed')
    if operation=='switch':
        _git(executable,root,['switch','--no-guess','--no-recurse-submodules','--no-overwrite-ignore',name])
        now=_identity(executable,root)
        if now['ref']!=ref or now['head']!=oid or not _clean(executable,root):
            raise ValueError('Switch outcome differs from review; inspect workspace, do not retry automatically')
    else:
        if operation=='rename':
            _git(executable,root,['branch','-m',name,new_name])
        else:
            _git(executable,root,['branch','-d',name])
        after=branch_inventory(executable,root)
        refs={row['ref']:row['commit'] for row in after['branches']}
        if after['identity']!=actual['identity'] or ref in refs or (new_ref is not None and refs.get(new_ref)!=oid):
            raise ValueError('Branch operation outcome differs from review; inspect repository')
    return {'operation':operation,'branch':ref,'commit':oid,'new_branch':new_ref,
            'remote_published':False,'working_tree_changed':operation=='switch','tests_verified':False}

def _worktree_rows(executable,root):
    raw=_git(executable,root,['worktree','list','--porcelain','-z'])
    rows=[];row=None
    for field in raw.decode('utf-8','strict').split('\0'):
        if field.startswith('worktree '):
            if row is not None:raise ValueError('Invalid worktree inventory')
            path=field[9:]
            if not Path(path).is_absolute() or any(ord(c)<32 for c in path):
                raise ValueError('Invalid worktree path')
            row={'path':str(Path(path).resolve()),'head':None,'ref':None,'locked':False,'prunable':False,'detached':False,'bare':False}
        elif not field:
            if row is not None:
                rows.append(row);row=None
        elif row is None:raise ValueError('Invalid worktree record')
        elif field.startswith('HEAD '):
            oid=field[5:]
            if not OID.fullmatch(oid):raise ValueError('Invalid worktree HEAD')
            row['head']=oid
        elif field.startswith('branch '):
            ref=field[7:]
            if not ref.startswith('refs/heads/'):raise ValueError('Invalid worktree ref')
            row['ref']=ref
        elif field=='detached':row['detached']=True
        elif field=='bare':row['bare']=True
        elif field=='locked' or field.startswith('locked '):row['locked']=True
        elif field=='prunable' or field.startswith('prunable '):row['prunable']=True
        else:raise ValueError('Unknown worktree record field')
    if row is not None:rows.append(row)
    if not 1<=len(rows)<=64 or len({r['path'] for r in rows})!=len(rows):
        raise ValueError('Worktree inventory exceeds bound or contains duplicate paths')
    return {'rows':rows,'sha':hashlib.sha256(raw).hexdigest()}

def worktree_inventory(executable,root):
    review=branch_inventory(executable,root)
    result={**review,'worktrees':_worktree_rows(executable,root)}
    if branch_inventory(executable,root)!=review:raise ValueError('Repository changed during worktree inspection')
    return result

def _real_directory(path):
    path=Path(path)
    if not path.is_absolute():raise ValueError('Choose an absolute directory')
    for part in (path,*path.parents):
        if part.is_symlink() or getattr(part,'is_junction',lambda:False)():
            raise ValueError('Linked directories are not eligible')
    actual=path.resolve(strict=True)
    if not actual.is_dir():raise ValueError('Directory is unavailable')
    return actual

def _overlap(a,b):
    return a==b or a in b.parents or b in a.parents

def _worktree_destination(review,parent,name):
    parent=_real_directory(parent)
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',name) or name.endswith('.') or name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        raise ValueError('Use a simple new directory name')
    path=parent/name
    if path.exists() or path.is_symlink() or getattr(path,'is_junction',lambda:False)():
        raise ValueError('Destination must not exist')
    if any(_overlap(path,Path(r['path'])) for r in review['worktrees']['rows']):
        raise ValueError('Destination overlaps an existing repository worktree')
    st=parent.stat()
    return {'path':str(path),'parent':str(parent),'parent_dev':st.st_dev,'parent_ino':st.st_ino}

def _removal_target(executable,root,review,path):
    if not isinstance(path,str):raise ValueError('Choose an exact linked worktree path')
    target=_real_directory(path)
    rows=review['worktrees']['rows']
    record=next((r for r in rows[1:] if r['path']==str(target)),None)
    if not record or target==Path(review['identity']['root']) or record['bare'] or record['locked'] or record['prunable'] or record['detached'] or not record['ref']:
        raise ValueError('Only an unlocked, existing, attached linked worktree other than the selected repository can be removed')
    if any(_overlap(target,Path(r['path'])) for r in rows if r['path']!=str(target)):
        raise ValueError('Worktree overlaps another registered worktree')
    dotgit=target/'.git'
    if dotgit.is_symlink() or not dotgit.is_file():raise ValueError('Expected a linked worktree metadata file')
    def common(where):
        return Path(_text(executable,where,['rev-parse','--path-format=absolute','--git-common-dir'])).resolve(strict=True)
    if common(root)!=common(target):raise ValueError('Worktree belongs to another repository')
    if _identity(executable,target)['head']!=record['head'] or _identity(executable,target)['ref']!=record['ref']:
        raise ValueError('Worktree identity changed')
    if _git(executable,target,['status','--porcelain=v1','-z','--untracked-files=all','--ignored=matching','--ignore-submodules=none']):
        raise ValueError('Removal requires no staged, modified, untracked or ignored files')
    return record

def worktree_plan(executable,root,review,operation,*,branch=None,parent=None,name=None,path=None):
    current=worktree_inventory(executable,root)
    if current!=review:raise ValueError('Worktree inventory changed; review again')
    if operation=='add':
        ref=_local_ref(executable,root,branch)
        refs={r['ref']:r['commit'] for r in current['branches']}
        if ref not in refs or ref in [r['ref'] for r in current['worktrees']['rows']]:
            raise ValueError('Choose an existing local branch not checked out in any worktree')
        dest=_worktree_destination(current,parent,name)
        target={'destination':dest,'ref':ref,'head':refs[ref]}
    elif operation=='remove':
        target=_removal_target(executable,root,current,path)
    else:raise ValueError('Unsupported worktree operation')
    return {'schema':'janus-git-worktree-v1','operation':operation,'identity':current['identity'],
            'inventory_sha':hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),
            'target':target,'expires_at':int(time.time())+1800}

def apply_worktree(executable,root,plan):
    if not isinstance(plan,dict) or set(plan)!={'schema','operation','identity','inventory_sha','target','expires_at'} or plan['schema']!='janus-git-worktree-v1':
        raise ValueError('Invalid worktree plan')
    if type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800:
        raise ValueError('Worktree review expired')
    actual=worktree_inventory(executable,root)
    if actual['identity']!=plan['identity'] or hashlib.sha256(json.dumps(actual,sort_keys=True).encode()).hexdigest()!=plan['inventory_sha']:
        raise ValueError('Repository or worktree inventory changed since approval')
    target=plan['target']
    if plan['operation']=='add':
        dest=target['destination']
        checked=worktree_plan(executable,root,actual,'add',branch=target['ref'][11:],parent=dest['parent'],name=Path(dest['path']).name)
        if checked['target']!=target:raise ValueError('Worktree destination or branch changed')
        path=Path(dest['path'])
        _git(executable,root,['worktree','add','--',str(path),target['ref'][11:]])
        after=worktree_inventory(executable,root)
        row=next((r for r in after['worktrees']['rows'] if r['path']==str(path)),None)
        if after['identity']!=actual['identity'] or not row or row['ref']!=target['ref'] or row['head']!=target['head']:
            raise ValueError('Worktree creation outcome differs; inspect repository, do not retry automatically')
    elif plan['operation']=='remove':
        checked=_removal_target(executable,root,actual,target['path'])
        if checked!=target:raise ValueError('Removal target changed')
        path=Path(target['path'])
        _git(executable,root,['worktree','remove','--',str(path)])
        after=worktree_inventory(executable,root)
        if path.exists() or after['identity']!=actual['identity'] or any(r['path']==str(path) for r in after['worktrees']['rows']) or after['branches']!=actual['branches']:
            raise ValueError('Worktree removal outcome differs; inspect repository')
    else:raise ValueError('Unsupported worktree operation')
    return {'operation':plan['operation'],'path':str(path),'branch':target['ref'],'commit':target['head'],
            'branch_deleted':False,'remote_published':False,'security_sandbox':False,'tests_verified':False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--git',required=True);parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        plan=json.loads(args.plan)
        schema=plan.get('schema')
        if schema=='janus-git-branch-create-v1':result=apply_branch(args.git,args.root,plan)
        elif schema=='janus-git-branch-operation-v1':result=apply_branch_operation(args.git,args.root,plan)
        elif schema=='janus-git-worktree-v1':result=apply_worktree(args.git,args.root,plan)
        else:result=apply(args.git,args.root,plan)
        print(json.dumps(result,sort_keys=True))
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError) as exc:
        parser.exit(1,str(exc)+'\n')

if __name__=='__main__':main()
