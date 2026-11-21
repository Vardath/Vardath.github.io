"""Validate local-model project plans against their *actual* specifications.

A filename being safe is necessary, not sufficient. In particular, XML-based
X4 extensions must never be approved as generic Python entrypoints.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .workspace import safe_target

class PlanError(ValueError):
    pass


def project_kind(request: str) -> str:
    return 'x4' if re.search(r'\b(?:x4(?::?\s+foundations)?|egosoft|xenon\s+pe)\b', request or '', re.I) else 'general'


def validate_project_plan(steps: list[dict], request: str) -> list[dict]:
    """Fail closed on known domain-specific omissions. Never infer game IDs."""
    if project_kind(request) != 'x4':
        return steps
    paths = [str(s['path']).replace('\\', '/').casefold() for s in steps]
    notes = ' '.join(str(s['description']) for s in steps).casefold()
    combined = ' '.join(paths) + ' ' + notes
    missing = []
    if len(steps) < 4:
        missing.append('at least four X4 extension files, not a generic single-file program')
    if 'content.xml' not in paths:
        missing.append('extension metadata (content.xml)')
    if not any(p.startswith('md/') and p.endswith('.xml') for p in paths):
        missing.append('Mission Director XML (md/*.xml)')
    if not any(p.startswith(('assets/', 'libraries/')) and p.endswith('.xml') for p in paths):
        missing.append('game-specific ship/equipment asset XML (assets/ or libraries/)')
    # An X4 task must describe the relevant vanilla definitions and game-file evidence.
    if not re.search(r'vanilla|original|installed game|game assets|game definitions|references', notes):
        missing.append('inspection/verification of installed vanilla game definitions')
    # PE-specific requirements are mandatory only when that ship is requested.
    if re.search(r'\bxenon\s+pe\b|\bpe\s+(?:xenon|corvette|ship)\b', request or '', re.I):
        requirements = (
            ('ship variant / macro and equipment connection mapping', r'\b(?:pe|corvette)\b', r'connection|macro|ship'),
            ('cargo storage increase', r'cargo|storage', None),
            ('speed and handling changes', r'speed|velocity', r'handling|steer|maneuver|acceleration|rotation'),
            ('forward weapon upgrades', r'weapon|gun', None),
            ('turret upgrades', r'turret', None),
            ('player-owned ownership check and respawn', r'player.owned|ownership|player ship|owned ship|player faction', r'spawn|respawn|replacement'),
        )
        for label, first, second in requirements:
            if not re.search(first, combined, re.I) or (second and not re.search(second, combined, re.I)):
                missing.append(label)
        # Only demand numerical specifications the user actually requested.
        if re.search(r'\b50[\s,_.]*000\b|\b50k\b', request, re.I) and not re.search(r'\b50[\s,_.]*000\b|\b50k\b', combined, re.I):
            missing.append('50,000 damage per successful weapon/turret hit')
        if re.search(r'\b60\s*(?:seconds?|secs?)\b|\b1\s*min(?:ute)?\b', request, re.I) and not re.search(r'\b60\s*(?:seconds?|secs?)\b|\b1\s*min(?:ute)?\b', combined, re.I):
            missing.append('60-second ownership-monitor respawn timer')
        if re.search(r'\b4\s*(?:x|times)\b|\bquadrupl', request, re.I) and not re.search(r'\b4\s*(?:x|times)\b|\bquadrupl', combined, re.I):
            missing.append('four-times base speed')
        if re.search(r'\b10\s*(?:x|times)\b', request, re.I) and not re.search(r'\b10\s*(?:x|times)\b', combined, re.I):
            missing.append('ten-times cargo capacity')
    if any(p.endswith('.py') for p in paths):
        missing.append('X4 installable extension XML rather than Python application entrypoints')
    if missing:
        raise PlanError('Plan does not cover the X4 specification: ' + '; '.join(missing) + '. No work has been queued. Provide extracted vanilla references or inspect the installed X4 assets before trusting equipment identifiers.')
    return steps


def parse_build_plan(text: str, project: str | Path, *, request: str = '') -> list[dict]:
    raw = text.strip()
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.I)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise PlanError('Model did not return a valid JSON plan; review and retry.') from e
    if isinstance(data, dict) and 'blocked' in data:
        raise PlanError('Plan needs source inspection: ' + str(data.get('blocked', 'game references unavailable'))[:500])
    if not isinstance(data, dict) or set(data) != {'files'}:
        raise PlanError('Plan must contain only a "files" array')
    steps = data['files']
    if not isinstance(steps, list) or not 1 <= len(steps) <= 24:
        raise PlanError('Plan requires 1..24 files')
    paths = set()
    validated = []
    for step in steps:
        if not isinstance(step, dict) or set(step) != {'path', 'description'}:
            raise PlanError('Every file must specify path and description')
        path, desc = step['path'], step['description']
        if not isinstance(path, str) or not isinstance(desc, str) or not 3 <= len(desc) <= 1000:
            raise PlanError('Invalid step path or description')
        try:
            dest = safe_target(Path(project), path)
        except Exception as e:
            raise PlanError('Unsafe file path in model plan: ' + str(e)) from e
        rel = dest.relative_to(Path(project).resolve()).as_posix()
        if rel.casefold() in paths:
            raise PlanError('Duplicate file path in model plan')
        paths.add(rel.casefold())
        validated.append({'path': rel, 'description': desc.strip()})
    return validate_project_plan(validated, request)


def build_plan_prompt(request: str, inventory: dict | None = None, *, x4_evidence: str = '') -> str:
    tools = ', '.join(x['name'] for x in (inventory or {}).get('tools', []) if x.get('found'))
    header = ('Return ONLY valid JSON with a "files" array. Each entry needs "path" '
              'and "description". Choose concrete relative source files ordered by dependency, '
              'up to 24; no absolute paths or shell/install commands. Do not confuse an example '
              'format with the actual project type. Do NOT invent verified game asset identifiers.\n')
    if project_kind(request) == 'x4':
        domain = ('''This project is an X4: Foundations EXTENSION, not a Python app. NEVER output src/main.py.
Propose actual X4 XML file stages, including content.xml, ship macro/asset patches, separate customised weapons/turret macro definitions and a Mission Director md/*.xml ownership watcher when the user requests respawning.
The plan descriptions must explain how vanilla definitions and existing connection slots will be inspected, equipment verified, what needs an extracted game reference, and how all numeric user requirements (e.g. 50,000/hit, 4x speed, 10x cargo, 60-second replacement) will be validated. Do not fabricate the exact vanilla IDs.
If the available evidence cannot justify a trustworthy plan, return ONLY {"blocked":"Which X4 game definitions or extracted reference files must be inspected before selecting equipment"}; never output a generic fallback plan.
''')
    else:
        domain = ('Select source files appropriate to the USER project language/framework. '
                  'Do not default to Python unless the request demands Python.\n')
    evidence = ('\nVERIFIED LOCAL X4 REFERENCE CANDIDATES (not necessarily PE; cross-check each ID):\n' + x4_evidence + '\n') if x4_evidence else ''
    return header + domain + 'Local programs detected: ' + (tools or 'none') + evidence + '\nUSER PROJECT REQUIREMENTS:\n' + request


def build_budgeted_plan_prompt(request: str, inventory: dict | None = None, *,
                               x4_evidence: str = '', max_chars: int = 7500) -> str:
    """Fit verified auxiliary X4 evidence without ever trimming the user spec.

    Source inspection can add hundreds of characters after a saved request has
    already passed its length check. Keep the entire original specification and
    retain complete source-reference lines, preferring PE connections and at
    least one ship, weapon and turret definition. Never cut an identifier in
    half or silently pretend the user supplied less than they did.

    The complete inspection report remains on disk; this is only the small
    model's evidence window, not a mutation to its verified source files.
    """
    full = build_plan_prompt(request, inventory, x4_evidence=x4_evidence)
    if len(full) <= max_chars:
        return full
    # Preserve non-X4 behavior and avoid treating lost requirements as success.
    if project_kind(request) != 'x4' or not x4_evidence.strip():
        raise PlanError(
            f'Planning input requires {len(full):,} characters, exceeding the '
            f'{max_chars:,}-character local-model limit. The original request is saved in full.')

    header_only = build_plan_prompt(request, inventory)
    if len(header_only) >= max_chars:
        raise PlanError(
            f'The complete project specification and planning instructions require '
            f'{len(header_only):,} characters (limit {max_chars:,}). Nothing was '
            'truncated, and no job was queued.')

    lines = [line.strip() for line in x4_evidence.splitlines() if line.strip()]
    # Entries carry full filenames and IDs; SHA snippets are dispensable here
    # because the verified reference files and source hashes remain on disk.
    lines = [re.sub(r'\s+SHA\s+[0-9a-fA-F]{8,64}$', '', line) for line in lines]
    priority = ('PE connection:', 'ship_candidates:', 'weapon_candidates:',
                'turret_candidates:', 'storage_candidates:')
    # Reserve a representative source of each essential kind before adding
    # remaining connection slots and alternative equipment candidates.
    essentials = []
    for category in priority:
        match = next((line for line in lines if line.startswith(category)), None)
        if match is not None:
            essentials.append(match)
    ordered = essentials + [line for line in lines if line not in essentials]

    selected = []
    for line in ordered:
        candidate = build_plan_prompt(request, inventory, x4_evidence='\n'.join(selected + [line]))
        if len(candidate) <= max_chars:
            selected.append(line)
    required = [category for category in priority[:4]
                if any(line.startswith(category) for line in lines)]
    missing = [category for category in required
               if not any(line.startswith(category) for line in selected)]
    if not selected or missing:
        raise PlanError(
            'The complete specification fits but essential X4 reference evidence '
            f'cannot fit alongside it ({", ".join(missing) or "no complete line"}). '
            'No user requirements were shortened; no executable job was queued.')
    result = build_plan_prompt(request, inventory, x4_evidence='\n'.join(selected))
    assert len(result) <= max_chars and request in result
    return result


def file_step_prompt(user_request: str, path: str, description: str, existing: str,
                     siblings: list[dict]) -> str:
    overview = '\n'.join(f"{s['path']}: {s['description']}" for s in siblings)
    return (f'Generate ONLY the complete source file, not markdown or a patch. '
            f'Do not claim to have built or tested anything.\nPROJECT REQUEST:\n{user_request}'
            f'\nCOMPLETE PLAN:\n{overview}\nCURRENT FILE: {path}\nSTEP GOAL: {description}'
            f'\nEXISTING CONTENT:\n{existing}\nReturn the complete file text.')


def source_grounded_pe_plan(request: str, report: dict) -> list[dict]:
    """Recover a *review-only* X4 PE draft after an invalid small-model answer.

    Never infer actual ship identifiers from chat history or catalog filenames.
    A local preflight must have inspected the exact vanilla PE macro, physical
    connection slots and real weapon/turret definitions. This returns file
    intentions, NOT executable game assets or user approval to write them.
    """
    if not re.search(r'\b(?:xenon\s+pe|pe\s+(?:xenon|corvette|ship))\b',request or '',re.I):
        raise PlanError('Only an explicitly requested Xenon PE can use this fallback plan')
    if not isinstance(report,dict) or not (report.get('ready_for_planning')
        and report.get('pe_macro_verified') and report.get('pe_component_verified')
        and report.get('weapon_candidates') and report.get('turret_candidates')
        and report.get('pe_component_connections')):
        raise PlanError('Actual PE macro, component slots and weapon/turret XML must be verified first')
    pe=next((x for x in report.get('ship_candidates',[])
             if 'ship_xen_m_corvette_02_a_macro' in ' '.join(x.get('identifiers',[]))),None)
    if not pe:
        raise PlanError('Verified PE macro source is not present in the inspected ship candidates')
    ship_file=pe['file']
    comp_file=report.get('pe_component_file')
    if not comp_file:
        raise PlanError('Verified PE component XML path is unavailable')
    gun=report['weapon_candidates'][0]['file']
    turret=report['turret_candidates'][0]['file']
    slot_count=len(report['pe_component_connections'])
    return [
        {'path':'content.xml','description':
          'Create stand-alone Vardath Xenon PE X4 extension metadata, with no unrelated game overrides; validate the installed X4 version and extension loading.'},
        {'path':'assets/units/size_m/macros/vardath_xen_pe_macro.xml','description':
          f'Inspect verified vanilla PE macro {ship_file} and component {comp_file}; clone into an isolated player-only macro with 10x cargo/storage, and preserve actual equipment connections. '
          f'Reconcile all {slot_count} identified PE connection tags without inventing equipment IDs.'},
        {'path':'assets/units/size_m/vardath_xen_pe.xml','description':
          f'Create or register an isolated PE component from verified vanilla source {comp_file}, keeping functional connection tags. '
          'Improve 4x base speed with correctly compatible propulsion and improve acceleration, handling, turning and braking; verify actual installed engine definitions.'},
        {'path':'assets/props/WeaponSystems/macros/vardath_pe_weapon_macro.xml','description':
          f'Inspect source weapon XML {gun} and PE connections, then create a separate compatible high-fire-rate main weapon; 50,000 damage per successful hit, not DPS. '
          'Do not alter all vanilla ships.'},
        {'path':'assets/props/WeaponSystems/macros/vardath_pe_turret_macro.xml','description':
          f'Inspect source turret XML {turret} and original PE turret connection tags, then create a separate high-fire-rate compatible turret; 50,000 damage per successful hit. '
          'Do not affect ordinary faction equipment.'},
        {'path':'index/macros.xml','description':
          'Register the dedicated PE, engine/equipment and turret macros using verified installed-game index conventions. Do not register generic Python applications.'},
        {'path':'md/vardath_xen_pe.xml','description':
          'Create a save-safe Mission Director 60-second player-owned ownership monitor and replacement spawn; equip the separate PE variant with validated main weapon and turret connections. '
          'Spawn exactly one after 60 seconds when the player no longer owns one, including existing saves, without duplication.'},
        {'path':'README.md','description':
          'Document installation, source evidence, static XML and game-asset validation, 10x cargo, 4x speed/handling, 50,000 per-hit weapons/turrets, ownership respawn, and outstanding in-game verification.'},
    ]


def budgeted_file_step_prompt(user_request: str, path: str, description: str,
                              existing: str, siblings: list[dict], *, max_chars: int=7500) -> str:
    """Keep full user specification and current-file goal, compress only plan metadata.

    Truncation of user instructions or existing source is never permitted.
    """
    full=file_step_prompt(user_request,path,description,existing,siblings)
    if len(full)<=max_chars:
        return full
    core=(f'Generate ONLY the complete source file; no markdown or patch. Do not claim testing.\n'
          f'ORIGINAL PROJECT REQUIREMENTS (full):\n{user_request}\n'
          f'CURRENT FILE: {path}\nSTEP GOAL: {description}\n'
          f'EXISTING CONTENT (full):\n{existing}\n'
          'Return the complete file text. Verify references from installed sources; never fabricate IDs.\n')
    if len(core)>max_chars:
        raise PlanError(f'Full specification, current goal and existing content require {len(core):,} '
                        f'characters; model limit is {max_chars:,}. No user requirements were shortened.')
    overview='OTHER PLANNED FILE PATHS:\n'
    for item in siblings:
        line=str(item['path'])+'\n'
        if len(core)+len(overview)+len(line)<=max_chars:
            overview+=line
    return core+overview
