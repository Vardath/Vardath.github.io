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
_GUT_RATIO = re.compile(r'(?im)(?<!\d)(\d+)\s*/\s*(\d+)\s+passed\.?')
_GUT_COUNTS = re.compile(r'(?im)(?<!\d)(\d+)\s+passed\s+(\d+)\s+failed\.?')
_GUT_ABORT = re.compile(r'(?i)\b(?:SCRIPT ERROR|Parse Error|\[GUT ERROR\]|Tests failed|No tests found)\b')


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
    godot_gut=(any('godot' in x for x in args[:1]) and '-s' in args and
               any(x.replace('\\','/').endswith('addons/gut/gut_cmdln.gd') for x in args))
    x4_audit=(len(args)>=2 and args[1].replace('\\','/').endswith('/engine_acceptance_cli.py'))
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
    elif godot_gut:
        ratios=[(int(a),int(b)) for a,b in _GUT_RATIO.findall(lines)]
        counts=[(int(a),int(b)) for a,b in _GUT_COUNTS.findall(lines)]
        success=(ratios and ratios[-1][0]>0 and ratios[-1][0]==ratios[-1][1]) or (
            counts and counts[-1][0]>0 and counts[-1][1]==0)
        result['test_count']=ratios[-1][1] if ratios else counts[-1][0] if counts else 0
        if not success or _GUT_ABORT.search(lines) or not re.search(r'(?i)All tests passed!',lines):
            result.update(accepted=False,assurance='unverified',
                          reason='Godot GUT did not evidence a completed nonempty passing suite')
        else:
            result.update(assurance='godot_gut_tests_passed',
                          reason=f'Godot GUT reported {result["test_count"]} passing tests; gameplay not fully proven')
    elif x4_audit:
        try:
            report=json.loads(lines)
        except (ValueError,TypeError):
            report={}
        if (report.get('engine')!='x4_extension' or not report.get('accepted') or
                report.get('issues') or report.get('pending')):
            result.update(accepted=False,assurance='unverified',reason='X4 static artifact audit did not pass')
        else:
            result.update(assurance='x4_static_xml_passed',
                          reason='X4 local XML/index audit passed; no in-game execution or behavior proven')
    elif godot_editor:
        result.update(assurance='editor_load_only',reason='Godot editor loaded successfully; no gameplay test proved')
    return result


def attach_verification(snapshot: dict, assessment: dict, command: list[str], *, engine_report:dict|None=None) -> dict:
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
    if engine_report is not None:
        # Engine inspection is a *separate* static assurance. Include the exact
        # files it examined so later changes invalidate the evidence.
        if engine_report.get('issues') or engine_report.get('pending'):
            raise ValueError('Engine artifact findings must be repaired before attaching evidence')
        if engine_report.get('engine') not in ('x4_extension','godot','android_gradle','general'):
            raise ValueError('Unknown engine audit type')
        hashes=engine_report.get('source_hashes')
        if not isinstance(hashes,dict) or len(hashes)>256 or any(
                not isinstance(k,str) or not isinstance(v,str) or
                re.fullmatch(r'[0-9a-f]{64}',v) is None for k,v in hashes.items()):
            raise ValueError('Invalid engine source evidence')
        result['verification']['engine']=engine_report['engine']
        result['verification']['engine_sources']=dict(sorted(hashes.items()))
    return result
