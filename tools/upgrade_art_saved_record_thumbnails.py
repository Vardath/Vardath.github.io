from __future__ import annotations

import pathlib
import runpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
target = ROOT / 'tools' / 'build_art_archive_from_test_corpus.py'
text = target.read_text(encoding='utf-8')

old = '''        body = [
            '<details class="corpus-section source-index" id="lattice-art-saved-records" open>',
            f'<summary><strong>Lattice-art corpus — additional saved scored records</strong><span>{len(rows):,} museum records</span></summary>',
            '<p class="corpus-note">Additional scored museum records saved by the lattice-art test. The visual atlas above carries the examples with assembled thumbnail URLs; these source links retain the wider saved example set.</p>',
            '<div class="source-chip-grid">',
        ]
        for row in rows:
            body.append(
                f'<a class="source-chip" href="{safe(row.get("url"))}" target="_blank" rel="noopener noreferrer">'
                f'<b>{safe(row.get("title"))}</b><small>{safe(row.get("culture_group"))} · {safe(row.get("motifs"))}</small></a>'
            )
'''

new = '''        body = [
            '<details class="corpus-section source-index" id="lattice-art-saved-records" open>',
            f'<summary><strong>Lattice-art corpus — additional saved scored records</strong><span>{len(rows):,} museum records</span></summary>',
            '<p class="corpus-note">Additional scored museum records saved by the lattice-art test. Every retained record with a resolved museum image is shown as a source-linked thumbnail card; a text-only fallback remains only for records whose source provides no usable image.</p>',
            '<div class="corpus-grid">',
        ]
        for row in rows:
            if row.get('image_url'):
                body.append(card({
                    'title': row.get('title'),
                    'url': row.get('url'),
                    'image_url': row.get('image_url'),
                    'tradition': row.get('culture_group'),
                    'cohort': 'saved scored record',
                    'source': f"{row.get('source') or 'Museum source'} · {row.get('motifs') or ''}",
                    'year': row.get('date'),
                    'family_count': None,
                }))
            else:
                body.append(
                    f'<a class="source-chip" href="{safe(row.get("url"))}" target="_blank" rel="noopener noreferrer">'
                    f'<b>{safe(row.get("title"))}</b><small>{safe(row.get("culture_group"))} · {safe(row.get("motifs"))}</small></a>'
                )
'''

if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit('Expected lattice saved-record generator block was not found; refusing an unsafe patch.')

target.write_text(text, encoding='utf-8')
ns = runpy.run_path(str(target))
ns['write_extra_test_archives']()
print('Upgraded lattice-art saved records to thumbnail cards and rebuilt the include.')
