(()=>{
'use strict';
if(window.__VARDATH_TEST5_MIRROR_DICTIONARY__)return;
window.__VARDATH_TEST5_MIRROR_DICTIONARY__=true;
const PAGE=60;
const DATA_ROOT='data/man-grid-test5-web/';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const nfmt=n=>Number(n||0).toLocaleString();
const pct=x=>(100*Number(x||0)).toFixed(1)+'%';
const fmt=(n,d=3)=>Number(n||0).toFixed(d);
function css(){
 if(document.getElementById('test5MirrorDictionaryStyles'))return;
 const s=document.createElement('style');s.id='test5MirrorDictionaryStyles';s.textContent=`
#test5MirrorDictionary{min-width:0}
#test5MirrorDictionary .t5-kicker{color:var(--cyan);font-size:.76rem;text-transform:uppercase;letter-spacing:.1em;font-weight:700}
#test5MirrorDictionary .t5-head{display:flex;gap:14px;align-items:flex-end;justify-content:space-between;flex-wrap:wrap}
#test5MirrorDictionary .t5-tools{display:flex;gap:8px;flex-wrap:wrap;align-items:end}
#test5MirrorDictionary .t5-tools label{display:block;color:var(--muted);font-size:.78rem;margin-bottom:4px}
#test5MirrorDictionary .t5-tools input,#test5MirrorDictionary .t5-tools select{background:#0d1119;color:inherit;border:1px solid var(--line);border-radius:8px;padding:9px 10px;min-width:150px}
#test5MirrorDictionary .t5-sort{margin:10px 0 12px;padding:10px 12px;border:3px solid var(--cyan);border-radius:10px;background:#101923;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
#test5MirrorDictionary .t5-sort label{font-weight:900;color:var(--cyan);font-size:1rem;letter-spacing:.05em}
#test5MirrorDictionary .t5-sort select{min-width:230px;padding:9px 12px;font-weight:800;background:#0c1018;color:white;border:2px solid var(--cyan);border-radius:9px}
#test5MirrorDictionary .t5-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px;margin-top:7px}
#test5MirrorDictionary .t5-card{background:#0d1119;border:1px solid var(--line);border-radius:8px;padding:7px 8px;min-width:0}
#test5MirrorDictionary .t5-cardhead{display:flex;align-items:baseline;justify-content:space-between;gap:8px;min-width:0}
#test5MirrorDictionary .t5-word{font:700 1.08rem Georgia,serif;color:var(--cyan);line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#test5MirrorDictionary .t5-meaning{font-size:.88rem;font-weight:700;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
#test5MirrorDictionary .t5-path{font-family:ui-monospace,monospace;font-size:.64rem;margin:3px 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;opacity:.85}
#test5MirrorDictionary .t5-actions{display:flex;gap:3px;align-items:center;flex-wrap:nowrap;margin:0}
#test5MirrorDictionary .t5-card .btn{padding:3px 6px;font-size:.66rem;line-height:1.05;white-space:nowrap}
#test5MirrorDictionary .t5-info{margin-left:auto;font-size:.82rem;color:var(--cyan);cursor:help;line-height:1}
#test5MirrorDictionary .t5-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:14px 0}
#test5MirrorDictionary .t5-stats>div,#test5MirrorDictionary .t5-method,#test5MirrorDictionary .t5-compare{border:1px solid var(--line);border-radius:11px;padding:12px;background:#0d1119}
#test5MirrorDictionary .t5-num{display:block;font:700 1.35rem Georgia,serif;color:var(--cyan)}
#test5MirrorDictionary .t5-warning{border-left:4px solid var(--warn);padding:12px 14px;background:#18150e;border-radius:8px;margin:14px 0}
#test5MirrorDictionary .t5-ok{border-left:4px solid var(--good);padding:12px 14px;background:#0f1716;border-radius:8px;margin:14px 0}
#test5MirrorDictionary .t5-method ol{margin:8px 0 0 22px;padding:0}
#test5MirrorDictionary .t5-method li{margin:7px 0}
#test5MirrorDictionary .t5-pager{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin:14px 0}
#test5MirrorDictionary .t5-pager .buttons{display:flex;gap:7px}
#test5MirrorDictionary .t5-note,#test5MirrorDictionary .t5-count{color:var(--muted);font-size:.82rem}
#test5MirrorDictionary .t5-comparegrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
#test5MirrorDictionary .t5-comparegrid>div{border:1px solid var(--line);border-radius:9px;padding:10px;background:#10141d}
#test5MirrorDictionary .t5-empty{padding:18px;border:1px dashed var(--line);border-radius:10px;color:var(--muted)}
#test5MirrorDictionary .t5-card details{margin-top:7px;border-top:1px solid var(--line);padding-top:5px}
#test5MirrorDictionary .t5-card summary{cursor:pointer;color:var(--cyan);font-size:.72rem}
@media(max-width:1050px){#test5MirrorDictionary .t5-grid{grid-template-columns:repeat(4,minmax(0,1fr))}#test5MirrorDictionary .t5-card .btn{padding:3px 5px;font-size:.63rem}}
@media(max-width:700px){#test5MirrorDictionary .t5-grid{grid-template-columns:repeat(2,minmax(0,1fr))}#test5MirrorDictionary .t5-stats{grid-template-columns:repeat(2,1fr)}#test5MirrorDictionary .t5-comparegrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){#test5MirrorDictionary .t5-stats,#test5MirrorDictionary .t5-comparegrid{grid-template-columns:1fr}#test5MirrorDictionary .t5-tools>*{width:100%}#test5MirrorDictionary .t5-tools input,#test5MirrorDictionary .t5-tools select{width:100%}}
@media(max-width:430px){#test5MirrorDictionary .t5-grid{grid-template-columns:1fr}}
`;document.head.appendChild(s);
}
async function loadIndex(){const r=await fetch(DATA_ROOT+'index.json?v=20260912-test5dict2',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status+' index');return r.json();}
async function loadPart(p,pi){const r=await fetch(DATA_ROOT+p.file+'?v=20260912-test5dict2',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status+' '+p.file);const text=await r.text();return text.split('\n').map(x=>x.trim()).filter(Boolean).map((line,i)=>{const v=JSON.parse(line);return {rank:pi*3000+i+1,meaning:v[0],ipa:v[1],languages:+v[2],families:+v[3],distance:+v[4],stability:+v[5],confidence:+v[6],_part:pi,_line:i+1};});}
async function loadAll(){const index=await loadIndex();const chunks=await Promise.all(index.parts.map((p,i)=>loadPart(p,i)));return {index,words:chunks.flat()};}
function confLabel(c){return c>=.9?'very high model fit':c>=.8?'high model fit':c>=.7?'moderate-high model fit':'exploratory';}
function waitForTest3(attempt=0){
 const anchor=document.getElementById('exact-test-3');
 if(anchor){build(anchor);return;}
 if(attempt<240)setTimeout(()=>waitForTest3(attempt+1),125);
 else console.error('Test 5 dictionary: Test 3 anchor did not appear.');
}
async function build(anchor){
 if(document.getElementById('test5MirrorDictionary'))return;
 css();
 const sec=document.createElement('section');sec.id='test5MirrorDictionary';sec.className='section wrap';
 sec.innerHTML='<div class="status">Loading the 50-shard exact mirrored-Man-Grid dictionary…</div>';
 anchor.insertAdjacentElement('afterend',sec);
 try{
  const {index,words}=await loadAll();
  const s=index.summary||{},g=index.grid||{},c=index.calculation||{};
  sec.innerHTML=`
  <div class="t5-kicker">Corrected research · Test 5 complete · 50 exact shards</div>
  <div class="t5-head"><div><h2>Test 5 — Candidate Original Language Dictionary</h2><p class="lead">The reconstructed dictionary now uses the exact mirrored Man Grid as the calculation itself. All ${nfmt(index.entries)} meanings were rebuilt through the ten rectangular layers on both LEFT and RIGHT; feature-space distance was not used for Test 5 reconstruction.</p></div><div class="t5-tools"><div><label for="t5Search">Search meaning or reconstructed word</label><input id="t5Search" type="search" placeholder="e.g. water, hand, sun"></div><div><label for="t5Filter">Filter</label><select id="t5Filter"><option value="all">All entries</option><option value="hiconf">Confidence ≥ 0.90</option><option value="stable">Stability ≥ 0.90</option><option value="manyfam">10+ families</option><option value="basic">Short meanings only</option></select></div></div></div>
  <div class="t5-sort"><label for="t5Sort">↕ SORT DICTIONARY:</label><select id="t5Sort" aria-label="Sort Test 5 dictionary"><option value="meaning">Meaning A–Z</option><option value="confidence">Highest confidence</option><option value="stability">Highest stability</option><option value="families">Most families</option><option value="languages">Most languages</option><option value="distance">Lowest mirror-grid distance</option></select></div>
  <div class="t5-ok"><b>The corrected 50-shard run completed and merged.</b> All <b>${s.shards_real_better_than_control}/${s.shards_compared}</b> shards beat their wrong-meaning control. The run produced <b>${nfmt(index.entries)} reconstructed meanings</b>; phoneme snapping and sequence substitutions were both calculated with the exact bilateral mirror-grid metric.</div>
  <div class="t5-stats"><div><span class="t5-num">${nfmt(index.entries)}</span><b>reconstructed meanings</b></div><div><span class="t5-num">${s.shards_real_better_than_control}/${s.shards_compared}</span><b>shards beat control</b></div><div><span class="t5-num">${nfmt(g.cells)}</span><b>rectangular grid cells</b></div><div><span class="t5-num">${g.layers_per_side}</span><b>layers per mirrored side</b></div><div><span class="t5-num">${pct(s.mean_confidence)}</span><b>mean model confidence</b></div></div>
  <div class="t5-method"><h4>How this corrected dictionary was calculated</h4><ol><li><b>Use the exact mirrored Man Grid.</b> Every PHOIBLE sound is projected through all ten rectangular layers on LEFT and RIGHT of the 1,074-cell structure.</li><li><b>Snap sounds to the Test 1 root inventory through Grid geometry.</b> Segment-to-root assignment uses normalized row/column separation across the exact mirrored layers; it does not choose roots by the old 37-feature distance.</li><li><b>Score whole words through the Grid.</b> Word comparison uses normalized edit distance. A phoneme substitution costs the bilateral mean of LEFT→RIGHT and RIGHT→LEFT structural distance across all ten layers; insertion/deletion cost is <b>${fmt(c.gap_cost,2)}</b>.</li><li><b>Reconstruct across independent language families.</b> Meanings require cross-language and cross-family evidence; the earlier feature-scored Test 4 candidate is not injected as a prior.</li><li><b>Require all 50 deterministic shards.</b> Every shard was required before merge, and all 50 beat the wrong-meaning control.</li></ol></div>
  <div class="t5-warning"><b>Research boundary:</b> this is an experimental model reconstruction, not proof that a literal single prehistoric world language existed or that these exact forms were historically spoken. Modern international names and borrowings can also produce very high agreement and should not be mistaken for ancient evidence. <b>Circle boundary:</b> no phonological operator has been assigned to the central transformative circle, so Test 5 does not invent one.</div>
  <div class="t5-compare"><h4>Corrected Test 5 result</h4><p class="t5-note">This section follows Tests 2 and 3 because those tests establish the exact Grid locality and common-parent controls used as the corrected foundation. This dictionary is the lexical expansion using the same structural Grid geometry.</p><div class="t5-comparegrid"><div><span class="t5-num">${pct(s.mean_stability)}</span><b>mean stability</b></div><div><span class="t5-num">${nfmt(s.stability_ge_090)}</span><b>entries ≥ 0.90 stability</b></div><div><span class="t5-num">${nfmt(s.confidence_ge_080)}</span><b>entries ≥ 0.80 confidence</b></div><div><span class="t5-num">${fmt(s.mean_family_distance,3)}</span><b>mean family mirror distance</b></div></div></div>
  <div class="t5-pager"><div id="t5Count" class="t5-count"></div><div class="buttons"><button class="btn" id="t5Prev">← Previous</button><button class="btn" id="t5Next">Next →</button></div></div><div id="t5Grid" class="t5-grid"></div><div class="t5-pager"><div id="t5PageInfo" class="t5-count"></div><div class="buttons"><button class="btn" id="t5Prev2">← Previous</button><button class="btn" id="t5Next2">Next →</button></div></div>`;
  const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#test5MirrorDictionary"]')){const a=document.createElement('a');a.href='#test5MirrorDictionary';a.textContent='Test 5 dictionary';nav.appendChild(a);}
  wire(sec,index,words);
 }catch(e){sec.innerHTML='<div class="status error"><b>Test 5 dictionary failed to load.</b> '+esc(e.message)+'</div>';console.error(e);}
}
function wire(sec,index,WORDS){
 let page=0,rows=WORDS.slice();
 const search=sec.querySelector('#t5Search'),sort=sec.querySelector('#t5Sort'),filter=sec.querySelector('#t5Filter');
 function apply(){const q=search.value.trim().toLowerCase();rows=WORDS.filter(w=>{const c=Number(w.confidence||0),st=Number(w.stability||0),f=Number(w.families||0),m=String(w.meaning||'');if(filter.value==='hiconf'&&c<.9)return false;if(filter.value==='stable'&&st<.9)return false;if(filter.value==='manyfam'&&f<10)return false;if(filter.value==='basic'&&(m.includes(' ')||m.length>12))return false;if(q&&!(`${m} ${w.ipa||''}`.toLowerCase().includes(q)))return false;return true;});if(sort.value==='meaning')rows.sort((a,b)=>String(a.meaning).localeCompare(String(b.meaning)));else if(sort.value==='families')rows.sort((a,b)=>b.families-a.families||b.confidence-a.confidence);else if(sort.value==='languages')rows.sort((a,b)=>b.languages-a.languages||b.confidence-a.confidence);else if(sort.value==='stability')rows.sort((a,b)=>b.stability-a.stability||b.confidence-a.confidence);else if(sort.value==='distance')rows.sort((a,b)=>a.distance-b.distance||b.confidence-a.confidence);else rows.sort((a,b)=>b.confidence-a.confidence||b.families-a.families);page=0;render();}
 function card(w){const c=Number(w.confidence||0),tip=`${nfmt(w.languages)} languages · ${nfmt(w.families)} families · mirror distance ${fmt(w.distance,6)} · stability ${fmt(w.stability,4)} · confidence ${fmt(c,4)} (${confLabel(c)})`;return `<article class="t5-card" title="${esc(tip)}"><div class="t5-cardhead"><div class="t5-meaning">${esc(w.meaning)}</div><div class="t5-word">${esc(w.ipa)}</div></div><div class="t5-path" title="${esc(tip)}">${nfmt(w.languages)} lang · ${nfmt(w.families)} fam · d ${fmt(w.distance,4)} · stab ${pct(w.stability)}</div><div class="t5-actions"><button class="btn" data-t5-play title="Hear reconstructed word">▶ Hear</button><button class="btn" data-t5-slow title="Hear slowly">▶ Slow</button><span class="t5-info" title="${esc(tip)}">ⓘ</span></div><details><summary>Metrics</summary><div class="t5-note">Confidence ${fmt(c,4)} · stability ${fmt(w.stability,4)} · mean family mirror distance ${fmt(w.distance,6)} · rank ${nfmt(w.rank)}</div></details></article>`;}
 function render(){const pages=Math.max(1,Math.ceil(rows.length/PAGE));if(page>=pages)page=pages-1;const slice=rows.slice(page*PAGE,page*PAGE+PAGE),grid=sec.querySelector('#t5Grid');grid.innerHTML=slice.length?slice.map(card).join(''):'<div class="t5-empty">No reconstructed entries match that search/filter.</div>';sec.querySelector('#t5Count').textContent=`Showing ${slice.length?`${page*PAGE+1}–${page*PAGE+slice.length}`:'0'} of ${nfmt(rows.length)} matching entries (${nfmt(WORDS.length)} total)`;sec.querySelector('#t5PageInfo').textContent=`Page ${page+1} of ${pages}`;for(const id of ['t5Prev','t5Prev2'])sec.querySelector('#'+id).disabled=page<=0;for(const id of ['t5Next','t5Next2'])sec.querySelector('#'+id).disabled=page>=pages-1;bindAudio(grid);}
 function move(d){page+=d;render();sec.querySelector('#t5Grid').scrollIntoView({block:'start',behavior:'smooth'});}
 for(const id of ['t5Prev','t5Prev2'])sec.querySelector('#'+id).onclick=()=>move(-1);for(const id of ['t5Next','t5Next2'])sec.querySelector('#'+id).onclick=()=>move(1);
 search.oninput=apply;sort.onchange=apply;filter.onchange=apply;apply();
}
const pairs=[['t͡ʃ','ch'],['d͡ʒ','j'],['tʃ','ch'],['dʒ','j'],['aɪ','eye'],['aʊ','ow'],['ɔɪ','oy'],['eɪ','ay'],['oʊ','oh'],['əʊ','oh'],['ɪə','ear'],['eə','air'],['ʊə','oor']];
const phones={'ɑ':'ah','ɒ':'o','ɔ':'aw','æ':'a','ə':'uh','ɚ':'er','ɝ':'er','ɛ':'eh','ɜ':'er','ɞ':'uh','ɪ':'ih','i':'ee','ʊ':'oo','u':'oo','ʌ':'uh','e':'eh','o':'oh','ø':'er','œ':'er','y':'ee','ɐ':'uh','ɘ':'uh','ɤ':'uh','ɯ':'oo','ɨ':'ih','ʉ':'oo','ɶ':'a','ʃ':'sh','ʒ':'zh','θ':'th','ð':'th','ŋ':'ng','ɲ':'ny','ɳ':'n','ɴ':'n','ɱ':'m','ç':'hy','x':'kh','χ':'kh','ɣ':'gh','ʁ':'r','ʀ':'r','ɹ':'r','ɾ':'r','ɽ':'r','ɻ':'r','ʎ':'ly','ɬ':'hl','ɮ':'zl','ʋ':'v','β':'v','ɸ':'f','ʂ':'sh','ʐ':'zh','ɕ':'sh','ʑ':'zh','ʔ':'','q':'k','ɢ':'g','ɖ':'d','ʈ':'t','ɟ':'g','c':'k','j':'y','ː':'','ˑ':'','̆':'','̯':'','̃':'','̥':'','̬':'','̩':'','̪':'','̺':'','̻':'','̚':'','ˈ':'','ˌ':'','.':' ','-':' ','|':' '};
function respell(raw){let s=String(raw||'').trim().replace(/^\/+|\/+$/g,'').normalize('NFC');for(const [a,b] of pairs)s=s.split(a).join(b);let o='';for(const c of s)o+=Object.hasOwn(phones,c)?phones[c]:c;return o.replace(/[^A-Za-z' ]+/g,' ').replace(/\s+/g,' ').trim()||s;}
let voice=null;function pick(){const v=speechSynthesis?.getVoices?.()||[];voice=v.find(x=>/^en-AU$/i.test(x.lang))||v.find(x=>/^en-GB$/i.test(x.lang))||v.find(x=>/^en/i.test(x.lang))||v[0]||null;return voice;}
if(window.speechSynthesis){pick();speechSynthesis.addEventListener?.('voiceschanged',pick);}
function speak(raw,slow){if(!window.speechSynthesis)return;const u=new SpeechSynthesisUtterance(respell(raw));u.rate=slow?.58:.82;u.pitch=.96;u.volume=1;u.voice=voice||pick();speechSynthesis.cancel();speechSynthesis.speak(u);}
function bindAudio(root){root.querySelectorAll('[data-t5-play],[data-t5-slow]').forEach(b=>b.onclick=e=>{e.preventDefault();const raw=b.closest('.t5-card')?.querySelector('.t5-word')?.textContent||'';speak(raw,b.hasAttribute('data-t5-slow'));});}
waitForTest3();
})();