"""Triad's pinned native OpenVINO IR profiles, separate from former GGUF files."""
from pathlib import Path
import json
import os
import re

ROOT=Path(__file__).resolve().parent.parent
MODEL_ID='deepthort-triad'
MODEL_SET_DIR='triad-openvino-compact-v1'
RUNTIME_VERSION='2026.4.1.0'
# name, publisher repository, exact revision, model.bin minimum bytes
PROFILES={
 'implementation':('Granite 4.1 3B INT4 code-calibrated','HarmenWessels/granite-4.1-3b-int4-cw-code-ov','0e0f06a3823a72ab3755ecf9715050b5125cf5a4',1_700_000_000),
 'janus':('DeepSeek-R1-Distill-Qwen-1.5B INT4','OpenVINO/DeepSeek-R1-Distill-Qwen-1.5B-int4-ov','2b0c1510bd75adf4dc3910025b32a973ca9edc8a',1_300_000_000),
 'sentinel':('Qwen3-1.7B INT4','OpenVINO/Qwen3-1.7B-int4-ov','6f32d81e9deebeca30bb5490a7176cf4fa8c79e3',1_100_000_000),
}
REQUIRED=frozenset(('config.json','tokenizer_config.json','openvino_model.xml','openvino_model.bin',
    'openvino_tokenizer.xml','openvino_tokenizer.bin','openvino_detokenizer.xml','openvino_detokenizer.bin'))
OPTIONAL=frozenset(('generation_config.json','openvino_config.json','tokenizer.json','added_tokens.json',
    'special_tokens_map.json','merges.txt','vocab.json','tokenizer.model','chat_template.jinja',
    'chat_template_original.jinja','README.md','LICENSE','LICENSE.txt'))
def model_path(role,root=ROOT):return Path(root)/'models'/MODEL_SET_DIR/role
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
def smoke_verified(role,root=ROOT):
    record=json.loads((model_path(role,root)/'native-smoke.json').read_text(encoding='utf-8'))
    p=PROFILES[role]
    return (record.get('role')==role and record.get('repo')==p[1]
            and record.get('revision')==p[2] and record.get('runtime')==RUNTIME_VERSION
            and record.get('native_generation')=='passed'
            and record.get('exact_arithmetic_reply') in ('passed','failed'))

def ready(root=ROOT):
    try:
        marker=json.loads((Path(root)/'runtime/openvino-verified.json').read_text(encoding='utf-8'))
        return (runtime_path(root).is_file() and marker.get('version')==RUNTIME_VERSION
                and all(installed_files(r,root) and smoke_verified(r,root) for r in PROFILES))
    except (OSError,ValueError,KeyError,TypeError):return False
def total_weights(root=ROOT):
    return sum(sum(m['size'] for m in installed_files(r,root).values()) for r in PROFILES)
