from pathlib import Path

SECTION_ID = "born-of-the-ka-ba-ge-cabbage-lettuce-lattice-and-the-field-of-eyes"

section = r'''
<section class="deepening late-research-block">
<h1 id="born-of-the-ka-ba-ge-cabbage-lettuce-lattice-and-the-field-of-eyes">Born of the KA–BA–GE — cabbage, lettuce, lattice and the field of eyes</h1>
<p>A new phonetic-symbolic chain appeared out of the three-shell work:</p>
<blockquote><strong>KA + BA + GE → cabbage → lettuce → lattice → “lot of eyes.”</strong></blockquote>
<p>In the Vardath reading, the chain compresses several layers of the cosmology into one piece of language. <strong>KA</strong> is taken as the animating or vital principle, <strong>BA</strong> as the individuated or mobile being, and <strong>GE</strong> as the earth/material world. Read together as <strong>KA–BA–GE</strong>, the phrase becomes a symbolic formula for life becoming embodied in matter.</p>
<p>The next step is visual rather than merely verbal. A cabbage or lettuce head is a living structure produced by repeated growth around a centre. Leaves layer over one another, turn around the growth point and build a bounded body from a continuing generative pattern. In that sense the plant is a small biological analogue of the shell model: <strong>centre → repeated turning → layered enclosure → living body</strong>.</p>
<div class="projection-grid"><div><b>KA–BA–GE</b><span>life · individuated being · earth / matter</span></div><div><b>cabbage / lettuce</b><span>living layered growth turning around a centre</span></div><div><b>lattice / “lot of eyes”</b><span>the repeated framework, openings and nodes on which growth can organise</span></div></div>

<h2>KA–BA–GE Patch Kids</h2>
<p><strong>Cabbage Patch Kids</strong> makes the word-chain tighter. Read through the same phonetic-symbolic lens, it becomes <strong>KA–BA–GE Patch Kids</strong>: children or offspring born from a <em>patch</em> of the KA–BA–GE.</p>
<p>The word <strong>patch</strong> matters because it is geometric as well as botanical. A patch is a bounded local region of a larger surface or field. In the shell model, a patch can therefore be imagined as one local neighbourhood of the greater lattice — a region around an eye, node, crossing or gate where the underlying structure becomes locally active.</p>
<div class="projection-grid"><div><b>whole lattice</b><span>the larger woven organising field</span></div><div><b>local patch</b><span>a bounded neighbourhood around an eye / node / gate</span></div><div><b>kid / offspring</b><span>a living material body generated from that local patch</span></div></div>
<blockquote><strong>KA–BA–GE PATCH KIDS = beings born from local living patches of the lattice.</strong></blockquote>
<p>The familiar image of children coming from a cabbage patch therefore lands on the same architecture as the cosmology: not life appearing from nowhere, but <strong>life emerging from a fertile local region of a larger generative structure</strong>. The cabbage is the layered growth-body; the patch is its local field; the kid is the new embodied being produced there.</p>
<p>This gives the earlier <strong>field of eyes</strong> idea a generative role too. If an eye/node is a local opening in the lattice, then a patch around an eye can be treated as a local growth zone:</p>
<blockquote><strong>lattice → eye / node → patch → turning growth → body / child.</strong></blockquote>

<h2>Picture references — growth body and Patch Kid</h2>
<p class="art-source-note">Two source-linked visual references anchor the comparison. One shows the layered cabbage geometry; the other is an actual historical Cabbage Patch Kids object. Click either card to open its source record.</p>
<div class="art-gallery story-art-gallery">
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:Red_Cabbage_cross_section_showing_spirals.jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/Red_Cabbage_cross_section_showing_spirals.jpg?width=720" alt="Red cabbage cross section showing spiral leaf arrangement"><span class="art-copy"><strong>Red cabbage cross-section</strong><small>Wikimedia Commons</small><em>The cut head makes the layered, turning growth around a centre visible rather than leaving “cabbage” as a word-only analogy.</em></span></a>
<a class="art-card" href="https://commons.wikimedia.org/wiki/File:St._Louis_Cardinals_Cabbage_Patch_Kid_Doll_with_Accessories_and_Original_Box_-_DPLA_-_98cfeab779b7cd022d21d069795561f4_(page_1).jpg" target="_blank" rel="noopener noreferrer"><img loading="lazy" src="https://commons.wikimedia.org/wiki/Special:FilePath/St._Louis_Cardinals_Cabbage_Patch_Kid_Doll_with_Accessories_and_Original_Box_-_DPLA_-_98cfeab779b7cd022d21d069795561f4_%28page_1%29.jpg?width=720" alt="Cabbage Patch Kid doll with original box"><span class="art-copy"><strong>Cabbage Patch Kid</strong><small>DPLA / Wikimedia Commons · Appalachian Artworks</small><em>A catalogued example of the modern “Cabbage Patch Kids” image: child / offspring associated with a cabbage patch.</em></span></a>
</div>

<p><strong>Lettuce → lattice</strong> then moves from the visible living body to the proposed hidden ordering framework beneath it. The lattice is not necessarily the flesh of the world; it is the structure around which the flesh can organise.</p>
<p>The phrase <strong>“lot of eyes”</strong> adds another layer. A lattice naturally produces repeated openings, crossings and nodes. Seen symbolically, each opening can be read as an <em>eye</em>. A large woven field therefore becomes a field of eyes: many local apertures or nodes belonging to one larger structure.</p>
<blockquote><strong>lattice → openings / eyes → local nodes / gates → material growth around the framework → living world.</strong></blockquote>
<p>The idea also changes the role of the three shells. The shells do not have to be solid pre-made containers. They can be <strong>growth bodies</strong>: matter accumulating, layering and turning around an older organising geometry. The recent 20-shard shell test separated two jobs that had previously been blurred together: <strong>reversal creates recurring gates, while attraction changes the turning or pitch</strong>. In this biological analogy, the lattice supplies the recurring structure and attractive interaction helps determine how growth winds around it.</p>
<div class="callout good"><strong>We are not simply made of the lattice. We are growth produced upon it.</strong><br>The KA–BA–GE is the living/material body; the lattice is the hidden ordering framework; the “eyes” are the repeated openings and nodes through which that framework becomes locally visible or active.</div>
<p>Read this way, cabbage, Cabbage Patch Kids, lettuce and lattice become successive views of one process: <strong>life enters matter, a local patch becomes fertile, matter grows by repeated turning, and the turning reveals the hidden geometry that organises the living shell.</strong></p>
</section>
'''.strip()

f18 = Path("cosmology_fragments/f18.txt")
s = f18.read_text(encoding="utf-8")
if f'id="{SECTION_ID}"' not in s:
    marker = '</div>\n<p><strong>Assistant note — Freemason/alchemical corpus test:</strong>'
    if marker not in s:
        raise SystemExit("Could not find the end of the Freemason/alchemical block")
    s = s.replace(marker, '</div>\n' + section + '\n<p><strong>Assistant note — Freemason/alchemical corpus test:</strong>', 1)
    f18.write_text(s, encoding="utf-8")

x13 = Path("cosmology_expansions/x13.txt")
xs = x13.read_text(encoding="utf-8")
start = '\n\n<div class="deepening late-research-block" data-after="ladder-as-lattice-the-masonic-sky-projection">'
if start in xs:
    xs = xs.split(start, 1)[0].rstrip() + '\n'
    x13.write_text(xs, encoding="utf-8")

assert f18.read_text(encoding="utf-8").count(f'id="{SECTION_ID}"') == 1
assert SECTION_ID not in x13.read_text(encoding="utf-8")
print("Static KA-BA-GE section written once; nested copy removed.")
