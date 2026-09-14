from pathlib import Path

p = Path('cosmology_fragments/f18.txt')
s = p.read_text(encoding='utf-8')
new_id = 'ark-arc-sky-the-travelling-fingertrap'

if f'id="{new_id}"' not in s:
    anchor_id = 'born-of-the-ka-ba-ge-cabbage-lettuce-lattice-and-the-field-of-eyes'
    pos = s.find(f'id="{anchor_id}"')
    if pos < 0:
        raise SystemExit('KA-BA-GE section anchor not found')
    end = s.find('</section>', pos)
    if end < 0:
        raise SystemExit('KA-BA-GE section closing tag not found')
    end += len('</section>')

    section = r'''
<section class="late-research-block" id="ark-arc-sky-section">
<h1 id="ark-arc-sky-the-travelling-fingertrap">The travelling fingertrap — ARK → ARC → SKY</h1>
<p>The baby-in-the-river motif changes meaning when it is placed beside the mature fingertrap geometry. Across the stories, the transport object is rarely one fixed thing. It may be a reed basket, chest, ark, trough, drum, leather bag, wicker box, hollow bamboo segment or other bounded carrier. The recurring function is more stable than the material: <strong>a living seed is enclosed inside a small protected world, surrendered to a current, carried through danger, recovered at another boundary and opened into a new domain.</strong></p>

<div class="callout"><strong>Vardath reading:</strong> the basket is the fingertrap in its contracted transport state. The fingertrap does not merely sit under the sky. It can be the same woven shell that, after transit, opens outward into an arc and then into the sky of the next stable world.</div>

<h2>The cross-cultural waterborne-child grammar</h2>
<p>The pattern is wider than the familiar Moses–Sargon comparison. The examples below differ in theology, date and transmission history, but they repeatedly preserve the same structural sequence: threatened or exceptional birth → enclosure → water/current → transport → retrieval → fosterage or changed identity → later emergence as hero, ruler, prophet, holy person or culture-founder.</p>
<table>
<thead><tr><th>tradition</th><th>child / figure</th><th>carrier and current</th><th>source</th></tr></thead>
<tbody>
<tr><td>Old Hittite / Anatolian</td><td>Thirty sons of the Queen of Kaneš</td><td>baskets launched into a river and carried toward Zalpa</td><td><a href="https://scholar.lib.vt.edu/ejournals/ElAnt/V11N1/singer.html" target="_blank" rel="noopener noreferrer">Singer, Kaneš / Zalpa text</a></td></tr>
<tr><td>Akkadian / Mesopotamian</td><td>Sargon</td><td>reed basket sealed with bitumen, entrusted to the river</td><td><a href="https://etana.org/node/578" target="_blank" rel="noopener noreferrer">ETANA, Birth Legend of Sargon</a></td></tr>
<tr><td>Hebrew Bible</td><td>Moses</td><td>papyrus <em>tēvāh</em>, coated with bitumen and pitch, placed among Nile reeds</td><td><a href="https://www.sefaria.org/Exodus.2?lang=en" target="_blank" rel="noopener noreferrer">Exodus 2</a></td></tr>
<tr><td>Qur'an / Arabic</td><td>Mūsā</td><td><em>al-tābūt</em> cast into the water; the water casts it onto the shore</td><td><a href="https://corpus.quran.com/translation.jsp?chapter=20&verse=39" target="_blank" rel="noopener noreferrer">Qur'an 20:39</a></td></tr>
<tr><td>Mahābhārata / Sanskrit</td><td>Karṇa</td><td>sealed wicker / casket-like container sent through connected rivers</td><td><a href="https://www.wisdomlib.org/hinduism/book/the-mahabharata-mohan/d/doc7589.html" target="_blank" rel="noopener noreferrer">Mahābhārata, Karṇa birth narrative</a></td></tr>
<tr><td>Roman</td><td>Romulus and Remus</td><td>floating vessel exposed to the Tiber flood</td><td><a href="https://cts.perseids.org/read/latinLit/phi0914/phi001/perseus-eng3/1.4.1-1.4.9" target="_blank" rel="noopener noreferrer">Livy 1.4</a></td></tr>
<tr><td>Buddhist commentary</td><td>Padumavatī's 500 sons</td><td>five hundred sealed boxes thrown into the water and recovered downstream</td><td><a href="https://sacred-texts.com/journals/jras/1893-13.htm" target="_blank" rel="noopener noreferrer">Manorathapūraṇī tradition</a></td></tr>
<tr><td>Nyanga / Congo</td><td>Mwindo</td><td>newborn sealed inside a hollow drum and thrown into the river</td><td><a href="https://edblogs.columbia.edu/worldepics/project/mwindo-epic/" target="_blank" rel="noopener noreferrer">Columbia World Epics — Mwindo</a></td></tr>
<tr><td>Welsh Taliesin tradition</td><td>Taliesin</td><td>infant enclosed in a leather bag and cast into the sea</td><td><a href="https://en.wikisource.org/wiki/The_Mabinogion_%28Guest_1877%29/Taliesin" target="_blank" rel="noopener noreferrer">Guest, Taliesin</a></td></tr>
<tr><td>Southwest Chinese origin tradition</td><td>Bamboo King</td><td>child found inside a hollow bamboo segment travelling on the river</td><td><a href="https://ctext.org/wiki.pl?chapter=617024&if=en" target="_blank" rel="noopener noreferrer">Chinese Text Project — Bamboo King tradition</a></td></tr>
</tbody>
</table>

<h2>The invariant object is a travelling enclosure</h2>
<p>Once the stories are compared structurally, the important object is not a literal basket. What survives across cultures is a <strong>small enclosed world capable of carrying life through a moving medium</strong>. The Vardath model already has such an object: a woven fingertrap whose geometry changes with tension and opening.</p>
<div class="projection-grid">
<div><b>living seed</b><span>baby · hero · preserved life · future world</span></div>
<div><b>contracted fingertrap</b><span>basket · ark · chest · drum · tube · bag</span></div>
<div><b>current</b><span>river · flood · sea · moving medium</span></div>
<div><b>gate</b><span>shore · reeds · weir · net · bank · receiver</span></div>
<div><b>opening</b><span>retrieval · unsealing · second birth · adoption</span></div>
<div><b>new domain</b><span>foster household · kingdom · temple · next world</span></div>
</div>

<h2>ARK → ARC → SKY</h2>
<p>The fingertrap supplies a single geometric object with several possible states. In the closed transport state it is the <strong>ARK</strong>: a narrow woven enclosure around the living interior. During reopening, the same structure widens and bows outward into an <strong>ARC</strong>. At maximum opening, seen from inside the new domain, the expanded woven surface becomes the <strong>SKY</strong>: the broad lattice overhead.</p>
<div class="projection-grid">
<div><b>ARK — contracted</b><span>narrow woven carrier · sealed survival state · world inside</span></div>
<div><b>ARC — opening</b><span>tube flares · walls curve outward · transit becomes vault</span></div>
<div><b>SKY — opened</b><span>broad lattice canopy · nodes/lights spread over the enclosing surface</span></div>
</div>
<p>The sequence is therefore not “a boat travels under a sky.” In the Vardath reading it is more radical: <strong>life travels inside the structure that will become its next sky.</strong></p>
<blockquote><strong>life → contracted fingertrap / ark → current → gate → reopening arc → sky / next world</strong></blockquote>

<h2>Moses and Noah — the same enclosure at different scales</h2>
<p>The Hebrew wording makes this comparison unusually sharp. The noun <a href="https://biblehub.com/hebrew/8392.htm" target="_blank" rel="noopener noreferrer"><em>tēvāh</em></a> is used for Noah's Ark and for the small enclosure carrying Moses. One story preserves a whole living remnant inside the enclosure; the other preserves one child. In the Vardath model this becomes a scale relation rather than two unrelated props:</p>
<blockquote><strong>child in ark ~ life in world ~ world in sky-shell.</strong></blockquote>
<p>Noah is the large-scale version: life is carried through a destructive water transition inside a bounded survival world and emerges afterward. Moses, Sargon, Karṇa and the other exposed children preserve the same grammar at human scale.</p>

<h2>Krishna is the controlled-crossing variant</h2>
<p>The Krishna tradition is not a passive foundling story, but it is visually important because it makes the same architecture explicit: the newborn is carried <strong>in a basket through the river</strong> from a death-threatened birth household into a foster household. Ancient Mathura imagery already depicts Vasudeva carrying the infant Krishna in a basket across the Yamunā. In this version the carrier is guided rather than abandoned to the current, but the sequence—child, enclosure, dangerous water, crossing, new household—remains visible.</p>

<h2>Visual references — carrier, current, gate and reopening</h2>
<div class="art-gallery story-art-gallery">
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:Finger_trap_toys.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/Finger%20trap%20toys.jpg?width=720" alt="Woven Chinese finger traps"><span class="art-copy"><strong>Fingertrap — changing woven tube</strong><small>Wikimedia Commons · CC BY 2.5</small><em>the geometric carrier proposed by the Vardath model</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:030.The_Child_Moses_on_the_Nile.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/030.The%20Child%20Moses%20on%20the%20Nile.jpg?width=720" alt="Gustave Doré illustration of the child Moses on the Nile"><span class="art-copy"><strong>Moses — child inside the little ark</strong><small>Gustave Doré · 1866 · public domain</small><em>reed enclosure · water · reeds / shore · retrieval</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:Birth_of_Sargon_BM_ME_K.3401.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/Birth%20of%20Sargon%20BM%20ME%20K.3401.jpg?width=720" alt="Cuneiform tablet containing the Birth Legend of Sargon"><span class="art-copy"><strong>Sargon — birth legend tablet</strong><small>7th century BCE copy · British Museum tradition</small><em>reed basket · bitumen · river · adoption</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:Romulus_and_Remus_Exposed_on_the_Tiber_,_pl_.2_from_the_series_The_Story_of_Romulus_and_Remus.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/Romulus%20and%20Remus%20Exposed%20on%20the%20Tiber%20%2C%20pl%20.2%20from%20the%20series%20The%20Story%20of%20Romulus%20and%20Remus.jpg?width=720" alt="Romulus and Remus exposed on the Tiber"><span class="art-copy"><strong>Romulus and Remus — Tiber exposure</strong><small>Battista Fontana · 16th century · public domain</small><em>floating vessel · flood/current · shore · fosterage</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:Vasudeva_carrying_baby_Krishna_in_a_basket_across_the_Yamuna,_Art_of_Mathura,_circa_1st_century_CE.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/Vasudeva%20carrying%20baby%20Krishna%20in%20a%20basket%20across%20the%20Yamuna%2C%20Art%20of%20Mathura%2C%20circa%201st%20century%20CE.jpg?width=720" alt="Vasudeva carrying baby Krishna in a basket across the Yamuna"><span class="art-copy"><strong>Krishna — basket across the Yamunā</strong><small>Mathura tradition · c. 1st century CE</small><em>child · basket · river crossing · transfer to foster world</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:The_Ark_of_Noah._Dispersed_manuscript_of_universal_history._Herat,_ca._1428._The_David_Collection,_Copenhagen,_accession_number_8-2005.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/The%20Ark%20of%20Noah.%20Dispersed%20manuscript%20of%20universal%20history.%20Herat%2C%20ca.%201428.%20The%20David%20Collection%2C%20Copenhagen%2C%20accession%20number%208-2005.jpg?width=720" alt="Noah's Ark in a fifteenth-century Herat manuscript"><span class="art-copy"><strong>Noah — the enclosure scaled up to a world</strong><small>Herat · c. 1428 · public domain</small><em>living remnant carried through water inside one bounded vessel</em></span></a>
</div>
<p class="art-source-note">Each thumbnail links to its source record. The images illustrate the historical motif family and the fingertrap geometry; they are not evidence by themselves that the Vardath cosmology is the historical meaning of the stories.</p>

<h2>What this predicts next</h2>
<p>The interpretation is testable. If the travelling-fingertrap reading is more than free resemblance, waterborne-child stories should disproportionately use <strong>woven, hollow, tubular, sealed, flexible or reopenable enclosures</strong>; they should disproportionately terminate at a distinct boundary or receiver; and the stories should disproportionately pair transport with <strong>changed household, changed identity or second-birth language</strong>. Those features can be frozen before a multilingual corpus search and tested against exposed-child stories that do not involve water.</p>
<div class="callout"><strong>Evidence boundary:</strong> ARK → ARC is a geometric transformation inside the Vardath model, not a claim that English <em>ark</em> and <em>arc</em> share a historical etymology. The research claim being developed here is structural: one changing enclosure can occupy a narrow carrier state, an opening curved state and a broad canopy state.</div>
</section>
'''

    s = s[:end] + '\n' + section + s[end:]
    p.write_text(s, encoding='utf-8')

s = p.read_text(encoding='utf-8')
assert s.count(f'id="{new_id}"') == 1
assert s.count('id="ark-arc-sky-section"') == 1
