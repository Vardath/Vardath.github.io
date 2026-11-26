"""Versioned, non-installable self-update preparation for the V70 boundary."""
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import zipfile
from .agent_contract import canonical_sha
from .self_development import observe,_candidate,TARGET

PROBE=Path(__file__).with_name('self_update_probe.py')
MAX_ARCHIVE=200000

def _sha(raw):return hashlib.sha256(raw).hexdigest()

def _read(path,limit):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:
        raise ValueError('Missing, linked or oversized staged update member')
    raw=path.read_bytes()
    if len(raw)>limit:raise ValueError('Staged update member changed size')
    return raw

def _snapshot(root,state,body):
    observed=observe(root)
    if not observed or body['state']!='staged' or observed['key']!=body['key'] or body['authority'] is not False:
        raise ValueError('No current independently reviewed self-update candidate')
    candidate=_candidate(observed,json.dumps({'replacement':body['candidate']['replacement']}))
    if body['review']['accepted'] is not True or body['review']['candidate_sha']!=candidate['candidate_sha'] or body['candidate']['candidate_sha']!=candidate['candidate_sha']:
        raise ValueError('Independent review does not match candidate')
    parent=Path(state)/'self-development'
    folder=parent/body['key']
    if parent.is_symlink() or folder.is_symlink() or not folder.is_dir():
        raise ValueError('Invalid staged candidate folder')
    manifest=json.loads(_read(folder/'manifest.json',32000))
    if any(manifest.get(k)!=v for k,v in body.items()) or manifest.get('installation_authorized') is not False or manifest.get('runtime_verified') is not False:
        raise ValueError('Staged review manifest changed')
    baseline=_read(folder/'baseline.py.txt',32000)
    new=_read(folder/'candidate.py.txt',32000)
    if baseline!=observed['source'].encode('utf-8') or new!=candidate['source'].encode('utf-8'):
        raise ValueError('Staged source bytes differ from exact reviewed source')
    return observed,candidate,folder,baseline,new

def _probe(python,folder,stopped):
    if stopped():return None
    args=[str(Path(python).resolve(strict=True)),'-I','-B',str(PROBE.resolve(strict=True)),str(folder)]
    proc=subprocess.Popen(args,cwd=str(folder),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,shell=False,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    end=time.monotonic()+30
    try:
        while True:
            if stopped() or time.monotonic()>=end:
                proc.kill();proc.communicate(timeout=5)
                if stopped():return None
                raise ValueError('Isolated diagnostic probe timed out')
            try:
                out,err=proc.communicate(timeout=.2)
                break
            except subprocess.TimeoutExpired:continue
        if proc.returncode!=0 or len(out)>8192:
            raise ValueError('Isolated diagnostic probe did not pass')
        return json.loads(out)
    finally:
        if proc.poll() is None:
            proc.kill();proc.communicate(timeout=5)

def _verify_zip(path,expected,baseline,new):
    raw=_read(path,MAX_ARCHIVE)
    with zipfile.ZipFile(io.BytesIO(raw),'r') as z:
        if sorted(z.namelist())!=['baseline.py.txt','candidate.py.txt','update-manifest.json']:
            raise ValueError('Unexpected update package members')
        if any(i.file_size>32000 for i in z.infolist()) or z.testzip() is not None:
            raise ValueError('Invalid update package')
        if json.loads(z.read('update-manifest.json'))!=expected or z.read('baseline.py.txt')!=baseline or z.read('candidate.py.txt')!=new:
            raise ValueError('Update package bytes differ')
    return _sha(raw)

def prepare(root,state,body,stopped,*,python):
    if stopped():return None
    observed,candidate,folder,baseline,new=_snapshot(root,state,body)
    request={'old':observed['evidence']['observed'],'new':candidate['replacement'],
             'caps':observed['evidence']['caps'],'baseline_sha':_sha(baseline),'candidate_sha':_sha(new)}
    # Separate isolated copy, no live state or source is mounted into the test.
    with tempfile.TemporaryDirectory(prefix='probe-',dir=folder) as tmp:
        work=Path(tmp)
        (work/'baseline.py.txt').write_bytes(baseline);(work/'candidate.py.txt').write_bytes(new)
        (work/'probe.json').write_text(json.dumps(request),encoding='utf-8')
        result=_probe(python,work,stopped)
        if result is None:return None
        expected={'schema':'diagnostic-probe-v1','baseline_sha':request['baseline_sha'],
                  'candidate_sha':request['candidate_sha'],'cases_passed':8,
                  'assurance':'isolated_formatter_runtime_only'}
        if result!=expected:raise ValueError('Probe result does not match exact candidate')
        # Exercise forward and rollback bytes against a separate scratch file.
        scratch=work/'rollback-test.py.txt';scratch.write_bytes(baseline)
        if _sha(scratch.read_bytes())!=request['baseline_sha']:raise ValueError('Baseline copy failed')
        scratch.write_bytes(new)
        if _sha(scratch.read_bytes())!=request['candidate_sha']:raise ValueError('Forward copy failed')
        scratch.write_bytes(baseline)
        if _sha(scratch.read_bytes())!=request['baseline_sha']:raise ValueError('Rollback copy failed')
    if stopped():return None
    _snapshot(root,state,body)
    manifest={'schema':'deepthort-self-update-preparation-v1','version':'diagnostic-'+candidate['candidate_sha'][:16],
              'target':TARGET,'scope_sha':observed['key'],'review_sha':canonical_sha(body['review']),
              'baseline_sha':request['baseline_sha'],'candidate_sha':request['candidate_sha'],
              'runtime_probe':result,'rollback_bytes_verified':True,'full_application_verified':False,
              'installation_authorized':False,'installer':False}
    archive=folder/(manifest['version']+'.zip')
    if not archive.exists():
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('baseline.py.txt',baseline);z.writestr('candidate.py.txt',new)
            z.writestr('update-manifest.json',json.dumps(manifest,sort_keys=True))
        if stopped():return None
        with archive.open('xb') as stream:stream.write(buffer.getvalue())
    archive_sha=_verify_zip(archive,manifest,baseline,new)
    if stopped():return None
    _snapshot(root,state,body)
    return {'version':manifest['version'],'package':archive.name,'package_sha':archive_sha,'manifest':manifest}
