"""Validate local-model project plans against their *actual* specifications.

A filename being safe is necessary, not sufficient. In particular, XML-based
X4 extensions must never be approved as generic Python entrypoints.
"""
from __future__ import annotations
import json
import re
from .flight_recorder import record
from pathlib import Path
from .workspace import safe_target

class PlanError(ValueError):
    pass

class VanillaSourceCollision(PlanError):
    """A single proposed output would replace an inspected game definition."""

    def __init__(self, path: str):
        self.path = path
        super().__init__('The proposed output shadows an inspected vanilla source. Choose a new variant filename: '+path)


def extension_id(request: str) -> str:
    match = re.search(r'(?im)^\s*(?:[-*]\s*)?(?:independent extension|extension id)\s*:\s*`?([a-z0-9_-]+)`?\s*$', request)
    return match[1].lower() if match else ''


# Maximum number of independent local-model planning passes. A validated
# proposal returns immediately; invalid/repeated proposals can be revised.
MAX_PLAN_ATTEMPTS = 40


def project_kind(request: str) -> str:
    request = request or ''
    # A new Android game may cite X4 as an inspiration; it must not be forced
    # through the unrelated X4 extension preflight/validator on that basis.
    actual_android_game = re.search(
        r'\b(?:faction command|android\s+(?:2d\s+)?game|mobile\s+(?:2d\s+)?game|'
        r'game\s+(?:for\s+)?android)\b', request, re.I)
    explicit_x4_mod = re.search(
        r'\b(?:x4\s+(?:foundations\s+)?(?:mod|extension)|mod\s+for\s+x4|xenon\s+pe)\b',
        request, re.I)
    if actual_android_game and not explicit_x4_mod:
        return 'android_game'
    if re.search(r'\b(?:x4(?::?\s+foundations)?|egosoft|xenon\s+pe)\b', request, re.I):
        return 'x4'
    if re.search(r'\b(?:game|faction command|apk)\b', request, re.I) and re.search(
            r'\b(?:build|make|create|develop|implement|game|android)\b', request, re.I):
        return 'android_game' if re.search(r'\b(?:android|apk)\b', request, re.I) else 'game'
    return 'general'


def incompatible_x4_path(path: str, request: str='') -> bool:
    """Identify application scaffolding that cannot be loaded as X4 extension content."""
    rel = path.replace('\\', '/').casefold()
    if rel.startswith(('tools/','tests/')) and rel in request.replace('\\','/').casefold().split('`'):
        return False  # A deliberately named companion script is a separate deliverable.
    return (rel.startswith(('src/main/', 'src/test/', 'app/src/', 'content/x4/', 'x4/extensions/',
                            'game/extensions/', 'x4 foundations/extensions/'))
            or rel.endswith(('.py', '.java', '.kt', '.cpp', '.cs', '.class')))


def _x4_output_path(relative: str, request: str, evidence: str) -> str:
    """Accept a packaging prefix only when its extension ID matches the user's explicit ID."""
    identity = extension_id(request)
    wrapper = re.fullmatch(r'(?:content/x4/|x4/)?extensions/([^/]+)/(.+)', relative, re.I)
    if wrapper and identity and wrapper[1].casefold()==identity:
        inner = wrapper[2].casefold()
        if inner=='content.xml' or inner.startswith(('assets/','libraries/','md/','index/','t/','ui/','maps/','aiscripts/')):
            relative = wrapper[2]
        else:
            raise PlanError('The packaged proposal does not identify a recognized extension destination: '+relative)
    if incompatible_x4_path(relative,request):
        raise PlanError('The X4 specification requires an extension-relative output. Rejected application path: '+relative)
    if re.search(r'independent (?:ship|variant|extension)',request,re.I):
        # A matching game-relative path would override an inspected vanilla
        # definition even inside a separate extension directory.
        for line in evidence.splitlines():
            match = re.match(r'\w+_candidates:\s+(.+?) IDs ', line)
            if match and relative.casefold()==match[1].casefold():
                raise VanillaSourceCollision(relative)
    return relative


