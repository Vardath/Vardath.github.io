"""Read-only source contracts and requirement-to-test traceability.

The language model may *declare* public APIs or test intentions in its own file
step descriptions.  Such declarations are NOT proof: this module compares them
against the source that actually exists, without importing or running it.
Unlabelled/ambiguous user requirements are left untouched and unverified.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

from .workspace import safe_target

_REQUIRES = re.compile(r'(?:^|[;\n])\s*(provides|uses|verifies)\s*:\s*([^;\n]+)', re.I)
_REQ_LABEL = re.compile(r'^\s*(?:[-*+]\s*)?REQ[-_ ](\d{1,6})\s*[.:]', re.I)
_REFS = re.compile(r'(?i)^REQ[-_ ](\d{1,6})$')
_SYMBOL = re.compile(r'^[A-Za-z_]\w*$')
_TEST_PATH = re.compile(r'(^|/)(?:test_[^/]+\.py|[^/]+_test\.py|[^/]+\.(?:test|spec)\.[jt]sx?|tests?/[^/]+\.gd)$', re.I)
_AMBIGUOUS = re.compile(r'(?i)(?<!\w)(?:maybe|perhaps|approximately|roughly|as needed|if possible|or similar|and/or|etc\.)(?!\w)')


def source_ambiguities(original: str, candidates: list[dict], *, limit: int = 100) -> list[dict]:
    """Advisory exact excerpts, never a guess that the specification is wrong."""
    results = []
    for r in candidates:
        excerpt = original[r['start_char']:r['end_char']]
        for match in _AMBIGUOUS.finditer(excerpt):
            results.append({'requirement_id':r['id'], 'start_char':r['start_char']+match.start(),
                            'end_char':r['start_char']+match.end(), 'phrase':match.group(0),
                            'status':'review_suggested_not_blocking'})
            if len(results)>=limit:return results
    return results


def explicit_requirement_labels(original: str, candidates: list[dict]) -> dict[str,dict]:
    """Use user-written labels only. Detect duplicates rather than merge them."""
    from .agent_plan import PlanError
    labels = {}
    for row in candidates:
        source=original[row['start_char']:row['end_char']]
        found=_REQ_LABEL.match(source)
        if not found:continue
        key=f'REQ-{int(found.group(1))}'
        if key in labels:
            raise PlanError(f'Duplicate source requirement label {key}')
        labels[key]={'requirement_id':row['id'],'start_char':row['start_char'],
                     'end_char':row['end_char'],'source_sha256':hashlib.sha256(source.encode()).hexdigest()}
    return labels


def model_contracts(steps: list[dict], labels: dict[str,dict]) -> list[dict]:
    """Parse only explicitly model-declared paths/symbols/test labels.

    `provides: Symbol`, `uses: path/to/provider.py::Symbol` and
    `verifies: REQ-4` are metadata embedded in model-authored descriptions.
    New or unknown references fail closed; no code and no tests are invented.
    """
    from .agent_plan import PlanError
    paths={s['path'].casefold():s['path'] for s in steps}
    declarations=[]
    for step in steps:
        path=step['path'].replace('\\','/')
        for kind, raw in _REQUIRES.findall(step['description']):
            kind=kind.casefold()
            for item in raw.split(','):
                token=item.strip()
                if not token:
                    raise PlanError(f'Empty {kind} declaration for {path}')
                row={'path':path,'kind':kind,'value':token}
                if kind=='provides':
                    if not path.endswith('.py') or not _SYMBOL.fullmatch(token):
                        raise PlanError(f'Invalid Python export contract {token!r} for {path}')
                elif kind=='uses':
                    if '::' not in token:
                        raise PlanError(f'Use contract requires provider.py::Symbol, found {token!r}')
                    provider,symbol=token.rsplit('::',1)
                    canonical=paths.get(provider.replace('\\','/').casefold())
                    if (canonical is None or not canonical.endswith('.py') or
                            not path.endswith('.py') or not _SYMBOL.fullmatch(symbol)):
                        raise PlanError(f'Invalid or unknown local use contract {token!r} in {path}')
                    row['provider']=canonical
                    row['symbol']=symbol
                elif kind=='verifies':
                    found=_REFS.fullmatch(token)
                    key=f'REQ-{int(found.group(1))}' if found else None
                    if key not in labels:
                        raise PlanError(f'{path} claims to verify missing explicit requirement {token!r}')
                    if not _TEST_PATH.search(path):
                        raise PlanError(f'{path} declares verifies: {key}, but is not a test-file path')
                    row['requirement']=key
                declarations.append(row)
    return declarations


def _test_count(tree: ast.Module) -> int:
    """Count syntactically declared unittest/pytest test functions, not successes."""
    count=0
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
            count+=1
        if isinstance(node,ast.ClassDef) and (node.name.startswith('Test') or
                any(isinstance(b,(ast.Name,ast.Attribute)) and
                    (getattr(b,'id',None)=='TestCase' or getattr(b,'attr',None)=='TestCase') for b in node.bases)):
            count+=sum(isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)) and
                        child.name.startswith('test_') for child in node.body)
    return count


def inspect_model_contracts(project: str | Path, steps: list[dict], original: str,
                            candidates: list[dict]) -> dict:
    """Check declared API/test intentions against actual, hashable source.

    An absent planned file remains pending. A successful AST check remains
    static evidence only; no source requirement is marked behaviorally verified.
    """
    base=Path(project).resolve(strict=True)
    labels=explicit_requirement_labels(original,candidates)
    declarations=model_contracts(steps,labels)
    by_path={}
    for d in declarations:by_path.setdefault(d['path'],[]).append(d)
    parses={}
    for path in sorted({d['path'] for d in declarations}|
                       {d.get('provider') for d in declarations if d.get('provider')}):
        rel=str(path)
        target=safe_target(base,rel)
        if not target.is_file():
            parses[rel]={'state':'pending_source'}
            continue
        if target.stat().st_size>220_000:
            parses[rel]={'state':'source_too_large_for_static_audit'}
            continue
        try:
            data=target.read_bytes()
            source=data.decode('utf-8')
            tree=ast.parse(source, filename=rel) if rel.endswith('.py') else None
        except (OSError,UnicodeError,SyntaxError,ValueError) as exc:
            parses[rel]={'state':'source_parse_error','detail':str(exc)[:180]}
            continue
        exports=set()
        if tree is not None:
            for node in tree.body:
                if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    exports.add(node.name)
                elif isinstance(node,(ast.Assign,ast.AnnAssign)):
                    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                    exports.update(t.id for t in targets if isinstance(t,ast.Name))
        parses[rel]={'state':'source_present','sha256':hashlib.sha256(data).hexdigest(),
                     'tree':tree,'exports':exports,
                     'tests':_test_count(tree) if tree is not None else None}
    checks=[]
    issues=[]
    for decl in declarations:
        path=decl['path']; kind=decl['kind']; source=parses[path]
        status='pending_source'
        reason='Source not yet available or cannot be parsed'
        if source['state']=='source_present':
            if kind=='provides':
                status='static_export_found' if decl['value'] in source['exports'] else 'missing_declared_export'
                reason=('Top-level export exists' if status=='static_export_found' else
                        'Declared export absent from existing source')
            elif kind=='verifies':
                count=source['tests']
                status=('static_test_discovered' if count is not None and count>0 else
                        'no_test_cases_found' if count is not None else 'test_runner_not_statically_supported')
                reason=f'{count} syntactically discoverable Python test(s)' if count is not None else 'Unverified non-Python test source'
            elif kind=='uses':
                provider=parses.get(decl['provider'],{'state':'pending_source'})
                if provider['state']=='source_present':
                    if decl['symbol'] not in provider['exports']:
                        status='missing_provider_export';reason='Provider has no declared symbol'
                    else:
                        module=decl['provider'][:-3].replace('/','.')
                        imports=[n for n in ast.walk(source['tree']) if isinstance(n,ast.ImportFrom)]
                        use_imports=any((n.module==module or n.module==module.rsplit('.',1)[-1]) and
                                        any(a.name==decl['symbol'] for a in n.names) for n in imports)
                        status='static_import_found' if use_imports else 'missing_declared_import'
                        reason='Expected local import exists' if use_imports else 'Consumer lacks the declared import'
                else:
                    status='provider_pending';reason='Provider source not yet available'
        elif source['state']=='source_parse_error':
            status='source_parse_error';reason=source['detail']
        check={'path':path,'kind':kind,'declaration':decl['value'],
               'state':status,'detail':reason}
        if kind=='verifies':check['requirement']=decl['requirement']
        if kind=='uses':check['provider']=decl['provider']
        checks.append(check)
        if status in ('missing_declared_export','missing_provider_export',
                      'missing_declared_import','no_test_cases_found','source_parse_error'):
            issues.append(check)
    linked={d['requirement'] for d in declarations if d['kind']=='verifies'}
    return {'explicit_requirement_labels':len(labels),
            'model_declared_contracts':len(declarations),
            'unlinked_labelled_requirements':sorted(set(labels)-linked),
            'checks':checks,'issues':issues,
            'ambiguity_candidates':source_ambiguities(original,candidates),
            'assurance':'Static API and test discovery only; no test run or behavioral acceptance is implied',
            'acceptance_confirmed':False}


def main(argv: list[str] | None = None) -> int:
    """Read-only inspection command for a proposed plan and exact specification."""
    import argparse
    import json
    from .requirements_intelligence import requirement_candidates
    from .specification_library import sections
    parser=argparse.ArgumentParser(description='Audit declared source contracts without execution')
    parser.add_argument('project',help='Existing local project directory')
    parser.add_argument('plan_file',help='JSON file with model-authored files array')
    parser.add_argument('specification',help='Original UTF-8 specification file')
    args=parser.parse_args(argv)
    plan=Path(args.plan_file)
    spec=Path(args.specification)
    if not plan.is_file() or plan.stat().st_size>4_000_000:
        parser.error('Plan JSON is unavailable or too large for inspection')
    if not spec.is_file() or spec.stat().st_size>120_000_000:
        parser.error('Original specification is unavailable or exceeds local inspection limit')
    content=json.loads(plan.read_text(encoding='utf-8'))
    steps=content.get('files') if isinstance(content,dict) else content
    if not isinstance(steps,list) or any(not isinstance(x,dict) or
            not isinstance(x.get('path'),str) or not isinstance(x.get('description'),str)
            for x in steps):
        parser.error('Expected model-authored path/description entries')
    original=spec.read_text(encoding='utf-8')
    rows=[(i,start,end) for i,(start,end) in enumerate(sections(original))]
    report=inspect_model_contracts(args.project,steps,original,requirement_candidates(original,rows))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 2 if report['issues'] else 0


if __name__=='__main__':
    raise SystemExit(main())
