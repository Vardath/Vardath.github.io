"""Read-only X4 macro/component reference evidence from extracted game indexes.

The selected vanilla reference directory is not the game installation and may
omit DLC and other mods. A name absent from these two indexes is *unresolved*,
not a claim that the mod is broken. No XML is modified or game executable run.
"""
from __future__ import annotations

import hashlib
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .workspace import safe_target

MAX_INDEX_BYTES = 10_000_000
MAX_INPUT_BYTES = 2_000_000
MAX_FILES = 256


def _xml_file(path: Path, cap: int) -> tuple[ET.Element,str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError('Source missing or symlinked')
    size=path.stat().st_size
    if size>cap or size<8:
        raise ValueError('Source exceeds bounded audit size')
    content=path.read_bytes()
    if re.search(rb'<!\s*(?:DOCTYPE|ENTITY)\b',content,re.I):
        raise ValueError('DTD or entity declarations are excluded')
    return ET.fromstring(content),hashlib.sha256(content).hexdigest()


def inspect_x4_reference_links(project: str | Path, reference_dir: str | Path,
                               *, max_files: int=MAX_FILES) -> dict:
    """Compare explicit macro/component refs against actual extracted indexes.

    Does not infer ship weapon compatibility, DLC status, game behavior, nor
    endorse an unregistered asset. Unknown identifiers stay unresolved.
    """
    if not 1<=max_files<=MAX_FILES:
        raise ValueError('Invalid reference scan file count')
    root=Path(project).resolve(strict=True)
    refs=Path(reference_dir).resolve(strict=True)
    if not root.is_dir() or not refs.is_dir():
        raise ValueError('Existing project and extracted-reference directories required')
    index_names={'macro':'index/macros.xml','component':'index/components.xml'}
    known={kind:set() for kind in index_names}
    source_hashes={}
    observations=[]
    for kind,rel in index_names.items():
        target=safe_target(refs,rel)
        try:
            tree,digest=_xml_file(target,MAX_INDEX_BYTES)
        except (OSError,ValueError,ET.ParseError) as exc:
            observations.append({'code':'extracted_index_unavailable','source':rel,
                                 'detail':str(exc)[:130]})
            continue
        if tree.tag!='index':
            observations.append({'code':'extracted_index_root_invalid','source':rel})
            continue
        entries=tree.findall('entry')
        if len(entries)>80000:
            observations.append({'code':'extracted_index_too_many_entries','source':rel})
            continue
        known[kind]={entry.get('name','').casefold() for entry in entries if entry.get('name')}
        source_hashes[rel]=digest
    available={kind:bool(items) for kind,items in known.items()}
    local={kind:set() for kind in known}
    for kind,rel in index_names.items():
        target=safe_target(root,rel)
        if not target.is_file():continue
        try:
            tree,_=_xml_file(target,MAX_INPUT_BYTES)
            if tree.tag=='index':
                local[kind]={entry.get('name','').casefold() for entry in tree.iter('entry')
                             if entry.get('name')}
        except (OSError,ValueError,ET.ParseError):
            # This file is assessed by the independent static X4 audit.
            continue
    files=[]
    for folder in ('assets','md','libraries'):
        base=root/folder
        if not base.is_dir() or base.is_symlink():continue
        for path,dirs,names in os.walk(base,followlinks=False):
            dirs[:]=[name for name in sorted(dirs) if not (Path(path)/name).is_symlink()]
            for name in sorted(names):
                if name.lower().endswith('.xml'):
                    files.append(Path(path)/name)
                    if len(files)>max_files:
                        raise ValueError('X4 reference scan exceeds bounded file count')
    matched=[];unresolved=[];local_matches=[];input_hashes={}
    for item in files:
        relative=item.relative_to(root).as_posix()
        if item.is_symlink():
            observations.append({'code':'symlink_skipped','source':relative})
            continue
        try:
            tree,digest=_xml_file(item,MAX_INPUT_BYTES)
        except (OSError,ValueError,ET.ParseError):
            # Independent X4 audit reports malformed project XML.
            continue
        input_hashes[relative]=digest
        for kind in ('macro','component'):
            for element in tree.iter(kind):
                name=element.get('ref','').strip()
                if not name or len(name)>200:continue
                entry={'path':relative,'kind':kind,'name':name}
                if name.casefold() in local[kind]:
                    local_matches.append(entry)
                elif name.casefold() in known[kind]:
                    matched.append(entry)
                else:
                    unresolved.append(entry)
                if len(matched)+len(local_matches)+len(unresolved)>10000:
                    raise ValueError('X4 reference scan exceeds bounded reference count')
    return {
        'vanilla_index_available':available,
        'vanilla_index_sha256':source_hashes,
        'inspected_project_sha256':input_hashes,
        'resolved_vanilla_count':len(matched),
        'resolved_local_count':len(local_matches),
        'unresolved_count':len(unresolved),
        'unresolved_samples':unresolved[:12],
        'observations':observations,
        'gameplay_verified':False,
        'assurance':'Selected extracted vanilla indexes only; unknown names may belong to DLC or other mods',
    }
