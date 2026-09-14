from pathlib import Path
p = Path('cosmology_fragments/f18.txt')
s = p.read_text(encoding='utf-8')
old = '<p class="art-source-note">Each thumbnail links to its source record. The images illustrate the historical motif family and the fingertrap geometry; they are not evidence by themselves that the Vardath cosmology is the historical meaning of the stories.</p>'
new = '<p class="art-source-note">Each thumbnail links to its source record.</p>'
if old in s:
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
assert old not in p.read_text(encoding='utf-8')
assert p.read_text(encoding='utf-8').count(new) == 1
