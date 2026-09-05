// Friendly relationship and world-map presentation for the phonetic bridge.
// Additive only: keeps the existing research atlas intact and clearly separates
// bridge-derived similarity from external Glottolog genealogy/geography.
(function(){
  const $=id=>document.getElementById(id);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct=x=>Number.isFinite(+x)?(100*+x).toFixed(1)+'%':'—';
  const state={langs:[],pairs:[],byIso:new Map(),pairMap:new Map(),glot:new Map(),families:new Map(),map:null,markers:new Map(),lines:[],layer:'bridge',loaded:false,glotLoaded:false};
  const pairKey=(a,b)=>a<b?a+'|'+b:b+'|'+a;
  const getPair=(a,b)=>state.pairMap.get(pairKey(a,b));

  function csv(text){
    const rows=[];let row=[],field='',q=false;
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(q){if(c==='"'){if(text[i+1]==='"'){field+='"';i++;}else q=false;}else field+=c;continue;}
      if(c==='"'){q=true;continue;} if(c===','){row.push(field);field='';continue;} if(c==='\n'){row.push(field);rows.push(row);row=[];field='';continue;} if(c!=='\r')field+=c;
    }
    if(field.length||row.length){row.push(field);rows.push(row);} const h=rows.shift()||[];
    return rows.filter(r=>r.some(x=>x!=='')).map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]??''])));
  }
  async function text(url){const r=await fetch(url,{cache:'force-cache'});if(!r.ok)throw new Error(r.status+' '+url);return r.text();}

  function css(){if($('friendlyMapsStyle'))return;const s=document.createElement('style');s.id='friendlyMapsStyle';s.textContent=`
    .fm-start{border:1px solid #385064;background:linear-gradient(180deg,#111b25,#0d131c);border-radius:18px;padding:22px;margin-top:20px}.fm-picker{display:grid;grid-template-columns:1fr auto 1fr;gap:12px;align-items:end}.fm-picker select{width:100%;background:#0c1018;color:#fff;border:1px solid #3d455d;border-radius:9px;padding:11px}.fm-swap{height:42px}.fm-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}.fm-card{border:1px solid #30384d;border-radius:13px;padding:14px;background:#10151f}.fm-card b{display:block;color:#5ce1e6;font-size:1.25rem}.fm-lists{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.fm-list{border:1px solid #30384d;border-radius:13px;padding:14px;background:#10151f}.fm-row{display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #252d3d}.fm-row:last-child{border-bottom:0}.fm-tag{display:inline-block;border:1px solid #39455f;border-radius:999px;padding:3px 7px;font-size:.72rem;margin:2px;background:#121824}.fm-external{border-left:4px solid #80e7a8;background:#0f1815;padding:13px 15px;border-radius:9px;margin:14px 0}.fm-world{height:620px;border:1px solid #30384d;border-radius:15px;overflow:hidden;background:#0b1018}.fm-mapbar{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}.fm-mapbuttons{display:flex;gap:7px;flex-wrap:wrap}.fm-mapbuttons button.active{border-color:#5ce1e6;box-shadow:0 0 0 1px rgba(92,225,230,.25) inset}.fm-legend{font-size:.82rem;color:#aab1c5}.fm-source{font-size:.78rem;color:#8f98ad;margin-top:9px}.fm-familycanvas{width:100%;height:420px;display:block;border:1px solid #30384d;border-radius:14px;background:#0b1018}.leaflet-container{background:#0b1018}.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#121824;color:#eef1f8}.leaflet-control-attribution{font-size:10px}.fm-warning{padding:12px;border:1px solid #704040;background:#1d1113;border-radius:9px}@media(max-width:800px){.fm-picker{grid-template-columns:1fr}.fm-swap{width:100%}.fm-summary,.fm-lists{grid-template-columns:1fr}.fm-world{height:520px}}
  `;document.head.appendChild(s);}

  function install(){
    if($('friendlyRelationships'))return;css();
    const sec=document.createElement('section');sec.className='section wrap';sec.id='friendlyRelationships';sec.innerHTML=`
      <h2>Start here: compare languages visually</h2>
      <p class="lead">The research maps below are powerful but dense. This view answers the simpler question first: <b>how closely do two languages behave in the bridge, and does that agree with accepted linguistic relationships?</b></p>
      <div class="fm-start">
        <div class="fm-picker"><div class="control"><label>Language A</label><select id="fmA"></select></div><button id="fmSwap" class="btn fm-swap" type="button">⇄ Swap</button><div class="control"><label>Language B</label><select id="fmB"></select></div></div>
        <div id="fmPairSummary" class="fm-summary"></div>
        <div class="fm-external"><b>Two completely different tests are shown side by side.</b> “Bridge similarity” comes from our 4×4 gate experiment. “Outside relationship” comes from Glottolog’s genealogical classification and coordinates and does <b>not</b> use the bridge, magic square, gates or powers-of-three system.</div>
        <div class="fm-lists"><div class="fm-list"><h3>Closest by our bridge</h3><p class="small">Languages whose measured stable gate patterns most resemble the selected language.</p><div id="fmBridgeList"></div></div><div class="fm-list"><h3>Related in outside linguistics</h3><p class="small">Languages in this benchmark that Glottolog places in the same genealogical family.</p><div id="fmExternalList">Loading Glottolog…</div></div></div>
      </div>
    `;
    const atlas=$('languageAtlas'),anchor=atlas||$('magic')||$('status');if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(sec,anchor);else document.querySelector('main')?.appendChild(sec);

    const ext=document.createElement('section');ext.className='section wrap';ext.id='externalRelationships';ext.innerHTML=`
      <h2>Independent relationship map</h2>
      <p class="lead">This is the control view: accepted genealogical relationships from <b>Glottolog</b>, drawn without using any result from our phonetic bridge. If our experimental map is meaningful, we can compare the two rather than quietly building known families into the answer.</p>
      <canvas id="fmFamilyCanvas" class="fm-familycanvas"></canvas>
      <div id="fmFamilyText" class="detail" style="margin-top:12px">Loading independent language-family data…</div>
      <div class="fm-source">External source: Glottolog CLDF language catalogue (family classification, macroarea and coordinates). This section is intentionally independent of the Vardath bridge calculation.</div>
    `;if(atlas&&atlas.parentNode)atlas.parentNode.insertBefore(ext,atlas.nextSibling);else document.querySelector('main')?.appendChild(ext);

    const world=document.createElement('section');world.className='section wrap';world.id='worldLanguageMap';world.innerHTML=`
      <h2>Languages on the world map</h2>
      <p class="lead">Put the same comparison back onto geography. Select a language above, then switch between <b>bridge neighbours</b> and <b>Glottolog family</b> to see whether similarity follows descent, geography, both, or neither.</p>
      <div class="fm-mapbar"><div class="fm-mapbuttons"><button class="btn active" data-fm-layer="bridge" type="button">Bridge neighbours</button><button class="btn" data-fm-layer="family" type="button">Glottolog family</button><button class="btn" data-fm-layer="all" type="button">All benchmark languages</button></div><div class="fm-legend">Selected language = large marker · lines show the chosen relationship layer</div></div>
      <div id="fmWorld" class="fm-world"></div><div id="fmMapFallback"></div>
      <div class="fm-source">Positions and family membership: Glottolog. Basemap: OpenStreetMap when available. Bridge-neighbour lines are experimental; family lines are external controls.</div>
    `;if(ext&&ext.parentNode)ext.parentNode.insertBefore(world,ext.nextSibling);else document.querySelector('main')?.appendChild(world);

    const nav=document.querySelector('.nav');if(nav){[['friendlyRelationships','Simple view'],['externalRelationships','Outside map'],['worldLanguageMap','World map']].forEach(([id,label])=>{if(!nav.querySelector('a[href="#'+id+'"]')){const a=document.createElement('a');a.href='#'+id;a.textContent=label;nav.appendChild(a);}});}

    $('fmSwap').onclick=()=>{const a=$('fmA').value;$('fmA').value=$('fmB').value;$('fmB').value=a;render();};
    $('fmA').onchange=render;$('fmB').onchange=render;
    document.querySelectorAll('[data-fm-layer]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-fm-layer]').forEach(x=>x.classList.remove('active'));b.classList.add('active');state.layer=b.dataset.fmLayer;drawWorld();});
    load();
  }

  async function load(){
    try{
      const [lt,pt]=await Promise.all([text('data/phonetic-benchmark-languages.csv?v=friendly1'),text('data/phonetic-benchmark-pairs.csv?v=friendly1')]);
      state.langs=csv(lt).filter(r=>String(r.canonical).toLowerCase()==='true').map(r=>({iso:r.iso,name:r.name||r.iso,family:r.family||'Unclassified',macroarea:r.macroarea||''}));
      state.byIso=new Map(state.langs.map(x=>[x.iso,x]));state.pairs=csv(pt).map(p=>({...p,jaccard:+p.jaccard,cosine:+p.cosine,jsd_bits:+p.jsd_bits}));state.pairMap=new Map(state.pairs.map(p=>[pairKey(p.iso_a,p.iso_b),p]));
      const opts=state.langs.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(l=>`<option value="${esc(l.iso)}">${esc(l.name)} · ${esc(l.iso)}</option>`).join('');$('fmA').innerHTML=opts;$('fmB').innerHTML=opts;
      const eng=state.langs.find(x=>x.iso==='eng'),deu=state.langs.find(x=>x.iso==='deu')||state.langs.find(x=>x.name.toLowerCase().includes('german'));if(eng)$('fmA').value=eng.iso;if(deu)$('fmB').value=deu.iso;else if(state.langs[1])$('fmB').value=state.langs[1].iso;
      state.loaded=true;render();loadGlottolog();
    }catch(e){$('fmPairSummary').innerHTML=`<div class="fm-warning">Could not load benchmark data: ${esc(e.message)}</div>`;}
  }

  async function loadGlottolog(){
    try{
      const url='https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv';const rows=csv(await text(url));
      const idName=new Map(rows.map(r=>[r.ID,r.Name]));
      for(const r of rows){if(r.Level==='family')state.families.set(r.ID,r.Name);if(r.ISO639P3code&&state.byIso.has(r.ISO639P3code))state.glot.set(r.ISO639P3code,{id:r.ID,name:r.Name,lat:+r.Latitude,lon:+r.Longitude,familyId:r.Family_ID||'',familyName:idName.get(r.Family_ID)||'',macroarea:r.Macroarea||'',countries:r.Countries||'',isolate:String(r.Is_Isolate).toLowerCase()==='true'});}
      state.glotLoaded=true;render();loadLeaflet();
    }catch(e){$('fmExternalList').innerHTML=`<div class="fm-warning">Glottolog could not be loaded: ${esc(e.message)}</div>`;$('fmFamilyText').innerHTML=`<div class="fm-warning">Independent map unavailable: ${esc(e.message)}</div>`;}
  }

  function neighbours(iso){const out=[];for(const l of state.langs){if(l.iso===iso)continue;const p=getPair(iso,l.iso);if(p)out.push({l,p,score:p.jaccard});}return out.sort((a,b)=>b.score-a.score);}
  function sameFamily(iso){const g=state.glot.get(iso);if(!g||!g.familyId)return[];return state.langs.filter(l=>l.iso!==iso&&state.glot.get(l.iso)?.familyId===g.familyId).sort((a,b)=>a.name.localeCompare(b.name));}
  function distanceKm(a,b){const A=state.glot.get(a),B=state.glot.get(b);if(!A||!B||!Number.isFinite(A.lat)||!Number.isFinite(B.lat))return null;const R=6371,toR=x=>x*Math.PI/180,dlat=toR(B.lat-A.lat),dlon=toR(B.lon-A.lon),q=Math.sin(dlat/2)**2+Math.cos(toR(A.lat))*Math.cos(toR(B.lat))*Math.sin(dlon/2)**2;return 2*R*Math.asin(Math.sqrt(q));}

  function render(){if(!state.loaded)return;const a=$('fmA').value,b=$('fmB').value,A=state.byIso.get(a),B=state.byIso.get(b),p=getPair(a,b),gA=state.glot.get(a),gB=state.glot.get(b);const same=!!(gA&&gB&&gA.familyId&&gA.familyId===gB.familyId);const d=distanceKm(a,b);
    $('fmPairSummary').innerHTML=`<div class="fm-card"><span class="small">Bridge similarity</span><b>${p?pct(p.jaccard):'—'}</b><span class="small">shared stable-gate pattern</span></div><div class="fm-card"><span class="small">Outside relationship</span><b>${!state.glotLoaded?'loading…':same?'Same family':'Different families'}</b><span class="small">${gA&&gB?esc((gA.familyName||'unclassified')+(same?'':' / '+(gB.familyName||'unclassified'))):'Glottolog control'}</span></div><div class="fm-card"><span class="small">Geographic separation</span><b>${d==null?'—':Math.round(d).toLocaleString()+' km'}</b><span class="small">Glottolog reference coordinates</span></div>`;
    $('fmBridgeList').innerHTML=neighbours(a).slice(0,8).map((x,i)=>`<div class="fm-row"><span>${i+1}. <b>${esc(x.l.name)}</b> <span class="fm-tag">${esc(x.l.iso)}</span></span><span>${pct(x.score)}</span></div>`).join('');
    if(state.glotLoaded){const fam=sameFamily(a);$('fmExternalList').innerHTML=fam.length?fam.slice(0,20).map(l=>`<div class="fm-row"><span><b>${esc(l.name)}</b> <span class="fm-tag">${esc(l.iso)}</span></span><span>${esc(state.glot.get(l.iso)?.macroarea||'')}</span></div>`).join(''):`<p class="small">No other canonical benchmark language shares ${esc(gA?.familyName||'this Glottolog family')}. This may be an isolate, unclassified entry, or simply absent from the WikiPron benchmark.</p>`;drawFamily();drawWorld();}
  }

  function drawFamily(){const c=$('fmFamilyCanvas');if(!c||!state.glotLoaded)return;const dpr=devicePixelRatio||1,w=c.clientWidth||900,h=c.clientHeight||420;c.width=w*dpr;c.height=h*dpr;const x=c.getContext('2d');x.scale(dpr,dpr);x.clearRect(0,0,w,h);x.fillStyle='#0b1018';x.fillRect(0,0,w,h);const iso=$('fmA').value,L=state.byIso.get(iso),g=state.glot.get(iso),fam=sameFamily(iso).slice(0,18);x.textAlign='center';x.textBaseline='middle';x.font='600 17px Arial';x.fillStyle='#eef1f8';x.fillText(g?.familyName||'No Glottolog family classification',w/2,34);const cx=w/2,cy=h/2,r=Math.min(w,h)*.34;fam.forEach((l,i)=>{const a=Math.PI*2*i/Math.max(1,fam.length)-Math.PI/2,nx=cx+Math.cos(a)*r,ny=cy+Math.sin(a)*r;x.strokeStyle='rgba(128,231,168,.35)';x.lineWidth=1.5;x.beginPath();x.moveTo(cx,cy);x.lineTo(nx,ny);x.stroke();x.fillStyle='#182231';x.strokeStyle='#80e7a8';x.lineWidth=1.5;x.beginPath();x.arc(nx,ny,22,0,Math.PI*2);x.fill();x.stroke();x.fillStyle='#eef1f8';x.font='12px Arial';x.fillText(l.iso.toUpperCase(),nx,ny);x.fillStyle='#aab1c5';x.font='11px Arial';x.fillText(l.name.length>19?l.name.slice(0,18)+'…':l.name,nx,ny+34);});x.fillStyle='#243244';x.strokeStyle='#5ce1e6';x.lineWidth=3;x.beginPath();x.arc(cx,cy,38,0,Math.PI*2);x.fill();x.stroke();x.fillStyle='#fff';x.font='700 15px Arial';x.fillText(L?.name||iso,cx,cy);$('fmFamilyText').innerHTML=g?`<b>${esc(L.name)}</b> is classified by Glottolog in <b>${esc(g.familyName||(g.isolate?'an isolate':'no named family'))}</b>. ${fam.length?`This benchmark contains <b>${fam.length}</b> other canonical language${fam.length===1?'':'s'} from that family.`:'No other member of that family is represented in the canonical benchmark.'} This diagram uses that external genealogy only; bridge similarity is not involved.`:'No Glottolog record matched this benchmark ISO code.';}

  function loadLeaflet(){if(window.L){initMap();return;}const link=document.createElement('link');link.rel='stylesheet';link.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';document.head.appendChild(link);const s=document.createElement('script');s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';s.onload=initMap;s.onerror=()=>{$('fmMapFallback').innerHTML='<div class="fm-warning" style="margin-top:10px">Interactive basemap library could not load. The independent family diagram above still works.</div>';};document.head.appendChild(s);}
  function initMap(){if(state.map||!window.L||!state.glotLoaded)return;state.map=L.map('fmWorld',{worldCopyJump:true,minZoom:2}).setView([18,10],2);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:7,attribution:'&copy; OpenStreetMap contributors'}).addTo(state.map);drawWorld();}
  function clearMap(){if(!state.map)return;for(const m of state.markers.values())state.map.removeLayer(m);state.markers.clear();for(const l of state.lines)state.map.removeLayer(l);state.lines=[];}
  function drawWorld(){if(!state.map||!state.glotLoaded)return;clearMap();const iso=$('fmA').value,g0=state.glot.get(iso);if(!g0)return;let visible=[];if(state.layer==='bridge')visible=[state.byIso.get(iso),...neighbours(iso).slice(0,14).map(x=>x.l)];else if(state.layer==='family')visible=[state.byIso.get(iso),...sameFamily(iso)];else visible=state.langs.slice();const uniq=new Map(visible.filter(Boolean).map(l=>[l.iso,l]));for(const l of uniq.values()){const g=state.glot.get(l.iso);if(!g||!Number.isFinite(g.lat)||!Number.isFinite(g.lon))continue;const sel=l.iso===iso,m=L.circleMarker([g.lat,g.lon],{radius:sel?9:5,weight:sel?3:1,opacity:1,fillOpacity:.75}).addTo(state.map);m.bindPopup(`<b>${esc(l.name)}</b><br>${esc(l.iso)}<br>${esc(g.familyName||'Unclassified')}<br>${esc(g.macroarea||'')}`);m.on('click',()=>{if(state.byIso.has(l.iso)){$('fmA').value=l.iso;render();}});state.markers.set(l.iso,m);}
    const links=state.layer==='bridge'?neighbours(iso).slice(0,14).map(x=>x.l):state.layer==='family'?sameFamily(iso):[];for(const l of links){const g=state.glot.get(l.iso);if(!g||!Number.isFinite(g.lat)||!Number.isFinite(g.lon))continue;state.lines.push(L.polyline([[g0.lat,g0.lon],[g.lat,g.lon]],{weight:1.5,opacity:.45,dashArray:state.layer==='family'?'4 5':null}).addTo(state.map));}
    const pts=[...state.markers.values()].map(m=>m.getLatLng());if(state.layer!=='all'&&pts.length>1)state.map.fitBounds(L.latLngBounds(pts).pad(.18),{maxZoom:4});else state.map.setView([18,10],2);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install();
})();
