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
    request = request or ''
    if re.search(r'\b(?:x4(?::?\s+foundations)?|egosoft|xenon\s+pe)\b', request, re.I):
        return 'x4'
    if re.search(r'\b(?:game|faction command|apk)\b', request, re.I) and re.search(
            r'\b(?:build|make|create|develop|implement|game|android)\b', request, re.I):
        return 'android_game' if re.search(r'\b(?:android|apk)\b', request, re.I) else 'game'
    return 'general'


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
    if any(p.endswith('.py') for p in paths):
        missing.append('X4 installable extension XML rather than Python application entrypoints')
    if missing:
        raise PlanError('Plan does not cover the X4 specification: ' + '; '.join(missing) + '. No work has been queued. Provide extracted vanilla references or inspect the installed X4 assets before trusting equipment identifiers.')
    return steps


def parse_build_plan(text: str, project: str | Path, *, request: str = '',
                     fragment: bool = False) -> list[dict]:
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
    return validated if fragment else validate_project_plan(validated, request)


def build_plan_prompt(request: str, inventory: dict | None = None, *, x4_evidence: str = '') -> str:
    tools = ', '.join(x['name'] for x in (inventory or {}).get('tools', []) if x.get('found'))
    header = ('Return ONLY valid JSON with a "files" array. Each entry needs "path" '
              'and "description". Choose concrete relative source files ordered by dependency, '
              'up to 5 in this first pass; subsequent passes will complete the plan. No absolute paths or shell/install commands. Do not confuse an example '
              'format with the actual project type. Do NOT invent verified game asset identifiers.\n')
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


def build_revision_prompt(request: str, steps: list[dict], problems: str, *,
                          x4_evidence: str = '', max_chars: int = 7500,
                          path_window: int = 0) -> str:
    """Ask the model to repair its own proposal within a bounded context.

    Never truncate the original specification or alter/drop accumulated plan
    steps. The small model sees a whole-path subset when its context cannot
    hold the entire plan. The full plan remains in ``generate_model_plan`` and
    is revalidated before a draft can ever be approved. A later revision can
    rotate the subset instead of failing just because the model proposed many
    long paths. No files/plan steps are manufactured here.
    """
    header = (
        'Your previous project plan was incomplete or invalid. REVISE IT YOURSELF. '
        'Return ONLY JSON {"files":[{"path":"...","description":"..."}]}, '
        'with 1 to 6 NEW files or corrections of existing paths. '
        'Every path must be a real relative source file. '
        'Previous plan steps remain saved and are merged with your corrections; '
        'only a bounded selection of paths may appear below. '
        'Do not repeat unchanged files. Use verified source evidence; never guess IDs. '
        'Do not claim any testing or construction has occurred.\n'
    )
    findings = str(problems).strip()[:1300]
    base = (header + 'VALIDATOR FINDINGS:\n' + findings +
            '\nORIGINAL SPECIFICATION (COMPLETE):\n' + request + '\n')
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
    manifest_header = f'PREVIOUS MODEL-PROPOSED PATHS (total {len(path_list)}; saved locally):\n'
    omitted_reserve = 130
    manifest_lines = []
    selected_indices = set()
    if len(manifest_header) + omitted_reserve <= remaining and path_list:
        # Rotate first position in later passes if the manifest is too large.
        begin = path_window % len(path_list)
        ordered_indices = list(range(begin, len(path_list))) + list(range(begin))
        used = len(manifest_header) + omitted_reserve
        for index in ordered_indices:
            line = path_list[index] + '\n'
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
                        max_chars: int = 7500, max_rounds: int = 4,
                        stage=None) -> tuple[str, list[dict]]:
    """Generate a complete plan through bounded, evidence-driven model revisions.

    No file intentions are hardcoded here. Each proposed path/description must
    originate in local model output. The validator can reject or request more;
    it never manufactures a substitute plan. No executable work is queued.
    """
    if not 1 <= max_rounds <= 8:
        raise ValueError('max_rounds must be 1..8')
    if len(first_prompt) > max_chars:
        raise PlanError('Initial planning request exceeds the model context limit')
    all_steps: dict[str, dict] = {}
    failures = []
    seen_answers = set()
    prompt = first_prompt
    for round_no in range(1, max_rounds + 1):
        if stage:
            stage(f'Local model planning — pass {round_no}/{max_rounds}; '
                  f'{len(all_steps)} model-proposed files retained')
        # A fresh request session prevents previous 7K-character planning inputs
        # from polluting the next call or crossing chat/project boundaries.
        answer = client.chat(f'{session}-{round_no}', prompt, max_tokens=640)
        if answer.strip() in seen_answers:
            raise PlanError('The local model repeated an identical proposal instead of '
                            'correcting the identified errors. No substitute plan was created; '
                            'the original request is preserved for retry.')
        seen_answers.add(answer.strip())
        try:
            fragment = parse_build_plan(answer, project, fragment=True)
            if project_kind(request) == 'x4' and any(
                x['path'].lower().endswith('.py') for x in fragment):
                raise PlanError('An X4 extension cannot use generic Python app files')
            for entry in fragment:
                all_steps[entry['path'].casefold()] = entry
            if len(all_steps) > 24:
                raise PlanError('The plan now exceeds the maximum of 24 files')
            try:
                approved_shape = validate_project_plan(list(all_steps.values()), request)
            except PlanError as exc:
                finding = str(exc)
            else:
                # The draft is still only a proposal; user must approve to execute.
                return json.dumps({'files': approved_shape}, ensure_ascii=False), approved_shape
        except PlanError as exc:
            finding = str(exc)
        failures.append(finding)
        if round_no == max_rounds:
            break
        if stage:
            stage(f'Planning pass {round_no} rejected: {finding[:140]}; asking model to correct it')
        prompt = build_revision_prompt(
            request, list(all_steps.values()), finding, x4_evidence=x4_evidence,
            max_chars=max_chars, path_window=round_no - 1)
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
