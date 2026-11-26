"""Bounded Python static security indicators; no project code execution."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

MAX_FILES=1000
MAX_ENTRIES=12000
MAX_FILE=180000
MAX_BYTES=24_000_000
MAX_FINDINGS=200
SKIP={'state','backups','cache','vendor','site-packages','env','venv','node_modules','models','dist','build','__pycache__','runtime'}
SECRET_NAMES={'secrets.py','credentials.py','passwords.py','local_settings.py','settings_local.py'}

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def linked(path):
    s=path.lstat()
    return stat.S_ISLNK(s.st_mode) or bool(getattr(s,'st_file_attributes',0)&0x400)

def exclusions(values):
    if not isinstance(values,(tuple,list,set)) or len(values)>4096:
        raise ValueError('Invalid inspection exclusions')
    result=set()
    for value in values:
        if not isinstance(value,str):raise ValueError('Invalid excluded path')
        parts=value.replace('\\','/').casefold().split('/')
        if any(p in ('','.','..') or ':' in p or '\0' in p for p in parts):
            raise ValueError('Invalid excluded path')
        result.add('/'.join(parts))
    result=sorted(result)
    if len(json.dumps(result,ensure_ascii=True))>10000:raise ValueError('Inspection exclusions exceed review bound')
    return result

def excluded(relative,exclude):
    parts=relative.casefold().split('/')
    return (any(x.startswith('.') or x in SKIP for x in parts)
            or parts[-1] in SECRET_NAMES
            or any('/'.join(parts[:i]) in exclude for i in range(1,len(parts)+1)))

def identity(s):
    return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns

def read_source(path):
    if linked(path) or not path.is_file():raise ValueError('Unsafe source file')
    before=path.stat()
    if before.st_size>MAX_FILE:raise ValueError('Source file exceeds bound')
    with path.open('rb') as stream:raw=stream.read(MAX_FILE+1)
    if linked(path) or len(raw)!=before.st_size or identity(path.stat())!=identity(before):
        raise ValueError('Source changed during read')
    return raw

def inventory(root,exclude,*,inspect=None):
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('Project directory required')
    exclude=set(exclusions(exclude)); files={}; total=0; entries=0; omitted=0
    def fail(error):raise error
    for directory,dirs,names in os.walk(root,followlinks=False,onerror=fail):
        base=Path(directory);entries+=len(dirs)+len(names)
        if entries>MAX_ENTRIES:raise ValueError('Source inventory exceeds entry bound')
        kept=[]
        for name in sorted(dirs):
            path=base/name;rel=path.relative_to(root).as_posix()
            if excluded(rel,exclude) or linked(path):omitted+=1;continue
            kept.append(name)
        dirs[:]=kept
        for name in sorted(names):
            if not name.casefold().endswith('.py'):continue
            path=base/name;rel=path.relative_to(root).as_posix()
            if excluded(rel,exclude) or linked(path) or not path.is_file():
                omitted+=1;continue
            if path.stat().st_size>MAX_FILE:omitted+=1;continue
            if len(files)>=MAX_FILES:raise ValueError('Source inventory exceeds file bound')
            raw=read_source(path);total+=len(raw)
            if total>MAX_BYTES:raise ValueError('Source inventory exceeds total byte bound')
            files[rel]=hashlib.sha256(raw).hexdigest()
            if inspect is not None:inspect(rel,raw)
    if not files:raise ValueError('No eligible Python source')
    return {'sha':digest(files),'files':len(files),'bytes':total,'omitted':omitted}

def review(root,exclude=()):
    root=Path(root).resolve(strict=True)
    exclude=exclusions(exclude)
    return {'schema':'janus-source-security-v1','project':str(root),'exclude':exclude,
            'inventory':inventory(root,exclude),'expires_at':int(time.time())+1800}

def validate(root,plan):
    root=Path(root).resolve(strict=True)
    if (not isinstance(plan,dict) or set(plan)!={'schema','project','exclude','inventory','expires_at'}
        or plan['schema']!='janus-source-security-v1' or plan['project']!=str(root)
        or type(plan['expires_at']) is not int or not time.time()<plan['expires_at']<=time.time()+1800
        or exclusions(plan['exclude'])!=plan['exclude']):
        raise ValueError('Invalid or expired source scan approval')
    return root

def indicators(raw):
    """Lexical import aliases only; no data-flow or exploitability claim."""
    tree=ast.parse(raw)
    aliases={}
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            for a in n.names:aliases[a.asname or a.name.split('.')[0]]=a.name if a.asname else a.name.split('.')[0]
        elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module:
            for a in n.names:
                if a.name!='*':aliases[a.asname or a.name]=n.module+'.'+a.name
    def dotted(node):
        parts=[]
        while isinstance(node,ast.Attribute):
            parts.append(node.attr);node=node.value
        if not isinstance(node,ast.Name):return ''
        return '.'.join([aliases.get(node.id,node.id),*reversed(parts)])
    def literal(n,key,val):
        return any(k.arg==key and isinstance(k.value,ast.Constant) and k.value.value is val for k in n.keywords)
    rules=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call):continue
        name=dotted(n.func);rule=None
        if name in ('eval','exec','builtins.eval','builtins.exec'):rule='DYNAMIC_CODE'
        elif name=='os.system' or (name in ('subprocess.run','subprocess.Popen','subprocess.call','subprocess.check_call','subprocess.check_output') and literal(n,'shell',True)):rule='SHELL_EXECUTION'
        elif name in ('pickle.load','pickle.loads','dill.load','dill.loads','marshal.load','marshal.loads'):rule='UNSAFE_DESERIALIZATION'
        elif name in ('yaml.unsafe_load','yaml.full_load'):rule='YAML_REVIEW_LOADER'
        elif name=='yaml.load':
            loader=next((k.value for k in n.keywords if k.arg=='Loader'),n.args[1] if len(n.args)>1 else None)
            if loader is None or dotted(loader) not in ('yaml.SafeLoader','yaml.CSafeLoader'):rule='YAML_REVIEW_LOADER'
        elif name=='ssl._create_unverified_context' or (name.startswith(('requests.','httpx.')) and literal(n,'verify',False)):rule='TLS_VERIFICATION_DISABLED'
        elif name=='tempfile.mktemp':rule='UNSAFE_TEMP_NAME'
        if rule:rules.append({'line':n.lineno,'column':n.col_offset+1,'rule':rule})
    return sorted(rules,key=lambda x:(x['line'],x['column'],x['rule']))

def scan(root,plan):
    root=validate(root,plan);findings=[];count=0;unparsed=0
    def inspect(rel,raw):
        nonlocal count,unparsed
        try:items=indicators(raw)
        except (SyntaxError,ValueError,UnicodeError,RecursionError):
            unparsed+=1;return
        count+=len(items)
        findings.extend(dict(item,path=rel) for item in items[:max(0,MAX_FINDINGS-len(findings))])
    actual=inventory(root,plan['exclude'],inspect=inspect)
    if actual!=plan['inventory'] or inventory(root,plan['exclude'])!=actual:
        raise ValueError('Reviewed source inventory changed')
    validate(root,plan)
    return {'schema':'janus-source-security-result-v1','inventory':actual,
            'findings':findings,'finding_count':count,'truncated':count>len(findings),
            'unparsed_files':unparsed,'status':'potential_risks' if count else ('inconclusive' if unparsed or actual['omitted'] else 'no_indicators_in_scanned_python'),
            'source_executed':False,'complete_security_verified':False,
            'method':'limited Python AST indicators; no dataflow or alias-scope analysis'}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True);parser.add_argument('--plan',required=True)
    args=parser.parse_args()
    try:
        result=scan(args.root,json.loads(args.plan))
        print(json.dumps(result,sort_keys=True),flush=True)
        return 0 if result['status']=='no_indicators_in_scanned_python' else 1
    except (OSError,ValueError) as error:
        print(json.dumps({'schema':'janus-source-security-result-v1','status':'blocked','reason':str(error)[:400]}),flush=True)
        return 1

if __name__=='__main__':sys.exit(main())
