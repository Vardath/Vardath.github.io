#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
html=ROOT/'phonetic-bridge.html'
loader=ROOT/'phonetic-no-autoscroll.js'

text=html.read_text(encoding='utf-8')
# Collapse every layout/scroll loader reference to one authoritative pair.
text=re.sub(r'\s*<script\s+defer\s+src="phonetic-layout-safe-guard\.js\?v=[^"]+"></script>','',text)
text=re.sub(r'\s*<script\s+defer\s+src="phonetic-no-autoscroll\.js\?v=[^"]+"></script>','',text)
needle='<script defer src="phonetic-numeral-sounds.js?v=20260905-num1"></script>'
guard='<script defer src="phonetic-layout-safe-guard.js?v=20260912-guard1"></script>'
tag='<script defer src="phonetic-no-autoscroll.js?v=20260911-sequence3"></script>'
insert=guard+'\n'+tag
if needle in text:
    text=text.replace(needle,insert+'\n'+needle,1)
else:
    text=text.replace('</head>',insert+'\n</head>',1)
html.write_text(text,encoding='utf-8')

src=loader.read_text(encoding='utf-8')
required=[
    "#originalLanguageDictionary{grid-column:1/-1!important",
    "grid-template-columns:repeat(4,minmax(0,1fr))!important",
    "__VARDATH_PHONETIC_LAYOUT_GUARD__",
    "script[src*=\"phonetic-no-autoscroll.js\"]",
    "history.replaceState(null,'',location.pathname+location.search)",
    "window.scrollTo(0,0)",
    "phonetic-dictionary-audio-fix.js','20260910-wordaudio3",
    "phonetic-manuscript-grid.js','20260911-sequence3",
]
missing=[x for x in required if x not in src]
if missing:
    raise SystemExit('Layout/top/audio/corrected-sequence lock missing from phonetic-no-autoscroll.js: '+', '.join(missing))

final=html.read_text(encoding='utf-8')
scroll_count=len(re.findall(r'phonetic-no-autoscroll\.js\?v=',final))
guard_count=len(re.findall(r'phonetic-layout-safe-guard\.js\?v=',final))
if scroll_count!=1:
    raise SystemExit(f'Expected exactly one phonetic-no-autoscroll loader, found {scroll_count}')
if guard_count!=1:
    raise SystemExit(f'Expected exactly one safe layout guard, found {guard_count}')
if final.index('phonetic-layout-safe-guard.js')>final.index('phonetic-no-autoscroll.js'):
    raise SystemExit('Safe layout guard must load before phonetic-no-autoscroll.js')
if '20260905-scroll1' in final or '20260910-top-lock23' in final:
    raise SystemExit('Stale phonetic loader cache key returned')
if '20260911-sequence3' not in final:
    raise SystemExit('Authoritative corrected-sequence loader cache key missing')
print('phonetic lock OK: safe static layout guard, refresh-to-top, reconstructed-word audio, corrected Man Grid sequence')
