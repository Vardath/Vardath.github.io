#!/usr/bin/env python3
import html, json, pathlib, re, time, urllib.error, urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'cosmology_expansions'/'art_mythology'/'06-deity-named-supplement.txt'
API='https://commons.wikimedia.org/w/api.php'
UA='Vardath-Art-Archive/1.2 (source-linked deity atlas; https://vardath.github.io)'
PAUSE=1.2
BAD=re.compile(r'\b(map|flag|logo|coat of arms|stamp|coin|banknote|diagram|chart|screenshot|icon|emoji|cosplay|tattoo)\b',re.I)
GOOD={'image/jpeg','image/png','image/webp','image/gif','image/tiff','image/svg+xml'}

DEITIES=[
 ('Greek','Zeus','Zeus ancient statue'),('Greek','Athena','Athena ancient statue'),('Greek','Apollo','Apollo ancient statue'),('Greek','Artemis','Artemis ancient statue'),('Greek','Hermes','Hermes ancient statue'),('Greek','Aphrodite','Aphrodite ancient statue'),
 ('Roman','Jupiter','Jupiter Roman statue'),('Roman','Mars','Mars Roman statue'),('Roman','Venus','Venus Roman statue'),('Roman','Minerva','Minerva Roman statue'),
 ('Norse','Odin','Odin mythology illustration'),('Norse','Thor','Thor mythology illustration'),('Norse','Freyja','Freyja mythology illustration'),('Norse','Tyr','Tyr Norse mythology illustration'),
 ('Egyptian','Ra','Ra Egyptian god art'),('Egyptian','Isis','Isis Egyptian goddess art'),('Egyptian','Osiris','Osiris Egyptian god art'),('Egyptian','Horus','Horus Egyptian god art'),('Egyptian','Anubis','Anubis Egyptian god art'),('Egyptian','Sekhmet','Sekhmet Egyptian goddess statue'),('Egyptian','Thoth','Thoth Egyptian god art'),
 ('Mesopotamian','Inanna / Ishtar','Inanna Ishtar ancient relief'),('Mesopotamian','Enki / Ea','Enki Ea Mesopotamian god'),('Mesopotamian','Marduk','Marduk ancient relief'),('Mesopotamian','Nergal','Nergal Mesopotamian god'),
 ('Hindu','Shiva','Shiva painting sculpture'),('Hindu','Vishnu','Vishnu painting sculpture'),('Hindu','Krishna','Krishna painting'),('Hindu','Ganesha','Ganesha painting sculpture'),('Hindu','Kali','Kali goddess painting'),('Hindu','Durga','Durga goddess painting'),('Hindu','Lakshmi','Lakshmi painting'),('Hindu','Saraswati','Saraswati painting'),
 ('Buddhist','Avalokiteshvara','Avalokiteshvara painting sculpture'),('Buddhist','Tara','Green Tara thangka'),('Buddhist','Manjushri','Manjushri Buddhist painting'),('Buddhist','Vajrapani','Vajrapani Buddhist painting'),
 ('Shinto / Japanese','Amaterasu','Amaterasu Japanese mythology art'),('Shinto / Japanese','Susanoo','Susanoo Japanese mythology art'),('Shinto / Japanese','Inari','Inari Japanese deity art'),('Shinto / Japanese','Hachiman','Hachiman Japanese deity art'),
 ('Aztec / Nahua','Quetzalcoatl','Quetzalcoatl codex'),('Aztec / Nahua','Tlaloc','Tlaloc codex'),('Aztec / Nahua','Huitzilopochtli','Huitzilopochtli codex'),('Aztec / Nahua','Tezcatlipoca','Tezcatlipoca codex'),
 ('Maya','Chaac','Maya Chaac god'),('Maya','Itzamna','Maya Itzamna god'),
 ('Chinese','Mazu','Mazu Chinese goddess painting'),('Chinese / Buddhist','Guanyin','Guanyin Chinese painting'),('Chinese','Jade Emperor','Jade Emperor Chinese art'),
 ('Slavic','Perun','Perun Slavic mythology illustration'),('Slavic','Veles','Veles Slavic mythology illustration'),('Slavic','Mokosh','Mokosh Slavic mythology illustration'),
 ('Celtic / Irish','Lugh','Lugh Celtic mythology illustration'),('Celtic / Irish','Brigid','Brigid Celtic goddess art'),('Celtic / Irish','The Dagda','Dagda Celtic mythology illustration'),('Gaulish Celtic','Cernunnos','Cernunnos ancient depiction')
]

