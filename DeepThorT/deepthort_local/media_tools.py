"""Local attachments, document extraction and optional offline media engines.

No remote service is ever contacted while extracting documents or running models.
External model downloads require a separate explicit GUI approval.
"""
from __future__ import annotations
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

TEXT_EXT = {'.py','.js','.ts','.tsx','.jsx','.html','.css','.json','.md','.txt','.log',
            '.csv','.tsv','.yaml','.yml','.toml','.ini','.xml','.sql','.gd','.cs','.cpp','.h',
            '.java','.kt','.sh','.ps1','.bat','.cmd','.gitignore','.rst'}
IMAGE_EXT = {'.png','.jpg','.jpeg','.webp','.bmp','.gif'}
DOCUMENT_EXT = {'.pdf','.docx'}
SUPPORTED = TEXT_EXT | IMAGE_EXT | DOCUMENT_EXT
MAX_FILE_BYTES = 24*1024*1024
MAX_EXTRACT_CHARS = 9_000


def classify(path: str | Path) -> str:
    ext = Path(path).suffix.casefold()
    if ext in IMAGE_EXT: return 'image'
    if ext in TEXT_EXT: return 'text'
    if ext in DOCUMENT_EXT: return 'document'
    return 'unsupported'


def validate_attachment(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve(strict=True)
    if not p.is_file(): raise ValueError('Attachment is not a regular file')
    if classify(p) == 'unsupported': raise ValueError(f'Unsupported file format: {p.suffix or "(none)"}')
    if not 0 < p.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError('Attachment must be nonempty and no more than 24 MiB')
    return p


def _extract_docx(p: Path) -> str:
    # DOCX is a ZIP; use stdlib rather than requiring a Python Word dependency.
    with zipfile.ZipFile(p) as z:
        info = z.getinfo('word/document.xml')
        if info.file_size > 25*1024*1024: raise ValueError('DOCX XML exceeds safe extraction limit')
        xml = z.read(info)
    root = ET.fromstring(xml)
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    paragraphs = []
    for paragraph in root.iter(ns+'p'):
        words = [el.text or '' for el in paragraph.iter(ns+'t')]
        if words: paragraphs.append(''.join(words))
    return '\n'.join(paragraphs)


def _extract_pdf(p: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError('PDF reading needs the optional local pypdf package. Approve its installation in the Files & Images tab.') from e
    reader = PdfReader(str(p), strict=False)
    if len(reader.pages) > 150: raise ValueError('PDF exceeds 150-page local safety limit')
    segments = []
    total = 0
    for page in reader.pages:
        s = page.extract_text() or ''
        segments.append(s)
        total += len(s)
        if total > MAX_EXTRACT_CHARS: break
    return '\n'.join(segments)


def extract_attachment(path: str | Path, *, char_limit: int = MAX_EXTRACT_CHARS) -> str:
    p = validate_attachment(path)
    if not 100 <= char_limit <= MAX_EXTRACT_CHARS: raise ValueError('Invalid extraction limit')
    kind = classify(p)
    if kind == 'image':
        raise RuntimeError(f'{p.name} is an image, not text. Run Analyze Image using the optional local vision model.')
    if kind == 'document':
        content = _extract_docx(p) if p.suffix.lower()=='.docx' else _extract_pdf(p)
    else:
        content = p.read_text(encoding='utf-8-sig',errors='replace')
    if len(content)>char_limit:
        raise ValueError(f'File {p.name} contains {len(content):,} characters; the local model cannot ingest it all in one request. Select a shorter section instead of silently truncating.')
    return content


def composed_prompt(prompt: str, paths: list[str], *, max_chars: int = 7500) -> str:
    """Create one bounded input. Overflow is an explicit failure, not truncation."""
    if not isinstance(prompt,str) or not prompt.strip(): raise ValueError('A prompt is required')
    pieces = [prompt]
    if len(paths) > 8: raise ValueError('At most eight attachments per job')
    for path in paths:
        p = validate_attachment(path)
        content = extract_attachment(p)
        pieces.append(f'\n\n--- USER-ATTACHED FILE: {p.name} ---\n{content}\n--- END FILE ---')
    full = ''.join(pieces)
    if len(full)>max_chars:
        raise ValueError(f'Combined prompt and attachments contain {len(full):,} characters (maximum {max_chars:,}). No input was truncated. Split into smaller requests.')
    return full


def validate_image_output_path(project: str | Path, relative: str) -> Path:
    """Generated pictures may be saved only below the selected project."""
    from .workspace import safe_target
    if not relative.lower().endswith('.png'):raise ValueError('Generated output must be a .png file')
    return safe_target(Path(project),relative)


def validate_image_prompt(prompt: str, width: int, height: int, steps: int):
    if not prompt or len(prompt)>2000:raise ValueError('Image prompt must be 1..2000 characters')
    if (width,height) not in ((256,256),(384,384),(512,512)):
        raise ValueError('Only bounded square image sizes are permitted')
    if not 1<=steps<=30:raise ValueError('Steps must be 1..30')


def cli_image_args(python_exe: str, script: Path, model_dir: Path, prompt: str,
                   output: Path, width: int, height: int, steps: int) -> list[str]:
    validate_image_prompt(prompt,width,height,steps)
    if not model_dir.is_dir():raise FileNotFoundError('Local diffusion model folder is missing. Approve the model installation first.')
    return [python_exe,str(script),'--model',str(model_dir),'--output',str(output),
            '--prompt',prompt,'--width',str(width),'--height',str(height),'--steps',str(steps)]
