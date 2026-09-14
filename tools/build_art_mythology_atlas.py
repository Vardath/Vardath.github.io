#!/usr/bin/env python3
import html, json, pathlib, re, time, urllib.parse, urllib.request
from collections import OrderedDict

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'cosmology_expansions' / 'art_mythology'
OUT.mkdir(parents=True, exist_ok=True)
API = 'https://commons.wikimedia.org/w/api.php'
UA = 'Vardath-Art-Archive/1.0 (source-linked research gallery; github.com/Vardath/Vardath.github.io)'

SECTIONS = OrderedDict([
  ('celtic-insular', {
    'title': 'Celtic knotwork, Insular manuscripts and interlace',
    'intro': 'Historic knotwork, carpet pages, stone crosses and interlace from the Celtic/Insular visual record. Christian manuscript material is labelled as such rather than treated as pre-Christian Celtic religion.',
    'per_query': 5,
    'queries': [
      ('Book of Kells carpet page', 'Book of Kells / Insular manuscript'),
      ('Lindisfarne Gospels carpet page', 'Lindisfarne Gospels / Insular manuscript'),
      ('Book of Durrow carpet page', 'Book of Durrow / Insular manuscript'),
      ('Celtic knot stone cross interlace', 'Stone knotwork / ringed crosses'),
      ('Pictish interlace stone', 'Pictish carved interlace'),
      ('Insular interlace manuscript', 'Insular manuscript ornament'),
      ('Celtic spiral ornament manuscript', 'Spiral and knot ornament')
    ]
  }),
  ('norse-stones', {
    'title': 'Norse dragon stones, runestones and picture stones',
    'intro': 'Runestones and picture stones carrying serpents, dragons, knot-beasts, heroic scenes and rune bands. The section includes archaeological stones and later documentary photographs/drawings of them.',
    'per_query': 4,
    'queries': [
      ('Ramsund Sigurd inscription', 'Ramsund / Sigurd and Fafnir'),
      ('Jelling stone animal ornament', 'Jelling style'),
      ('Urnes style runestone', 'Urnes style'),
      ('Ringerike style runestone', 'Ringerike style'),
      ('Gotland picture stone', 'Gotland picture stones'),
      ('Stora Hammars stone', 'Stora Hammars stones'),
      ('Altuna runestone Thor', 'Altuna / Thor scene'),
      ('Ledberg stone runestone', 'Ledberg stone'),
      ('Sigurd runestone dragon', 'Sigurd stones / dragon-slayer imagery')
    ]
  }),
  ('runes-symbols', {
    'title': 'Runes, rune rows and historic symbols',
    'intro': 'Rune rows, inscriptions and symbol material from different periods. Elder/Younger Futhark and inscribed stones are kept distinct from much later Icelandic magical-sign manuscripts such as Vegvísir and Ægishjálmur.',
    'per_query': 4,
    'queries': [
      ('Elder Futhark inscription', 'Elder Futhark'),
      ('Younger Futhark inscription', 'Younger Futhark'),
      ('Anglo Saxon futhorc runes', 'Anglo-Saxon Futhorc'),
      ('Kylver Stone runes', 'Kylver stone / early rune row'),
      ('Rok Runestone', 'Rök runestone'),
      ('Valknut archaeology', 'Valknut / interlocked-triangle motif'),
      ('Vegvisir manuscript', 'Later Icelandic magical sign: Vegvísir'),
      ('Aegishjalmur manuscript', 'Later Icelandic magical sign: Ægishjálmur'),
      ('Galdrabok magical signs', 'Later Icelandic magical-sign manuscripts'),
      ('historic bind rune inscription', 'Historic bind-runes')
    ]
  }),
  ('myth-illustrations', {
    'title': 'Mythological drawings, paintings and narrative art',
    'intro': 'Narrative myth imagery across multiple traditions. These are visual records of stories and iconography, not evidence that the traditions share a single historical source.',
    'per_query': 4,
    'queries': [
      ('Greek mythology engraving gods heroes', 'Greek mythology'),
      ('Roman mythology engraving gods', 'Roman mythology'),
      ('Norse mythology illustration Edda', 'Norse / Germanic mythology'),
      ('Egyptian mythology papyrus gods', 'Ancient Egyptian mythology'),
      ('Mesopotamian mythology relief gods', 'Mesopotamian mythology'),
      ('Ramayana painting manuscript', 'Hindu epic: Ramayana'),
      ('Mahabharata painting manuscript', 'Hindu epic: Mahabharata'),
      ('Buddhist Jataka painting', 'Buddhist Jataka narratives'),
      ('Japanese mythology ukiyo-e Susanoo', 'Japanese mythology'),
      ('Chinese mythology painting deity', 'Chinese mythology'),
      ('Aztec codex gods', 'Aztec/Nahua codex imagery'),
      ('Maya codex gods', 'Maya codex imagery')
    ]
  }),
  ('deities', {
    'title': 'Gods, goddesses and sacred figures — comparative visual atlas',
    'intro': 'A deliberately broad visual atlas across religions and mythologies. The grouping is for browsing only: each card retains its own tradition label and Commons source, and sacred figures are not being asserted to be equivalents of one another.',
    'per_query': 2,
    'queries': [
      ('Zeus ancient statue', 'Greek — Zeus'), ('Athena ancient statue', 'Greek — Athena'),
      ('Apollo ancient statue', 'Greek — Apollo'), ('Aphrodite ancient statue', 'Greek — Aphrodite'),
      ('Odin mythology illustration', 'Norse — Odin'), ('Thor mythology illustration', 'Norse — Thor'),
      ('Freyja mythology illustration', 'Norse — Freyja'), ('Tyr mythology illustration', 'Norse — Týr'),
      ('Ra Egyptian god', 'Egyptian — Ra'), ('Isis Egyptian goddess', 'Egyptian — Isis'),
      ('Osiris Egyptian god', 'Egyptian — Osiris'), ('Horus Egyptian god', 'Egyptian — Horus'),
      ('Anubis Egyptian god', 'Egyptian — Anubis'), ('Sekhmet Egyptian goddess', 'Egyptian — Sekhmet'),
      ('Inanna Ishtar ancient relief', 'Mesopotamian — Inanna/Ishtar'), ('Enki Ea ancient', 'Mesopotamian — Enki/Ea'),
      ('Marduk ancient relief', 'Mesopotamian — Marduk'), ('Nergal ancient god', 'Mesopotamian — Nergal'),
      ('Shiva painting sculpture', 'Hindu — Shiva'), ('Vishnu painting sculpture', 'Hindu — Vishnu'),
      ('Krishna painting', 'Hindu — Krishna'), ('Ganesha painting sculpture', 'Hindu — Ganesha'),
      ('Kali painting goddess', 'Hindu — Kali'), ('Durga painting goddess', 'Hindu — Durga'),
      ('Avalokiteshvara painting sculpture', 'Buddhist — Avalokiteśvara'), ('Green Tara thangka', 'Buddhist — Tārā'),
      ('Manjushri Buddhist painting', 'Buddhist — Mañjuśrī'), ('Vajrapani Buddhist painting', 'Buddhist — Vajrapāṇi'),
      ('Amaterasu Japanese mythology art', 'Shinto/Japanese — Amaterasu'), ('Susanoo Japanese mythology art', 'Shinto/Japanese — Susanoo'),
      ('Inari Japanese deity art', 'Shinto/Japanese — Inari'), ('Hachiman Japanese deity art', 'Shinto/Japanese — Hachiman'),
      ('Quetzalcoatl codex', 'Aztec/Nahua — Quetzalcoatl'), ('Tlaloc codex', 'Aztec/Nahua — Tlaloc'),
      ('Huitzilopochtli codex', 'Aztec/Nahua — Huitzilopochtli'), ('Tezcatlipoca codex', 'Aztec/Nahua — Tezcatlipoca'),
      ('Maya Chaac god', 'Maya — Chaac'), ('Maya Itzamna god', 'Maya — Itzamna'),
      ('Mazu Chinese goddess painting', 'Chinese — Mazu'), ('Guanyin Chinese painting', 'Chinese/Buddhist — Guanyin')
    ]
  })
])