def validate_project_plan(steps: list[dict], request: str) -> list[dict]:
    """Fail closed on known domain-specific omissions. Never infer game IDs."""
    kind = project_kind(request)
    if kind == 'general':
        return steps
    if kind in ('game', 'android_game'):
        paths = [str(s['path']).replace('\\', '/').casefold() for s in steps]
        details = ' '.join(str(s['description']) for s in steps).casefold()
        joined = ' '.join(paths) + ' ' + details
        missing = []
        if len(steps) < 4:
            missing.append('multiple substantive project files rather than a single stub')
        if not any(re.search(r'\.(?:kt|java|gd|cs|js|ts|tsx|py|lua|rs|cpp|c|h)$', p) for p in paths):
            missing.append('actual game source code, not just documentation')
        if not re.search(r'gameplay|game logic|simulation|game loop|entity|sector|combat|movement|turn logic', joined):
            missing.append('gameplay or simulation implementation')
        if not re.search(r'interface|ui|screen|scene|view|menu|input', joined):
            missing.append('playable interface or scene/input implementation')
        if kind == 'android_game' and not re.search(
            r'gradle|androidmanifest|project\.godot|export_presets|unity|android build|apk build', joined):
            missing.append('a genuine Android-compatible game build configuration')
        if not re.search(r'test|validation|verify|acceptance', joined):
            missing.append('verification and test plan')
        if missing:
            raise PlanError('Game plan is incomplete: ' + '; '.join(missing) + '. No work was queued.')
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
        # A manifest or README mentioning a weapon, mesh or timer cannot
        # implement it. Bind coverage to proposed game assets and MD scripts.
        def scoped(prefixes):
            return ' '.join(p+' '+s['description'].casefold() for p,s in zip(paths,steps)
                            if p.startswith(prefixes) and p.endswith('.xml'))
        assets = scoped(('assets/', 'libraries/'))
        mission = scoped(('md/',))
        combined = assets + ' ' + mission
        requirements = (
            ('ship variant / macro and equipment connection mapping', r'\b(?:pe|corvette)\b', r'connection|macro|ship'),
            ('cargo storage increase', r'cargo|storage', None),
            ('speed and handling changes', r'speed|velocity', r'handling|steer|maneuver|acceleration|rotation'),
            ('forward weapon upgrades', r'weapon|gun', None),
            ('turret upgrades', r'turret', None),
            ('player-owned ownership check and respawn', r'player.owned|ownership|player ship|owned ship|player faction', r'spawn|respawn|replacement'),
        )
        for label, first, second in requirements:
            scope = mission if label.startswith('player-owned') else assets
            if label == 'cargo storage increase' and not re.search(r'(?i)\b(?:cargo|storage)\s+(?:capacity|storage|increase)|\b(?:increase|more|[\d.]+\s*[×x])\s+(?:the\s+)?cargo\b', request):
                continue
            if not re.search(first, scope, re.I) or (second and not re.search(second, scope, re.I)):
                missing.append(label)
        if re.search(r'asteroid', request, re.I) and re.search(r'mesh|geometry', request, re.I):
            geometry = scoped(('assets/',))
            if not all(re.search(p,geometry) for p in ('asteroid', 'mesh|geometry|model', 'scal|siz')):
                missing.append('scaled asteroid mesh and ship geometry under assets/')
        if re.search(r'crew', request, re.I) and re.search(r'replace lost crew', request, re.I):
            if not re.search(r'crew',mission) or not re.search(r'replenish|replace|restock|refill',mission):
                missing.append('Mission Director crew replacement')
        if re.search(r'replenish',request,re.I) and re.search(r'consumables?', request, re.I):
            if not re.search(r'consumable|satellite|drone|flares',mission) or not re.search(r'replenish|restock|refill',mission):
                missing.append('Mission Director consumable replenishment')
        if re.search(r'blueprints?',request,re.I) and re.search(r'wharfs?|wharves',request,re.I):
            if not re.search(r'blueprints?',combined) or not re.search(r'wharf|wharves|production',combined):
                missing.append('wharf production and blueprint access')
        # Only demand numerical specifications the user actually requested.
        if re.search(r'\b50[\s,_.]*000\b|\b50k\b', request, re.I) and not re.search(r'\b50[\s,_.]*000\b|\b50k\b', combined, re.I):
            missing.append('50,000 damage per successful weapon/turret hit')
        if re.search(r'\b60\s*(?:seconds?|secs?)\b|\b1\s*min(?:ute)?\b', request, re.I) and not re.search(r'\b60\s*(?:seconds?|secs?)\b|\b1\s*min(?:ute)?\b', combined, re.I):
            missing.append('60-second ownership-monitor respawn timer')
        fourfold = r'\b4\s*(?:×|x\b|times\b)|\bquadrupl'
        if re.search(fourfold, request, re.I) and not re.search(fourfold, combined, re.I):
            missing.append('four-times base speed')
        if re.search(r'\b10\s*(?:x|times)\b', request, re.I) and not re.search(r'\b10\s*(?:x|times)\b', combined, re.I):
            missing.append('ten-times cargo capacity')
        # Asset registration and independent projectile definitions are
        # dependency checks, not a prewritten plan. The local model must choose
        # the actual file paths and explain how source definitions are reused.
        new_asset_macros = any(p.startswith('assets/') and '/macros/' in p for p in paths)
        if new_asset_macros and 'index/macros.xml' not in paths:
            missing.append('index/macros.xml for independently named asset macros')
        new_components = any(p.startswith('assets/units/') and p.endswith('.xml')
                             and '/macros/' not in p for p in paths)
        if new_components and 'index/components.xml' not in paths:
            missing.append('index/components.xml to register a new component or reuse the vanilla component instead')
        if re.search(r'\b50[\s,_.]*000\b|\b50k\b', request, re.I):
            if not any(re.search(r'bullet|projectile', p) for p in paths):
                missing.append('independent projectile/bullet definition for per-hit damage')
        # Verified PE slots are M-class. L/XL capital-class candidates from
        # an alphabetical catalog scan cannot be used as PE equipment.
        if re.search(r'\b(?:weapon|turret)_[a-z0-9]+_(?:l|xl)_', notes):
            missing.append('reject L/XL-class weapon or turret source references on the M-class PE')
    if any(incompatible_x4_path(p,request) for p in paths):
        missing.append('installable X4 extension layout (remove unrelated application source paths)')
    if missing:
        raise PlanError('Plan does not cover the X4 specification: ' + '; '.join(missing) + '. No work has been queued. Provide extracted vanilla references or inspect the installed X4 assets before trusting equipment identifiers.')
    return steps


