"""Pinned multimedia checkpoint and local install receipts (not inference proof)."""
import json
import re
from pathlib import Path
from .triad_profiles import ROOT, PROFILES, RUNTIME_VERSION, runtime_path, installed_files, smoke_verified

REPO = 'OpenVINO/stable-diffusion-v1-5-int8-ov'
REVISION = 'cb4df51ea6b332962d8df636d6a4e0209c2f51e9'
LICENSE = 'creativeml-openrail-m'
MAX_BYTES = 3_000_000_000
FILES = frozenset({
    'README.md', 'model_index.json', 'feature_extractor/preprocessor_config.json',
    'safety_checker/config.json', 'safety_checker/model.safetensors',
    'scheduler/scheduler_config.json',
    *('tokenizer/'+name for name in ('merges.txt','vocab.json','special_tokens_map.json',
        'tokenizer_config.json','openvino_tokenizer.xml','openvino_tokenizer.bin',
        'openvino_detokenizer.xml','openvino_detokenizer.bin')),
    *(part+'/'+name for part in ('text_encoder','unet','vae_encoder','vae_decoder')
      for name in ('config.json','openvino_model.xml','openvino_model.bin')),
})


def model_path(root=ROOT):
    return Path(root)/'models'/'multimedia-openvino-sd15-int8'


def validate_manifest(data):
    if data.get('sha') != REVISION:
        raise ValueError('Unexpected multimedia publisher revision')
    entries = {}
    for row in data['siblings']:
        name = row['rfilename']
        if name not in FILES:
            continue
        if name in entries:
            raise ValueError('Duplicate multimedia file')
        digest = (row.get('lfs') or {}).get('sha256') or row.get('blobId')
        size = row.get('size')
        if type(size) is not int or size <= 0 or not isinstance(digest,str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',digest):
            raise ValueError('Missing publisher file identity: '+name)
        entries[name] = {'size':size, 'digest':digest}
    if set(entries) != FILES or not 900_000_000 <= sum(x['size'] for x in entries.values()) <= MAX_BYTES:
        raise ValueError('Incomplete or unexpected multimedia snapshot')
    return {'repo':REPO,'revision':REVISION,'license':LICENSE,'files':entries}


def installed(root=ROOT):
    """Fast size/receipt check; full publisher digests are verified by installer."""
    base = model_path(root)
    try:
        if base.is_symlink() or base.parent.is_symlink():
            return False
        receipt = base/'verified-install.json'
        if receipt.is_symlink() or receipt.stat().st_size > 65536:
            return False
        data = json.loads(receipt.read_text('utf-8'))
        if (data['repo'],data['revision'],data['license']) != (REPO,REVISION,LICENSE):
            return False
        entries = data['files']
        if set(entries) != FILES:
            return False
        if not 900_000_000 <= sum(x['size'] for x in entries.values()) <= MAX_BYTES:
            return False
        for name, row in entries.items():
            p = base/name
            if (p.is_symlink() or p.parent.is_symlink() or not p.is_file()
                    or type(row['size']) is not int or row['size']<=0
                    or p.stat().st_size != row['size']
                    or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',row['digest'])):
                return False
        return True
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return False


def install_plan(root=ROOT, *, role_ok=None, runtime_ok=None, media_ok=None):
    """Return exact missing components without disturbing valid model weights."""
    if role_ok is None:
        def role_ok(role):
            try:
                return bool(installed_files(role,root) and smoke_verified(role,root))
            except (OSError,ValueError,KeyError,TypeError):
                return False
    if runtime_ok is None:
        try:
            marker=json.loads((Path(root)/'runtime/openvino-verified.json').read_text('utf-8'))
            runtime_ok=runtime_path(root).is_file() and marker.get('version')==RUNTIME_VERSION
        except (OSError,ValueError,TypeError,AttributeError):
            runtime_ok=False
    if media_ok is None:
        media_ok=installed(root)
    commands=[]
    missing=[role for role in ('sentinel','janus','implementation') if not role_ok(role)]
    if missing:
        for role in missing:
            commands.append(('download_model.py',('--role',role),'Language model: '+role))
    elif not runtime_ok:
        commands.append(('download_model.py',('--runtime-only',),'OpenVINO runtime'))
    if not media_ok:
        commands.append(('download_multimedia.py',(),'Multimedia model: Stable Diffusion 1.5 INT8'))
    return commands
