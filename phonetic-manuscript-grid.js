(()=>{
'use strict';
if(window.__VARDATH_MANUSCRIPT_GRID_TOOL__)return;
window.__VARDATH_MANUSCRIPT_GRID_TOOL__=true;
const SPEC_URL='data/man-grid-structure-v1.json?v=20260911-structure1';
const PATH_KEY='vardath.manGrid.path.v3';
const QUEUE_KEY='vardath.manGrid.queue.v1';
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function loadJSON(key,fallback){try{const v=JSON.parse(localStorage.getItem(key)||'null');return v??fallback;}catch{return fallback;}}
function saveJSON(key,v){try{localStorage.setItem(key,JSON.stringify(v));}catch{}}
function visibleSelectText(sel){if(!sel||sel.selectedIndex<0)return'';return String(sel.options?.[sel.selectedIndex]?.textContent||'').trim();}
function css(){
 if($('#manGridStructureStyles'))return;
 const st=document.createElement('style');st.id='manGridStructureStyles';st.textContent=`
 .manugrid{margin-top:30px}.manugrid .mg-shell{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.55fr);gap:16px;align-items:start;margin:18px 0}.manugrid .mg-panel{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:15px;padding:16px;min-width:0}.manugrid .mg-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end;margin-bottom:12px}.manugrid .mg-field{flex:1 1 190px}.manugrid .mg-field.wide{flex-basis:100%}.manugrid .mg-field label{display:block;color:var(--muted);font-size:.8rem;margin-bottom:4px}.manugrid input,.manugrid textarea{width:100%;background:#0c1018;color:white;border:1px solid #3d455d;border-radius:9px;padding:10px;font:inherit}.manugrid textarea{min-height:68px;resize:vertical}.manugrid .mg-workbench{overflow:auto;max-height:78vh;border:1px solid #404861;border-radius:12px;background:#ece7da;padding:18px;touch-action:pan-x pan-y}.manugrid .mg-model{width:max-content;min-width:100%;display:flex;flex-direction:column;align-items:center;gap:14px;color:#15120f}.manugrid .mg-layer{display:flex;flex-direction:column;align-items:center;gap:6px}.manugrid .mg-layer-title{font:700 12px/1.2 Consolas,monospace;letter-spacing:.03em;color:#322b25}.manugrid .mg-pair{display:grid;grid-template-columns:max-content 26px max-content;gap:10px;align-items:stretch}.manugrid .mg-side-label{text-align:center;font:700 10px/1 Consolas,monospace;margin-bottom:4px;color:#655d55}.manugrid .mg-spine{width:2px;background:#342f2a;border-radius:2px;justify-self:center}.manugrid .mg-cellgrid{display:grid;grid-template-columns:repeat(var(--cols),var(--cell));grid-auto-rows:var(--cell);gap:2px;--cell:27px}.manugrid .mg-cell{position:relative;width:var(--cell);height:var(--cell);padding:0;border:1px solid #514a43;background:#faf7ef;color:#403a34;border-radius:2px;font:9px/1 Consolas,monospace;cursor:pointer}.manugrid .mg-cell:hover,.manugrid .mg-cell:focus{outline:none;border-color:#008fa0;box-shadow:0 0 0 1px #008fa0 inset}.manugrid .mg-cell.active{background:#d7f4f4;border-color:#008fa0}.manugrid .mg-cell.mirrored{background:#eadff3;border-color:#79548f}.manugrid .mg-cell[data-step]:after{content:attr(data-step);position:absolute;right:-3px;top:-5px;min-width:14px;height:14px;padding:0 2px;border-radius:7px;background:#071015;color:#5ce1e6;font:700 9px/14px Consolas,monospace;z-index:2}.manugrid .mg-circle-wrap{display:flex;align-items:center;justify-content:center;padding:6px 0}.manugrid .mg-circle{width:116px;height:116px;border-radius:50%;border:3px solid #3c3731;background:radial-gradient(circle at center,#f8f4e9 0 29%,#d7d0c1 30% 47%,#f8f4e9 48% 60%,#bdb4a4 61% 63%,#eee8db 64%);color:#1d1915;font:800 11px/1.15 Consolas,monospace;cursor:pointer;box-shadow:0 0 0 5px #ece7da}.manugrid .mg-circle.active{border-color:#008fa0;box-shadow:0 0 0 5px #ece7da,0 0 0 7px #008fa0}.manugrid .mg-lower .mg-cellgrid{--cell:25px}.manugrid .mg-stats{font-family:Consolas,monospace;color:var(--cyan);font-size:.82rem;margin-top:8px}.manugrid .mg-note{border-left:4px solid var(--cyan);padding:11px 13px;background:#0e171b;border-radius:8px;margin:12px 0;color:#c6d2df}.manugrid .mg-path{display:flex;flex-direction:column;gap:7px;max-height:46vh;overflow:auto;margin-top:10px}.manugrid .mg-step{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid #30374c;border-radius:9px;background:#101621}.manugrid .mg-step b{color:var(--cyan)}.manugrid .mg-step small{display:block;color:var(--muted);overflow-wrap:anywhere}.manugrid .mg-remove{border:1px solid #5c3d45;background:#231419;color:#ffb1b1;border-radius:8px;padding:5px 8px;cursor:pointer}.manugrid .mg-queue{padding:9px;border:1px solid #30374c;border-radius:9px;background:#0d121a;color:var(--muted);font-size:.84rem;min-height:42px}.manugrid .mg-queue b{color:var(--cyan)}.manugrid .mg-chip{display:inline-block;border:1px solid #36556a;background:#0f161c;color:#5ce1e6;border-radius:999px;padding:4px 8px;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
 @media(max-width:900px){.manugrid .mg-shell{grid-template-columns:1fr}.manugrid .mg-workbench{max-height:70vh}}
 @media(max-width:520px){.manugrid .mg-workbench{padding:12px}.manugrid .mg-cellgrid{--cell:25px}.manugrid .mg-lower .mg-cellgrid{--cell:23px}.manugrid .mg-pair{grid-template-columns:max-content 18px max-content;gap:7px}}
 `;document.head.appendChild(st);
}
function upperId(layer,side,row,col){return `${layer}-${side}-R${row}-C${col}`;}
function lowerId(layer,row,col){return `${layer}-R${row}-C${col}`;}
function parseCellId(id){
 let m=/^(U\d+)-(L|R)-R(\d+)-C(\d+)$/.exec(id);if(m)return{zone:'upper',layer:m[1],side:m[2],row:+m[3],column:+m[4]};
 m=/^(D\d+)-R(\d+)-C(\d+)$/.exec(id);if(m)return{zone:'lower',layer:m[1],row:+m[2],column:+m[3]};
 return null;
}
function gridHTML(layer,side){
 const cells=[];for(let r=1;r<=layer.rows;r++)for(let c=1;c<=layer.columns;c++){const id=side?upperId(layer.id,side,r,c):lowerId(layer.id,r,c);cells.push(`<button type="button" class="mg-cell" data-cell="${id}" aria-label="${id}" title="${id}">${r}.${c}</button>`);}return `<div class="mg-cellgrid" style="--cols:${layer.columns}">${cells.join('')}</div>`;
}
function layerHTML(layer,upper){
 if(upper)return `<div class="mg-layer mg-upper" data-layer="${layer.id}"><div class="mg-layer-title">${layer.id} · ${layer.columns} across × ${layer.rows} down · each side</div><div class="mg-pair"><div><div class="mg-side-label">LEFT</div>${gridHTML(layer,'L')}</div><div class="mg-spine" aria-hidden="true"></div><div><div class="mg-side-label">RIGHT</div>${gridHTML(layer,'R')}</div></div></div>`;
 return `<div class="mg-layer mg-lower" data-layer="${layer.id}"><div class="mg-layer-title">${layer.id} · ${layer.columns} across × ${layer.rows} down</div>${gridHTML(layer,null)}</div>`;
}
async function init(){
 css();
 let spec;try{const r=await fetch(SPEC_URL,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);spec=await r.json();}catch(e){console.error('Man Grid structure failed to load',e);return;}
 const old=$('#manuscript-grid');if(old)old.remove();
 const section=document.createElement('section');section.className='section wrap manugrid';section.id='manuscript-grid';section.innerHTML=`
 <h2>The Man Grid — computerized working grid</h2>
 <p class="lead">This is the discrete Man Grid structure: exact addressable cells, stacked in the supplied order, with the transformative circle between the upper and lower sections.</p>
 <div class="mg-note"><b>Structure:</b> upper paired grids 4×4, 7×5, 10×5, 7×4, 5×5 on the left and right; transformative circle; lower grids 6×5, 11×5, 17×4, 21×5, 25×5. Every cell has a stable machine-readable address.</div>
 <div class="mg-shell">
  <div class="mg-panel"><span class="mg-chip">691 addressable cells + transform circle</span><div class="mg-workbench"><div id="mgModel" class="mg-model">${spec.upper.map(x=>layerHTML(x,true)).join('')}<div class="mg-circle-wrap"><button type="button" class="mg-circle" id="mgCircle">TRANSFORMATIVE<br>CIRCLE</button></div>${spec.lower.map(x=>layerHTML(x,false)).join('')}</div></div><div id="mgStats" class="mg-stats">0 path steps</div></div>
  <div class="mg-panel">
   <h3 style="margin-top:0">Run a meaning / phonetic path</h3>
   <div class="mg-toolbar"><div class="mg-field wide"><label for="mgMeaning">Meaning / test label</label><input id="mgMeaning" type="text" autocomplete="off" placeholder="e.g. water, fire, mother"></div><div class="mg-field"><label for="mgToken">Current token / phoneme</label><input id="mgToken" type="text" autocomplete="off" placeholder="e.g. /k/"></div></div>
   <div class="mg-field wide"><label for="mgSequence">Token sequence queue</label><textarea id="mgSequence" placeholder="Space-separated IPA/phoneme sequence, e.g. k a t"></textarea></div>
   <div class="mg-toolbar" style="margin-top:8px"><button class="btn" id="mgLoadSequence" type="button">Load sequence</button><button class="btn" id="mgMirrorLast" type="button">Mirror last upper cell</button><button class="btn" id="mgUndo" type="button">Undo</button><button class="btn" id="mgClear" type="button">Clear path</button><button class="btn" id="mgExport" type="button">Export JSON</button></div>
   <div id="mgQueue" class="mg-queue"></div>
   <div id="mgPath" class="mg-path"></div>
  </div>
 </div>
 <div class="mg-note"><b>How it works:</b> load a phoneme/token sequence, then tap cells in order. Each tap consumes the next queued token and records the exact layer, side, row and column. Tap the circle when the path reaches the transformation boundary. Upper mirror operations swap left↔right at the same row/column only. No other transformation rule is invented by the interface.</div>`;
 const mirror=$('#mirror-lab');if(mirror?.parentNode)mirror.parentNode.insertBefore(section,mirror);else(document.querySelector('main')||document.body).appendChild(section);
 const nav=$('.nav');if(nav){let a=nav.querySelector('a[href="#manuscript-grid"]');if(!a){a=document.createElement('a');a.href='#manuscript-grid';nav.appendChild(a);}a.textContent='Man Grid tool';}
 let path=loadJSON(PATH_KEY,[]);if(!Array.isArray(path))path=[];
 let queue=loadJSON(QUEUE_KEY,[]);if(!Array.isArray(queue))queue=[];
 const meaning=$('#mgMeaning'),token=$('#mgToken'),sequence=$('#mgSequence'),queueBox=$('#mgQueue'),pathBox=$('#mgPath'),stats=$('#mgStats'),model=$('#mgModel'),circle=$('#mgCircle');
 function currentLanguage(){return visibleSelectText($('#sourceLanguage'));}
 function fallbackToken(){const t=token.value.trim();if(t)return t;const s=$('#sourceSegment');return visibleSelectText(s);}
 function save(){saveJSON(PATH_KEY,path);saveJSON(QUEUE_KEY,queue);}
 function renderQueue(){queueBox.innerHTML=queue.length?`<b>${queue.length} queued:</b> ${queue.map(esc).join(' · ')}`:'No queued tokens. Type a sequence and press “Load sequence”, or use the current-token field.';}
 function renderPath(){
  pathBox.innerHTML=path.length?path.map((s,i)=>`<div class="mg-step"><div><b>${i+1}. ${s.type==='transform'?'CIRCLE':esc(s.token||'∅')}</b><small>${s.type==='transform'?'transformative circle':esc(s.cell)}${s.meaning?' · meaning: '+esc(s.meaning):''}${s.language?' · '+esc(s.language):''}${s.mirrored?' · mirrored':''}</small></div><button class="mg-remove" type="button" data-i="${i}">×</button></div>`).join(''):'<div class="small">No path yet. Tap cells to build one.</div>';
  pathBox.querySelectorAll('.mg-remove').forEach(b=>b.onclick=()=>{path.splice(+b.dataset.i,1);save();renderAll();});
 }
 function renderModel(){
  model.querySelectorAll('.mg-cell').forEach(b=>{b.classList.remove('active','mirrored');b.removeAttribute('data-step');});circle.classList.remove('active');
  path.forEach((s,i)=>{if(s.type==='transform'){circle.classList.add('active');return;}const b=model.querySelector(`[data-cell="${CSS.escape(s.cell)}"]`);if(b){b.classList.add('active');if(s.mirrored)b.classList.add('mirrored');b.dataset.step=String(i+1);}});
  stats.textContent=`${path.length} path steps · ${spec.counts.total_cells} cells · ${queue.length} tokens queued`;
 }
 function renderAll(){renderQueue();renderPath();renderModel();}
 function addCell(cell,forcedToken=null,mirrored=false){const p=parseCellId(cell);if(!p)return;const q=forcedToken!==null?forcedToken:(queue.length?queue.shift():fallbackToken());path.push({type:'cell',cell,token:q||'',meaning:meaning.value.trim(),language:currentLanguage(),mirrored:!!mirrored,created:new Date().toISOString(),...p});save();renderAll();}
 model.addEventListener('click',e=>{const b=e.target.closest('.mg-cell');if(!b)return;addCell(b.dataset.cell);});
 circle.onclick=()=>{path.push({type:'transform',cell:'CIRCLE',meaning:meaning.value.trim(),language:currentLanguage(),created:new Date().toISOString()});save();renderAll();};
 $('#mgLoadSequence').onclick=()=>{const raw=sequence.value.trim();queue=raw?raw.split(/\s+/).filter(Boolean):[];save();renderAll();};
 $('#mgMirrorLast').onclick=()=>{const src=[...path].reverse().find(s=>s.type==='cell'&&s.zone==='upper');if(!src)return;const mirrorSide=src.side==='L'?'R':'L';addCell(upperId(src.layer,mirrorSide,src.row,src.column),src.token,true);};
 $('#mgUndo').onclick=()=>{path.pop();save();renderAll();};
 $('#mgClear').onclick=()=>{if(!path.length||confirm('Clear the current Man Grid path?')){path=[];save();renderAll();}};
 $('#mgExport').onclick=()=>{const payload={version:1,tool:'Vardath computerized Man Grid',spec,meaning:meaning.value.trim(),queue_remaining:queue,path};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='vardath-man-grid-path.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
 const allCellIds=[];for(const l of spec.upper)for(const side of l.paired_sides)for(let r=1;r<=l.rows;r++)for(let c=1;c<=l.columns;c++)allCellIds.push(upperId(l.id,side,r,c));for(const l of spec.lower)for(let r=1;r<=l.rows;r++)for(let c=1;c<=l.columns;c++)allCellIds.push(lowerId(l.id,r,c));
 function mirrorCell(id){const p=parseCellId(id);return p?.zone==='upper'?upperId(p.layer,p.side==='L'?'R':'L',p.row,p.column):null;}
 const api={spec,upperId,lowerId,parseCellId,mirrorCell,allCellIds:()=>allCellIds.slice(),getPath:()=>path.slice()};window.VARDATH_MAN_GRID_SPEC=spec;window.VARDATH_MAN_GRID_API=api;document.dispatchEvent(new CustomEvent('vardath-man-grid-ready',{detail:{spec,api}}));
 renderAll();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
