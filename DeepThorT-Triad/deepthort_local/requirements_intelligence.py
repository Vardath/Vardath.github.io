"""Conservative requirement candidates and explicit, model-authored file dependencies.

A candidate is a *verbatim anchored span*, never a claim of semantic coverage.
Dependency edges exist ONLY when a proposed description explicitly declares
`depends-on: path/to/file.ext` (comma-separated). No guessed API edges.
"""
from __future__ import annotations

import hashlib
import heapq
import re

_REQUIREMENT_START = re.compile(r'(?m)^(?:[ \t]*[-*+]\s+|[ \t]*\d{1,5}[.)]\s+|[ \t]*#{1,6}\s+|[ \t]*(?:REQ[-_ ]\d+[.:]\s+))')
_DECLARATION = re.compile(r'(?i)(?:^|[;\n])\s*depends-on\s*:\s*([^;\n]+)')
MAX_CANDIDATES_PER_SECTION = 64


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def requirement_candidates(original: str, section_rows: list[tuple]) -> list[dict]:
    """Create stable, hash-checked candidate spans, without summarizing input.

    Preserve every non-whitespace part of a section, including unstructured
    prose, by grouping the overflow rather than dropping any source text.
    Span offsets are Python Unicode-character offsets (same as spec index).
    """
    output=[]
    master=_sha(original)
    for section_row in section_rows:
        section, start, end = section_row[:3]
        text=original[start:end]
        if not text.strip():
            # Empty sections are retained by the original specification index.
            continue
        boundaries=[0]+[match.start() for match in _REQUIREMENT_START.finditer(text)
                        if match.start()!=0]
        boundaries=sorted(set(boundaries))
        if len(boundaries)>MAX_CANDIDATES_PER_SECTION:
            boundaries=boundaries[:MAX_CANDIDATES_PER_SECTION]
        for ordinal,local_start in enumerate(boundaries,1):
            local_end=boundaries[ordinal] if ordinal<len(boundaries) else len(text)
            excerpt=text[local_start:local_end]
            if not excerpt.strip():
                continue
            a,b=start+local_start,start+local_end
            digest=_sha(excerpt)
            identity=f'R{section+1:06d}-{ordinal:03d}-{digest[:10]}'
            kind=('explicit' if _REQUIREMENT_START.match(excerpt) else 'unstructured')
            output.append({'id':identity,'section_ordinal':section,
                           'start_char':a,'end_char':b,'sha256':digest,
                           'kind':kind,'master_sha256':master})
    return output


def declared_dependencies(steps: list[dict]) -> dict[str, tuple[str,...]]:
    """Parse only exact model declarations, reject dangling/self dependencies.

    The existing two-field file schema remains unchanged; dependencies are
    deliberately opt-in text *within* a model-authored description.
    """
    from .agent_plan import PlanError
    known={s['path'].casefold():s['path'] for s in steps}
    if len(known)!=len(steps):
        raise PlanError('Repeated file paths in dependency analysis')
    graph={s['path']:[] for s in steps}
    for step in steps:
        declarations=_DECLARATION.findall(step['description'])
        if any(raw.strip().casefold()=='none' for raw in declarations):
            if len(declarations)!=1:
                raise PlanError('Independent declaration cannot be combined with file dependencies')
            continue
        for raw in declarations:
            for entry in raw.split(','):
                candidate=entry.strip().replace('\\','/')
                if not candidate:
                    raise PlanError(f'Empty declared file dependency for {step["path"]}')
                dependency=known.get(candidate.casefold())
                if dependency is None:
                    raise PlanError(f'{step["path"]} declares a dependency on unknown file {candidate}; model must repair the plan')
                if dependency.casefold()==step['path'].casefold():
                    raise PlanError(f'{step["path"]} cannot depend on itself')
                if dependency not in graph[step['path']]:
                    graph[step['path']].append(dependency)
    return {k:tuple(v) for k,v in graph.items()}


def complete_dependencies(steps):
    """Opt in to a real dependency graph only with an explicit complete map.

    Undeclared dependencies remain unknown, not independent. Legacy plans
    and cross-milestone paths keep their existing conservative boundaries.
    """
    if not steps or not all(len(_DECLARATION.findall(s['description']))==1 for s in steps):return None
    known={s['path'].casefold() for s in steps}
    for s in steps:
        raw=_DECLARATION.findall(s['description'])[0].strip()
        if raw.casefold()=='none':continue
        if any(entry.strip().replace('\\','/').casefold() not in known for entry in raw.split(',')):
            return None
    _,graph=dependency_order(steps)
    return graph


def dependency_order(steps: list[dict]) -> tuple[list[dict], dict[str,tuple[str,...]]]:
    """Stable O((files+edges) log files) topological order.

    For the same collection of model-authored file intentions, always choose
    the earliest originally proposed path among currently ready files.  This
    keeps a 10,000-file project tractable while rejecting dependency cycles.
    """
    from .agent_plan import PlanError
    graph = declared_dependencies(steps)
    original_positions = {step['path']: position for position,step in enumerate(steps)}
    outgoing = {path: [] for path in original_positions}
    indegree = {path: len(dependencies) for path, dependencies in graph.items()}
    for path,dependencies in graph.items():
        for required in dependencies:
            outgoing[required].append(path)
    available = [position for path,position in original_positions.items() if not indegree[path]]
    heapq.heapify(available)
    ordered = []
    while available:
        position = heapq.heappop(available)
        step = steps[position]
        ordered.append(step)
        for dependent in outgoing[step['path']]:
            indegree[dependent] -= 1
            if not indegree[dependent]:
                heapq.heappush(available, original_positions[dependent])
    if len(ordered) != len(steps):
        raise PlanError('Declared model file dependencies contain a cycle; model must reconcile the plan')
    return ordered,graph


def check_dependency_schedule(groups: list[tuple[list[dict],list[int]]], graph: dict[str,tuple[str,...]]) -> None:
    """Dependency file must not be placed in a later milestone than consumer."""
    from .agent_plan import PlanError
    assigned={s['path']:i for i,(steps,_) in enumerate(groups,1) for s in steps}
    for path,depends in graph.items():
        for required in depends:
            if assigned[required]>assigned[path]:
                raise PlanError(f'Milestone scheduling puts {required} after its declared dependent {path}')
