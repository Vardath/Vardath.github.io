const PHOIBLE_COMMIT='5c477f1934f57b3c1a16168fadc08e83dbc03362';
const BASE=`https://cdn.jsdelivr.net/gh/cldf-datasets/phoible@${PHOIBLE_COMMIT}/cldf/`;
const FILES=['languages.csv','inventories.csv','parameters.csv','values.csv'];

const FEATURE_NAMES=['tone','stress','syllabic','short','long','consonantal','sonorant','continuant','delayedRelease','approximant','tap','trill','nasal','lateral','labial','round','labiodental','coronal','anterior','distributed','strident','dorsal','high','low','front','back','tense','retractedTongueRoot','advancedTongueRoot','periodicGlottalSource','epilaryngealSource','spreadGlottis','constrictedGlottis','fortis','raisedLarynxEjective','loweredLarynxImplosive','click'];
const PRIMARY_FEATURES=new Set(['syllabic','consonantal','sonorant','continuant','labial','coronal','dorsal','high','low','front','back']);
const CELL_INFO={
A1:['High / front vowel','high/front vowel territory'],A2:['Low / front vowel','low/front vowel territory'],A3:['High / back vowel','high/back vowel territory'],A4:['Low / central / back vowel','low/central/back vowel territory'],
B1:['Labial sonorant','resonant + labial'],B2:['Coronal sonorant','resonant + coronal'],B3:['Dorsal sonorant','resonant + dorsal'],B4:['Deep / laryngeal sonorant','resonant + no primary oral place'],
C1:['Labial friction','continuant + labial'],C2:['Coronal friction','continuant + coronal'],C3:['Dorsal friction','continuant + dorsal'],C4:['Laryngeal / deep friction','continuant + no primary oral place'],
D1:['Labial closure','non-continuant + labial'],D2:['Coronal closure','non-continuant + coronal'],D3:['Dorsal closure','non-continuant + dorsal'],D4:['Laryngeal / deep closure','non-continuant + no primary oral place']};
const CELL_IDS=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4'];
const MAGIC=[16,2,3,13,5,11,10,8,9,7,6,12,4,14,15,1];
const state={languages:new Map(),inventories:new Map(),parameters:new Map(),inventorySegments:new Map(),languageInventories:new Map(),frequency:new Map(),loaded:false};

function el(id){return document.getElementById(id)}
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function setStatus(msg,kind=''){const box=el('loadStatus');if(!box)return;box.className='status '+kind;box.innerHTML=msg}

function parseCSV(text){
  const rows=[];let row=[],field='',q=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(q){if(c==='"'){if(text[i+1]==='"'){field+='"';i++}else q=false}else field+=c;continue}
    if(c==='"'){q=true;continue}
    if(c===','){row.push(field);field='';continue}
    if(c==='\n'){row.push(field);rows.push(row);row=[];field='';continue}
    if(c!=='\r')field+=c;
  }
  if(field.length||row.length){row.push(field);rows.push(row)}
  const header=rows.shift()||[];
  return {header,rows};
}
function index(header){const m={};header.forEach((h,i)=>m[h]=i);return m}
async function fetchText(name){
  const urls=[BASE+name,`https://raw.githubusercontent.com/cldf-datasets/phoible/${PHOIBLE_COMMIT}/cldf/${name}`];
  let err;
  for(const u of urls){try{const r=await fetch(u,{cache:'force-cache'});if(r.ok)return await r.text();err=new Error(`${r.status} ${u}`)}catch(e){err=e}}
  throw err||new Error('Data download failed');
}