def get(params, attempts=6):
    url=API+'?'+urllib.parse.urlencode(params)
    for a in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
            with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429,502,503) or a==attempts-1: raise
            try: wait=max(float(e.headers.get('Retry-After') or 0),4*(a+1))
            except Exception: wait=4*(a+1)
            print('RATE',e.code,'wait',wait);time.sleep(wait)
        except urllib.error.URLError:
            if a==attempts-1: raise
            time.sleep(3*(a+1))

def candidates(query):
    d=get({'action':'query','generator':'search','gsrsearch':query,'gsrnamespace':6,'gsrlimit':16,'prop':'imageinfo','iiprop':'url|mime|extmetadata','iiurlwidth':640,'format':'json','formatversion':2,'maxlag':5})
    out=[]
    for p in d.get('query',{}).get('pages',[]):
        title=p.get('title',''); ii=(p.get('imageinfo') or [{}])[0]
        if BAD.search(title) or ii.get('mime') not in GOOD: continue
        thumb=ii.get('thumburl') or ii.get('url')
        if not thumb: continue
        meta=ii.get('extmetadata') or {}
        page='https://commons.wikimedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_'),safe=':/()_,.-%')
        lic=(meta.get('LicenseShortName') or {}).get('value','')
        date=(meta.get('DateTimeOriginal') or meta.get('DateTime') or {}).get('value','')
        out.append({'title':title.removeprefix('File:'),'page':page,'thumb':thumb,'license':lic,'date':date})
    return out

def pick(name,query,used):
    rows=candidates(query)
    tokens=[t.lower() for t in re.findall(r"[A-Za-zÀ-ÿ]+",name) if len(t)>2 and t.lower() not in {'the','god','goddess'}]
    def score(r):
        t=r['title'].lower(); s=0
        if any(tok in t for tok in tokens): s+=10
        if re.search(r'\b(statue|relief|painting|sculpt|papyrus|codex|illustr|thangka|fresco|idol|figure)\b',t): s+=3
        if r['page'] in used:s-=100
        return s
    rows.sort(key=score,reverse=True)
    return rows[0] if rows and score(rows[0])>-50 else None

def esc(s):return html.escape(str(s or ''),quote=True).replace('{','&#123;').replace('}','&#125;')

def main():
    used=set(); cards=[]; counts={}; manifest=[]
    for tradition,name,query in DEITIES:
        try:item=pick(name,query,used)
        except Exception as e:
            print('WARN',tradition,name,repr(e));item=None
        if item:
            used.add(item['page']);counts[tradition]=counts.get(tradition,0)+1
            bits=[tradition,name]
            if item.get('date'):bits.append(item['date'][:10])
            if item.get('license'):bits.append(item['license'])
            cards.append(f'<a class="myth-card" href="{esc(item["page"])}" target="_blank" rel="noopener noreferrer"><img loading="lazy" decoding="async" src="{esc(item["thumb"])}" alt="{esc(item["title"])}"><span><b>{esc(name)} — {esc(item["title"])}</b><small>{esc(" · ".join(bits))}</small></span></a>')
            manifest.append({'tradition':tradition,'name':name,'query':query,**item})
            print('OK',tradition,name,item['title'])
        else:print('MISS',tradition,name)
        time.sleep(PAUSE)
    chips=''.join(f'<span>{esc(k)} <b>{v}</b></span>' for k,v in counts.items())
    body=['<section class="gallery-section mythology-atlas" id="atlas-named-deities">','<h2>Named gods, goddesses and sacred figures</h2>','<p class="art-source-note">A named-figure supplement to the broader deity search above. Each card is a source-linked Commons image selected independently for that figure; living religious traditions and historical mythologies are presented side by side for visual reference, not as claims of equivalence.</p>',f'<div class="atlas-key">{chips}</div>','<div class="myth-grid">',*cards,'</div>','</section>']
    OUT.write_text('\n'.join(body)+'\n',encoding='utf-8')
    (ROOT/'research'/'art_deity_named_manifest.json').write_text(json.dumps({'count':len(cards),'records':manifest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    art=ROOT/'art.html';s=art.read_text(encoding='utf-8');marker='<!-- NAMED_DEITY_SUPPLEMENT -->'
    if marker not in s:
        inc='\n'+marker+'\n{% include_relative cosmology_expansions/art_mythology/06-deity-named-supplement.txt %}\n'
        anchor='{% include_relative cosmology_expansions/art_mythology/05-deities.txt %}'
        s=s.replace(anchor,anchor+inc,1)
        art.write_text(s,encoding='utf-8')
    print('TOTAL NAMED DEITIES',len(cards))

if __name__=='__main__':main()
