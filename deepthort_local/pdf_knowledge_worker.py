"""Fixed subprocess entry point for local text-layer PDF extraction.

No document paths, shell, network, rendering, OCR, attachments or JavaScript.
The parent sends exact source bytes on stdin and accepts bounded JSON only.
"""
from __future__ import annotations

import io
import json
import sys

PARSER_VERSION = '7.1.1'
MAX_PDF_BYTES = 4 * 1024 * 1024
MAX_PAGES = 128
MAX_TEXT = 512 * 1024
MAX_LINES = 20000
MAX_RESPONSE = 4 * 1024 * 1024


def extract(raw):
    from pypdf import PdfReader, __version__
    if __version__ != PARSER_VERSION:
        raise ValueError('Unsupported PDF parser version')
    if not raw.startswith(b'%PDF-') or len(raw) > MAX_PDF_BYTES:
        raise ValueError('Invalid or oversized PDF')
    reader = PdfReader(io.BytesIO(raw), strict=True)
    if reader.is_encrypted:
        raise ValueError('Encrypted PDFs are unsupported')
    count = len(reader.pages)
    if not 1 <= count <= MAX_PAGES:
        raise ValueError('PDF exceeds page limit or contains no pages')
    rows = []
    total = 0
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        total += len(text)
        if total > MAX_TEXT:
            raise ValueError('PDF extracted text exceeds budget')
        for line, value in enumerate(text.splitlines(), 1):
            if len(rows) >= MAX_LINES:
                raise ValueError('PDF exceeds line budget')
            if value.strip():
                rows.append([number, line, value])
    if not rows:
        raise ValueError('No extractable text layer; OCR is not supported')
    return rows


def main():
    try:
        # Windows children inherit the supervised desktop Job Object. On
        # POSIX the fixed subprocess also has its own conservative limits.
        if sys.platform != 'win32':
            import resource
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
            resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
        raw = sys.stdin.buffer.read(MAX_PDF_BYTES + 1)
        rows = extract(raw)
        output = json.dumps({'schema': 1, 'parser': PARSER_VERSION, 'rows': rows},
                            ensure_ascii=True, separators=(',', ':')).encode('ascii')
        if len(output) > MAX_RESPONSE:
            raise ValueError('PDF response exceeds budget')
        sys.stdout.buffer.write(output)
        return 0
    except Exception:
        # Do not relay source-controlled diagnostic strings into a prompt.
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
