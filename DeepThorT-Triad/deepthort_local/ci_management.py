"""Reviewed exact GitHub Actions workflow run and required-job inspection."""
from __future__ import annotations
import re
import socket
from .github_pull_request import _request,repository,literal
from .website_monitor import PinnedHTTPS

MAX_JOBS=30

def checked(s):
    if not isinstance(s,dict) or set(s)!={'repository','run_id','commit','required_jobs'}:
        raise ValueError('Expected repository, run ID, commit and required job names')
    repository(s['repository'])
    if type(s['run_id']) is not int or not 1<=s['run_id']<=2**53-1 or not isinstance(s['commit'],str) or not re.fullmatch(r'[a-f0-9]{40}',s['commit']):
        raise ValueError('Choose exact run ID and full lowercase SHA')
    jobs=s['required_jobs']
    if not isinstance(jobs,list) or not 1<=len(jobs)<=10:raise ValueError('Choose 1–10 required jobs')
    for name in jobs:literal(name,100)
    if len(set(jobs))!=len(jobs):raise ValueError('Duplicate required job')
    return s

def identity(s,r):
    if not isinstance(r,dict) or r.get('id')!=s['run_id'] or r.get('head_sha')!=s['commit']:
        raise ValueError('Workflow identity mismatch')
    repo=r.get('repository')
    if not isinstance(repo,dict) or str(repo.get('full_name','')).casefold()!=s['repository'].casefold():
        raise ValueError('Workflow repository mismatch')
    attempt=r.get('run_attempt')
    if type(attempt) is not int or attempt<1 or r.get('status') not in ('queued','in_progress','completed','requested','waiting','pending'):
        raise ValueError('Invalid run status or attempt')
    return (attempt,r['status'],r.get('conclusion'))

def assess(s,run,jobs,after):
    checked(s);first=identity(s,run)
    if identity(s,after)!=first:raise ValueError('Workflow changed during inspection')
    if not isinstance(jobs,dict) or not isinstance(jobs.get('jobs'),list):
        raise ValueError('Invalid jobs response')
    rows=jobs['jobs'];total=jobs.get('total_count')
    if type(total) is not int or total!=len(rows) or not 1<=total<=MAX_JOBS:
        raise ValueError('Incomplete or oversized job inventory')
    seen=set();ids=set();result=[]
    for j in rows:
        if not isinstance(j,dict) or j.get('run_id')!=s['run_id'] or j.get('head_sha')!=s['commit'] or j.get('run_attempt')!=first[0]:
            raise ValueError('Job identity mismatch')
        name=literal(j.get('name'),100);ident=j.get('id')
        if name in seen or type(ident) is not int or ident<=0 or ident in ids:
            raise ValueError('Ambiguous job inventory')
        if j.get('status') not in ('queued','in_progress','completed','waiting','pending','requested'):
            raise ValueError('Unknown job state')
        seen.add(name);ids.add(ident)
        result.append({'name':name,'id':ident,'status':j['status'],'conclusion':j.get('conclusion')})
    required=set(s['required_jobs'])
    green=(first[1:] == ('completed','success') and required<=seen and
           all(j['status']=='completed' and j['conclusion']=='success' for j in result if j['name'] in required))
    return {'schema':'janus-ci-evidence-v1','repository':s['repository'],'run_id':s['run_id'],
            'commit':s['commit'],'attempt':first[0],'status':first[1],'conclusion':first[2],
            'required_jobs':s['required_jobs'],'missing_jobs':sorted(required-seen),'jobs':result,
            'required_jobs_green':green,'merge_authorized':False,'deployment_authorized':False,
            'snapshot_only':True}

def inspect(s,token,cancelled=None,*,approved=False,resolver=socket.getaddrinfo,connection=PinnedHTTPS):
    if approved is not True:raise PermissionError('Explicit CI observation approval required')
    s=checked(s);base='/repos/'+s['repository']+'/actions/runs/'+str(s['run_id'])
    def get(path):
        return _request('GET',path,None,token,cancelled,resolver=resolver,connection=connection,expected=200)
    run,h1=get(base);attempt=identity(s,run)[0]
    jobs,h2=get(base+'/attempts/'+str(attempt)+'/jobs?per_page=30&page=1')
    after,h3=get(base)
    return dict(assess(s,run,jobs,after),response_sha256=[h1,h2,h3])
