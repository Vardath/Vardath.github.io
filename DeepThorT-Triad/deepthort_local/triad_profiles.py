"""Triad's pinned native OpenVINO IR profiles, separate from former GGUF files."""
from pathlib import Path
import json
import os
import re

ROOT=Path(__file__).resolve().parent.parent
MODEL_ID='deepthort-triad'
RUNTIME_VERSION='2026.4.1.0'
# name, publisher repository, exact revision, model.bin minimum bytes
PROFILES={
 'implementation':('Qwen2.5-Coder-7B-Instruct INT4','OpenVINO/Qwen2.5-Coder-7B-Instruct-int4-ov','25d797085dbbe41b1aa8d32bc9ab1e35b7ac10f4',4_000_000_000),
 'janus':('Phi-4-mini-instruct INT4','OpenVINO/Phi-4-mini-instruct-int4-ov','e5813af02e8560a9186c41f932f21cbb584a0907',2_000_000_000),
 'sentinel':('LFM2.5-1.2B-Instruct INT4','OpenVINO/LFM2.5-1.2B-Instruct-int4-ov','5a2950a17b666b07208c75819fe1a9c080668114',600_000_000),
}
REQUIRED=frozenset(('config.json','tokenizer_config.json','openvino_model.xml','openvino_model.bin',
    'openvino_tokenizer.xml','openvino_tokenizer.bin','openvino_detokenizer.xml','openvino_detokenizer.bin'))
OPTIONAL=frozenset(('generation_config.json','openvino_config.json','tokenizer.json','added_tokens.json',
    'special_tokens_map.json','merges.txt','vocab.json','tokenizer.model','chat_template.jinja',
    'chat_template_original.jinja','README.md','LICENSE','LICENSE.txt'))
def model_path(role,root=ROOT):return Path(root)/'models'/'triad-openvino'/role
def runtime_path(root=ROOT):
    return Path(root)/'runtime'/'openvino-env'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
def role_for_council(role):
    return 'sentinel' if role.upper().startswith('SENTINEL') else 'janus'
def installed_files(role,root=ROOT):
    base=model_path(role,root)
    data=json.loads((base/'verified-install.json').read_text(encoding='utf-8'))
    p=PROFILES[role]
    if data.get('repo')!=p[1] or data.get('revision')!=p[2]:raise ValueError('Wrong installed model revision')
    entries=data['files']
    if not isinstance(entries,dict) or not REQUIRED<=entries.keys() or not entries.keys()<=REQUIRED|OPTIONAL:
        raise ValueError('Invalid installed model file set')
    for name,meta in entries.items():
        size=meta['size'];sha=meta['digest']
        if type(size) is not int or size<1 or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',sha):
            raise ValueError('Invalid file receipt')
        path=base/name
        if not path.is_file() or path.stat().st_size!=size:raise ValueError('Model file missing or changed: '+name)
    if entries['openvino_model.bin']['size']<p[3]:raise ValueError('Incomplete weights')
    return entries
def ready(root=ROOT):
    try:
        marker=json.loads((Path(root)/'runtime/openvino-verified.json').read_text(encoding='utf-8'))
        return (runtime_path(root).is_file() and marker.get('version')==RUNTIME_VERSION
                and all(installed_files(r,root) for r in PROFILES))
    except (OSError,ValueError,KeyError,TypeError):return False
def total_weights(root=ROOT):
    return sum(sum(m['size'] for m in installed_files(r,root).values()) for r in PROFILES)