BAD_TITLE = re.compile(r'\b(map|flag|logo|coat of arms|stamp|coin|banknote|diagram|chart|screenshot|icon|emoji|cosplay|tattoo)\b', re.I)
GOOD_MIME = {'image/jpeg','image/png','image/webp','image/gif','image/tiff','image/svg+xml'}

def fetch_json(params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(API + '?' + q, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def commons_search(query, limit):
    data = fetch_json({
      'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':max(limit*4,12),
      'prop':'imageinfo','iiprop':'url|mime|extmetadata','iiurlwidth':640,'format':'json','formatversion':2
    })
    out=[]
    for p in data.get('query',{}).get('pages',[]):
        title=p.get('title','')
        if BAD_TITLE.search(title):
            continue
        ii=(p.get('imageinfo') or [{}])[0]
        if ii.get('mime') not in GOOD_MIME:
            continue
        thumb=ii.get('thumburl') or ii.get('url')
        if not thumb:
            continue
        meta=ii.get('extmetadata') or {}
        lic=(meta.get('LicenseShortName') or {}).get('value','')
        date=(meta.get('DateTimeOriginal') or meta.get('DateTime') or {}).get('value','')
        artist=(meta.get('Artist') or {}).get('value','')
        artist=re.sub('<[^>]+>',' ',artist)
        artist=re.sub(r'\s+',' ',artist).strip()
        page='https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ','_'), safe=':/()_,.-%')
        out.append({'title':title.removeprefix('File:'),'page':page,'thumb':thumb,'license':lic,'date':date,'artist':artist})
        if len(out)>=limit:
            break
    return out

