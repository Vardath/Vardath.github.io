from pathlib import Path
main = Path('cosmology_fragments/f18.txt')
notes = Path('cosmology_expansions/assistant-notes.txt')
s = main.read_text(encoding='utf-8')
old = '<p><strong>Assistant note — Freemason/alchemical corpus test:</strong> This metadata-level result <strong>does not prove a physical event</strong> or historical transmission of the Vardath cosmology. The primary ≥3-family prediction failed; explicit pair combinations were sparse; the aggregate Masonic gate/ladder effect was mostly document-channel driven; the aggregate alchemical paired-polarity effect was also document-channel driven and disappeared in the historical ≤1930 check; and one negative-control family, furniture, was enriched. The most robust historical/source-channel findings are the Masonic four/eight signal and the alchemical serpent/braid visual signal. A blinded image-level test is the appropriate next discriminator.</p>\n'
if old in s:
    s = s.replace(old, '', 1)
main.write_text(s, encoding='utf-8')

n = notes.read_text(encoding='utf-8')
heading = '<h2>Freemason / alchemical corpus test</h2>'
if heading not in n:
    anchor = '<h2>Tiamat, Apsu and Kingu</h2>'
    if anchor not in n:
        raise SystemExit('Assistant Notes anchor not found')
    block = heading + '<p>This metadata-level result does not by itself establish a physical event or historical transmission of the Vardath cosmology. The primary ≥3-family prediction failed; explicit pair combinations were sparse; the aggregate Masonic gate/ladder effect was mostly document-channel driven; the aggregate alchemical paired-polarity effect was also document-channel driven and disappeared in the historical ≤1930 check; and one negative-control family, furniture, was enriched. The most robust historical/source-channel findings are the Masonic four/eight signal and the alchemical serpent/braid visual signal. A blinded image-level test is the appropriate next discriminator.</p>'
    n = n.replace(anchor, block + anchor, 1)
notes.write_text(n, encoding='utf-8')
assert 'Assistant note — Freemason/alchemical corpus test' not in main.read_text(encoding='utf-8')
assert notes.read_text(encoding='utf-8').count(heading) == 1
