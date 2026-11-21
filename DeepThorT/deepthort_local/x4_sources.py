"""Bounded, read-only discovery of actual X4: Foundations game XML sources.

Catalog file *names* are not proof of extracted ship/equipment definitions.
This module never unpacks/installs/executables, changes game files, or scans whole drives.
"""
from __future__ import annotations
import hashlib
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

MAX_XML_BYTES = 2_500_000
MAX_FILES = 450
MAX_SCAN_BYTES = 20_000_000
PE_MACRO = "ship_xen_m_corvette_02_a_macro"  # Lookup hint; verify actual installed XML before use.


def _existing(folder):
    try:
        p = Path(folder).expanduser().resolve()
        return p if p.is_dir() else None
    except (ValueError, OSError):
        return None


def likely_installations(extra_roots=()):
    """Probe named game locations, never blindly search all disk contents."""
    base = list(extra_roots)
    home = Path.home()
    base.extend([home/'Steam', home/'SteamLibrary', home/'Games',
                 Path('C:/Program Files (x86)/Steam'), Path('C:/Program Files/Steam'),
                 Path('D:/SteamLibrary'), Path('E:/SteamLibrary'),
                 Path('D:/Steam'), Path('E:/Steam'), Path('D:/Games'), Path('E:/Games')])
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
                base.append(Path(winreg.QueryValueEx(k,'SteamPath')[0]))
        except (OSError, ImportError):
            pass
    result=[];seen=set()
    for b in base:
        b=_existing(b)
        if not b:continue
        candidates=[b, b/'steamapps'/'common'/'X4 Foundations',
                    b/'SteamLibrary'/'steamapps'/'common'/'X4 Foundations',
                    b/'X4 Foundations', b/'GOG Games'/'X4 Foundations']
        vdf=b/'steamapps'/'libraryfolders.vdf'
        if vdf.is_file() and vdf.stat().st_size < 500_000:
            try:
                raw=vdf.read_text('utf-8',errors='replace')
                # Parse only quoted Steam library paths, not arbitrary recursive filesystem paths.
                for path in re.findall(r'"path"\s+"([^"]+)"', raw,flags=re.I)[:30]:
                    candidates.append(Path(path.replace('\\','/'))/'steamapps'/'common'/'X4 Foundations')
            except OSError:pass
        for cand in candidates:
            folder=_existing(cand)
            if not folder:continue
            if (folder/'X4.exe').is_file() or (folder/'01.cat').is_file():
                key=os.path.normcase(str(folder))
                if key not in seen:result.append(folder);seen.add(key)
    return result


def _selected_files(root:Path,subfolder:str,limit:int,pattern='*.xml'):
    folder=root/subfolder
    if not folder.is_dir():return []
    try:
        return [p for p in sorted(folder.glob(pattern)) if p.is_file() and not p.is_symlink()][:limit]
    except OSError:return []


def _xml_summary(path:Path, base:Path):
    try:
        size=path.stat().st_size
        if size>MAX_XML_BYTES or size<8:return None
        data=path.read_bytes()
        doc=ET.fromstring(data)
        macros=[]
        for el in doc.iter():
            if el.tag.lower().split('}')[-1] in ('macro','component','ware'):
                name=el.attrib.get('name') or el.attrib.get('id') or ''
                if name:macros.append(str(name)[:160])
                if len(macros)>=16:break
        return {'file':path.relative_to(base).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),
                'bytes':size,'identifiers':macros[:16]}
    except (OSError,ET.ParseError,ValueError):return None