def esc(s): return html.escape(str(s or ''), quote=True).replace('{','&#123;').replace('}','&#125;')

def card(item, label):
    bits=[esc(label)]
    if item.get('date'): bits.append(esc(item['date'][:10]))
    if item.get('license'): bits.append(esc(item['license']))
    meta=' · '.join(bits)
    artist=esc(item.get('artist',''))
    artist_line=f'<em>{artist[:180]}</em>' if artist else ''
    return (f'<a class="myth-card" href="{esc(item["page"])}" target="_blank" rel="noopener noreferrer">'
            f'<img loading="lazy" decoding="async" src="{esc(item["thumb"])}" alt="{esc(item["title"])}">'
            f'<span><b>{esc(item["title"])}</b><small>{meta}</small>{artist_line}</span></a>')

def build():
    used=set(); totals={}; files=[]
    for idx,(slug,sec) in enumerate(SECTIONS.items(),1):
        rows=[]
        query_counts=[]
        for query,label in sec['queries']:
            got=[]
            try:
                results=commons_search(query, sec['per_query'])
            except Exception as e:
                print('WARN search failed',query,e)
                results=[]
            for item in results:
                key=item['page']
                if key in used: continue
                used.add(key); got.append((item,label)); rows.append((item,label))
            query_counts.append((label,len(got)))
            time.sleep(0.12)
        totals[slug]=len(rows)
        jump=''.join(f'<span>{esc(label)} <b>{n}</b></span>' for label,n in query_counts if n)
        body=[f'<section class="gallery-section mythology-atlas" id="atlas-{slug}">',
              f'<h2>{esc(sec["title"])}</h2>', f'<p class="art-source-note">{esc(sec["intro"])}</p>',
              f'<div class="atlas-key">{jump}</div>', '<div class="myth-grid">']
        body.extend(card(item,label) for item,label in rows)
        body.extend(['</div>','</section>'])
        fn=OUT/f'{idx:02d}-{slug}.txt'; fn.write_text('\n'.join(body)+'\n',encoding='utf-8'); files.append(fn)
        print(slug,len(rows))

    intro = '''<section class="gallery-section mythology-atlas-intro" id="mythology-symbol-atlas">
<h2>Mythology, symbols and sacred-image atlas</h2>
<p>This archive expansion moves beyond the images that happened to appear in the cosmology tests. It deliberately adds a much wider comparative visual field: Celtic and Insular knotwork; Norse runestones and dragon/serpent ornament; rune systems and later Icelandic magical signs; mythological narrative art from multiple cultures; and a broad deity/sacred-figure atlas. Every card links to its Wikimedia Commons source page.</p>
<p class="art-source-note"><strong>Dating discipline:</strong> visual similarity is not being used as a dating claim. Medieval Christian Insular manuscripts, Viking Age runestones, ancient temple/relief art, early-modern mythological engravings and nineteenth-century myth illustrations are different source classes and remain labelled as such.</p>
<div class="atlas-jumps">'''
    for slug,sec in SECTIONS.items(): intro += f'<a href="#atlas-{slug}">{esc(sec["title"])} ({totals[slug]})</a>'
    intro += '</div></section>\n'
    (OUT/'00-intro.txt').write_text(intro,encoding='utf-8')

    manifest={'generated_from':'Wikimedia Commons MediaWiki API','sections':totals,'unique_images':sum(totals.values()),'queries':{k:v['queries'] for k,v in SECTIONS.items()}}
    (ROOT/'research'/'art_mythology_atlas_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    art=ROOT/'art.html'; s=art.read_text(encoding='utf-8')
    marker='<!-- MYTHOLOGY_SYMBOL_ATLAS -->'
    if marker not in s:
        block='\n'+marker+'\n{% include_relative cosmology_expansions/art_mythology/00-intro.txt %}\n'
        for fn in files: block += '{% include_relative '+str(fn.relative_to(ROOT)).replace('\\','/')+' %}\n'
        s=s.replace('<!-- FULL_TEST_CORPUS_ARCHIVE -->',block+'\n<!-- FULL_TEST_CORPUS_ARCHIVE -->',1)
    css='''\n.mythology-atlas-intro{border-color:#6c4e86;background:linear-gradient(180deg,#1b1425,#10151d)}.atlas-jumps{display:flex;gap:7px;flex-wrap:wrap;margin-top:14px}.atlas-jumps a{font-size:.78rem;text-decoration:none;border:1px solid #4b4264;border-radius:999px;padding:6px 9px;background:#151222}.atlas-key{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.atlas-key span{font-size:.68rem;color:var(--muted);border:1px solid #313b50;border-radius:999px;padding:3px 7px}.atlas-key b{color:var(--cyan)}.myth-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-top:14px}.myth-card{display:flex;flex-direction:column;min-width:0;background:#0d121a;border:1px solid #303a4e;border-radius:9px;overflow:hidden;color:var(--text);text-decoration:none}.myth-card:hover{border-color:var(--violet);transform:translateY(-1px)}.myth-card img{width:100%;aspect-ratio:1/1;object-fit:cover;background:#070a0f}.myth-card span{padding:8px;min-width:0}.myth-card b{display:block;font-size:.73rem;line-height:1.25}.myth-card small{display:block;color:var(--muted);font-size:.62rem;line-height:1.35;margin-top:4px}.myth-card em{display:block;color:#b8c1d6;font-style:normal;font-size:.58rem;line-height:1.3;margin-top:3px;max-height:2.6em;overflow:hidden}@media(max-width:760px){.myth-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}\n'''
    if '.mythology-atlas-intro{' not in s: s=s.replace('</style>',css+'</style>',1)
    art.write_text(s,encoding='utf-8')
    print('TOTAL',sum(totals.values()))

if __name__=='__main__': build()
