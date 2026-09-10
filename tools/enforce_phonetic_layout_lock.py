#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
html=ROOT/'phonetic-bridge.html'
loader=ROOT/'phonetic-no-autoscroll.js'

text=html.read_text(encoding='utf-8')
# Collapse every no-autoscroll loader reference to one authoritative tag.
text=re.sub(r'\s*<script\s+defer\s+src="phonetic-no-autoscroll\.js\?v=[^"]+"></script>','',text)
needle='<script defer src="phonetic-numeral-sounds.js?v=20260905-num1"></script>'
tag='<script defer src="phonetic-no-autoscroll.js?v=20260910-layout-lock20"></script>'
if needle in text:
    text=text.replace(needle,tag+'\n'+needle,1)
else:
    text=text.replace('</head>',tag+'\n</head>',1)
html.write_text(text,encoding='utf-8')

src=loader.read_text(encoding='utf-8')
required=[
    "#originalLanguageDictionary{grid-column:1/-1!important",
    "grid-template-columns:repeat(4,minmax(0,1fr))!important",
    "__VARDATH_PHONETIC_LAYOUT_GUARD__",
    "script[src*=\"phonetic-no-autoscroll.js\"]",
]
missing=[x for x in required if x not in src]
if missing:
    raise SystemExit('Layout lock missing from phonetic-no-autoscroll.js: '+', '.join(missing))

# Hard regression assertions.
final=html.read_text(encoding='utf-8')
count=len(re.findall(r'phonetic-no-autoscroll\.js\?v=',final))
if count!=1:
    raise SystemExit(f'Expected exactly one phonetic-no-autoscroll loader, found {count}')
if '20260905-scroll1' in final:
    raise SystemExit('Stale scroll1 loader returned')
print('phonetic layout lock OK: one loader, full-span dictionary, four desktop columns')