function fnum(v){
  if(v===undefined||v===null||v===''||v==='N'||v==='0')return 0;
  const p=String(v).split(',');let n=0,c=0;
  for(const x of p){if(x==='+'){n++;c++}else if(x==='-'){n--;c++}}
  return c?n/c:0;
}
function isPlus(v){return fnum(v)>.25}
function classify(p){
  if(!p)return null;
  const cls=(p.SegmentClass||'').toLowerCase();
  if(cls==='tone'||isPlus(p.tone))return 'PROSODY';
  if(cls==='vowel'||isPlus(p.syllabic)&&!isPlus(p.consonantal)){
    const high=fnum(p.high),low=fnum(p.low),front=fnum(p.front),back=fnum(p.back);
    const vertical=high-low;
    const horizontal=front-back;
    if(vertical>=0)return horizontal>=0?'A1':'A3';
    return horizontal>=0?'A2':'A4';
  }
  let row=isPlus(p.sonorant)?'B':isPlus(p.continuant)?'C':'D';
  let col='4';
  const places=[['1',fnum(p.labial)],['2',fnum(p.coronal)],['3',fnum(p.dorsal)]].sort((a,b)=>b[1]-a[1]);
  if(places[0][1]>.25)col=places[0][0];
  return row+col;
}
function featureDistance(a,b){
  let sum=0,wSum=0,parts=[];
  for(const f of FEATURE_NAMES){
    if(f==='tone'&&classify(a)!=='PROSODY'&&classify(b)!=='PROSODY')continue;
    const av=fnum(a[f]),bv=fnum(b[f]);
    const w=PRIMARY_FEATURES.has(f)?2:1;
    const d=Math.abs(av-bv)/2;
    if(d>0.001)parts.push([f,d*w]);
    sum+=d*w;wSum+=w;
  }
  parts.sort((x,y)=>y[1]-x[1]);
  return {distance:wSum?sum/wSum:1,parts};
}
function nearest(source,targetIds,constrained=false){
  const sc=classify(source);let pool=targetIds.map(id=>state.parameters.get(id)).filter(Boolean);
  if(sc==='PROSODY')pool=pool.filter(p=>classify(p)==='PROSODY');else pool=pool.filter(p=>classify(p)!=='PROSODY');
  let same=pool.filter(p=>classify(p)===sc);
  let fallback=false;
  if(constrained&&same.length)pool=same;else if(constrained)fallback=true;
  const ranked=pool.map(p=>({p,...featureDistance(source,p)})).sort((a,b)=>a.distance-b.distance);
  return {ranked:ranked.slice(0,5),fallback};
}

