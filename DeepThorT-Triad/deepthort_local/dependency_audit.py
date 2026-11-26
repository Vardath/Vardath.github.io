"""Reviewed dependency advisory lookup; no installation, source upload or fix."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

ENDPOINT='https://api.osv.dev/v1/querybatch'
MANIFESTS=('requirements.txt','package-lock.json')
MAX_BYTES=8_000_000
MAX_PACKAGES=500
MAX_RESPONSE=2_000_000
NAME=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')
NPM=re.compile(r'(?:@[a-z0-9][a-z0-9._-]{0,63}/)?[a-z0-9][a-z0-9._-]{0,127}')
VERSION=re.compile(r'[0-9][A-Za-z0-9.+!_-]{0,79}')
ADVISORY=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}')

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def linked(path):
    return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&0x400)

def read_manifest(root,name):
    path=root/name
    if linked(path) or not path.is_file():raise ValueError('Unsafe dependency manifest')
    before=path.stat()
    if before.st_size>MAX_BYTES:raise ValueError('Dependency manifest exceeds byte bound')
    with path.open('rb') as stream:raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES or len(raw)!=before.st_size or path.stat()!=before:
        raise ValueError('Dependency manifest changed during read')
    return raw

def strict_json(raw):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    def invalid(value):raise ValueError('Invalid JSON number')
    try:return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)
    except RecursionError as exc:raise ValueError('JSON exceeds nesting limit') from exc

def inventory(root):
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('Project directory required')
    packages=set(); manifests={}; omitted=0
    for name in MANIFESTS:
        path=root/name
        if not path.exists() and not path.is_symlink():continue
        raw=read_manifest(root,name)
        manifests[name]=hashlib.sha256(raw).hexdigest()
        if name=='requirements.txt':
            for line in raw.decode('utf-8-sig').splitlines():
                line=line.split('#',1)[0].strip()
                if not line:continue
                match=re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]{0,127})\s*==\s*([0-9][A-Za-z0-9.+!_-]{0,79})',line)
                if not match:
                    omitted+=1;continue
                package,version=match.groups()
                packages.add(('PyPI',re.sub(r'[-_.]+','-',package).lower(),version))
        else:
            obj=strict_json(raw)
            if not isinstance(obj,dict) or obj.get('lockfileVersion') not in (2,3) or not isinstance(obj.get('packages'),dict):
                raise ValueError('Only npm package-lock versions 2 and 3 supported')
            for location,entry in obj['packages'].items():
                if location=='':continue
                package=location.rsplit('node_modules/',1)[-1]
                if (not location.startswith('node_modules/') and '/node_modules/' not in location) or not isinstance(entry,dict):
                    omitted+=1;continue
                package=entry.get('name',package)
                version=entry.get('version')
                if (entry.get('link') or not isinstance(package,str) or not NPM.fullmatch(package) or
                    not isinstance(version,str) or not VERSION.fullmatch(version)):
                    omitted+=1;continue
                packages.add(('npm',package,version))
        if len(packages)>MAX_PACKAGES:raise ValueError('Dependency inventory exceeds package bound')
    if not packages:raise ValueError('No supported exact dependency versions found')
    return {'manifests':manifests,'packages':[list(x) for x in sorted(packages)],'omitted':omitted}

def review(root):
    root=Path(root).resolve(strict=True)
    observed=inventory(root)
    return {'schema':'janus-dependency-audit-v1','project':str(root),'inventory_sha':digest(observed),
            'count':len(observed['packages']),'expires_at':int(time.time())+1800},observed

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','project','inventory_sha','count','expires_at'}
        or plan['schema']!='janus-dependency-audit-v1' or plan['project']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800):
        raise ValueError('Invalid or expired audit approval')
    observed=inventory(root)
    if digest(observed)!=plan['inventory_sha'] or len(observed['packages'])!=plan['count']:
        raise ValueError('Reviewed dependency inventory changed')
    return observed

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def lookup(queries):
    # Explicitly approved fixed HTTPS endpoint; no inherited proxy or redirects.
    opener=build_opener(ProxyHandler({}),NoRedirect())
    request=Request(ENDPOINT,data=json.dumps({'queries':queries}).encode(),
                    headers={'Content-Type':'application/json','Accept':'application/json'},method='POST')
    with opener.open(request,timeout=30) as response:
        raw=response.read(MAX_RESPONSE+1)
    if len(raw)>MAX_RESPONSE:raise ValueError('Advisory response exceeds bound')
    return strict_json(raw)

def audit(root,plan,*,query=lookup):
    observed=validate(root,plan)
    packages=observed['packages']
    queries=[{'package':{'ecosystem':e,'name':n},'version':v} for e,n,v in packages]
    findings=[]; incomplete=0
    for start in range(0,len(queries),100):
        batch=queries[start:start+100]
        response=query(batch)
        results=response.get('results') if isinstance(response,dict) else None
        if not isinstance(results,list) or len(results)!=len(batch):
            raise ValueError('Incomplete advisory response')
        for package,result in zip(packages[start:start+len(batch)],results):
            if not isinstance(result,dict) or set(result)-{'vulns','next_page_token'}:
                raise ValueError('Unexpected advisory result')
            if result.get('next_page_token'):incomplete+=1
            vulns=result.get('vulns',[])
            if not isinstance(vulns,list):raise ValueError('Invalid advisory list')
            ids=set()
            for entry in vulns:
                ident=entry.get('id') if isinstance(entry,dict) else None
                if not isinstance(ident,str) or not ADVISORY.fullmatch(ident):raise ValueError('Invalid advisory ID')
                ids.add(ident)
            if ids:findings.append({'package':package,'advisories':sorted(ids)})
    # Do not interpret a response as current if project manifests changed.
    validate(root,plan)
    return {'schema':'janus-dependency-audit-result-v1','checked_at_unix':int(time.time()),
        'provider':ENDPOINT,'inventory_sha':plan['inventory_sha'],'manifest_sha256':observed['manifests'],
        'queried':len(packages),'omitted_entries':observed['omitted'],'paginated_results':incomplete,
        'findings':findings,'status':'advisories_found' if findings else ('inconclusive' if incomplete or observed['omitted'] else 'no_known_advisories_for_queried_versions'),
        'complete_project_security_verified':False,'python_transitive_dependencies_verified':False}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        result=audit(args.root,json.loads(args.plan))
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='no_known_advisories_for_queried_versions' else 1
    except (OSError,ValueError) as error:
        print(json.dumps({'schema':'janus-dependency-audit-result-v1','status':'blocked','reason':str(error)[:400]}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
