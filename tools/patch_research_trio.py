from pathlib import Path

# Landing page: keep the research trio clear and add bottom links.
p=Path('index.html')
s=p.read_text(encoding='utf-8-sig')
s=s.replace('<a href="phonetic-corpus.html">256 Gate Corpus Lab</a>','')
bottom='<div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin:0 auto 22px"><a href="phonetic-bridge.html" style="color:#eee;text-decoration:none;border:1px solid #444;border-radius:22px;padding:8px 14px;background:#1f1f2a">Phonetic Bridge</a><a href="vardath-cosmology.html" style="color:#eee;text-decoration:none;border:1px solid #444;border-radius:22px;padding:8px 14px;background:#1f1f2a">Vardath Cosmology</a></div>'
if bottom not in s:
    s=s.replace('<footer>© 2026 Vardath</footer>',bottom+'<footer>© 2026 Vardath</footer>')
p.write_text(s,encoding='utf-8')

# Phonetic Bridge: link to the other two pages at top and bottom.
p=Path('phonetic-bridge.html')
s=p.read_text(encoding='utf-8')
old='<div class="wrap top"><a class="brand" href="index.html">VARDATH</a><a class="back" href="index.html">← Main site</a></div>'
new='<div class="wrap top"><a class="brand" href="index.html">VARDATH</a><div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end"><a class="back" href="index.html">Vardath Home</a><a class="back" href="vardath-cosmology.html">Vardath Cosmology</a></div></div>'
if old in s:
    s=s.replace(old,new,1)
nav='<div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-bottom:18px"><a class="footerlink" href="index.html">Vardath Home</a><span>·</span><a class="footerlink" href="vardath-cosmology.html">Vardath Cosmology</a></div>'
if nav not in s:
    s=s.replace('<footer>','<footer>'+nav,1)
p.write_text(s,encoding='utf-8')

# Cosmology: navigation plus recovered cross-cultural myth architecture.
p=Path('vardath-cosmology.html')
s=p.read_text(encoding='utf-8')
old='<div class="wrap top"><a class="brand" href="index.html">VARDATH</a><a class="back" href="index.html">← Main site</a></div>'
new='<div class="wrap top"><a class="brand" href="index.html">VARDATH</a><div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end"><a class="back" href="index.html">Vardath Home</a><a class="back" href="phonetic-bridge.html">Phonetic Bridge</a></div></div>'
if old in s:
    s=s.replace(old,new,1)
if '<a href="#mythologies">Shared myth structure</a>' not in s:
    s=s.replace('<a href="#maps">Maps & edges</a>','<a href="#mythologies">Shared myth structure</a><a href="#maps">Maps & edges</a>',1)
