"""Fourth intelligent core: pinned Gemma VLM checkpoint (not a diffusion model)."""
import json
import re
from pathlib import Path
from .triad_profiles import ROOT

REPO = 'OpenVINO/gemma-4-E2B-it-int4-ov'
REVISION = '81a7dc381261ebcea9aac4849aac35496475b389'
MODEL_NAME = 'Gemma 4 E2B Instruct INT4'
MIN_BYTES = 4_000_000_000
MAX_BYTES = 5_000_000_000
FILES = frozenset({
    'README.md','chat_template.jinja','config.json','generation_config.json',
    'openvino_config.json','preprocessor_config.json','processor_config.json',
    'tokenizer.json','tokenizer_config.json',
    *('openvino_'+part+'.'+ext for part in (
        'detokenizer','language_model','text_embeddings_model',
        'text_embeddings_per_layer_model','tokenizer','vision_embeddings_model')
      for ext in ('xml','bin')),
})


def path(root=ROOT):
    return Path(root)/'models'/'creative-gemma4-e2b-int4'


def valid_entries(entries):
    if not isinstance(entries,dict) or set(entries)!=FILES:
        raise ValueError('Missing or unexpected creative model files')
    for row in entries.values():
        if (type(row['size']) is not int or row['size']<=0 or
                not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',row['digest'])):
            raise ValueError('Invalid creative model file identity')
    if not MIN_BYTES<=sum(x['size'] for x in entries.values())<=MAX_BYTES:
        raise ValueError('Unexpected creative model download size')


def manifest(data):
    if data.get('sha')!=REVISION:
        raise ValueError('Incorrect creative model revision')
    entries={}
    for row in data['siblings']:
        name=row['rfilename']
        if name not in FILES:continue
        if name in entries:raise ValueError('Duplicate model file')
        entries[name]={'size':row['size'],'digest':(row.get('lfs') or {}).get('sha256') or row.get('blobId')}
    valid_entries(entries)
    return {'repo':REPO,'revision':REVISION,'license':'apache-2.0','files':entries}


def installed(root=ROOT):
    try:
        base=path(root)
        receipt=base/'verified-install.json'
        if base.is_symlink() or base.parent.is_symlink() or receipt.is_symlink() or receipt.stat().st_size>65536:
            return False
        data=json.loads(receipt.read_text('utf-8'))
        if (data['repo'],data['revision'],data['license'])!=(REPO,REVISION,'apache-2.0'):
            return False
        valid_entries(data['files'])
        return all((base/n).is_file() and not (base/n).is_symlink() and
                   (base/n).stat().st_size==row['size'] for n,row in data['files'].items())
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return False
