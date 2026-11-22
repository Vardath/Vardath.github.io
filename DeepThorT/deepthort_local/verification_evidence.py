"""Conservative analysis of authorized verification process output.

Only the already-approved desktop test runner invokes this code, after the
process exits. An exit-zero command discovering zero tests must not be called a
successful test. No command is executed here.
"""
from __future__ import annotations

import hashlib
import json
import re

_UNITTEST = re.compile(r'(?m)^Ran\s+(\d+)\s+tests?\s+in\s+[\d.]+s?\s*$')
_DOTNET = re.compile(r'(?i)\bPassed:\s*(\d+)\b')


def assess_verification(command: list[str], exit_code: int,
                        captured_lines: list[str]) -> dict:
    """Return an auditable, bounded assessment, not a game-play certification."""
    if not isinstance(command,list) or not command:
        raise ValueError('A real, approved verification command is required')
    lines='\n'.join(str(x) for x in captured_lines[-300:])[-60000:]
    args=[str(x).casefold() for x in command]
    python_unittest=any(x=='unittest' for x in args) and 'discover' in args
    dotnet_test=any(x in ('dotnet','dotnet.exe') for x in args) and 'test' in args
    godot_editor=any('godot' in x for x in args[:1]) and '--editor' in args
    result={'accepted':exit_code==0,'assurance':'process_exit_only',
            'test_count':None, 'reason':'Approved command exited zero; behavior not established',
            'output_sha256':hashlib.sha256(lines.encode()).hexdigest(),
            'output_captured':bool(lines)}
    if exit_code!=0:
        result.update(accepted=False,assurance='failed',reason=f'Test process exited {exit_code}')
    elif python_unittest:
        counts=[int(m) for m in _UNITTEST.findall(lines)]
        count=counts[-1] if counts else 0
        result['test_count']=count
        if count<1 or not re.search(r'(?m)^OK(?:\s*\([^\n]*\))?\s*$',lines):
            result.update(accepted=False,assurance='unverified',
                          reason='Python unittest produced no evidenced passing test cases')
        else:
            result.update(assurance='python_tests_passed',
                          reason=f'Python unittest reported {count} passing test(s); game behavior not independently proven')
    elif dotnet_test:
        counts=[int(n) for n in _DOTNET.findall(lines)]
        count=sum(counts) if counts else 0
        result['test_count']=count
        if count<1:
            result.update(accepted=False,assurance='unverified',
                          reason='.NET did not report any passing tests')
        else:
            result.update(assurance='dotnet_tests_passed',reason=f'.NET reported {count} passing test(s)')
    elif godot_editor:
        result.update(assurance='editor_load_only',reason='Godot editor loaded successfully; no gameplay test proved')
    return result


def attach_verification(snapshot: dict, assessment: dict, command: list[str]) -> dict:
    """Bind source fingerprints and a bounded successful test report."""
    if not assessment.get('accepted') or snapshot.get('snapshot_schema')!='deepthort-approved-verification-v1':
        raise ValueError('Only an accepted verification may be attached')
    result=dict(snapshot)
    result['verification']={
        'assurance':assessment['assurance'],
        'test_count':assessment['test_count'],
        'output_sha256':assessment['output_sha256'],
        'argv_sha256':hashlib.sha256(json.dumps(command,ensure_ascii=False,
                            separators=(',',':')).encode()).hexdigest(),
    }
    return result
