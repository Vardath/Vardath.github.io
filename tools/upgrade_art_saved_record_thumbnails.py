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

# The original one-shot full-corpus workflow embedded its own older copy of the
# lattice rendering logic. Patch that too so a future archaeology rebuild cannot
# silently turn the thumbnail cards back into text-only chips.
legacy = ROOT / '.github' / 'workflows' / 'build-art-archive-from-test-corpus.yml'
w = legacy.read_text(encoding='utf-8')
legacy_start = "          # Lattice-art saved examples do not consistently contain image URLs in the CSV;"
legacy_done = "          # Lattice-art saved examples carry resolved museum image URLs in the CSV."
if legacy_start in w:
    start = w.index(legacy_start)
    end_marker = "          (OUT/'00-extra-test-archives.txt').write_text"
    end = w.index(end_marker, start)
    replacement = '''          # Lattice-art saved examples carry resolved museum image URLs in the CSV.
          # Render them as the same thumbnail cards used elsewhere in the archive; keep a
          # text-only fallback only for a genuinely unresolved source image.
          lattice=ROOT/'research/lattice_art_corpus_results/2026-09-13_examples.csv'
          if lattice.exists():
              rows=list(csv.DictReader(lattice.open(encoding='utf-8')))
              e=['<details class="corpus-section source-index" id="lattice-art-saved-records" open>',
                 f'<summary><strong>Lattice-art corpus — additional saved scored records</strong><span>{len(rows):,} museum records</span></summary>',
                 '<p class="corpus-note">Additional scored museum records saved by the lattice-art test. Every retained record with a resolved museum image is shown as a source-linked thumbnail card; a text-only fallback remains only for records whose source provides no usable image.</p>',
                 '<div class="corpus-grid">']
              for r in rows:
                  if r.get('image_url'):
                      pseudo={'title':r.get('title'),'url':r.get('url'),'image_url':r.get('image_url'),'tradition':r.get('culture_group'),'cohort':'saved scored record','source':f"{r.get('source') or 'Museum source'} · {r.get('motifs') or ''}",'year':r.get('date'),'family_count':None}
                      e.append(card(pseudo))
                  else:
                      title=safe(r.get('title')); url=safe(r.get('url')); culture=safe(r.get('culture_group')); motifs=safe(r.get('motifs'))
                      e.append(f'<a class="source-chip" href="{url}" target="_blank" rel="noopener noreferrer"><b>{title}</b><small>{culture} · {motifs}</small></a>')
              e+=['</div>','</details>']
              extra.append('\\n'.join(e))
'''
    w = w[:start] + replacement + w[end:]
elif legacy_done not in w:
    raise SystemExit('Expected legacy corpus workflow lattice block was not found; refusing an unsafe patch.')
legacy.write_text(w, encoding='utf-8')

ns = runpy.run_path(str(target))
ns['write_extra_test_archives']()
print('Upgraded lattice-art saved records to thumbnail cards, rebuilt the include, and protected the legacy rebuild workflow.')
