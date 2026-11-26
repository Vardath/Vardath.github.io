"""Bounded local Git observations, not command authority or test evidence."""
from __future__ import annotations
import hashlib
from pathlib import Path
import time
from .git_commit import _git,_text,OID
from .workspace import safe_target

TTL=900
MAX_CHANGES=512
MAX_COMMITS=20

def _safe_text(value,limit):
    return ''.join(c if c.isprintable() else ' ' for c in value)[:limit]

def _status(executable,root):
    raw=_git(executable,root,['status','--porcelain=v2','-z','--branch','--no-renames',
                              '--untracked-files=normal','--ignore-submodules=all'])
    headers={};changes=[]
    for field in raw.decode('utf-8','strict').split('\0'):
        if not field:continue
        if field.startswith('# '):
            k,sep,v=field[2:].partition(' ')
            if not sep:raise ValueError('Invalid Git status header')
            headers[k]=v
            continue
        if field.startswith('1 '):
            parts=field.split(' ',8)
            if len(parts)!=9:raise ValueError('Invalid ordinary Git status')
            xy,path=parts[1],parts[8]
        elif field.startswith('u '):
            parts=field.split(' ',10)
            if len(parts)!=11:raise ValueError('Invalid unmerged Git status')
            xy,path=parts[1],parts[10]
        elif field.startswith('? '):
            xy,path='??',field[2:]
        else:raise ValueError('Unsupported Git status record')
        if len(xy)!=2 or not path:raise ValueError('Invalid Git status record')
        if len(changes)>=MAX_CHANGES:raise ValueError('Change inventory exceeds review bound')
        changes.append({'xy':xy,'path':path})
    head=headers.get('branch.oid');name=headers.get('branch.head')
    if head!='(initial)' and not OID.fullmatch(head or ''):raise ValueError('Unknown Git HEAD')
    if not name:raise ValueError('Unknown Git branch')
    return {'head':None if head=='(initial)' else head,'branch':name,'changes':changes,
            'sha':hashlib.sha256(raw).hexdigest()}

def _history(executable,root,head,relative=None):
    if head is None:return []
    if not OID.fullmatch(head):raise ValueError('Invalid observed HEAD')
    args=['log','--no-show-signature','--no-decorate','--max-count='+str(MAX_COMMITS),
          '--format=%H%x00%P%x00%aI%x00%s','-z',head,'--']
    if relative is not None:args.append(relative)
    fields=_git(executable,root,args).decode('utf-8','strict').split('\0')
    if fields and fields[-1]=='':fields.pop()
    if len(fields)%4:raise ValueError('Invalid Git history record')
    result=[]
    for i in range(0,len(fields),4):
        oid,parents,date,subject=fields[i:i+4]
        if not OID.fullmatch(oid) or any(not OID.fullmatch(p) for p in parents.split()):
            raise ValueError('Invalid history commit identity')
        result.append({'commit':oid,'parents':parents.split(),'date':_safe_text(date,40),'subject':_safe_text(subject,240)})
    if len(result)>MAX_COMMITS:raise ValueError('History exceeds review bound')
    return result

def observe(executable,root,*,relative=None,exclude=()):
    root=Path(root).resolve(strict=True)
    if Path(_text(executable,root,['rev-parse','--show-toplevel'])).resolve(strict=True)!=root:
        raise ValueError('Choose the exact local Git repository root')
    if relative is not None:
        relative=safe_target(root,relative,must_exist=True).relative_to(root).as_posix()
        if relative.casefold() in {str(x).casefold() for x in exclude}:raise ValueError('Selected source is excluded from inspection')
    before=_status(executable,root)
    history=_history(executable,root,before['head'],relative)
    if _status(executable,root)!=before:raise ValueError('Repository changed during observation; refresh')
    return {'schema':'janus-git-observation-v1','project':str(root),'observed_at':int(time.time()),
            'head':before['head'],'branch':before['branch'],'changes':before['changes'],
            'history':history,'path':relative,'status_sha':before['sha']}

def shared(snapshot):
    if snapshot['path'] is not None:raise ValueError('Share a project-wide snapshot, not selected-file history')
    return {'project':snapshot['project'],'observed_at':snapshot['observed_at'],
            'branch':_safe_text(snapshot['branch'],80),'head':snapshot['head'],
            'commits':[{'commit':r['commit'],'date':r['date']} for r in snapshot['history'][:3]],
            'status_sha':snapshot['status_sha'],'historical_only':True,'authority':False}

def advisory(receipt,project,*,now=None):
    if not isinstance(receipt,dict):return []
    now=time.time() if now is None else now
    if receipt.get('project')!=str(Path(project).resolve()) or receipt.get('historical_only') is not True or receipt.get('authority') is not False:return []
    stamp=receipt.get('observed_at')
    if type(stamp) is not int or not 0<=now-stamp<TTL:return []
    return [{k:receipt[k] for k in ('observed_at','branch','head','commits','status_sha','historical_only','authority')}]
