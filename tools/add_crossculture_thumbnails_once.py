from pathlib import Path

p = Path('cosmology_fragments/f18.txt')
s = p.read_text(encoding='utf-8')
marker = '<h3>The Starbucks siren belongs to the survival test, not the ancient corpus</h3>'
if 'id="cross-cultural-example-thumbnails"' not in s:
    if marker not in s:
        raise SystemExit('target heading not found')
    gallery = r'''
<div id="cross-cultural-example-thumbnails" class="art-gallery story-art-gallery">
<a class="art-card" href="https://www.metmuseum.org/art/collection/search/313400" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://collectionapi.metmuseum.org/api/collection/v1/iiif/313400/2347320/main-image" alt="Moche nose ornament with intertwined serpents"><span class="art-copy"><strong>Moche — intertwined serpent nose ornament</strong><small>Peru · 500–800 CE · The Met</small><em>paired serpents · bilateral symmetry · interlace · eye-shaped openings</em></span></a>
<a class="art-card" href="https://www.clevelandart.org/art/1975.62" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://www.clevelandart.org/_next/image?url=https%3A%2F%2Fpiction.clevelandart.org%2Fcma%2Fump.di%3Fe%3D5AC335A2FB1534BC33305ADF655576A233A30BDAFD091B5305B47F4DA45DA612%26s%3D24247294%26se%3D399313166%26v%3D1%26f%3D%5Cd3118%5Cu2831189%5C1975.62_o5.jpg&amp;w=640&amp;q=75" alt="Chinese Warring States Hu jar with interlacing dragons"><span class="art-copy"><strong>China — Hu jar</strong><small>Warring States · 481–221 BCE · Cleveland Museum of Art</small><em>plait band · interlacing dragons · circular/ring forms</em></span></a>
<a class="art-card" href="https://www.clevelandart.org/art/1941.292" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://www.clevelandart.org/_next/image?url=https%3A%2F%2Fpiction.clevelandart.org%2Fcma%2Fump.di%3Fe%3D4C9F94B61C96C186FEE8B68CE3B9C59E658ABD9508547F0CD4228E33654F39FC%26s%3D24247294%26se%3D399313166%26v%3D4%26f%3D1941.292_o5.jpg&amp;w=640&amp;q=75" alt="Buyid silk fragment with interlaced eight-point star"><span class="art-copy"><strong>Iraq / Iran — interlaced eight-point star textile</strong><small>Buyid period · 950–1050 · Cleveland Museum of Art</small><em>interlaced bands · eight-point structure · circular centre · cross</em></span></a>
<a class="art-card" href="https://art.thewalters.org/object/29.2/" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://art.thewalters.org/images/art/thumbnails/s_PS1_29.2_VwA_DD_T09.jpg" alt="Aztec knotted rattlesnake"><span class="art-copy"><strong>Aztec — Knotted Rattlesnake</strong><small>Mexico · 1100–1520 · Walters Art Museum</small><em>serpent literally forms a knot · eye detail · sky/rain/cycle association</em></span></a>
<a class="art-card" href="https://art.thewalters.org/object/54.2890/" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://art.thewalters.org/images/art/thumbnails/s_PS4_54.2890_SideA_DD_AT21_25613-tms.jpg" alt="Ethiopian processional cross with radiating lattice"><span class="art-copy"><strong>Ethiopia — Processional Cross</strong><small>14th–15th century · Walters Art Museum</small><em>radiating lattice · central hub · concentric rings · repeated cruciform nodes</em></span></a>
<a class="art-card" href="https://www.britishmuseum.org/collection/object/H_1893-0618-72" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://media.britishmuseum.org/media/Repository/Documents/2014_10/1_7/0b42160a_f336_4ed3_b148_a3b700758559/mid_00034891_001.jpg" alt="Late Viking Ringerike style bone pin with interlace"><span class="art-copy"><strong>Late Viking — Ringerike interlace pin</strong><small>11th century · British Museum</small><em>interlocking triangles · paired spirals · double tendrils · ring-bound crossing</em></span></a>
</div>
<p class="art-source-note">These are the exact museum-linked examples named immediately above, shown here as thumbnails so the geometry can be inspected without leaving the section.</p>
'''
    s = s.replace(marker, gallery + marker, 1)
    p.write_text(s, encoding='utf-8')

s = p.read_text(encoding='utf-8')
assert s.count('id="cross-cultural-example-thumbnails"') == 1
