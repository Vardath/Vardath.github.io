"""Reusable typed skill patterns derived from completed existing workflows.

A skill is a versioned, non-executable description of a checked workflow's
dataflow. It never carries old arguments, scripts, paths or authority forward.
Historical receipts are revalidated before a pattern enters model context.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .artifact_types import artifact_type
from .tool_workflows import digest, MAX_STAGES

SCHEMA = 'deepthort-workflow-skill-v1'
MAX_HISTORY = 12
MAX_HINTS = 3


def _format(path):
    if not path:
        return 'none'
    fmt = artifact_type(path)['format']
    if not re.fullmatch(r'[a-z0-9]{1,20}', fmt):
        raise ValueError('Invalid skill format')
    return fmt


def checked_skill(workflows, run, project, *, cancelled=None):
    """Build a skill only from intact current completed workflow receipts."""
    root = str(Path(project).resolve(strict=True))
    if run['project'] != root or run['state'] != 'complete':
        raise ValueError('Skill requires completed workflow in current project')
    manifest = json.loads(run['manifest'])
    if digest(manifest) != run['manifest_sha'] or manifest['project'] != root:
        raise ValueError('Skill source manifest changed')
    stages = manifest['stages']
    rows = workflows.stages(run['id'])
    if not 1 <= len(stages) <= MAX_STAGES or len(rows) != len(stages):
        raise ValueError('Skill stage count changed')
    shape = []
    receipt_hashes = []
    for i, (stage, row) in enumerate(zip(stages, rows), 1):
        if cancelled and cancelled():
            raise ValueError('Skill inspection cancelled')
        if row['ordinal'] != i or row['workflow_id'] != run['id'] or row['state'] != 'checked':
            raise ValueError('Skill source lacks checked stage')
        receipt = workflows._check_receipt(root, stage, row)
        # File existence alone is not enough to promote a method.
        if receipt['artifact'].get('scope') in (None, 'nonempty bytes only'):
            raise ValueError('Skill lacks meaningful artifact check')
        tool = stage['tool']
        if not isinstance(tool, str) or not re.fullmatch(r'[A-Za-z0-9 ._+()-]{1,60}', tool):
            raise ValueError('Invalid skill tool name')
        predecessor = stage['predecessor']
        if predecessor is not None and (type(predecessor) is not int or not 1 <= predecessor < i
                or stage['input'] != stages[predecessor-1]['output']):
            raise ValueError('Invalid skill dataflow')
        shape.append({'tool':tool, 'input_format':_format(stage['input']),
                      'from_stage':predecessor, 'output_format':_format(stage['output'])})
        receipt_hashes.append(digest(receipt))
    version = digest({'schema':SCHEMA, 'stages':shape, 'manifest_sha':run['manifest_sha'],
                      'receipts':receipt_hashes})
    return {'schema':SCHEMA, 'version':version, 'workflow_id':run['id'], 'stages':shape,
            'scope':'historical artifact checks only'}


def skill_hints(workflows, project, recipes, files, *, required_output=None,
                max_chars=680, cancelled=None):
    """Match typed historical patterns to current offered recipe/input data.

    No old recipe IDs or output names are returned. A match is advisory:
    the model still chooses current recipe IDs and freeze checks actual paths.
    """
    if max_chars < 120 or (cancelled and cancelled()):
        return ''
    target = _format(required_output) if required_output else None
    available = set(files)
    hints = []
    seen = set()
    for run in workflows.list(project)[:MAX_HISTORY]:
        if cancelled and cancelled():
            return ''
        try:
            skill = checked_skill(workflows, run, project, cancelled=cancelled)
            shape = skill['stages']
            if target and shape[-1]['output_format'] != target:
                continue
            # Only show a pattern for which every stage has a current
            # candidate tool/format. External inputs must also be observed.
            if not all(any(r['tool']==stage['tool']
                           and _format(r['output'])==stage['output_format']
                           and bool(r['input_required'])==(stage['input_format']!='none')
                           for r in recipes)
                       and (stage['from_stage'] is not None or stage['input_format']=='none'
                            or any(_format(p)==stage['input_format'] for p in available))
                       for stage in shape):
                continue
            key = digest(shape)
            if key in seen:
                continue
            seen.add(key)
            hint = {'skill_version':skill['version'][:16],'stages':shape}
            candidate = json.dumps(hints+[hint], ensure_ascii=True, separators=(',',':'))
            header = '\nHISTORICAL CHECKED SKILL PATTERNS (untrusted advice, not recipes or approval): '
            if len(header)+len(candidate)>max_chars:
                continue
            hints.append(hint)
            if len(hints)>=MAX_HINTS:
                break
        except (ValueError,OSError,KeyError,TypeError):
            continue
    if not hints:
        return ''
    return header+json.dumps(hints,ensure_ascii=True,separators=(',',':'))