def parse_build_plan(text: str, project: str | Path, *, request: str = '',
                     fragment: bool = False, inspected_evidence: str = '') -> list[dict]:
    raw = text.strip()
    if raw.startswith('```'):
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.I)
        raw = re.sub(r'\s*```$', '', raw)
    try:
        data = json.loads(raw)
    except ValueError:
        # A small local model may prefix an otherwise valid plan with prose.
        # Accept only one complete JSON object with our exact known schema;
        # never infer a missing bracket, path, description, or file intention.
        decoder = json.JSONDecoder()
        embedded = []
        for match in re.finditer(r'\{', raw):
            try:
                candidate, end = decoder.raw_decode(raw, match.start())
            except ValueError:
                continue
            if isinstance(candidate, dict) and set(candidate) in ({'files'}, {'blocked'}):
                embedded.append((candidate, match.start(), end))
        if len(embedded) != 1:
            raise PlanError('Model did not return one complete valid JSON plan object; review and retry.')
        data = embedded[0][0]
    if isinstance(data, dict) and 'blocked' in data:
        raise PlanError('Plan needs source inspection: ' + str(data.get('blocked', 'game references unavailable'))[:500])
    if not isinstance(data, dict) or set(data) != {'files'}:
        raise PlanError('Plan must contain only a "files" array')
    steps = data['files']
    if not isinstance(steps, list) or not 1 <= len(steps) <= 24:
        raise PlanError('Plan requires 1..24 files')
    paths = set()
    validated = []
    x4 = project_kind(request) == 'x4'
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
        if x4:
            try:
                canonical = _x4_output_path(rel,request,inspected_evidence)
            except VanillaSourceCollision as exc:
                if len(steps) != 1:
                    raise PlanError(str(exc)) from exc
                raise
            if rel != canonical:
                try:
                    rel = safe_target(Path(project), canonical).relative_to(Path(project).resolve()).as_posix()
                except ValueError as exc:
                    raise PlanError('Unsafe extension-relative output path') from exc
        from .artifact_types import require_text_target
        try:require_text_target(rel)
        except ValueError as exc:raise PlanError(str(exc)) from exc
        if rel.casefold() in paths:
            raise PlanError('Duplicate file path in model plan')
        paths.add(rel.casefold())
        validated.append({'path': rel, 'description': desc.strip()})
    return validated if fragment else validate_project_plan(validated, request)


