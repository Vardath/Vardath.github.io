"""Build a reviewed offline distribution bundle from exact game build and release notes."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from deepthort_local import typed_project_tool as guard
from deepthort_local import software_deployment as deploy

SCHEMA='janus-game-distribution-v1'
EXTRA=('artifact','.zip')

def checked(s):
    if not isinstance(s,dict) or set(s)!={'artifact','name','version','sha256','entrypoint','release_notes'}:
        raise ValueError('Expected exact game archive, name, version, hash, entrypoint and release notes')
    deploy.checked({k:s[k] for k in ('artifact','name','version','sha256')})
    entry=s['entrypoint']
    if not isinstance(entry,str) or not 1<=len(entry)<=220 or not entry.lower().endswith('.exe'):
        raise ValueError('Choose exact Windows executable archive member')
    from deepthort_local.installer_project import component
    for part in entry.split('/'):component(part)
    notes=s['release_notes']
    if not isinstance(notes,str) or not notes.strip() or len(notes)>8000 or any(ord(c)<32 and c not in '\n\t' for c in notes):
        raise ValueError('Choose bounded release notes')
    return s

def pe_header(raw):
    # Minimal PE identity check, not signature, architecture compatibility or safety proof.
    if len(raw)<64 or raw[:2]!=b'MZ':raise ValueError('Entrypoint lacks DOS signature')
    pos=struct.unpack_from('<I',raw,60)[0]
    if pos<64 or pos+24>len(raw) or raw[pos:pos+4]!=b'PE\0\0':
        raise ValueError('Entrypoint lacks PE signature')
    machine,sections=struct.unpack_from('<HH',raw,pos+4)
    optional,flags=struct.unpack_from('<HH',raw,pos+20)
    if machine not in (0x14c,0x8664,0xaa64) or not 1<=sections<=96 or not flags&2 or flags&0x2000 or optional<2 or pos+24+optional+40*sections>len(raw):
        raise ValueError('Entrypoint is not an identified PE executable')
    magic=struct.unpack_from('<H',raw,pos+24)[0]
    if magic!=(0x10b if machine==0x14c else 0x20b):raise ValueError('PE optional header mismatch')
    return {0x14c:'x86',0x8664:'x64',0xaa64:'arm64'}[machine]

def inspect(raw,s):
    checked(s)
    audit=deploy.inspect(raw,{k:s[k] for k in ('artifact','name','version','sha256')})
    members=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if s['entrypoint'] not in z.namelist():raise ValueError('Exact entrypoint absent')
        entry=z.getinfo(s['entrypoint'])
        if entry.is_dir():raise ValueError('Entrypoint must be a file')
        architecture=pe_header(z.read(entry))
        for i in z.infolist():
            if i.is_dir():continue
            digest=hashlib.sha256()
            with z.open(i) as f:
                for block in iter(lambda:f.read(65536),b''):digest.update(block)
            members.append({'path':i.filename,'bytes':i.file_size,'sha256':digest.hexdigest()})
    return {'schema':SCHEMA,'name':s['name'],'version':s['version'],'platform':'windows',
            'architecture':architecture,'entrypoint':s['entrypoint'],'build_sha256':s['sha256'],
            'files':sorted(members,key=lambda x:x['path']),'archive_verified':True,
            'pe_header_verified':True,'signature_verified':False,'gameplay_verified':False,
            'published_remotely':False,'store_accepted':False,'installed':False}

def bundle(raw,s):
    receipt=inspect(raw,s)
    name=s['name']+'-'+s['version']+'-windows.zip'
    # Preserve original build archive byte-for-byte, avoiding extraction or mutation.
    entries={name:raw,'RELEASE_NOTES.txt':(s['release_notes'].rstrip()+'\n').encode(),
             'JANUS-DISTRIBUTION.json':(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()}
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_STORED) as z:
        for n,data in entries.items():z.writestr(n,data)
    payload=buf.getvalue()
    if len(payload)>guard.MAX_OUTPUT:raise ValueError('Distribution bundle exceeds output limit')
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        if z.testzip() is not None or sorted(z.namelist())!=sorted(entries) or any(z.read(k)!=v for k,v in entries.items()):
            raise ValueError('Distribution bundle verification failed')
    return payload,receipt

def validate(root,plan):
    s,dst,src=guard.validate(root,plan,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    if plan['guards'][1]['expected']!=s['sha256'] or dst.name!=s['name']+'-'+s['version']+'-distribution.zip':
        raise ValueError('Exact build digest and versioned distribution destination required')
    return s,dst,src

def review(root,source,output,exclude=()):
    plan,s=guard.review(root,source,output,exclude,schema=SCHEMA,checked=checked,output_suffix='.zip',extra=EXTRA)
    _,_,src=validate(root,plan)
    _,receipt=bundle(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    return plan,dict(s,observations=receipt,scope='Prepare new offline Windows game distribution archive with exact original build, release notes, per-file digests and bounded PE header check. No execution, installation, remote transfer, signature or store acceptance.')

def execute(root,plan):
    s,dst,src=validate(root,plan)
    payload,receipt=bundle(guard.exact(src,plan['guards'][1],guard.MAX_INPUT),s)
    digest=guard.publish(payload,dst,lambda:validate(root,plan))
    return {'status':'game_distribution_bundle_prepared','output':plan['output'],'sha256':digest,**receipt}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--plan',required=True);a=p.parse_args()
    try:print(json.dumps(execute(a.root,json.loads(a.plan)),sort_keys=True),flush=True);return 0
    except Exception as e:
        print(json.dumps({'status':'blocked_or_failed','error_type':type(e).__name__,'reason':'Reviewed game distribution preparation failed'}),flush=True);return 1
if __name__=='__main__':sys.exit(main())
