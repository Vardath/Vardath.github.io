from __future__ import annotations

import csv
import html
import json
import pathlib
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = pathlib.Path('/tmp/vardath-art-corpus')
OUT = ROOT / 'cosmology_expansions' / 'art_corpus'
OUT.mkdir(parents=True, exist_ok=True)


def safe(value) -> str:
    s = html.escape(str(value or ''), quote=True)
    # Prevent source metadata from accidentally becoming Liquid syntax at Jekyll build time.
    return s.replace('{', '&#123;').replace('}', '&#125;')


def card(record: dict) -> str:
    title = safe(record.get('title') or 'Untitled record')
    url = safe(record.get('url'))
    image = safe(record.get('image_url'))
    tradition = safe((record.get('tradition') or '').title())
    cohort = safe((record.get('cohort') or '').title())
    source = safe(record.get('source') or record.get('channel') or '')
    year = record.get('year')
    yearpart = f' · {safe(year)}' if year not in (None, '') else ''
    family_count = record.get('family_count')
    if isinstance(family_count, int) and family_count:
        word = 'family' if family_count == 1 else 'families'
        fampart = f' · {family_count} motif {word}'
    else:
        fampart = ''
    return (
        f'<a class="corpus-card" href="{url}" target="_blank" rel="noopener noreferrer">'
        f'<img loading="lazy" decoding="async" src="{image}" alt="{title}">'
        f'<span><b>{title}</b><small>{tradition} · {cohort} · {source}{yearpart}{fampart}</small></span></a>'
    )


