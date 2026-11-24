"""Invoke only the bundled, isolated PDF text worker with bounded data."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from .pdf_knowledge_worker import (
    MAX_PDF_BYTES, MAX_PAGES, MAX_TEXT, MAX_LINES, MAX_RESPONSE, PARSER_VERSION,
)

TIMEOUT = 18


def pdf_lines(raw):
    if not raw.startswith(b'%PDF-') or len(raw) > MAX_PDF_BYTES:
        raise ValueError('Invalid or oversized PDF')
    python = Path(sys.executable).resolve(strict=True)
    if os.name == 'nt' and python.name.casefold() == 'pythonw.exe':
        python = python.with_name('python.exe').resolve(strict=True)
    worker = Path(__file__).with_name('pdf_knowledge_worker.py').resolve(strict=True)
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try:
        result = subprocess.run(
            [str(python), '-I', str(worker)], input=raw,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=TIMEOUT, check=False, shell=False, creationflags=flags,
            cwd=str(worker.parent),
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError('PDF extraction timed out') from exc
    if result.returncode or len(result.stdout) > MAX_RESPONSE:
        raise ValueError('PDF extraction unavailable or refused: requires pinned pypdf '
                         + PARSER_VERSION + ', a supported text layer and bounded document')
    try:
        data = json.loads(result.stdout)
        if (not isinstance(data, dict) or set(data) != {'schema', 'parser', 'rows'}
                or type(data['schema']) is not int or data['schema'] != 1
                or data['parser'] != PARSER_VERSION):
            raise ValueError('Unexpected PDF extraction protocol')
        rows = data['rows']
        if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_LINES:
            raise ValueError('Invalid PDF row count')
        total = 0
        previous = (0, 0)
        clean = []
        for row in rows:
            if (not isinstance(row, list) or len(row) != 3
                    or type(row[0]) is not int or type(row[1]) is not int
                    or not 1 <= row[0] <= MAX_PAGES or not 1 <= row[1] <= MAX_TEXT
                    or not isinstance(row[2], str) or not row[2].strip()
                    or '\n' in row[2] or '\r' in row[2]
                    or (row[0], row[1]) <= previous):
                raise ValueError('Invalid PDF source position')
            total += len(row[2])
            if total > MAX_TEXT:
                raise ValueError('PDF text exceeds budget')
            previous = (row[0], row[1])
            clean.append((row[0], row[1], row[2]))
        return clean
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise ValueError('Invalid bounded PDF extraction response') from exc