def build_plan_prompt(request: str, inventory: dict | None = None, *, x4_evidence: str = '') -> str:
    tools = ', '.join(x['name'] for x in (inventory or {}).get('tools', []) if x.get('found'))
    header = ('Return ONLY valid JSON with a "files" array. Each entry needs "path" '
              'and "description". Declare actual prerequisite files in descriptions as "; depends-on: path1, path2"; '
              'use "; depends-on: none" only when a file truly has no planned file prerequisite. '
              'Omit the declaration if uncertain; never invent dependencies or independence. Choose concrete relative source files, '
              'up to 2 in this first pass; subsequent passes will complete the plan. Keep each description short and concrete. No absolute paths or shell/install commands. Do not confuse an example '
              'format with the actual project type. Do NOT invent verified game asset identifiers. '
              'Plan text source and asset-generation scripts here, not binary images, models, audio, executables or packages. Native outputs require a separate artifact workflow.\n')
    if project_kind(request) == 'x4':
        domain = ('''This project is an X4: Foundations EXTENSION, not a Python app. NEVER output src/main.py.
Propose actual X4 XML file stages, including content.xml, ship macro/asset patches, separate customised weapons/turret macro definitions and a Mission Director md/*.xml ownership watcher when the user requests respawning.
The plan descriptions must explain how vanilla definitions and existing connection slots will be inspected, equipment verified, what needs an extracted game reference, and how all numeric user requirements (e.g. 50,000/hit, 4x speed, 10x cargo, 60-second replacement) will be validated. Do not fabricate the exact vanilla IDs.
If the available evidence cannot justify a trustworthy plan, return ONLY {"blocked":"Which X4 game definitions or extracted reference files must be inspected before selecting equipment"}; never output a generic fallback plan.
''')
    elif project_kind(request) in ('game', 'android_game'):
        domain = ('This request is for a functioning game, not a mockup. Inspect the existing '
                  'project if present; choose actual source, gameplay simulation, screens, '
                  'build configuration and verification files appropriate to the specified '
                  'engine and platform. Do not replace the user design with a generic demo.\n')
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


def remaining_plan_gaps(steps: list[dict], request: str) -> list[str]:
    """Extract the existing validator's unmet criteria for targeted model feedback.

    Nothing is added to the plan here. Validator findings (not a hardcoded
    ship or game file template) determine what the model should investigate.
    """
    try:
        validate_project_plan(steps, request)
        return []
    except PlanError as exc:
        message = str(exc)
        for prefix in ('Plan does not cover the X4 specification: ',
                       'Game plan is incomplete: '):
            if message.startswith(prefix):
                message = message[len(prefix):]
                break
        message = message.split('. No work', 1)[0]
        message = message.split('. No work has', 1)[0]
        return [gap.strip().removesuffix('.') for gap in message.split(';') if gap.strip()]


def planning_focus(steps: list[dict], request: str, pass_number: int) -> str:
    """Rotate specific unsatisfied criteria even when invalid output adds no files."""
    gaps = remaining_plan_gaps(steps, request)
    specific = [g for g in gaps if not g.startswith(('at least four ', 'multiple substantive '))]
    pool = specific or gaps
    return pool[(max(1, pass_number) - 2) % len(pool)] if pool else 'correct the rejected output format'



