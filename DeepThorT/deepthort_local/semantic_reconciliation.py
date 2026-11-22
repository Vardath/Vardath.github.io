"""Conservative, read-only requirement reconciliation and source-interface audit.

No source specification is rewritten, no new requirements/files are invented, and
no test is marked passed by model output. Only exactly comparable, *explicit*
modal/numeric constraints are auto-blocking; everything else is advisory.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from .workspace import safe_target, WorkspaceError

_BULLET = re.compile(r'^\s*(?:[-*+]\s+|\d{1,5}[.)]\s+|REQ[-_ ]\d+[.:]\s+)?', re.I)
_MODAL = re.compile(r'^(?P<subject>[\w][\w \-/]{0,90}?)\s+(?P<modal>must|shall|should)\s+(?P<negative>not\s+)?(?P<action>[^.!?;\n]{2,240})[.!?]?$', re.I)
_QUANTIFIED = re.compile(r'^(?P<verb>support|have|provide|allow|contain|handle|store|accept)\s+(?P<bound>at\s+least|at\s+most|exactly)\s+(?P<quantity>\d{1,10})\s+(?P<measure>[\w \-/]{2,90})$', re.I)
_COMPLEX = re.compile(r'\b(?:unless|except|only\s+if|provided\s+that|in\s+case\s+of)\b',re.I)


def _norm(text: str) -> str:
    return ' '.join(text.casefold().strip().split()).rstrip(' .')


def explicit_constraints(original: str, candidates: list[dict]) -> list[dict]:
    """Extract exactly anchored normative statements, retaining source offsets.

    Not an NLP solver. Conditional/non-comparable prose stays untouched. Numeric
    comparisons only share a key if subject, verb and measured noun all match.
    """
    findings=[]
    for candidate in candidates:
        start,end=candidate['start_char'],candidate['end_char']
        body=original[start:end]
        offset=start
        for raw in body.splitlines(keepends=True):
            line=raw.rstrip('\r\n')
            stripped=_BULLET.sub('',line).strip()
            local=line.find(stripped) if stripped else 0
            match=_MODAL.fullmatch(stripped)
            if match and not _COMPLEX.search(match.group('action')):
                subject=_norm(match.group('subject'))
                action=_norm(match.group('action'))
                negative=bool(match.group('negative'))
                finding={'requirement_id':candidate['id'], 'section':candidate['section_ordinal']+1,
                         'start_char':offset+local, 'end_char':offset+local+len(stripped),
                         'source':stripped, 'subject':subject,'action':action,
                         'strength':_norm(match.group('modal')),
                         'negative':negative, 'kind':'modal'}
                quantity=_QUANTIFIED.fullmatch(action) if not negative else None
                if quantity:
                    finding.update({'kind':'numeric','key':(subject,_norm(quantity.group('verb')),
                                     _norm(quantity.group('measure'))),
                                    'bound':_norm(quantity.group('bound')),
                                    'quantity':int(quantity.group('quantity'))})
                findings.append(finding)
            offset+=len(raw)
    return findings


def reconcile_explicit_requirements(original: str, candidates: list[dict]) -> dict:
    """Report demonstrable clashes; do not infer intent from different wording.

    Block contradictory MUST/SHALL statements only. SHOULD statements and
    ambiguous or conditional instructions remain candidates for human review.
    """
    norms=explicit_constraints(original,candidates)
    conflicts=[]
    by_key={}
    numeric={}
    encountered=set()
    for item in norms:
        if item['kind']=='numeric':
            key=item['key']
            old=numeric.setdefault(key,[])
            if item['strength'] in ('must','shall'):
                for prior in old:
                    a,b=prior,item
                    if a['strength'] not in ('must','shall'):
                        continue
                    lo_a=a['quantity'] if a['bound'] in ('exactly','at least') else -1
                    hi_a=a['quantity'] if a['bound'] in ('exactly','at most') else float('inf')
                    lo_b=b['quantity'] if b['bound'] in ('exactly','at least') else -1
                    hi_b=b['quantity'] if b['bound'] in ('exactly','at most') else float('inf')
                    if max(lo_a,lo_b)>min(hi_a,hi_b):
                        pair=tuple(sorted((a['start_char'],b['start_char'])))
                        if pair not in encountered:
                            conflicts.append({'kind':'incompatible_numeric_bounds',
                                              'left':_public(a),'right':_public(b)})
                            encountered.add(pair)
            old.append(item)
        else:
            key=(item['subject'],item['action'])
            prev=by_key.setdefault(key,[])
            if item['strength'] in ('must','shall'):
                for old in prev:
                    if (old['strength'] in ('must','shall') and
                        old['negative'] != item['negative']):
                        pair=tuple(sorted((old['start_char'],item['start_char'])))
                        if pair not in encountered:
                            conflicts.append({'kind':'opposing_explicit_obligations',
                                              'left':_public(old),'right':_public(item)})
                            encountered.add(pair)
            prev.append(item)
    return {'explicit_statements':len(norms),'blocking_conflicts':conflicts,
            'interpretation':'Exact explicit obligations and numeric bounds only; no semantic equivalence inferred'}


def _public(row):
    return {k:row[k] for k in ('requirement_id','section','start_char','end_char','source')}


_REQUIREMENT_ID = re.compile(r'^\s*(?:[-*+]\s+)?REQ[-_ ](?P<id>\d{1,6})\s*[.:]\s*', re.I)
_REQUIRES = re.compile(r'(?i)(?:^|[;\n])\s*depends-on(?:-requirement)?\s*:\s*((?:REQ[-_ ]\d{1,6}\s*,?\s*)+)')
_REQUIRES_ID = re.compile(r'(?i)REQ[-_ ](\d{1,6})\b')


def declared_requirement_dependencies(original: str, candidates: list[dict]) -> list[dict]:
    """Validate only user-written `REQ-N: ...; depends-on: REQ-M` edges.

    File dependency scheduling remains separate. A whole section's source-file
    association does not establish that its individual requirements are met.
    """
    from .agent_plan import PlanError
    declarations={}
    for item in candidates:
        body=original[item['start_char']:item['end_char']]
        start=_REQUIREMENT_ID.match(body)
        if start is None:
            continue
        ident=int(start.group('id'))
        if ident in declarations:
            raise PlanError(f'Duplicate explicit requirement label REQ-{ident}; reconcile specification')
        declarations[ident]=(item,body)
    edges=[]
    for identifier,(item,body) in declarations.items():
        for raw in _REQUIRES.findall(body):
            for dep in _REQUIRES_ID.findall(raw):
                required=int(dep)
                if required==identifier:
                    raise PlanError(f'REQ-{identifier} cannot depend on itself')
                if required not in declarations:
                    raise PlanError(f'REQ-{identifier} depends on unknown requirement REQ-{required}')
                edges.append({'requirement':f'REQ-{identifier}',
                              'requires':f'REQ-{required}',
                              'source_requirement_id':item['id'],
                              'required_source_id':declarations[required][0]['id']})
    if edges:
        deps={name:set() for name in declarations}
        for edge in edges:
            deps[int(edge['requirement'][4:])].add(int(edge['requires'][4:]))
        ready=[name for name,requires in deps.items() if not requires]
        seen=0
        reverse={key:set() for key in deps}
        for key,required in deps.items():
            for r in required:reverse[r].add(key)
        while ready:
            key=ready.pop()
            seen+=1
            for dependent in reverse[key]:
                deps[dependent].discard(key)
                if not deps[dependent]:ready.append(dependent)
        if seen!=len(deps):
            raise PlanError('Explicit source requirement dependencies contain a cycle')
    return edges


def acceptance_candidates(original: str, candidates: list[dict], *, limit: int = 2000) -> dict:
    """Return exact user-derived acceptance obligations. Never mark them passed.

    Generated tests and actual runtime assertions require later, approved work.
    """
    if not 1<=limit<=10000:
        raise ValueError('Acceptance report limit must be 1..10000')
    norms=explicit_constraints(original,candidates)
    items=[]
    for item in norms[:limit]:
        items.append({**_public(item), 'criterion':item['source'],
                      'suggested_evidence':'approved automated or manual acceptance test',
                      'verification_state':'unverified'})
    return {'count':len(norms),'shown':len(items),'criteria':items,
            'coverage':'only explicitly phrased obligations; other specification prose retained and not silently considered covered',
            'all_verified':False}


def audit_python_interfaces(project: str | Path, steps: list[dict], *, max_files: int = 256) -> dict:
    """Parse existing planned Python files without executing code or imports.

    Direct `from local.module import Symbol` can be checked against a local
    module's statically visible definitions. Dynamic exports cannot be proven.
    Missing files are pending, not treated as passing checks.
    """
    if not 1<=max_files<=2000:
        raise ValueError('Interface audit limit must be 1..2000')
    base=Path(project).resolve(strict=True)
    mapping={}
    for step in steps:
        path=step['path']
        if not path.lower().endswith('.py'):
            continue
        rel=Path(path.replace('\\','/'))
        stem=rel.with_suffix('')
        parts=stem.parts[:-1] if stem.name=='__init__' else stem.parts
        if parts:
            mapping['.'.join(parts)]=path
    findings=[]
    known={}; pending=[]
    for module,rel in list(mapping.items())[:max_files]:
        target=safe_target(base,rel)
        if not target.is_file():
            pending.append(rel)
            continue
        if target.stat().st_size>180000:
            findings.append({'path':rel,'kind':'source_too_large_for_static_audit'})
            continue
        try:
            code=target.read_text(encoding='utf-8')
            parsed=ast.parse(code,filename=rel)
        except (UnicodeError,OSError,SyntaxError,ValueError) as exc:
            findings.append({'path':rel,'kind':'source_parse_error',
                             'detail':str(exc)[:240]})
            continue
        exports=set()
        dynamic=False
        for node in parsed.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                exports.add(node.name)
                if node.name=='__getattr__':dynamic=True
            elif isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                for target_node in targets:
                    if isinstance(target_node,ast.Name):exports.add(target_node.id)
            elif isinstance(node,ast.ImportFrom):
                for alias in node.names:
                    exports.add(alias.asname or alias.name)
            elif isinstance(node,ast.Import):
                for alias in node.names:
                    exports.add(alias.asname or alias.name.split('.')[0])
        known[module]=(rel,parsed,exports,dynamic)
    checked=0
    for module,(rel,tree,_,_) in known.items():
        for node in ast.walk(tree):
            if not isinstance(node,ast.ImportFrom) or not node.names:
                continue
            if node.level:
                # Resolve explicit relative imports only when the provider is in scope.
                parts=module.split('.')[:-1]
                if node.level>len(parts)+1:
                    continue
                provider='.'.join(parts[:len(parts)-(node.level-1)]+([node.module] if node.module else []))
            else:
                provider=node.module or ''
            if provider not in mapping:
                continue
            checked+=1
            if provider not in known:
                if mapping[provider] not in pending:
                    findings.append({'path':rel,'kind':'provider_unavailable',
                                     'provider':mapping[provider]})
                continue
            _,_,exported,dynamic=known[provider]
            for alias in node.names:
                if alias.name=='*' or dynamic:
                    continue
                if alias.name not in exported:
                    findings.append({'path':rel,'kind':'missing_local_export',
                                     'provider':mapping[provider], 'symbol':alias.name,
                                     'line':node.lineno})
    return {'planned_python_files':len(mapping),'parsed_files':len(known),
            'pending_files':sorted(pending),'checked_local_imports':checked,
            'issues':findings,
            'level':'static source inspection only; no imports executed or runtime tests performed'}


def capture_verified_sources(project: str | Path, steps: list[dict]) -> dict:
    """Capture a read-only fingerprint of approved job outputs at tool completion.

    The caller must be the already-approved test completion event. This helper
    does not run commands or declare requirements satisfied.
    """
    import hashlib
    import json
    base=Path(project).resolve(strict=True)
    if not 1<=len(steps)<=24:
        raise ValueError('Expected one approved, bounded milestone')
    results={}
    for item in steps:
        rel=item['path']
        path=safe_target(base,rel,must_exist=True)
        if path.stat().st_size>220_000:
            raise ValueError(f'Verified source exceeds bounded artifact size: {rel}')
        if rel.casefold() in (r.casefold() for r in results):
            raise ValueError('Duplicate approved verification path')
        results[rel]=hashlib.sha256(path.read_bytes()).hexdigest()
    canonical=json.dumps(results,sort_keys=True,separators=(',',':'))
    return {'snapshot_schema':'deepthort-approved-verification-v1',
            'files':results,'sha256':hashlib.sha256(canonical.encode()).hexdigest()}


def verified_sources_current(project: str | Path, steps: list[dict], snapshot: dict) -> bool:
    """Reject stale/tampered test evidence; missing files never count as current."""
    if not isinstance(snapshot,dict) or snapshot.get('snapshot_schema')!='deepthort-approved-verification-v1':
        return False
    try:
        expected=capture_verified_sources(project,steps)
        # v28 appends an approved-check summary. The source digest must still
        # match exactly; an older v27 snapshot stays readable but does not
        # gain new test-level assurances retroactively.
        if any(snapshot.get(key)!=value for key,value in expected.items()):
            return False
        if set(snapshot)-set(expected)-{'verification'}:
            return False
        evidence=snapshot.get('verification')
        if evidence is None:return True
        if not isinstance(evidence,dict) or set(evidence)!={
                'assurance','test_count','output_sha256','argv_sha256'}:
            return False
        if evidence['assurance'] not in ('process_exit_only','python_tests_passed',
                                          'dotnet_tests_passed','editor_load_only'):
            return False
        if (evidence['assurance'] in ('python_tests_passed','dotnet_tests_passed') and
            (not isinstance(evidence['test_count'],int) or evidence['test_count']<1)):
            return False
        if any(not isinstance(evidence[k],str) or
               not re.fullmatch(r'[0-9a-f]{64}',evidence[k])
               for k in ('output_sha256','argv_sha256')):
            return False
        return True
    except (OSError, ValueError, WorkspaceError):
        return False


def main(argv: list[str] | None = None) -> int:
    """Read-only CLI for inspecting local specification and Python interfaces."""
    import argparse
    import json
    from .requirements_intelligence import requirement_candidates
    from .specification_library import sections
    parser=argparse.ArgumentParser(description='Inspect untrusted project requirements; never execute code')
    commands=parser.add_subparsers(dest='command',required=True)
    spec=commands.add_parser('requirements',help='Find exact stated conflicts, edges and unverified criteria')
    spec.add_argument('source_file',help='UTF-8 specification text')
    spec.add_argument('--limit',type=int,default=100,help='Maximum criteria to print')
    api=commands.add_parser('interfaces',help='Statically inspect planned local Python modules')
    api.add_argument('project',help='Existing project directory')
    api.add_argument('plan_file',help='UTF-8 JSON with a files array of proposed paths')
    args=parser.parse_args(argv)
    if args.command=='requirements':
        source=Path(args.source_file)
        if not source.is_file() or source.stat().st_size>120_000_000:
            parser.error('Specification missing or exceeds the local inspection size limit')
        original=source.read_text(encoding='utf-8')
        rows=[(ordinal,start,end) for ordinal,(start,end) in enumerate(sections(original))]
        candidates=requirement_candidates(original,rows)
        findings=reconcile_explicit_requirements(original,candidates)
        findings['dependencies']=declared_requirement_dependencies(original,candidates)
        findings['acceptance']=acceptance_candidates(original,candidates,limit=args.limit)
        print(json.dumps(findings,indent=2,ensure_ascii=False))
        return 2 if findings['blocking_conflicts'] else 0
    plan=Path(args.plan_file)
    if not plan.is_file() or plan.stat().st_size>4_000_000:
        parser.error('Plan missing or exceeds the local inspection size limit')
    payload=json.loads(plan.read_text(encoding='utf-8'))
    steps=payload['files'] if isinstance(payload,dict) else payload
    if not isinstance(steps,list) or any(not isinstance(s,dict) or
                                         not isinstance(s.get('path'),str) for s in steps):
        parser.error('Plan must contain an array of entries with relative file paths')
    result=audit_python_interfaces(args.project,steps)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 2 if result['issues'] else 0


if __name__=='__main__':
    raise SystemExit(main())
