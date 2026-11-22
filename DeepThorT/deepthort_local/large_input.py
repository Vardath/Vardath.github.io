"""Import UTF-8 long-form project specifications without filling a Tk text widget.

Files are user-selected and read only. Their fingerprint is checked again at
submission, and the exact text is stored in the durable conversation request.
The import preview is never substituted for original requirements.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
from .specification_library import MAX_STORED_REQUEST_CHARS

# UTF-8 requires at most four bytes per codepoint. This is not an inference cap.
MAX_SPEC_SOURCE_BYTES = MAX_STORED_REQUEST_CHARS * 4


def read_specification_file(path: str | Path) -> str:
    p=Path(path).expanduser().resolve(strict=True)
    if not p.is_file():
        raise ValueError('Specification source must be an existing regular file')
    if p.suffix.lower() not in {'.txt','.md','.rst','.json','.yaml','.yml'}:
        raise ValueError('Import only user-authored text formats (TXT, MD, RST, JSON, YAML)')
    size=p.stat().st_size
    if size<1 or size>MAX_SPEC_SOURCE_BYTES:
        raise ValueError('Specification exceeds supported local file size')
    # UTF-8-sig accepts ordinary UTF-8 and an optional BOM. Other encodings
    # need explicit conversion; replacement characters are not acceptable.
    content=p.read_text(encoding='utf-8-sig')
    if not content.strip() or len(content)>MAX_STORED_REQUEST_CHARS:
        raise ValueError('Specification is empty or exceeds the local storage safety ceiling')
    return content


def imported_source(path: str | Path) -> dict:
    content=read_specification_file(path)
    return {'path':str(Path(path).resolve(strict=True)),
            'sha256':hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'characters':len(content)}


def resolve_import(source: dict, additional: str='') -> str:
    """Fail closed when a selected file changes; never use a stale preview."""
    content=read_specification_file(source['path'])
    if len(content)!=source['characters'] or hashlib.sha256(content.encode()).hexdigest()!=source['sha256']:
        raise ValueError('Imported specification file changed since selection; reimport it')
    if additional.strip():
        return content + '\n\nADDITIONAL USER INSTRUCTIONS (entered after importing):\n' + additional.strip()
    return content