def inspect_x4_sources(*, project_dir=None, game_dir=None, reference_dir=None,
                       discover_roots=(), max_files=MAX_FILES):
    """Inspect a selected game directory and extracted references; no installs or writes."""
    game=_existing(game_dir) if game_dir else None
    discovered=likely_installations(discover_roots) if not game else []
    if not game and discovered:game=discovered[0]
    ref=_existing(reference_dir) if reference_dir else None
    project=_existing(project_dir) if project_dir else None
    # Do NOT interpret an arbitrary mod project as extracted vanilla game data.
    report={'game_dir':str(game) if game else '',
            'reference_dir':str(ref) if ref else '', 'catalogs':[], 'files':[],
            'ship_candidates':[], 'weapon_candidates':[], 'turret_candidates':[],
            'storage_candidates':[], 'catalog_index_hints':[], 'pe_macro_verified':False,
            'pe_component_verified':False, 'pe_component_connections':[],
            'ready_for_planning':False,'blocked_reasons':[]}
    if game:
        cats=sorted(game.glob('[0-9][0-9].cat'))[:30]
        report['catalogs']=[str(x.name) for x in cats if x.is_file() and (game/x.with_suffix('.dat').name).is_file()]
        # Catalog indexes list file paths, but NOT XML contents. Treat as hints only.
        for cat in cats[:8]:
            try:
                with cat.open('rb') as f: raw=f.read(500_000)
                content=raw.decode('utf-8',errors='replace')
                hints=[line[:170] for line in content.splitlines() if
                       re.search(r'(?:xen.*(?:ship|corvette)|ship.*xen|weapon.*xen)',line,re.I)]
                report['catalog_index_hints'].extend(hints[:8])
            except OSError:continue
        report['catalog_index_hints']=report['catalog_index_hints'][:15]
    if ref:
        # Fast bounded scanning of expected X4 asset locations only.
        sets=[('assets/units/size_m/macros',220,'ship'),
              ('assets/props/WeaponSystems',100,'weapon'),
              ('assets/props/ShipUpgrades',40,'storage'),
              ('assets/props/Engines',40,'engine'),
              ('index',5,'index'),('libraries',8,'libraries')]
        remaining=min(max_files,MAX_FILES)
        remaining_bytes=MAX_SCAN_BYTES
        for sub,limit,category in sets:
            if remaining<=0:break
            folder=ref/sub
            if not folder.is_dir():continue
            if category=='ship':
                # PE may sort near the end of hundreds of ship files; prioritise
                # the exact requested vanilla macro rather than an arbitrary prefix.
                target=folder/(PE_MACRO+'.xml')
                paths=([target] if target.is_file() else [])
                paths.extend(p for p in _selected_files(ref,sub,limit) if p!=target)
                paths=paths[:limit]
            elif category=='weapon':
                # A regular alphabetical prefix would starve the turret branch.
                # Sample both weapons and turrets from known macro subfolders.
                candidates=[]
                try:
                    for child in sorted(folder.iterdir()):
                        if child.is_dir() and not child.is_symlink():
                            candidates.extend(_selected_files(ref,(child/'macros').relative_to(ref).as_posix(),250))
                except OSError:pass
                if not candidates:candidates=_selected_files(ref,sub,500)
                turrets=[p for p in candidates if 'turret' in p.name.lower()]
                weapons=[p for p in candidates if 'weapon' in p.name.lower()]
                # The PE component has medium slots. An alphabetical prefix
                # previously selected Argon L destroyer equipment as if it
                # were a useful candidate. Prefer medium-class identifiers,
                # but retain everything as UNVERIFIED compatibility candidates
                # until the actual connection tags are inspected.
                def candidate_priority(path):
                    name=path.name.lower()
                    medium=bool(re.search(r'(^|[_/])m([_/]|$)',name))
                    capital=bool(re.search(r'(^|[_/])(?:l|xl)([_/]|$)',name)) or '/capital/' in path.as_posix().lower()
                    return (0 if medium else 2 if capital else 1,
                            0 if 'xen' in name else 1, name)
                weapons.sort(key=candidate_priority)
                turrets.sort(key=candidate_priority)
                paths=(weapons[:limit//2]+turrets[:limit//2])[:limit]
            elif category in ('storage','engine'):
                paths=[]
                for child in sorted(folder.iterdir()):
                    if child.is_dir() and not child.is_symlink():
                        paths.extend(_selected_files(ref,(child/'macros').relative_to(ref).as_posix(),max(1,limit-len(paths))))
                        if len(paths)>=limit:break
                if not paths:paths=_selected_files(ref,sub,limit)
            else:paths=_selected_files(ref,sub,limit)
            for path in paths[:min(limit,remaining)]:
                try: size=path.stat().st_size
                except OSError:continue
                if size>remaining_bytes:continue
                remaining_bytes-=size
                summary=_xml_summary(path,ref)
                remaining-=1
                if not summary:continue
                name=summary['file'].lower()+' '+' '.join(summary['identifiers']).lower()
                if category=='ship' and 'xen' in name and 'ship' in name:
                    report['ship_candidates'].append(summary)
                elif category=='ship' and 'storage' in name:
                    report['storage_candidates'].append(summary)
                elif category=='weapon' and ('weapon' in name or 'turret' in name):
                    (report['turret_candidates'] if 'turret' in name else report['weapon_candidates']).append(summary)
                elif category=='storage' and ('storage' in name or 'cargo' in name):
                    report['storage_candidates'].append(summary)
                if category in ('index','libraries'):
                    report['files'].append(summary)
        for key in ('ship_candidates','weapon_candidates','turret_candidates','storage_candidates'):
            report[key]=report[key][:12]
        pe=next((x for x in report['ship_candidates'] if PE_MACRO in x['identifiers']),None)
        report['pe_macro_verified']=bool(pe)
        if pe:
            # The ship macro names a component: only that component reveals the
            # real connection slots. Do not infer turrets from the hull's name.
            try:
                macro_file=ref/pe['file']
                xml=ET.parse(macro_file)
                component_refs=[x.get('ref') for x in xml.iter('component') if x.get('ref')]
                for name in component_refs[:3]:
                    # X4 components are XML next to the units/.../macros folder.
                    comp=ref/'assets'/'units'/'size_m'/(name+'.xml')
                    if not comp.is_file() or comp.stat().st_size > MAX_XML_BYTES:continue
                    root=ET.parse(comp).getroot()
                    slots=[]
                    for con in root.iter('connection'):
                        tags=con.attrib.get('tags','')
                        if 'weapon' in tags or 'turret' in tags:
                            slots.append({'name':con.attrib.get('name','')[:100], 'tags':tags[:150]})
                    if slots:
                        report['pe_component_verified']=True
                        report['pe_component_connections']=slots[:24]
                        report['pe_component_file']=comp.relative_to(ref).as_posix()
                        report['pe_component_sha256']=hashlib.sha256(comp.read_bytes()).hexdigest()
                        break
            except (ET.ParseError, ValueError, OSError):pass
    if not game:report['blocked_reasons'].append('X4 installation not located. Select its game directory.')
    if game and not report['catalogs'] and not ref:report['blocked_reasons'].append('No catalog pairs or extracted references found at game location.')
    if not ref:report['blocked_reasons'].append('Vanilla XML not extracted. Locate an extracted X4 reference folder (assets/, libraries/, index/).')
    if ref and not report['pe_macro_verified']:report['blocked_reasons'].append('Exact Xenon PE macro '+PE_MACRO+' was not found in extracted references.')
    if ref and report['pe_macro_verified'] and not report['pe_component_verified']:report['blocked_reasons'].append('PE component XML with actual weapon/turret connection tags was not verified.')
    if ref and not report['weapon_candidates']:report['blocked_reasons'].append('No usable weapon macro references were verified.')
    if ref and not report['turret_candidates']:report['blocked_reasons'].append('No turret macro references were verified.')
    # Even when candidates exist, the exact Xenon PE identity and compatibility need verification.
    report['ready_for_planning']=bool(ref and report['pe_macro_verified'] and report['pe_component_verified'] and report['weapon_candidates'] and report['turret_candidates'])
    return report


def format_x4_inspection(report):
    lines=['X4 LOCAL ASSET INSPECTION (read-only; no files changed)',
           'Game: '+(report['game_dir'] or 'NOT FOUND'),
           'Extracted references: '+(report['reference_dir'] or 'NOT SELECTED'),
           'Paired base catalogs: '+str(len(report['catalogs'])),
           'Xenon M ship macro candidates: '+str(len(report['ship_candidates'])),
           'Exact Xenon PE macro: '+('verified' if report['pe_macro_verified'] else 'NOT VERIFIED'),
           'PE weapon/turret component slots: '+('verified' if report['pe_component_verified'] else 'NOT VERIFIED'),
           'Weapon macro candidates: '+str(len(report['weapon_candidates'])),
           'Turret macro candidates: '+str(len(report['turret_candidates'])),
           'Storage macro candidates: '+str(len(report['storage_candidates'])),
           'Plan evidence readiness: '+('candidate references available — verify exact PE identity' if report['ready_for_planning'] else 'BLOCKED')]
    for slot in report['pe_component_connections'][:8]:
        lines.append('PE slot: '+slot['name']+' ['+slot['tags']+']')
    for s in report['ship_candidates'][:5]:
        lines.append('Possible ship: '+s['file']+' ['+', '.join(s['identifiers'][:2])+']')
    for s in report['weapon_candidates'][:3]:lines.append('Possible weapon: '+s['file'])
    for s in report['turret_candidates'][:3]:lines.append('Possible turret: '+s['file'])
    for message in report['blocked_reasons']:lines.append('NEEDED: '+message)
    lines.append('If packed catalogs are present, use XRCatTool.exe from https://www.egosoft.com/download/x4/bonus_en.php (or X Tools on Steam).')
    lines.append('Extraction and downloads require your approval; no modifications to the X4 installation.')
    lines.append('Catalog index hints alone never establish exact vanilla equipment IDs.')
    return '\n'.join(lines)


def x4_evidence_for_prompt(report):
    """Representative VERIFIED XML references, never severing an identifier.

    The main inspection report retains the full evidence. This bounded extract
    prioritizes PE geometry and a real ship/weapon/turret representative, so a
    crowded reference catalogue cannot hide required connection information.
    """
    if not report['ready_for_planning']:
        return ''
    items=[]
    for entry in report['pe_component_connections'][:8]:
        items.append('PE connection: '+entry['name']+' tags '+entry['tags'])
    for key in ('ship_candidates','weapon_candidates','turret_candidates','storage_candidates'):
        for entry in report[key][:3]:
            items.append(f"{key}: {entry['file']} IDs {', '.join(entry['identifiers'][:3])} SHA {entry['sha256'][:12]}")
    result=[]
    for line in items:
        if len('\n'.join(result+[line]))>1800:
            continue
        result.append(line)
    return '\n'.join(result)


def find_catalog_tool(*, selected=None, game_dir=None, roots=()):
    """Return the actual executable only if present; never download or execute here."""
    import shutil
    possibilities=[]
    if selected:possibilities.append(Path(selected))
    located=shutil.which('XRCatTool.exe') or shutil.which('XRCatTool')
    if located:possibilities.append(Path(located))
    game=_existing(game_dir) if game_dir else None
    if game:
        possibilities.extend([
            game/'XRCatTool.exe', game.parent/'X Tools'/'XRCatTool.exe',
            game.parent/'X Rebirth Tools'/'XRCatTool.exe',
            game.parent/'X Tools'/'XTools_1.11'/'XRCatTool.exe'
        ])
    for root in roots:
        possibilities.append(Path(root)/'XRCatTool.exe')
    for path in possibilities:
        if path.is_file() and path.name.lower()=='xrcattool.exe':
            return str(path.resolve())
    return None


def catalog_extraction_command(tool, game_dir, output_dir):
    """Build an explicitly approved, filtered XRCatTool command, no shell injection.

    Only reads paired *numbered base-game* catalogs; never writes inside X4.
    """
    tool=Path(tool).resolve(strict=True)
    game=Path(game_dir).resolve(strict=True)
    out=Path(output_dir).resolve(strict=False)
    if tool.name.lower()!='xrcattool.exe' or not tool.is_file():
        raise ValueError('Select the official XRCatTool.exe executable')
    if not game.is_dir() or not (game/'X4.exe').is_file():
        raise ValueError('Select the X4 Foundations installation containing X4.exe')
    if out==game or game in out.parents:
        raise ValueError('Reference extraction must be outside the game installation')
    cats=[p for p in sorted(game.glob('*.cat')) if p.stem.isdigit() and
          p.with_suffix('.dat').is_file()]
    if not cats:raise ValueError('No paired numbered X4 CAT/DAT catalogs found')
    # Official tool takes multiple paths after -in, then -out, then -include regexes.
    patterns=[r'^index/.*\.xml$', r'^libraries/.*\.xml$',
              r'^assets/units/size_m/.*\.xml$',
              r'^assets/props/WeaponSystems/.*\.xml$',
              r'^assets/props/ShipUpgrades/.*\.xml$',
              r'^assets/props/Engines/.*\.xml$',
              r'^md/.*\.xml$']
    return [str(tool),'-in',*[str(p) for p in cats],'-out',str(out),'-include',*patterns]


def automatic_x4_preflight(*, project_dir=None, app_root=None, game_dir=None,
                           reference_dir=None, catalog_tool=None, discover_roots=()):
    """Read-only evidence discovery from an initial X4 request, never an install.

    Project files, game installation and previously extracted references are inspected
    automatically. Only an explicitly approved follow-up may execute XRCatTool.
    """
    app = Path(app_root).resolve() if app_root else None
    project = _existing(project_dir) if project_dir else None
    candidates = []
    if reference_dir: candidates.append(reference_dir)
    if app: candidates += [app/'reference'/'x4', app/'references'/'x4']
    if project: candidates.append(project/'reference'/'x4')
    refs = next((_existing(p) for p in candidates if _existing(p) and
                 (_existing(p)/'assets').is_dir()), None)
    roots = list(discover_roots)
    if project: roots += [project, project.parent]
    report = inspect_x4_sources(project_dir=project, game_dir=game_dir,
                                reference_dir=refs, discover_roots=roots)
    report['automatic_preflight'] = True
    report['project_files'] = []
    if project:
        # Bounded, read-only project inventory. Never crawl full game drives.
        try:
            for item in sorted(project.iterdir(), key=lambda p:p.name.casefold())[:90]:
                if item.is_file():
                    report['project_files'].append(item.name[:180])
                elif item.is_dir() and item.name.casefold() in ('extensions','md','libraries','assets'):
                    report['project_files'].append(item.name[:180]+'/')
        except OSError: pass
    tool = find_catalog_tool(selected=catalog_tool, game_dir=report['game_dir'] or None,
                             roots=[app] if app else ())
    report['catalog_tool'] = tool or ''
    report['can_offer_extraction'] = bool(report['game_dir'] and report['catalogs'] and
                                          not report['ready_for_planning'])
    return report


def is_x4_inspection_request(prompt: str, *, x4_context: bool = False) -> bool:
    """Handle a local inspection even if a follow-up only says 'examine it'."""
    return bool(re.search(r'\b(?:inspect|examine|locate|scan|check|discover|read)\b', prompt or '', re.I)
                and (x4_context or re.search(
                    r'\b(?:x4|xenon|egosoft|game\s+files?|ship\s+definitions?)\b',
                    prompt or '', re.I)))


def x4_request_in_context(prompt: str, *, project_dir=None, previous_prompts=()):
    """Follow-up inspection requests inherit the user's existing X4 project context."""
    if re.search(r'\b(?:x4|egosoft|xenon\s+pe)\b',prompt or '',re.I):
        return True
    contextual=bool(project_dir and re.search(r'(?i)(?:^|[^a-z0-9])x4(?:mods?|projects?|$|[^a-z0-9])',
                                             Path(project_dir).name))
    contextual=contextual or any(re.search(r'\b(?:x4|egosoft|xenon\s+pe)\b', p or '',re.I)
                              for p in list(previous_prompts)[-8:])
    return bool(contextual and is_x4_inspection_request(prompt,x4_context=True))