myth='''
<section class="section wrap" id="mythologies">
<h2>6A. Many mythologies as views of one structured event</h2>
<p class="lead">An earlier Vardath comparison did not treat the traditions as identical stories with renamed characters. The working idea was that geographically and culturally separated witnesses could preserve different parts, viewpoints and moral interpretations of the same class of state-changing event. The recurring architecture was summarized as <b>Axis → Gate → Operator → Vehicle → Manifestation → Medium → Witness → Reset</b>.</p>
<div class="notice"><b>Interpretive boundary:</b> this is a comparative hypothesis. Similar motifs can arise through cultural transmission, shared human symbolism, convergent storytelling, real natural disasters, or combinations of these. The Vardath reading asks whether the motifs become more coherent when treated as observations of one changing physical structure; it does not assume that resemblance proves a single historical event.</div>
<div class="cards">
<div class="card"><span class="badge history">1 · Axis</span><h3>Mountain, tree, pillar, throne, world-column</h3><p>Earlier comparisons grouped Mount Mashu, world mountains, world trees, pillars and throne/axis imagery as versions of a vertical organizing structure. In the mature lattice model, the candidate counterpart is the convergence axis: the line that is seen end-on as a central point while the expanded lattice is open, then becomes the scroll/finger-trap rod during contraction.</p></div>
<div class="card"><span class="badge history">2 · Gate</span><h3>Doors, windows, portals and solar passages</h3><p>1 Enoch's heavenly portals/windows and Gilgamesh's guarded passage through Mashu were compared as boundary-crossing imagery. The lattice model supplies a possible geometric meaning: convergence circles or throats where ordinary surface directions meet the axial degree of freedom and neighbouring stabilized layers can temporarily approach one another.</p></div>
<div class="card"><span class="badge history">3 · Operator</span><h3>God, lord, Watcher, guardian</h3><p>Myths often personify the event around an agent who opens, commands, divides, judges or governs the boundary. Marduk orders and divides Tiamat; Watchers cross a forbidden boundary; gate guardians control passage. In the model these characters need not be literal machine operators: they can be narrative personifications of the force, phase or agency associated with the transition.</p></div>
<div class="card"><span class="badge history">4 · Vehicle</span><h3>Chariot, wheel, throne, mount</h3><p>Ezekiel's integrated living-creature/wheel/throne vision, Enochic chariot/fire imagery and the Bhagavad Gita's chariot setting were previously compared as recurring vehicle structures. In the lattice reading, wheels and interlocked moving forms are natural visual metaphors for a rotating, braided framework whose local cells move while carrying observers or land.</p></div>
<div class="card"><span class="badge history">5 · Manifestation</span><h3>Many eyes, many limbs, dragons and serpents</h3><p>Krishna's overwhelming many-formed universal manifestation, Ezekiel's eyes/wings, and widespread serpentine or draconic sky imagery were treated as different descriptions of an object too complex or luminous to describe literally. A moving braided lattice viewed in partial silhouette, electrical discharge or repeated arcs could be encoded as coils, serpents, scales, wings, eyes or many simultaneous bodies.</p></div>
<div class="card"><span class="badge history">6 · Medium</span><h3>Wind, fire, lightning, radiance</h3><p>The older synthesis repeatedly found wind, fire, lightning and intense light surrounding the appearance. Vardath's speculative physical reading was an electrical/plasma-like pulse interacting with the canopy/lattice. This is now paired with the mechanical model: energy input changes tension, visibility and geometry as the structure contracts or opens.</p></div>
<div class="card"><span class="badge history">7 · Witness</span><h3>Special sight, revelation, survivors</h3><p>Witnesses are frequently shown something normally hidden: Arjuna is granted special sight; prophetic texts describe opened heavens; Gilgamesh reaches the remote flood survivor. In the three-layer model, a transition temporarily makes normally separated layers, axial structures or inhabitants visible from the present layer.</p></div>
<div class="card"><span class="badge history">8 · Reset</span><h3>Flood, destruction, separation and re-ordering</h3><p>The recurring sequence ends in environmental catastrophe, a flood or destruction, followed by a new cosmic or social order. That maps directly onto the proposed stabilization stage: surface material is displaced, the lattice finishes its phase transfer, layers separate again, celestial tracks regularize, and survivors inherit a changed landscape.</p></div>
</div>
<h3 style="margin-top:28px">The event sequence recovered from the older discussions</h3>
<div class="flow"><div class="step"><b>Stable enclosure</b><br><span class="small">the upper structure is normally hidden</span></div><div class="arrow">→</div><div class="step"><b>Pulse / activation</b><br><span class="small">fire, lightning, wind, radiance</span></div><div class="arrow">→</div><div class="step"><b>Axis & gate appear</b><br><span class="small">mountain, tree, pillar, doorway, wheel</span></div><div class="arrow">→</div><div class="step"><b>Layers approach</b><br><span class="small">heavens open; upper beings become accessible</span></div><div class="arrow">→</div><div class="step"><b>Contact</b><br><span class="small">gods / Watchers / giants / knowledge transfer</span></div><div class="arrow">→</div><div class="step"><b>Catastrophe</b><br><span class="small">flood, battle, land displacement, destruction</span></div><div class="arrow">→</div><div class="step"><b>Re-sealing</b><br><span class="small">new order; hidden world recedes</span></div></div>
<table class="compare"><thead><tr><th>Tradition examined in the earlier chats</th><th>What that perspective emphasizes</th><th>How it maps into the shared event architecture</th></tr></thead><tbody>
<tr><td><b>Enūma Eliš</b> — Tiamat, Apsu, Kingu, Marduk</td><td>Primordial mingling, rebellion, net/wind, division, cosmic ordering.</td><td>The structural perspective: an intertwined primordial state is forcibly changed, divided and stabilized; the old body remains as the architecture of the new cosmos.</td></tr>
<tr><td><b>1 Enoch / Watcher tradition</b></td><td>Heavenly portals, descent, forbidden knowledge, giant offspring, disorder and judgment/destruction.</td><td>The boundary/contact perspective: normally separated inhabitants cross during an open phase; knowledge and beings pass between layers; the episode ends in catastrophic reset.</td></tr>
<tr><td><b>Book of Giants / giant traditions</b></td><td>Oversized or hybrid beings linked with the pre-catastrophe world.</td><td>The biological/scale perspective: if neighbouring chambers differ in scale, contact with another layer could be remembered as encounters with larger beings. This remains an unverified consequence of the shell-growth hypothesis.</td></tr>
<tr><td><b>Gilgamesh</b></td><td>Mashu's axis-mountain and guarded solar passage; journey to the remote flood survivor.</td><td>The traveller's perspective: a gate in the world structure leads toward a normally inaccessible region, while the flood tradition preserves the reset side of the cycle.</td></tr>
<tr><td><b>Ezekiel</b></td><td>Living beings, interrelated wheels, eyes, wings, fire and a throne-like integrated structure.</td><td>The visual/mechanical perspective: a complex moving lattice/vehicle seen during activation and described through the closest available biological and mechanical vocabulary.</td></tr>
<tr><td><b>Bhagavad Gita / Krishna's universal form</b></td><td>Chariot setting, special vision, overwhelming luminous many-formed reality containing many divine identities.</td><td>The altered-perception perspective: the witness is allowed to perceive a larger normally hidden structure and describes simultaneity, multiplicity and radiance rather than a simple object.</td></tr>
</tbody></table>
<h3 style="margin-top:28px">Why the stories disagree if the event is shared</h3>
<p>The hypothesis expects disagreement. A witness beneath a convergence would describe an opening heaven or descending beings; a traveller approaching a throat would describe a guarded mountain or gate; someone seeing the moving mesh would describe wheels, serpents, dragons or a many-eyed creature; survivors of landscape displacement would preserve flood and destruction; priestly traditions could recast the same transition as divine judgment or creation. The stories therefore need not share names, theology or moral meaning. What should recur is the <i>order and geometry of the event</i>.</p>
<div class="notice cyan"><b>Connection to the new model:</b> the older myth synthesis supplied a sequence without a clear mechanism. The braided-shell model now offers candidate mechanics for several steps: the axis is the scroll rod; gates are convergence throats; wheels/serpents are views of moving braid geometry; opened heavens are temporary layer proximity; giants belong to the proposed scale difference between turns; flood/reset corresponds to surface displacement during restabilization; and the return of the hidden heavens is the lattice reopening and separating the layers.</div>
</section>
'''
if 'id="mythologies"' not in s:
    s=s.replace('<section class="section wrap" id="maps">',myth+'<section class="section wrap" id="maps">',1)
footer_nav='<div style="display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-bottom:18px"><a class="footerlink" href="index.html">Vardath Home</a><span>·</span><a class="footerlink" href="phonetic-bridge.html">Phonetic Bridge</a></div>'
if footer_nav not in s:
    s=s.replace('<footer>','<footer>'+footer_nav,1)
p.write_text(s,encoding='utf-8')
