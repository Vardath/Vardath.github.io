"""Reviewed bounded GitHub pull-request evidence; no comments, approval or merge."""
from __future__ import annotations
import re
import socket
from .github_pull_request import _request,repository
from .website_monitor import PinnedHTTPS
MAX_FILES=30
MAX_PATCH=16000
MAX_TOTAL_PATCH=120000
def checked(s):
    if not isinstance(s,dict) or set(s)!={'repository','number','head_sha','base_sha'}:raise ValueError('Expected repository, PR number and exact head/base SHAs')
    repository(s['repository'])
    if type(s['number']) is not int or not 1<=s['number']<=2147483647:raise ValueError('Invalid pull request number')
    for k in ('head_sha','base_sha'):
        if not isinstance(s[k],str) or not re.fullmatch(r'[0-9a-f]{40}',s[k]):raise ValueError('Expected exact commit SHA')
    return dict(s)
def path(v):
    if not isinstance(v,str) or not 1<=len(v)<=300 or '\\' in v or any(ord(c)<32 or 0xd800<=ord(c)<=0xdfff for c in v) or any(p in ('','.','..') for p in v.split('/')):
        raise ValueError('Invalid provider file path')
    return v
def meta(d,s):
    if not isinstance(d,dict) or d.get('number')!=s['number'] or type(d.get('changed_files')) is not int or not 1<=d['changed_files']<=MAX_FILES:
        raise ValueError('Invalid PR or file count outside review bound')
    for side in ('head','base'):
        if not isinstance(d.get(side),dict) or d[side].get('sha')!=s[side+'_sha']:raise ValueError('Pull request commit identity differs')
    repo=d['base'].get('repo')
    if not isinstance(repo,dict) or str(repo.get('full_name','')).casefold()!=s['repository'].casefold():raise ValueError('Wrong base repository')
    if d.get('state') not in ('open','closed') or type(d.get('draft')) is not bool:raise ValueError('Invalid remote state')
    return {'head_sha':s['head_sha'],'base_sha':s['base_sha'],'changed_files':d['changed_files'],'state':d['state'],'draft':d['draft']}
def flags(name):
    p=name.casefold();base=p.split('/')[-1];result=[]
    if p.startswith('.github/workflows/') or base in ('jenkinsfile','.gitlab-ci.yml','azure-pipelines.yml'):result.append('build_or_ci_configuration')
    if base in ('package.json','package-lock.json','pyproject.toml','cargo.toml','cargo.lock','go.mod','go.sum','pom.xml','build.gradle','requirements.txt') or base.startswith('requirements-'):result.append('dependency_or_build_manifest')
    if base.startswith('test_') or base.endswith(('_test.py','.test.js','.test.ts','.spec.ts')) or '/tests/' in '/'+p:result.append('test_path_candidate')
    return result
def files(data,count):
    if not isinstance(data,list) or len(data)!=count:raise ValueError('Incomplete changed-file enumeration')
    seen=set();result=[];used=0
    for f in data:
        if not isinstance(f,dict):raise ValueError('Invalid file record')
        name=path(f.get('filename'));status=f.get('status')
        if name in seen or status not in ('added','removed','modified','renamed','copied','changed','unchanged'):raise ValueError('Invalid duplicate or status')
        seen.add(name);a=f.get('additions');d=f.get('deletions')
        if any(type(v) is not int or not 0<=v<=10000000 for v in (a,d)):raise ValueError('Invalid line counts')
        patch=f.get('patch');reason=None
        if patch is None:reason='provider_patch_missing'
        elif not isinstance(patch,str) or any(0xd800<=ord(c)<=0xdfff for c in patch):raise ValueError('Invalid patch')
        elif len(patch)>MAX_PATCH or used+len(patch)>MAX_TOTAL_PATCH:reason='patch_exceeds_review_bound';patch=None
        if patch is not None:used+=len(patch)
        item={'path':name,'status':status,'additions':a,'deletions':d,'patch':patch,
              'patch_omission_reason':reason,'review_indicators':flags(name),'patch_completeness_verified':False}
        if status=='renamed':item['previous_path']=path(f.get('previous_filename'))
        result.append(item)
    return result
def inspect(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise ValueError('Explicit approval required for remote read')
    s=checked(s);endpoint='/repos/'+s['repository']+'/pulls/'+str(s['number'])
    def get(path):
        return _request('GET',path,None,token,cancelled,resolver=resolver,connection=connection,expected=200)
    first,first_sha=get(endpoint);identity=meta(first,s)
    raw,files_sha=get(endpoint+'/files?per_page=30&page=1')
    changes=files(raw,identity['changed_files'])
    last,last_sha=get(endpoint)
    if meta(last,s)!=identity:raise ValueError('Remote pull request changed during review')
    return {'status':'pull_request_evidence_retrieved','repository':s['repository'],'number':s['number'],
            'url':'https://github.com/'+s['repository']+'/pull/'+str(s['number']),
            'identity':identity,'files':changes,
            'summary':{'additions':sum(f['additions'] for f in changes),'deletions':sum(f['deletions'] for f in changes),
                       'patches_present':sum(f['patch'] is not None for f in changes)},
            'provider_response_sha256':[first_sha,files_sha,last_sha],
            'scope':'Provider-reported changed-file and bounded patch evidence; metadata rechecked, no atomic remote snapshot or semantic review. Patch completeness and tests unverified.',
            'review_posted':False,'approved':False,'merged':False}