def revision_focus(steps: list[dict], request: str, pass_number: int,
                   previous: str, stalled: int) -> str:
    """Give a missing criterion two attempts before rotating, not 40 repeats."""
    gaps = remaining_plan_gaps(steps, request)
    if previous and previous in gaps:
        if stalled < 2:
            return previous
        return gaps[(gaps.index(previous) + 1) % len(gaps)]
    return planning_focus(steps, request, 2)


def build_revision_prompt(request: str, steps: list[dict], problems: str, *,
                          x4_evidence: str = '', max_chars: int = 7500,
                          path_window: int = 0, focus: str = '',
                          format_recovery: bool = False) -> str:
    """Ask the model to repair its own proposal within a bounded context.

    Never truncate the original specification or alter/drop accumulated plan
    steps. The small model sees a whole-path subset when its context cannot
    hold the entire plan. The full plan remains in ``generate_model_plan`` and
    is revalidated before a draft can ever be approved. A later revision can
    rotate the subset instead of failing just because the model proposed many
    long paths. No files/plan steps are manufactured here.
    """
    header = (
        'Revise your incomplete plan. Return ONLY JSON '
        '{"files":[{"path":"relative/file.xml","description":"precise implementation"}]}. '
        'Propose 1–2 new files or substantive corrections; no unchanged entries. '
        'Earlier model files are retained locally. Verify game IDs; never invent them. '
        'Do not claim execution or testing.\n'
    )
    if format_recovery:
        # Repeated malformed responses have dominated actual Windows inference.
        # Ask for a single complete object, not another long truncated batch.
        # This does NOT generate a plan or weaken the normal validator.
        header = (
            'FORMAT RECOVERY: Previous response was not complete JSON. '
            'Return exactly ONE complete JSON object with ONE file: '
            '{"files":[{"path":"relative/file.ext","description":"one concrete step"}]}. '
            'Use a relevant path and a brief description (under 160 characters). '
            'Close all braces and brackets. No prose, markdown, or repeated files. '
            'Previous accepted files are retained locally.\n'
        )
    findings = str(problems).split('. No work',1)[0].strip()[:560]
    target = ('PRIMARY TARGET FOR THIS PASS (a criterion still missing from the '
              'accumulated plan): ' + focus[:180] + '\n'
              'Propose a source file addressing this target. Do not repeat an '
              'existing unchanged file. If a file already exists, improve its description. '
              'Do not write a complete essay or repeat the entire specification.\n') if focus else ''
    # Keep the complete original requirement text in EVERY model revision.
    # The user explicitly requires this; narrow the validator's focus and
    # optional metadata instead of dropping pieces of the specification.
    base = header + target + 'VALIDATOR FINDINGS:\n' + findings + \
           '\nORIGINAL SPECIFICATION (COMPLETE):\n' + request + '\n'
    if len(base) >= max_chars:
        raise PlanError('Complete original specification and correction instructions do not fit '
                        f'within {max_chars:,} characters; no specification was truncated.')

    # The original request, accumulated steps and full inspected evidence are
    # authoritative in local state. Context selection is NOT a state mutation.
    # Reserve space for a truthful omitted-path count before fitting entries.
    # Use entire paths (never incomplete/ambiguous file names).
    remaining = max_chars - len(base)
    if path_window < 0:
        raise ValueError('path_window must be nonnegative')
    path_list = [str(step['path']) for step in steps]
    manifest_header = f'PREVIOUS MODEL-PROPOSED FILES (total {len(path_list)}; saved locally):\n'
    # The old manifest contained paths alone. The model consequently had no
    # information about what each existing file was intended to implement,
    # frequently overwrote good descriptions and lost validated coverage.
    # Reserve a few complete, focus-relevant descriptions before plain paths.
    terms = {word for word in re.findall(r'[a-z]{4,}', focus.casefold())
             if word not in ('this','that','with','from','file','files','plan','missing')}
    related = sorted(range(len(steps)), key=lambda i: (
        -sum(term in (steps[i]['path']+' '+steps[i]['description']).casefold() for term in terms), i))
    detailed_indices = set(related[:3]) if focus else set()
    omitted_reserve = 130
    manifest_lines = []
    selected_indices = set()
    if len(manifest_header) + omitted_reserve <= remaining and path_list:
        # Rotate first position in later passes if the manifest is too large.
        begin = path_window % len(path_list)
        ordered_indices = list(range(begin, len(path_list))) + list(range(begin))
        used = len(manifest_header) + omitted_reserve
        for index in ordered_indices:
            detail = str(steps[index]['description']).replace('\n', ' ').strip()
            line = (path_list[index] + '\n  purpose: ' + detail[:170] + '\n'
                    if index in detailed_indices else path_list[index] + '\n')
            if used + len(line) <= remaining:
                manifest_lines.append(line)
                selected_indices.add(index)
                used += len(line)
        manifest = manifest_header + ''.join(manifest_lines)
    else:
        manifest = ''
    omitted = len(path_list) - len(selected_indices)
    if omitted:
        warning = (f'{omitted} other existing paths are omitted from THIS model context '
                   'only; all are retained for merging and validation.\n')
        # This warning must fit even if the request left very little space.
        if len(manifest) + len(warning) > remaining:
            manifest = ''
        if len(warning) <= remaining - len(manifest):
            manifest += warning
    remaining -= len(manifest)

    evidence_header = 'VERIFIED SOURCE CANDIDATES (inspect before selecting):\n'
    evidence_lines = []
    if remaining >= len(evidence_header):
        # Deduplicate and prefer game connections before secondary candidates.
        raw = [re.sub(r'\s+SHA\s+[0-9a-fA-F]{8,64}$', '', item.strip())
               for item in (x4_evidence or '').splitlines() if item.strip()]
        priority = ('PE connection:', 'ship_candidates:', 'weapon_candidates:',
                    'turret_candidates:', 'storage_candidates:')
        essential = []
        for category in priority:
            line = next((item for item in raw if item.startswith(category)), None)
            if line is not None and line not in essential:
                essential.append(line)
        ordered = essential + [item for item in raw if item not in essential]
        used = len(evidence_header)
        for line in ordered:
            item = line + '\n'
            if used + len(item) <= remaining:
                evidence_lines.append(item)
                used += len(item)
        evidence = evidence_header + ''.join(evidence_lines) if evidence_lines else ''
    else:
        evidence = ''
    result = base + manifest + evidence
    assert request in result and len(result) <= max_chars
    return result