function processData(texts){
  setStatus('Parsing PHOIBLE languages…');
  let t=parseCSV(texts['languages.csv']),ix=index(t.header);
  for(const r of t.rows){const id=r[ix.ID];state.languages.set(id,{ID:id,Name:r[ix.Name],Macroarea:r[ix.Macroarea],ISO:r[ix.ISO639P3code],Family:r[ix.Family_Name]})}
  setStatus('Parsing PHOIBLE inventories…');
  t=parseCSV(texts['inventories.csv']);ix=index(t.header);
  for(const r of t.rows){const id=r[ix.ID];state.inventories.set(id,{ID:id,Name:r[ix.Name],SourceID:r[ix.Inventory_source_ID],Source:r[ix.Source],URL:r[ix.URL],phonemes:+r[ix.count_phonemes]||0,consonants:+r[ix.count_consonants]||0,vowels:+r[ix.count_vowels]||0,tones:+r[ix.count_tones]||0})}
  setStatus('Parsing 3,000+ PHOIBLE segment feature vectors…');
  t=parseCSV(texts['parameters.csv']);ix=index(t.header);
  for(const r of t.rows){const p={};for(const h of t.header)p[h]=r[ix[h]];state.parameters.set(p.ID,p)}
  setStatus('Indexing 100,000+ inventory memberships…');
  t=parseCSV(texts['values.csv']);ix=index(t.header);
  for(const r of t.rows){const inv=r[ix.Inventory_ID],lang=r[ix.Language_ID],pid=r[ix.Parameter_ID];if(!inv||!lang||!pid)continue;
    if(!state.inventorySegments.has(inv))state.inventorySegments.set(inv,[]);state.inventorySegments.get(inv).push(pid);
    if(!state.languageInventories.has(lang))state.languageInventories.set(lang,new Set());state.languageInventories.get(lang).add(inv);
    state.frequency.set(pid,(state.frequency.get(pid)||0)+1;
  }
  state.loaded=true;
}

function populateLanguages(){
  const langs=[...state.languageInventories.keys()].map(id=>state.languages.get(id)).filter(Boolean).sort((a,b)=>a.Name.localeCompare(b.Name));
  const opts=langs.map(l=>`<option value="${esc(l.ID)}">${esc(l.Name)}${l.ISO?' · '+esc(l.ISO):''}</option>`).join('');
  el('sourceLanguage').innerHTML=opts;el('targetLanguage').innerHTML=opts;
  const choose=(select,needle,alt)=>{const list=[...select.options];const o=list.find(x=>x.text.toLowerCase().includes(needle))||list.find(x=>x.text.toLowerCase().includes(alt));if(o)select.value=o.value};
  choose(el('sourceLanguage'),'english','standard german');choose(el('targetLanguage'),'mandarin chinese','greek');
  updateInventorySelectors();
}
function inventoryOptions(langId){
  return [...(state.languageInventories.get(langId)||[])].map(id=>state.inventories.get(id)).filter(Boolean).sort((a,b)=>a.ID-b.ID);
}
function fillInventory(select,langId){
  const list=inventoryOptions(langId);select.innerHTML=list.map(i=>`<option value="${esc(i.ID)}">#${esc(i.ID)} · ${esc(i.SourceID||'source')} · ${i.phonemes} segments</option>`).join('');
}
function updateInventorySelectors(){
  fillInventory(el('sourceInventory'),el('sourceLanguage').value);fillInventory(el('targetInventory'),el('targetLanguage').value);populateSourceSegments();updateInventoryCards();
}
function populateSourceSegments(){
  const ids=state.inventorySegments.get(el('sourceInventory').value)||[];
  const ps=ids.map(id=>state.parameters.get(id)).filter(Boolean).sort((a,b)=>a.Name.localeCompare(b.Name));
  el('sourceSegment').innerHTML=ps.map(p=>`<option value="${esc(p.ID)}">/${esc(p.Name)}/ · ${esc(p.SegmentClass)} · ${esc(classify(p))}</option>`).join('');
  runMatch();
}
function langLabel(id){const l=state.languages.get(id);return l?`${l.Name}${l.ISO?' ('+l.ISO+')':''}`:id}
function invCard(langSel,invSel,target){
  const l=state.languages.get(el(langSel).value),i=state.inventories.get(el(invSel).value);if(!l||!i){el(target).innerHTML='';return}
  el(target).innerHTML=`<b>${esc(l.Name)}</b> · ${esc(l.Family||'family unlisted')} · ${esc(l.Macroarea||'')}<br>PHOIBLE inventory #${esc(i.ID)}: ${i.phonemes} segments (${i.consonants} consonants, ${i.vowels} vowels${i.tones?`, ${i.tones} tones`:''}) · source set ${esc(i.SourceID||'')}`;
}
function updateInventoryCards(){invCard('sourceLanguage','sourceInventory','sourceMeta');invCard('targetLanguage','targetInventory','targetMeta')}
function featuresHTML(p){
  const plus=FEATURE_NAMES.filter(f=>fnum(p[f])>.25);const minus=FEATURE_NAMES.filter(f=>fnum(p[f])<-.25);
  return `<div class="featureline"><b>+ features:</b> ${esc(plus.join(', ')||'none')}</div><div class="featureline"><b>− features:</b> ${esc(minus.join(', ')||'none')}</div>`;
}
function matchCard(title,res,sc){
  if(!res.ranked.length)return `<div class="matchcard"><h4>${title}</h4><p>No comparable target segment in this inventory.</p></div>`;
  const best=res.ranked[0],bc=classify(best.p),same=bc===sc;
  return `<div class="matchcard"><h4>${title}</h4><div class="bigipa">/${esc(best.p.Name)}/</div><div><span class="pill">${esc(bc)}</span> <span class="pill">distance ${best.distance.toFixed(4)}</span> ${same?'<span class="pill good">same cell</span>':'<span class="pill warn">different cell</span>'}</div><p>${res.fallback?'No target phoneme occupied the same bridge cell, so the bridge matcher fell back to the full target inventory.':''}</p><details><summary>Top five candidates</summary>${res.ranked.map((x,i)=>`<div>${i+1}. /${esc(x.p.Name)}/ — ${x.distance.toFixed(4)} — ${esc(classify(x.p))}</div>`).join('')}</details><details><summary>Largest feature differences</summary>${best.parts.slice(0,10).map(x=>`<span class="pill">${esc(x[0])}</span>`).join(' ')||'None'}</details></div>`;
}
function runMatch(){
  if(!state.loaded)return;const p=state.parameters.get(el('sourceSegment').value);if(!p)return;
  const targetIds=state.inventorySegments.get(el('targetInventory').value)||[];const sc=classify(p);
  const free=nearest(p,targetIds,false),bridge=nearest(p,targetIds,true);
  let verdict='';
  if(free.ranked.length&&bridge.ranked.length){const a=free.ranked[0],b=bridge.ranked[0];const delta=b.distance-a.distance;
    verdict=a.p.ID===b.p.ID?`<b class="goodtxt">Agreement:</b> the 4×4 constraint does not change the nearest PHOIBLE-feature match for this sound.`:`<b class="warntxt">Constraint cost:</b> the 4×4 changes the winner from /${esc(a.p.Name)}/ to /${esc(b.p.Name)}/ and adds ${delta.toFixed(4)} normalized feature-distance.`;
  }
  el('sourceDetail').innerHTML=`<div class="bigipa">/${esc(p.Name)}/</div><div><span class="pill">${esc(p.SegmentClass)}</span> <span class="pill">bridge ${esc(sc)}</span></div>${featuresHTML(p)}`;
  el('matchResults').innerHTML=`<div class="verdict">${verdict}</div><div class="matchgrid">${matchCard('Pure PHOIBLE nearest feature match',free,sc)}${matchCard('4×4-constrained nearest match',bridge,sc)}</div>`;
  highlightCell(sc);updateGateDemo();
}

function renderGrid(){
  const mode=el('overlayMode')?.value||'code';const bridge=el('bridge');if(!bridge)return;
  bridge.innerHTML=CELL_IDS.map((id,i)=>{let over=id;if(mode==='magic')over=MAGIC[i];if(mode==='power')over='2^'+(MAGIC[i]-1);if(mode==='binary')over=i.toString(2).padStart(4,'0');return `<button class="cell" data-cell="${id}" onclick="showCell('${id}')"><span class="overlay">${esc(over)}</span><strong>${id} · ${esc(CELL_INFO[id][0])}</strong><small>${esc(CELL_INFO[id][1])}</small></button>`}).join('');
}
window.showCell=function(id){
  document.querySelectorAll('.cell').forEach(x=>x.classList.toggle('active',x.dataset.cell===id));
  const ps=[...state.parameters.values()].filter(p=>classify(p)===id).sort((a,b)=>(state.frequency.get(b.ID)||0)-(state.frequency.get(a.ID)||0));
  const occ=ps.reduce((n,p)=>n+(state.frequency.get(p.ID)||0),0);
  el('cellDetail').innerHTML=`<h3>${id} · ${esc(CELL_INFO[id][0])}</h3><p>${ps.length?`${ps.length} PHOIBLE segment types currently classify here, representing ${occ.toLocaleString()} inventory occurrences in this snapshot.`:'Load PHOIBLE to calculate live occupancy.'}</p>${ps.length?`<div class="ipa-cloud">${ps.slice(0,40).map(p=>`<span title="${state.frequency.get(p.ID)||0} inventories">/${esc(p.Name)}/</span>`).join(' ')}</div>`:''}<p class="small">This cell assignment is the experimental bridge classifier, not a PHOIBLE category.</p>`;
}
function highlightCell(id){document.querySelectorAll('.cell').forEach(x=>x.classList.toggle('sourcecell',x.dataset.cell===id))}
function updateCellCounts(){renderGrid();showCell('A1')}

function updateGateDemo(){
  const p=state.parameters.get(el('sourceSegment')?.value);if(!p)return;const ids=state.inventorySegments.get(el('sourceInventory').value)||[];const ps=ids.map(id=>state.parameters.get(id)).filter(Boolean);
  const idx=ps.findIndex(x=>x.ID===p.ID);const next=ps[idx+1]||ps[0];const a=classify(p),b=classify(next);
  el('gateExample').innerHTML=`Example inventory-order pair: <span class="node">/${esc(p.Name)}/ · ${esc(a)}</span> <span class="arrowmini">→</span> <span class="node">/${esc(next?.Name||'')}/ · ${esc(b)}</span><br><span class="small">This is only an inventory pair, not corpus speech order. Real transition-frequency testing requires corpora, which PHOIBLE itself does not provide.</span>`;
}
function renderGateMatrix(){
  el('gateMatrix').innerHTML=CELL_IDS.flatMap(a=>CELL_IDS.map(b=>`<div class="g" title="${a} → ${b}">${a}<br>→<br>${b}</div>`)).join('');
}

function centroid(cell){
  const ps=[...state.parameters.values()].filter(p=>classify(p)===cell);if(!ps.length)return null;const c={};let total=0;
  for(const p of ps){const w=state.frequency.get(p.ID)||1;total+=w;for(const f of FEATURE_NAMES)c[f]=(c[f]||0)+fnum(p[f])*w}
  for(const f of FEATURE_NAMES)c[f]=(c[f]||0)/total;return c;
}
function centroidDistance(a,b){let sum=0,w=0;for(const f of FEATURE_NAMES){const wt=PRIMARY_FEATURES.has(f)?2:1;sum+=Math.abs((a[f]||0)-(b[f]||0))/2*wt;w+=wt}return sum/w}
function pathCost(order,centroids){let s=0;for(let n=1;n<order.length;n++)s+=centroidDistance(centroids[order[n-1]],centroids[order[n]]);return s}
function shuffle(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function runMagicTest(){
  if(!state.loaded)return;const c={};for(const id of CELL_IDS)c[id]=centroid(id);if(Object.values(c).some(x=>!x)){el('magicResult').innerHTML='Not all cells contain data; test unavailable.';return}
  const magicOrder=[...Array(16).keys()].sort((i,j)=>MAGIC[i]-MAGIC[j]).map(i=>CELL_IDS[i]);const magicCost=pathCost(magicOrder,c);
  const trials=5000,costs=[];for(let i=0;i<trials;i++)costs.push(pathCost(shuffle([...CELL_IDS]),c));costs.sort((a,b)=>a-b);
  const rank=costs.filter(x=>x<=magicCost).length/trials;const mean=costs.reduce((a,b)=>a+b,0)/trials;
  const interpretation=rank<.05?'unusually smooth relative to random paths':rank>.95?'unusually discontinuous relative to random paths':'within the ordinary random range';
  el('magicResult').innerHTML=`<div class="metric"><b>Dürer-order phonetic path cost</b><span>${magicCost.toFixed(4)}</span></div><div class="metric"><b>Random-path mean</b><span>${mean.toFixed(4)}</span></div><div class="metric"><b>Random percentile</b><span>${(rank*100).toFixed(1)}%</span></div><p>The numbered path is <b>${interpretation}</b> in this 5,000-permutation test. Lower cost means consecutive magic-square numbers move through more similar PHOIBLE feature centroids. This tests the overlay against chance; it does not by itself establish linguistic significance.</p><div class="small">Magic path: ${magicOrder.join(' → ')}</div>`;
}

function wire(){
  el('sourceLanguage').addEventListener('change',()=>{fillInventory(el('sourceInventory'),el('sourceLanguage').value);populateSourceSegments();updateInventoryCards()});
  el('targetLanguage').addEventListener('change',()=>{fillInventory(el('targetInventory'),el('targetLanguage').value);updateInventoryCards();runMatch()});
  el('sourceInventory').addEventListener('change',()=>{populateSourceSegments();updateInventoryCards()});
  el('targetInventory').addEventListener('change',()=>{updateInventoryCards();runMatch()});
  el('sourceSegment').addEventListener('change',runMatch);
  el('overlayMode').addEventListener('change',renderGrid);
  el('runMagic').addEventListener('click',runMagicTest);
}
async function boot(){
  renderGrid();renderGateMatrix();wire();setStatus('Downloading the pinned PHOIBLE CLDF snapshot…');
  try{
    const arr=await Promise.all(FILES.map(async n=>[n,await fetchText(n)]));const texts=Object.fromEntries(arr);processData(texts);populateLanguages();updateCellCounts();
    el('dataStats').innerHTML=`<span><b>${state.languages.size.toLocaleString()}</b> language records</span><span><b>${state.inventories.size.toLocaleString()}</b> inventories</span><span><b>${state.parameters.size.toLocaleString()}</b> segment types</span><span><b>${[...state.frequency.values()].reduce((a,b)=>a+b,0).toLocaleString()}</b> inventory memberships</span>`;
    setStatus(`PHOIBLE loaded. Real inventory and feature data are active. Snapshot commit <code>${PHOIBLE_COMMIT.slice(0,10)}</code>.`,'ok');
    runMatch();
  }catch(e){console.error(e);setStatus(`Could not load PHOIBLE data in this browser. ${esc(e.message)}. Try reloading; the page will not substitute illustrative data.`,'error')}
}
document.addEventListener('DOMContentLoaded',boot);
