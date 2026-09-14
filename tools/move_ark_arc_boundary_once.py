from pathlib import Path

main = Path('cosmology_fragments/f18.txt')
notes = Path('cosmology_expansions/assistant-notes.txt')

s = main.read_text(encoding='utf-8')
misplaced = '<div class="callout"><strong>Evidence boundary:</strong> ARK → ARC is a geometric transformation inside the Vardath model, not a claim that English <em>ark</em> and <em>arc</em> share a historical etymology. The research claim being developed here is structural: one changing enclosure can occupy a narrow carrier state, an opening curved state and a broad canopy state.</div>\n'
if misplaced in s:
    s = s.replace(misplaced, '', 1)
main.write_text(s, encoding='utf-8')

n = notes.read_text(encoding='utf-8')
heading = '<h2>ARK → ARC → SKY / travelling fingertrap</h2>'
if heading not in n:
    anchor = '<h2>Revelation</h2>'
    if anchor not in n:
        raise SystemExit('Assistant Notes insertion anchor not found')
    block = (
        '<h2>ARK → ARC → SKY / travelling fingertrap</h2>'
        '<p>The ARK → ARC → SKY sequence is Vardath’s geometric reading of one changing enclosure: a narrow carrier state, an opening curved state and a broad canopy state. It is <strong>not</strong> a claim that English <em>ark</em> and <em>arc</em> share a historical etymology.</p>'
        '<p>Likewise, the waterborne-child images and historical examples show that basket/chest/ark/drum/tube motifs genuinely recur across several traditions; they do not by themselves establish that those traditions historically encoded the Vardath fingertrap cosmology. The useful research question is structural and testable: whether waterborne-child traditions disproportionately preserve woven, hollow, tubular, sealed or reopenable carriers, boundary/gate retrieval, and changed-household or second-birth outcomes compared with appropriate controls.</p>'
    )
    n = n.replace(anchor, block + anchor, 1)
notes.write_text(n, encoding='utf-8')

assert 'Evidence boundary:</strong> ARK → ARC' not in main.read_text(encoding='utf-8')
assert notes.read_text(encoding='utf-8').count(heading) == 1
