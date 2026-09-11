// Interactive source-traced manuscript grid for the phonetic bridge page.
// Line coordinates are traced directly from the supplied reference image; hidden areas are not interpolated.
(function(){
'use strict';
if(window.__VARDATH_HISTORICAL_PHONETIC_GRID__)return;
window.__VARDATH_HISTORICAL_PHONETIC_GRID__=true;
const W=716,H=910;
let SEGMENTS=[];
const KEY='vardath.phoneticHistoricalGrid.markers.v1';
const $=s=>document.querySelector(s);
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function styles(){
 if($('#historicalGridStyles'))return;
 const st=document.createElement('style');st.id='historicalGridStyles';st.textContent=`
 #historical-grid .hg-shell{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(250px,.5fr);gap:16px;align-items:start}
 #historical-grid .hg-panel{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:15px;padding:16px}
 #historical-grid .hg-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end;margin-bottom:12px}
 #historical-grid .hg-field{flex:1 1 220px}#historical-grid .hg-field label{display:block;color:var(--muted);font-size:.8rem;margin-bottom:4px}
 #historical-grid input{width:100%;background:#0c1018;color:white;border:1px solid #3d455d;border-radius:9px;padding:10px}
 #historical-grid .hg-viewport{overflow:auto;max-height:76vh;border:1px solid #404861;border-radius:12px;background:#222;touch-action:pan-x pan-y}
 #historical-grid .hg-canvaswrap{position:relative;margin:auto;line-height:0;transform-origin:0 0}
 #historical-grid canvas{display:block;width:100%;height:auto;background:#f6f1e5;cursor:crosshair}
 #historical-grid .hg-readout{font-family:Consolas,monospace;color:var(--cyan);font-size:.82rem;margin:8px 0 0}
 #historical-grid .hg-list{display:flex;flex-direction:column;gap:7px;max-height:52vh;overflow:auto;margin-top:10px}
 #historical-grid .hg-item{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid #30374c;border-radius:9px;background:#101621}
 #historical-grid .hg-item b{color:var(--cyan)}#historical-grid .hg-item small{display:block;color:var(--muted)}
 #historical-grid .hg-remove{border:1px solid #5c3d45;background:#231419;color:#ffb1b1;border-radius:8px;padding:5px 8px;cursor:pointer}
 #historical-grid .hg-source-note{border-left:4px solid var(--cyan);padding:11px 13px;background:#0e171b;border-radius:8px;margin:12px 0;color:#c6d2df}
 @media(max-width:850px){#historical-grid .hg-shell{grid-template-columns:1fr}#historical-grid .hg-viewport{max-height:68vh}}
 `;document.head.appendChild(st);
}
function loadMarkers(){try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v:[];}catch{return [];}}
function saveMarkers(m){try{localStorage.setItem(KEY,JSON.stringify(m));}catch{}}
async function init(){
 const anchor=$('#grid');if(!anchor||$('#historical-grid'))return;
 styles();
 const nav=$('.nav');if(nav&&!nav.querySelector('a[href="#historical-grid"]')){const a=document.createElement('a');a.href='#historical-grid';a.textContent='Source grid tool';const gridLink=nav.querySelector('a[href="#grid"]');gridLink?gridLink.insertAdjacentElement('afterend',a):nav.appendChild(a);}
 try{const r=await fetch('phonetic-historical-grid-data.json?v=20260911-grid1',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);SEGMENTS=await r.json();if(!Array.isArray(SEGMENTS))throw new Error('invalid trace data');}catch(err){console.error('Historical grid trace failed to load',err);}
 const section=document.createElement('section');section.id='historical-grid';section.className='section wrap';section.innerHTML=`
 <h2>2b. Source grid workbench</h2>
 <p class="lead">The visible linework from the supplied manuscript grid is traced at its original 716×910 coordinate scale. Use this as a working phonetic mapping surface: click the grid to place labelled points, zoom for inspection, and export your placements.</p>
 <div class="hg-source-note"><b>Trace boundary:</b> only grid strokes visible in the supplied image are drawn. Areas hidden by hands, clothing, the circular object or writing are left unreconstructed rather than guessed.</div>
 <div class="hg-shell">
  <div class="hg-panel">
   <div class="hg-toolbar"><div class="hg-field"><label for="hgLabel">Marker / phoneme label</label><input id="hgLabel" autocomplete="off" placeholder="e.g. /k/, Sanskrit क, Gate 137"></div><button class="btn" id="hgZoomOut" type="button">−</button><button class="btn" id="hgZoomIn" type="button">+</button><button class="btn" id="hgResetZoom" type="button">100%</button></div>
   <div class="hg-viewport" id="hgViewport"><div class="hg-canvaswrap" id="hgCanvasWrap"><canvas id="hgCanvas" width="${W}" height="${H}" aria-label="Interactive traced phonetic manuscript grid"></canvas></div></div>
   <div class="hg-readout" id="hgReadout">x — / y — · click the grid to place a marker</div>
  </div>
  <div class="hg-panel"><h3 style="margin-top:0">Mapped points</h3><p class="small">If the label field is blank, the current source phoneme from the language tester is used when available. Points are saved locally in this browser.</p><div class="hg-toolbar"><button class="btn" id="hgUndo" type="button">Undo last</button><button class="btn" id="hgClear" type="button">Clear</button><button class="btn" id="hgExport" type="button">Export JSON</button></div><div id="hgList" class="hg-list"></div></div>
 </div>`;
 anchor.insertAdjacentElement('afterend',section);
 const canvas=$('#hgCanvas'),ctx=canvas.getContext('2d'),wrap=$('#hgCanvasWrap'),viewport=$('#hgViewport'),label=$('#hgLabel'),readout=$('#hgReadout'),list=$('#hgList');
 let markers=loadMarkers(),zoom=1;
 function drawGrid(){ctx.clearRect(0,0,W,H);ctx.fillStyle='#f6f1e5';ctx.fillRect(0,0,W,H);ctx.strokeStyle='#17130f';ctx.lineWidth=1.25;ctx.lineCap='square';ctx.beginPath();for(const s of SEGMENTS){ctx.moveTo(s[0],s[1]);ctx.lineTo(s[2],s[3]);}ctx.stroke();}
 function drawMarkers(){for(let i=0;i<markers.length;i++){const m=markers[i];ctx.save();ctx.fillStyle='rgba(7,15,20,.86)';ctx.strokeStyle='#5ce1e6';ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(m.x,m.y,7,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.font='bold 14px Arial';ctx.textBaseline='middle';const txt=m.label||`P${i+1}`,tw=ctx.measureText(txt).width;let tx=m.x+10;if(tx+tw+10>W)tx=m.x-tw-14;let ty=m.y;if(ty<12)ty=12;if(ty>H-12)ty=H-12;ctx.fillStyle='rgba(9,10,15,.88)';ctx.fillRect(tx-4,ty-10,tw+8,20);ctx.fillStyle='#5ce1e6';ctx.fillText(txt,tx,ty);ctx.restore();}}
 function redraw(){drawGrid();drawMarkers();}
 function renderList(){if(!markers.length){list.innerHTML='<div class="small">No mapped points yet.</div>';return;}list.innerHTML=markers.map((m,i)=>`<div class="hg-item"><div><b>${esc(m.label||('P'+(i+1)))}</b><small>x ${m.x.toFixed(1)} · y ${m.y.toFixed(1)}${m.language?' · '+esc(m.language):''}</small></div><button type="button" class="hg-remove" data-i="${i}">×</button></div>`).join('');list.querySelectorAll('.hg-remove').forEach(b=>b.onclick=()=>{markers.splice(+b.dataset.i,1);saveMarkers(markers);redraw();renderList();});}
 function fit(){const base=Math.min(W,Math.max(280,viewport.clientWidth-4));wrap.style.width=(base*zoom)+'px';$('#hgResetZoom').textContent=Math.round(zoom*100)+'%';}
 function setZoom(z){zoom=Math.min(4,Math.max(.5,z));fit();}
 function currentContext(){const seg=$('#sourceSegment'),lang=$('#sourceLanguage');return{label:(label.value.trim()||(seg&&seg.value)||''),language:(lang&&lang.options&&lang.selectedIndex>=0?lang.options[lang.selectedIndex].text:'')};}
 canvas.addEventListener('pointermove',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H;readout.textContent=`x ${x.toFixed(1)} / y ${y.toFixed(1)} · ${(x/W*100).toFixed(1)}% × ${(y/H*100).toFixed(1)}%`;});
 canvas.addEventListener('pointerleave',()=>readout.textContent='x — / y — · click the grid to place a marker');
 canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H,c=currentContext();markers.push({x:+x.toFixed(2),y:+y.toFixed(2),label:c.label||`P${markers.length+1}`,language:c.language,created:new Date().toISOString()});saveMarkers(markers);redraw();renderList();});
 $('#hgZoomOut').onclick=()=>setZoom(zoom/1.25);$('#hgZoomIn').onclick=()=>setZoom(zoom*1.25);$('#hgResetZoom').onclick=()=>setZoom(1);
 $('#hgUndo').onclick=()=>{markers.pop();saveMarkers(markers);redraw();renderList();};
 $('#hgClear').onclick=()=>{if(!markers.length||confirm('Clear all mapped points from this grid?')){markers=[];saveMarkers(markers);redraw();renderList();}};
 $('#hgExport').onclick=()=>{const payload={version:1,grid:{width:W,height:H,source:'source-traced supplied manuscript image'},markers},blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='phonetic-grid-markers.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
 addEventListener('resize',fit,{passive:true});drawGrid();drawMarkers();renderList();fit();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
