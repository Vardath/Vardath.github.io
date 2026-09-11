(()=>{
'use strict';
if(window.__VARDATH_MANUSCRIPT_GRID_TOOL__)return;
window.__VARDATH_MANUSCRIPT_GRID_TOOL__=true;
const W=716,H=910,DATA_URL='phonetic-historical-grid-data.json?v=20260911-realgrid2';
const KEY='vardath.manuscriptGrid.markers.v2',AXIS_KEY='vardath.manuscriptGrid.axis.v1';
const $=s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let SEGMENTS=[];
function css(){
 if($('#manuscriptGridToolStyles'))return;
 const st=document.createElement('style');st.id='manuscriptGridToolStyles';st.textContent=`
 .manugrid{margin-top:30px}.manugrid .mg-tool{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(280px,.65fr);gap:16px;align-items:start;margin:18px 0}.manugrid .mg-panel{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:15px;padding:16px}.manugrid .mg-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end;margin-bottom:12px}.manugrid .mg-field{flex:1 1 220px}.manugrid .mg-field.smallfield{flex:0 1 140px}.manugrid .mg-field label{display:block;color:var(--muted);font-size:.8rem;margin-bottom:4px}.manugrid input[type="text"],.manugrid input[type="number"]{width:100%;background:#0c1018;color:white;border:1px solid #3d455d;border-radius:9px;padding:10px}.manugrid .mg-viewport{overflow:auto;max-height:76vh;border:1px solid #404861;border-radius:12px;background:#222;touch-action:pan-x pan-y}.manugrid .mg-canvaswrap{position:relative;margin:auto;line-height:0}.manugrid canvas{display:block;width:100%;height:auto;background:#f6f1e5;cursor:crosshair}.manugrid .mg-readout{font-family:Consolas,monospace;color:var(--cyan);font-size:.82rem;margin-top:8px}.manugrid .mg-list{display:flex;flex-direction:column;gap:7px;max-height:48vh;overflow:auto;margin-top:10px}.manugrid .mg-item{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid #30374c;border-radius:9px;background:#101621}.manugrid .mg-item b{color:var(--cyan)}.manugrid .mg-item small{display:block;color:var(--muted)}.manugrid .mg-remove{border:1px solid #5c3d45;background:#231419;color:#ffb1b1;border-radius:8px;padding:5px 8px;cursor:pointer}.manugrid .mg-note{border-left:4px solid var(--cyan);padding:11px 13px;background:#0e171b;border-radius:8px;margin:12px 0;color:#c6d2df}.manugrid .mg-warning{border-left-color:var(--warn);background:#17131a}.manugrid .mg-axisrow{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.manugrid .mg-status{font-size:.82rem;color:var(--muted);margin-top:8px}.manugrid .mg-chip{display:inline-block;border:1px solid #36556a;background:#0f161c;color:#5ce1e6;border-radius:999px;padding:4px 8px;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
 @media(max-width:850px){.manugrid .mg-tool{grid-template-columns:1fr}.manugrid .mg-viewport{max-height:68vh}}
 `;document.head.appendChild(st);
}
function loadMarkers(){try{const v=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(v)?v:[];}catch{return [];}}
function saveMarkers(v){try{localStorage.setItem(KEY,JSON.stringify(v));}catch{}}
function loadAxis(){const v=+localStorage.getItem(AXIS_KEY);return Number.isFinite(v)&&v>=0&&v<=W?v:W/2;}
function saveAxis(v){try{localStorage.setItem(AXIS_KEY,String(v));}catch{}}
async function init(){
 css();
 try{const r=await fetch(DATA_URL,{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);SEGMENTS=await r.json();if(!Array.isArray(SEGMENTS))throw new Error('invalid trace');}catch(e){console.error('Man Grid trace load failed',e);SEGMENTS=[];}
 const section=document.createElement('section');section.className='section wrap manugrid';section.id='manuscript-grid';section.innerHTML=`
 <h2>The Man Grid — source-traced working surface</h2>
 <p class="lead">This is the actual visible grid linework transcribed from the supplied manuscript image and turned into an interactive phonetic mapping surface. It is no longer a schematic substitute.</p>
 <div class="mg-note"><b>Trace boundary:</b> only strokes visible in the supplied image are drawn. Areas hidden by the hands, circular object, clothing or writing are left blank rather than invented.</div>
 <div class="mg-tool">
  <div class="mg-panel">
   <span class="mg-chip">interactive grid</span>
   <div class="mg-toolbar"><div class="mg-field"><label for="mgLabel">Marker / phoneme label</label><input id="mgLabel" type="text" autocomplete="off" placeholder="e.g. /k/, क, Gate 137"></div><button class="btn" id="mgZoomOut" type="button">−</button><button class="btn" id="mgZoomIn" type="button">+</button><button class="btn" id="mgZoomReset" type="button">100%</button></div>
   <div class="mg-viewport" id="mgViewport"><div class="mg-canvaswrap" id="mgCanvasWrap"><canvas id="mgCanvas" width="${W}" height="${H}" aria-label="Interactive source-traced manuscript phonetic grid"></canvas></div></div>
   <div class="mg-readout" id="mgReadout">x — / y — · click the grid to place a point</div>
   <div class="mg-status" id="mgTraceStatus">${SEGMENTS.length?SEGMENTS.length+' traced line segments loaded':'Trace data did not load'}</div>
  </div>
  <div class="mg-panel">
   <h3 style="margin-top:0">Mapping controls</h3>
   <p class="small">Leave the label blank to use the currently selected source phoneme from the language tester. Points persist locally in this browser.</p>
   <div class="mg-axisrow"><div class="mg-field smallfield"><label for="mgAxis">Fold / mirror axis x</label><input id="mgAxis" type="number" min="0" max="716" step="0.5"></div><button class="btn" id="mgMirrorLast" type="button">Mirror last point</button></div>
   <p class="small">The default axis is the image midpoint (x = 358). Change it if the manuscript fold is calibrated differently; mirror operations use exactly the value shown here.</p>
   <div class="mg-toolbar"><button class="btn" id="mgUndo" type="button">Undo last</button><button class="btn" id="mgClear" type="button">Clear</button><button class="btn" id="mgExport" type="button">Export JSON</button></div>
   <div id="mgList" class="mg-list"></div>
  </div>
 </div>
 <div class="mg-note mg-warning"><b>Research boundary:</b> the geometry is source-derived; the linguistic meaning of any coordinate, layer or fold remains experimental until the manuscript labels and original historical purpose are independently identified. Earlier 4×4/16-state “Mirror-Man” results are not results from this traced grid.</div>`;
 const old=$('#manuscript-grid');if(old)old.remove();
 const mirror=$('#mirror-lab');if(mirror?.parentNode)mirror.parentNode.insertBefore(section,mirror);else(document.querySelector('main')||document.body).appendChild(section);
 const nav=$('.nav');if(nav){let a=nav.querySelector('a[href="#manuscript-grid"]');if(!a){a=document.createElement('a');a.href='#manuscript-grid';nav.appendChild(a)}a.textContent='Man Grid tool';}
 const canvas=$('#mgCanvas'),ctx=canvas.getContext('2d'),viewport=$('#mgViewport'),wrap=$('#mgCanvasWrap'),label=$('#mgLabel'),readout=$('#mgReadout'),axisInput=$('#mgAxis'),list=$('#mgList');
 let markers=loadMarkers(),axis=loadAxis(),zoom=1;axisInput.value=axis.toFixed(1);
 function drawBase(){ctx.clearRect(0,0,W,H);ctx.fillStyle='#f6f1e5';ctx.fillRect(0,0,W,H);ctx.strokeStyle='#17130f';ctx.lineWidth=1.25;ctx.lineCap='square';ctx.beginPath();for(const s of SEGMENTS){ctx.moveTo(s[0],s[1]);ctx.lineTo(s[2],s[3]);}ctx.stroke();ctx.save();ctx.setLineDash([7,6]);ctx.strokeStyle='rgba(0,130,150,.75)';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(axis,0);ctx.lineTo(axis,H);ctx.stroke();ctx.restore();}
 function drawMarkers(){markers.forEach((m,i)=>{ctx.save();const mirror=m.kind==='mirror';ctx.fillStyle=mirror?'rgba(75,42,92,.9)':'rgba(7,15,20,.88)';ctx.strokeStyle=mirror?'#c69cff':'#5ce1e6';ctx.lineWidth=2.5;ctx.beginPath();ctx.arc(m.x,m.y,7,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.font='bold 14px Arial';ctx.textBaseline='middle';const txt=m.label||`P${i+1}`,tw=ctx.measureText(txt).width;let tx=m.x+10;if(tx+tw+10>W)tx=m.x-tw-14;let ty=Math.max(12,Math.min(H-12,m.y));ctx.fillStyle='rgba(9,10,15,.88)';ctx.fillRect(tx-4,ty-10,tw+8,20);ctx.fillStyle=mirror?'#c69cff':'#5ce1e6';ctx.fillText(txt,tx,ty);ctx.restore();});}
 function redraw(){drawBase();drawMarkers();}
 function contextLabel(){const seg=$('#sourceSegment'),lang=$('#sourceLanguage');return{label:label.value.trim()||(seg&&seg.value)||'',language:lang&&lang.selectedIndex>=0?lang.options[lang.selectedIndex]?.text||'':''};}
 function renderList(){if(!markers.length){list.innerHTML='<div class="small">No mapped points yet.</div>';return;}list.innerHTML=markers.map((m,i)=>`<div class="mg-item"><div><b>${esc(m.label||('P'+(i+1)))}${m.kind==='mirror'?' ↔':''}</b><small>x ${m.x.toFixed(1)} · y ${m.y.toFixed(1)}${m.language?' · '+esc(m.language):''}</small></div><button class="mg-remove" type="button" data-i="${i}">×</button></div>`).join('');list.querySelectorAll('.mg-remove').forEach(b=>b.onclick=()=>{markers.splice(+b.dataset.i,1);saveMarkers(markers);redraw();renderList();});}
 function fit(){const base=Math.min(W,Math.max(280,viewport.clientWidth-4));wrap.style.width=(base*zoom)+'px';$('#mgZoomReset').textContent=Math.round(zoom*100)+'%';}
 function setZoom(v){zoom=Math.max(.5,Math.min(4,v));fit();}
 canvas.addEventListener('pointermove',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H;readout.textContent=`x ${x.toFixed(1)} / y ${y.toFixed(1)} · mirror x ${(2*axis-x).toFixed(1)}`;});
 canvas.addEventListener('pointerleave',()=>readout.textContent='x — / y — · click the grid to place a point');
 canvas.addEventListener('click',e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H,c=contextLabel();markers.push({x:+x.toFixed(2),y:+y.toFixed(2),label:c.label||`P${markers.length+1}`,language:c.language,kind:'source',created:new Date().toISOString()});saveMarkers(markers);redraw();renderList();});
 axisInput.addEventListener('change',()=>{const v=Math.max(0,Math.min(W,+axisInput.value||W/2));axis=v;axisInput.value=v.toFixed(1);saveAxis(axis);redraw();});
 $('#mgMirrorLast').onclick=()=>{const src=[...markers].reverse().find(m=>m.kind!=='mirror');if(!src)return;const mx=2*axis-src.x;if(mx<0||mx>W){alert('The mirrored point falls outside the traced image width at this axis.');return;}markers.push({...src,x:+mx.toFixed(2),kind:'mirror',label:(src.label||'')+' ↔',created:new Date().toISOString()});saveMarkers(markers);redraw();renderList();};
 $('#mgZoomOut').onclick=()=>setZoom(zoom/1.25);$('#mgZoomIn').onclick=()=>setZoom(zoom*1.25);$('#mgZoomReset').onclick=()=>setZoom(1);
 $('#mgUndo').onclick=()=>{markers.pop();saveMarkers(markers);redraw();renderList();};
 $('#mgClear').onclick=()=>{if(!markers.length||confirm('Clear all mapped Man Grid points?')){markers=[];saveMarkers(markers);redraw();renderList();}};
 $('#mgExport').onclick=()=>{const payload={version:2,grid:{width:W,height:H,traceSegments:SEGMENTS.length,axis},markers},blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='man-grid-phonetic-mapping.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
 addEventListener('resize',fit,{passive:true});redraw();renderList();fit();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