def load_visual_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted((ART / 'shards').glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        records.extend(data.get('records', []))

    # The same record can be rediscovered by more than one query/shard. Keep one visual card per
    # source record, but otherwise preserve target/control/noisy/zero-feature material exactly.
    unique: dict[str, dict] = {}
    for record in records:
        image = (record.get('image_url') or '').strip()
        url = (record.get('url') or '').strip()
        if not image or not url:
            continue
        unique.setdefault(url, record)
    return list(unique.values())


def write_group_files(records: list[dict]):
    groups = defaultdict(list)
    for record in records:
        key = (record.get('tradition', 'unknown'), record.get('cohort', 'unknown'), record.get('channel', 'unknown'))
        groups[key].append(record)
    for values in groups.values():
        values.sort(key=lambda r: (r.get('year') is None, r.get('year') or 99999, (r.get('title') or '').lower()))

    order = [
        ('masonic', 'target', 'commons'),
        ('masonic', 'target', 'openlibrary'),
        ('alchemy', 'target', 'commons'),
        ('alchemy', 'target', 'openlibrary'),
        ('masonic', 'control', 'commons'),
        ('masonic', 'control', 'openlibrary'),
        ('alchemy', 'control', 'commons'),
        ('alchemy', 'control', 'openlibrary'),
    ]
    labels = {
        ('masonic', 'target', 'commons'): 'Masonic target — Wikimedia Commons visual records',
        ('masonic', 'target', 'openlibrary'): 'Masonic target — Open Library covers/documents',
        ('alchemy', 'target', 'commons'): 'Alchemical target — Wikimedia Commons visual records',
        ('alchemy', 'target', 'openlibrary'): 'Alchemical target — Open Library covers/documents',
        ('masonic', 'control', 'commons'): 'Masonic controls — Wikimedia Commons visual records',
        ('masonic', 'control', 'openlibrary'): 'Masonic controls — Open Library covers/documents',
        ('alchemy', 'control', 'commons'): 'Alchemical controls — Wikimedia Commons visual records',
        ('alchemy', 'control', 'openlibrary'): 'Alchemical controls — Open Library covers/documents',
    }

    includes = []
    for index, key in enumerate(order, 1):
        values = groups.get(key, [])
        slug = '-'.join(key)
        filename = OUT / f'{index:02d}-{slug}.txt'
        control = key[1] == 'control'
        note = (
            'These are comparison/control images scored by the same frozen test. They are retained so the visual archive shows what the target corpus was compared with, not only the attractive matches.'
            if control else
            'These are target-corpus images actually gathered and scored by the frozen Masonic/alchemical test, including zero-feature and weak-feature records as well as stronger matches.'
        )
        body = [
            f'<details class="corpus-section" id="corpus-{slug}" {"" if control else "open"}>',
            f'<summary><strong>{safe(labels[key])}</strong><span>{len(values):,} source-linked images</span></summary>',
            f'<p class="corpus-note">{safe(note)}</p>',
            '<div class="corpus-grid">',
        ]
        body.extend(card(record) for record in values)
        body.extend(['</div>', '</details>'])
        filename.write_text('\n'.join(body) + '\n', encoding='utf-8')
        includes.append((key, filename, len(values), labels[key]))
    return includes


def write_extra_test_archives():
    sections = []

    ladder = ROOT / 'research' / 'masonic_ladder_sky_v2_results' / 'examples.csv'
    if ladder.exists():
        rows = [r for r in csv.DictReader(ladder.open(encoding='utf-8')) if r.get('image_url') and r.get('url')]
        body = [
            '<details class="corpus-section" id="ladder-sky-v2" open>',
            f'<summary><strong>Earlier Masonic ladder / sky visual test</strong><span>{len(rows):,} saved examples</span></summary>',
            '<p class="corpus-note">Image-bearing examples retained from the earlier ladder/sky test output. These are test archaeology rather than a replacement for the later broader corpus.</p>',
            '<div class="corpus-grid">',
        ]
        for row in rows:
            body.append(card({
                'title': row.get('title'), 'url': row.get('url'), 'image_url': row.get('image_url'),
                'tradition': 'masonic ladder/sky', 'cohort': 'saved example', 'source': 'Wikimedia Commons',
                'year': row.get('year'), 'family_count': None,
            }))
        body.extend(['</div>', '</details>'])
        sections.append('\n'.join(body))

    lattice = ROOT / 'research' / 'lattice_art_corpus_results' / '2026-09-13_examples.csv'
    if lattice.exists():
        rows = list(csv.DictReader(lattice.open(encoding='utf-8')))
        body = [
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
        body.extend(['</div>', '</details>'])
        sections.append('\n'.join(body))

    (OUT / '00-extra-test-archives.txt').write_text('\n'.join(sections) + '\n', encoding='utf-8')


def write_intro(records: list[dict], includes):
    counts = Counter(record.get('channel') for record in records)
    target = sum(record.get('cohort') == 'target' for record in records)
    control = sum(record.get('cohort') == 'control' for record in records)
    body = [
        '<section class="gallery-section corpus-intro" id="full-test-corpus-archive">',
        '<h2>Full scored visual test corpus — not just the showcase hits</h2>',
        '<p>The original Art Archive showed only a small set of illustrative hits. The preserved 20-shard Masonic/alchemical test actually gathered thousands of image-bearing records. This expansion restores that hidden visual corpus as a source-linked archive rather than selecting only images that resemble the model.</p>',
        '<div class="corpus-stats">',
        f'<div><b>{len(records):,}</b><span>unique image-bearing scored records</span></div>',
        f'<div><b>{target:,}</b><span>target-corpus images</span></div>',
        f'<div><b>{control:,}</b><span>control images</span></div>',
        f'<div><b>{counts.get("commons", 0):,}</b><span>Wikimedia Commons records</span></div>',
        f'<div><b>{counts.get("openlibrary", 0):,}</b><span>Open Library covers</span></div>',
        '</div>',
        '<p class="corpus-note"><strong>Archive rule:</strong> being present here means the record was gathered and scored in the test; it does not mean it was a positive motif hit. Target, control, weak, null and noisy records are deliberately retained so the page represents the research corpus rather than a curated confirmation gallery.</p>',
        '<nav class="corpus-jumps">',
    ]
    for key, filename, count, label in includes:
        body.append(f'<a href="#corpus-{"-".join(key)}">{safe(label)} ({count:,})</a>')
    body.extend([
        '<a href="#ladder-sky-v2">Ladder/sky test archaeology</a>',
        '<a href="#lattice-art-saved-records">Lattice-art saved records</a>',
        '</nav>', '</section>',
    ])
    (OUT / '00-corpus-intro.txt').write_text('\n'.join(body) + '\n', encoding='utf-8')
    return target, control, counts


def write_manifest(records: list[dict]):
    manifest = ROOT / 'research' / 'art_archive_masonic_alchemy_visual_manifest.csv'
    fields = ['source', 'channel', 'tradition', 'cohort', 'id', 'title', 'url', 'image_url', 'year', 'query', 'family_count']
    with manifest.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in sorted(records, key=lambda r: (r.get('tradition', ''), r.get('cohort', ''), r.get('channel', ''), r.get('title', ''))):
            writer.writerow({key: record.get(key) for key in fields})


def wire_art_page(includes):
    art = ROOT / 'art.html'
    text = art.read_text(encoding='utf-8')
    marker = '<!-- FULL_TEST_CORPUS_ARCHIVE -->'
    if marker not in text:
        block = [
            '', marker,
            '{% include_relative cosmology_expansions/art_corpus/00-corpus-intro.txt %}',
            '{% include_relative cosmology_expansions/art_corpus/00-extra-test-archives.txt %}',
        ]
        for key, filename, count, label in includes:
            block.append('{% include_relative ' + str(filename.relative_to(ROOT)).replace('\\', '/') + ' %}')
        text = text.replace('</main>', '\n'.join(block) + '\n</main>', 1)

    if '.corpus-intro{' not in text:
        css = '''
.corpus-intro{border-color:#4b4772;background:linear-gradient(180deg,#17162a,#10131d)}
.corpus-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:9px;margin:18px 0}.corpus-stats div{padding:12px;background:#0d121a;border:1px solid var(--line);border-radius:10px;text-align:center}.corpus-stats b{display:block;color:var(--cyan);font-size:1.35rem}.corpus-stats span{display:block;color:var(--muted);font-size:.78rem}.corpus-jumps{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}.corpus-jumps a{font-size:.78rem;text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:5px 8px;background:#111724}.corpus-section{margin:18px 0;border:1px solid #2d3850;border-radius:13px;background:#0c1119;overflow:hidden}.corpus-section>summary{cursor:pointer;list-style:none;display:flex;justify-content:space-between;gap:12px;align-items:center;padding:15px 17px;background:#121826}.corpus-section>summary::-webkit-details-marker{display:none}.corpus-section>summary strong{color:#f0f7ff}.corpus-section>summary span{color:var(--cyan);font-size:.82rem;white-space:nowrap}.corpus-note{padding:0 17px;color:var(--muted);font-size:.86rem}.corpus-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:7px;padding:10px}.corpus-card{display:flex;flex-direction:column;min-width:0;background:#111620;border:1px solid #252e40;border-radius:8px;overflow:hidden;color:var(--text);text-decoration:none}.corpus-card:hover{border-color:var(--cyan)}.corpus-card img{width:100%;aspect-ratio:1/1;object-fit:cover;background:#070a0f}.corpus-card span{padding:7px;min-width:0}.corpus-card b{display:block;font-size:.72rem;line-height:1.25;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.corpus-card small{display:block;color:var(--muted);font-size:.62rem;line-height:1.3;margin-top:3px}.source-chip-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:7px;padding:10px}.source-chip{padding:9px;background:#111620;border:1px solid #252e40;border-radius:8px;text-decoration:none;color:var(--text)}.source-chip b{display:block;font-size:.76rem}.source-chip small{display:block;color:var(--muted);font-size:.65rem;margin-top:3px}@media(max-width:760px){.corpus-stats{grid-template-columns:repeat(2,1fr)}.corpus-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
'''
        text = text.replace('</style>', css + '</style>', 1)

    art.write_text(text, encoding='utf-8')


def main():
    records = load_visual_records()
    if len(records) < 5000:
        raise SystemExit(f'Expected thousands of image-bearing records, found only {len(records)}; refusing partial archive build.')
    includes = write_group_files(records)
    write_extra_test_archives()
    target, control, counts = write_intro(records, includes)
    write_manifest(records)
    wire_art_page(includes)
    print(f'visual records={len(records):,} target={target:,} control={control:,} commons={counts.get("commons",0):,} openlibrary={counts.get("openlibrary",0):,}')
    for key, filename, count, label in includes:
        print(filename.relative_to(ROOT), count)


if __name__ == '__main__':
    main()
