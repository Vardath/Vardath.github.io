"""Clean three-way merge proposal from actual Git unmerged index stages."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local.git_commit import _git,_text,OID
from deepthort_local.action_guards import snapshot_file
SCHEMA='janus-git-conflict-proposal-v1'
MAX_BYTES=64000
SUFFIXES={'.txt','.md','.py','.js','.ts','.json','.xml','.html','.css','.yaml','.yml','.toml','.ini','.c','.cpp','.h','.cs'}
def checked(s):
    if not isinstance(s,dict) or set(s)!={'path'} or not isinstance(s['path'],str) or Path(s['path']).suffix.casefold() not in SUFFIXES:
        raise ValueError('Select an unmerged text file')
    return s
def stages(root,s,exclude,git):
    root=Path(root).resolve(strict=True)
    if Path(_text(git,root,['rev-parse','--show-toplevel'])).resolve(strict=True)!=root:
        raise ValueError('Select the exact Git root')
    path=s['path'];guard.path_for(root,path,exclude,SUFFIXES,exists=True)
    data=_git(git,root,['ls-files','--unmerged','-z','--',path],limit=4096)
    found={}
    for entry in data.decode('utf-8','strict').split('\0'):
        if not entry:continue
        meta,name=entry.split('\t',1);mode,oid,stage=meta.split(' ')
        if name!=path or stage not in ('1','2','3') or stage in found or mode not in ('100644','100755') or not OID.fullmatch(oid):
            raise ValueError('Unsupported or ambiguous unmerged index stage')
        raw=_git(git,root,['cat-file','blob',oid],limit=MAX_BYTES)
        text=raw.decode('utf-8','strict')
        if '\0' in text or any(line.startswith(('<<<<<<<','|||||||','=======','>>>>>>>')) for line in text.splitlines()):
            raise ValueError('Binary or pre-conflicted source refused')
        found[stage]=({'stage':int(stage),'oid':oid,'mode':mode,'sha256':hashlib.sha256(raw).hexdigest()},raw)
    if set(found)!= {'1','2','3'} or len({v[0]['mode'] for v in found.values()})!=1:
        raise ValueError('Only three ordinary same-mode stages supported')
    return [found[k][0] for k in ('1','2','3')],[found[k][1] for k in ('1','2','3')]
def clean_merge(git,blobs):
    with tempfile.TemporaryDirectory(prefix='janus-merge-') as td:
        folder=Path(td)
        for name,raw in zip(('base.txt','ours.txt','theirs.txt'),blobs):(folder/name).write_bytes(raw)
        # Git exits nonzero on unresolved content overlap. Existing bounded
        # helper rejects it. Never choose ours/theirs automatically.
        result=_git(git,folder,['merge-file','--stdout','--','ours.txt','base.txt','theirs.txt'],limit=MAX_BYTES)
    if not result or b'\0' in result or any(line.startswith((b'<<<<<<<',b'|||||||',b'=======',b'>>>>>>>')) for line in result.splitlines()):
        raise ValueError('No clean nonempty merge proposal')
    result.decode('utf-8','strict')
    return result
def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.txt')
    git=shutil.which('git')
    if not git:raise ValueError('Git unavailable')
    git=str(Path(git).resolve(strict=True))
    plan['guards'].append(snapshot_file(git,kind='stat'))
    plan['stages'],blobs=stages(root,s,plan['exclude'],git)
    result=clean_merge(git,blobs)
    plan['result_sha256']=hashlib.sha256(result).hexdigest()
    if len(json.dumps(plan,ensure_ascii=True))>=4096:raise ValueError('Approval exceeds queue argument budget')
    return plan,dict(s,stages=plan['stages'],candidate=result.decode('utf-8'),scope='Clean three-way proposal only; no worktree, index, commit or merge-state changes.')
def validate(root,plan):
    if not isinstance(plan,dict) or set(plan).difference({'schema','root','source','output','exclude','guards','expires_at','stages','result_sha256'}) or len(plan.get('guards',[]))!=2:
        raise ValueError('Invalid merge review')
    core={k:v for k,v in plan.items() if k not in ('stages','result_sha256')}
    core['guards']=plan['guards'][:1]
    s,dst,_=guard.validate(root,core,schema=SCHEMA,checked=checked,output_suffix='.txt')
    git=shutil.which('git')
    if not git or snapshot_file(Path(git).resolve(strict=True),kind='stat')!=plan['guards'][1]:
        raise ValueError('Reviewed Git executable changed')
    observed,blobs=stages(root,s,core['exclude'],git)
    if observed!=plan['stages']:raise ValueError('Reviewed index stages changed')
    return s,dst,git,blobs
def execute(root,plan):
    s,dst,git,blobs=validate(root,plan);data=clean_merge(git,blobs)
    if hashlib.sha256(data).hexdigest()!=plan['result_sha256']:raise ValueError('Merge proposal differs from preview')
    digest=guard.publish(data,dst,lambda:validate(root,plan))
    return {'status':'clean_three_way_proposal','output':plan['output'],'sha256':digest,
        'path':s['path'],'stages':plan['stages'],'index_modified':False,'worktree_modified':False,'merge_committed':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked','error_type':type(e).__name__,'reason':'No clean reviewed merge proposal; inspect conflict and index state'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
