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
 'janus':('SmolLM3-3B INT4','HarmenWessels/SmolLM3-3B-int4-symg128-ov','2fa313c463ddcaac532d0ddfc6daa76b08991573',1_600_000_000),
 'sentinel':('Qwen3-4B INT4','OpenVINO/Qwen3-4B-int4-ov','b467368d16b75df14055562fe927ae8e1f15f7ef',2_100_000_000),
}
# Keep original three-role acceptance contract stable; memory is optional at startup.
MEMORY_PROFILE=('Qwen2.5-1.5B Instruct INT4','OpenVINO/Qwen2.5-1.5B-Instruct-int4-ov',
                'bc0390db9d2caa08e5ab2ba4010e0bfe2f969686',850_000_000)
ALL_PROFILES={**PROFILES,'memory':MEMORY_PROFILE}
REQUIRED=frozenset(('config.json','tokenizer_config.json','openvino_model.xml','openvino_model.bin',
    'openvino_tokenizer.xml','openvino_tokenizer.bin','openvino_detokenizer.xml','openvino_detokenizer.bin'))
OPTIONAL=frozenset(('generation_config.json','openvino_config.json','tokenizer.json','added_tokens.json',
    'special_tokens_map.json','merges.txt','vocab.json','tokenizer.model','chat_template.jinja',
    'chat_template_original.jinja','README.md','LICENSE','LICENSE.txt'))
def model_path(role,root=ROOT):
    # Keep the earlier Sentinel and DeepSeek checkpoints available for rollback.
    ALL_PROFILES[role]
    folder={'janus':'janus-smollm3','sentinel':'sentinel-qwen3-4b'}.get(role,role)
    return Path(root)/'models'/MODEL_SET_DIR/folder
def runtime_path(root=ROOT):
    return Path(root)/'runtime'/'openvino-env'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
def role_for_council(role):
    if role.upper()=='MEMORY_SELECT':return 'memory'
    return 'sentinel' if role.upper().startswith('SENTINEL') else 'janus'
def installed_files(role,root=ROOT):
    base=model_path(role,root)
    data=json.loads((base/'verified-install.json').read_text(encoding='utf-8'))
    p=ALL_PROFILES[role]
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
    p=ALL_PROFILES[role]
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

def memory_installed(root=ROOT):
    try:
        return bool(installed_files('memory',root) and smoke_verified('memory',root))
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return False