def generate_model_plan(client, session: str, request: str, project: str | Path,
                        first_prompt: str, *, x4_evidence: str = '',
                        max_chars: int = 7500, max_rounds: int = MAX_PLAN_ATTEMPTS,
                        stage=None, cancelled=None, continuation=None,
                        chat_id: str = '', checkpoint=None, reviewer=None) -> tuple[str, list[dict]]:
    """Generate a complete plan through bounded, evidence-driven model revisions.

    No file intentions are hardcoded here. Each proposed path/description must
    originate in local model output. The validator can reject or request more;
    it never manufactures a substitute plan. No executable work is queued.
    """
    if not 1 <= max_rounds <= MAX_PLAN_ATTEMPTS:
        raise ValueError(f'max_rounds must be 1..{MAX_PLAN_ATTEMPTS}')
    if len(first_prompt) > max_chars:
        raise PlanError('Initial planning request exceeds the model context limit')
    recovered = continuation.load(project,request,x4_evidence,context=first_prompt) if continuation else []
    if project_kind(request) == 'x4':
        recovered = [step for step in recovered if not incompatible_x4_path(step['path'],request)]
    if reviewer and recovered:
        accepted=[]
        for item in recovered:
            try:reviewer([item])
            except PlanError:continue
            accepted.append(item)
        recovered=accepted
    all_steps: dict[str, dict] = {x['path'].casefold():x for x in recovered}
    # Even a structurally valid saved fragment is not a validated project plan.
    # Re-evaluate the full current specification before accepting any draft.
    if recovered:
        if stage:stage(f'Restored {len(recovered)} prior model-authored file proposals '
                       'for this exact project, specification and X4 evidence; revalidating')
        try:
            validated=validate_project_plan(list(all_steps.values()),request)
        except PlanError:
            pass
        else:
            if continuation:continuation.clear(project,request,x4_evidence,context=first_prompt)
            return json.dumps({'files':validated},ensure_ascii=False),validated
    failures = []
    seen_answers = set()
    invalid_format_answers = set()
    prompt = first_prompt
    previous_focus = ''
    stagnant_on_focus = 0
    malformed_streak = 0
    for round_no in range(1, max_rounds + 1):
        if cancelled is not None and cancelled():
            raise PlanError('Planning stopped by user; original request is preserved')
        focus = ('' if round_no == 1 else revision_focus(
            list(all_steps.values()), request, round_no,
            previous_focus, stagnant_on_focus))
        if stage:
            stage(f'Local model planning — pass {round_no}/{max_rounds}; '
                  f'{len(all_steps)} files retained; next gap: {focus[:82]}')
        # A fresh request session prevents previous 7K-character planning inputs
        # from polluting the next call or crossing chat/project boundaries.
        # Each completed pass is already stored by LocalModelClient.chat in
        # sessions.sqlite3. An interrupted 40-pass run must replay those exact
        # model outputs locally, not spend another hour regenerating them.
        # Only reuse when the full revision prompt is identical; changed source
        # evidence or user instructions always require a fresh model answer.
        round_session = f'{session}-{round_no}'
        if checkpoint:
            prompt, instruction = checkpoint.attach(prompt, max_chars)
        lookup = getattr(client, 'completed_exchange', None)
        cached = lookup(round_session, prompt) if callable(lookup) else None
        if cached is None and chat_id:
            restore = getattr(client, 'historical_plan_exchange', None)
            if callable(restore):
                cached = restore(prompt, project=project, request=request, chat_id=chat_id)
                if cached is not None and stage:
                    stage('Recovered an exact-input, pre-v46 completed model reply ' 
                          'from local session history; checking current plan rules')
        if cached is not None:
            answer = cached
            if stage:
                stage(f'Planning pass {round_no}/{max_rounds} restored from '
                      'a completed local inference; no model time consumed')
        else:
            # The original 5K prompt-length gate was unreachable in practice:
            # real X4 revisions are ~7K and repeatedly returned malformed JSON
            # with a hard 384-token ceiling. Scale the output budget based on
            # consecutive format failures, independent of input length. A
            # compact one-file recovery request avoids unnecessary long output.
            tokens = (768 if malformed_streak >= 2 else
                      640 if malformed_streak else 384)
            answer = client.chat(round_session, prompt, max_tokens=tokens)
        if checkpoint:
            checkpoint.received(instruction, round_session, prompt, answer)
        if cancelled is not None and cancelled():
            raise PlanError('Planning stopped by user; no later passes will run')
        count_before = len(all_steps)
        revised_count = 0
        repeated = answer.strip() in seen_answers
        if repeated:
            # Do not abort a long planning task just because the small model
            # repeated an earlier INVALID answer. Record concrete feedback and
            # give the model another opportunity to correct it. No step is
            # added and no approval is possible from a repeated invalid draft.
            if answer.strip() in invalid_format_answers:
                finding = ('Model did not return one complete valid JSON plan object; '
                           'it repeats an earlier rejected malformed response. Return one '
                           'new, short, complete JSON object.')
            else:
                finding = ('The last proposal exactly repeats an earlier rejected '
                           'answer. It contributed no valid new files. Supply '
                           'different source-backed files or corrections that '
                           'address the validator findings; do not repeat unchanged JSON.')
        else:
            seen_answers.add(answer.strip())
            try:
                fragment = parse_build_plan(answer, project, request=request, fragment=True, inspected_evidence=x4_evidence)
                if reviewer:reviewer(fragment)
                # Merge transactionally. A bad fragment cannot permanently
                # poison the retained plan with >24 distinct paths and make
                # every remaining revision fail, regardless of its quality.
                candidate_steps = dict(all_steps)
                for entry in fragment:
                    if candidate_steps.get(entry['path'].casefold()) != entry:
                        revised_count += 1
                    candidate_steps[entry['path'].casefold()] = entry
                if len(candidate_steps) > 24:
                    raise PlanError('The proposed additions would exceed the '
                                    '24-file plan limit. Correct existing paths '
                                    'rather than adding more unrelated files.')
                # A rewrite of existing descriptions must not erase coverage
                # already established by an earlier accepted model proposal.
                # Newly introduced files can create fresh registration dependencies
                # and are therefore permitted to add *conditional* gaps.
                before = set(remaining_plan_gaps(list(all_steps.values()), request))
                after = set(remaining_plan_gaps(list(candidate_steps.values()), request))
                has_new_paths = any(key not in all_steps for key in candidate_steps)
                if not has_new_paths and after - before:
                    raise PlanError('Revision would remove already satisfied requirements: '
                                    + '; '.join(sorted(after-before)))
                all_steps = candidate_steps
                if continuation and revised_count:
                    continuation.save(project,request,x4_evidence,list(all_steps.values()),context=first_prompt)
                try:
                    approved_shape = validate_project_plan(list(all_steps.values()), request)
                except PlanError as exc:
                    finding = str(exc)
                else:
                    # Still only a draft. Execution requires explicit approval.
                    if continuation:continuation.clear(project,request,x4_evidence,context=first_prompt)
                    return json.dumps({'files': approved_shape}, ensure_ascii=False), approved_shape
            except PlanError as exc:
                finding = str(exc)
        # Valid partial JSON need not pass the full project validator yet;
        # count only structural format errors, never missing X4 requirements.
        malformed = finding.startswith((
            'Model did not return one complete valid JSON plan object',
            'Plan must contain only a \"files\" array',
            'Plan requires 1..24 files',
            'Every file must specify path and description',
            'Invalid step path or description',
        ))
        if malformed:
            invalid_format_answers.add(answer.strip())
        malformed_streak = malformed_streak + 1 if malformed else 0
        failures.append(finding)
        gaps = remaining_plan_gaps(list(all_steps.values()), request)
        # Only counts and bounded criteria go into diagnostics, never the
        # private original specification, proposed paths or model replies.
        db = getattr(client, 'db', None)
        if db is not None:
            record(Path(db).parent, 'planner', 'model_plan_pass',
                   pass_number=round_no, max_attempts=max_rounds,
                   proposed_file_count=len(all_steps),
                   net_new_files=len(all_steps) - count_before,
                   revised_file_entries=revised_count,
                   remaining_gap_count=len(gaps),
                   response_characters=len(answer),
                   input_characters=len(prompt),
                   original_specification_characters=len(request),
                   complete_specification_included=(request in prompt),
                   rejected_duplicate=repeated,
                   invalid_json='JSON' in finding or 'json' in finding,
                   focus_category=focus[:120],
                   output_token_budget=(0 if cached is not None else tokens),
                   format_failure_streak=malformed_streak)
        if round_no == max_rounds:
            break
        if previous_focus == focus and len(all_steps) == count_before and revised_count == 0:
            stagnant_on_focus += 1
        elif previous_focus == focus and focus in remaining_plan_gaps(list(all_steps.values()), request):
            stagnant_on_focus += 1
        else:
            stagnant_on_focus = 0
        previous_focus = focus
        next_focus = revision_focus(list(all_steps.values()), request, round_no + 1,
                                    previous_focus, stagnant_on_focus)
        if stage:
            stage(f'Planning pass {round_no} rejected: {finding[:100]}; '
                  f'{len(all_steps)} files, {len(gaps)} gaps; '
                  f'next correction: {next_focus[:90]}')
        prompt = build_revision_prompt(
            request, list(all_steps.values()), finding, x4_evidence=x4_evidence,
            max_chars=max_chars, path_window=round_no - 1, focus=next_focus,
            format_recovery=malformed_streak > 0)
    raise PlanError(
        f'Local model could not produce a validated plan after {max_rounds} attempts. '
        f'Last problem: {failures[-1][:650]}. No substitute plan was created; '
        'the original request remains available for retry.')


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
