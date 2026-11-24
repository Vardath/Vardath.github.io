"""Bounded metadata-only discovery for native workflow inputs.

No asset content is opened here. An actual workflow freezes the selected
input with the existing SHA-256 execution guard before authorization.
"""
from __future__ import annotations
import os
from pathlib import Path
from .action_guards import MAX_HASH_BYTES
from .artifact_types import artifact_type
from .workspace import SKIP_DIRS,safe_target

MAX_ENTRIES=6000
# Build and distribution folders can contain legitimate generated inputs.
# All other editor exclusions remain in force.
_SKIP={d.casefold() for d in SKIP_DIRS}-{'build','dist'}


def list_native_inputs(project,*,max_entries=MAX_ENTRIES):
    if type(max_entries) is not int or not 1<=max_entries<=MAX_ENTRIES:
        raise ValueError('Invalid native input scan bound')
    root=Path(project).resolve(strict=True)
    if not root.is_dir():raise ValueError('Project folder is missing')
    pending=[root]
    files=[]
    visited=0
    while pending and visited<max_entries:
        directory=pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if visited>=max_entries:break
                    visited+=1
                    if entry.name.startswith('.'):continue
                    try:
                        p=Path(entry.path)
                        if entry.is_symlink() or getattr(p,'is_junction',lambda:False)():continue
                        relative=p.relative_to(root).as_posix()
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name.casefold() not in _SKIP and safe_target(root,relative)==p:
                                pending.append(p)
                            continue
                        if not entry.is_file(follow_symlinks=False):continue
                        if artifact_type(relative)['kind']=='source':continue
                        if not 0<entry.stat(follow_symlinks=False).st_size<=MAX_HASH_BYTES:continue
                        if safe_target(root,relative,must_exist=True)==p:
                            files.append(relative)
                    except (OSError,ValueError):continue
        except OSError:continue
    return sorted(set(files))
