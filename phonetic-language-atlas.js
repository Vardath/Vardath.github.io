// Language Relationship Atlas for the Three Square Pyramid Phonetic Bridge.
// Uses existing full WikiPron gate-pair benchmark data. Additive only.
(function(){
  const $=id=>document.getElementById(id);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct=x=>Number.isFinite(+x)?(100*+x).toFixed(1)+'%':'—';
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  let atlas={langs:[],pairs:[],byIso:new Map(),pairMap:new Map(),groups:[],groupOf:new Map(),loaded:false,edgeTopK:4};

  function addCSS(){
    if($('languageAtlasStyle'))return;const st=document.createElement('style');st.id='languageAtlasStyle';st.textContent=`
      .la-controls{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:10px;align-items:end}.la-control label{display:block;font-size:.78rem;color:#aab1c5;margin-bottom:5px}.la-control select,.la-control input{width:100%;background:#0d111a;color:#eef;border:1px solid #39435a;border-radius:8px;padding:9px}.la-grid{display:grid;grid-template-columns:2fr 1fr;gap:14px;margin-top:14px}.la-panel{border:1px solid #30384d;border-radius:14px;background:#10151f;padding:14px}.la-canvaswrap{position:relative;min-height:620px}.la-canvaswrap canvas{width:100%;height:620px;border-radius:10px;background:#0b0f16;display:block}.la-tooltip{position:absolute;display:none;z-index:5;max-width:280px;background:#0c1119;border:1px solid #5ce1e6;border-radius:10px;padding:10px 12px;pointer-events:none;box-shadow:0 8px 30px rgba(0,0,0,.35);font-size:.82rem}.la-badge{display:inline-block;border:1px solid #3a465f;border-radius:999px;padding:3px 7px;font-size:.72rem;margin:2px 3px 2px 0;background:#111722}.la-table{width:100%;border-collapse:collapse}.la-table th,.la-table td{padding:8px;border-bottom:1px solid #2d3549;text-align:left;font-size:.84rem}.la-table th{font-size:.72rem;color:#aab1c5;text-transform:uppercase}.la-rank{font-variant-numeric:tabular-nums}.la-compat{font-weight:700;color:#80e7a8}.la-matrixwrap{position:relative;overflow:auto;max-height:760px;border:1px solid #30384d;border-radius:12px;background:#0b0f16}.la-matrixwrap canvas{display:block;image-rendering:auto}.la-legend{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:8px 0 12px;color:#aab1c5;font-size:.8rem}.la-grad{width:180px;height:10px;border-radius:999px;background:linear-gradient(90deg,#111722,#194654,#5ce1e6,#dffeff)}.la-groups{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}.la-group{border:1px solid #30384d;border-radius:12px;padding:12px;background:#0f141e}.la-group h4{margin:0 0 6px}.la-members{max-height:150px;overflow:auto;font-size:.8rem;color:#c7cede}.la-explain{border-left:3px solid #5ce1e6;background:#0e141e;border-radius:8px;padding:11px 13px;margin:12px 0;color:#c7cede}.la-statgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0}.la-stat{border:1px solid #30384d;border-radius:10px;padding:10px;background:#0f141e}.la-stat b{display:block;color:#5ce1e6;font-size:1.25rem}.la-modebtns{display:flex;gap:6px;flex-wrap:wrap}.la-modebtns button.active{border-color:#5ce1e6;box-shadow:0 0 0 1px rgba(92,225,230,.25) inset}.la-help{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border:1px solid #5ce1e6;border-radius:50%;font-size:.72rem;color:#5ce1e6;cursor:help;margin-left:4px}.la-note{font-size:.78rem;color:#aab1c5}.la-loading{padding:20px;text-align:center;color:#aab1c5}@media(max-width:1000px){.la-grid{grid-template-columns:1fr}.la-groups{grid-template-columns:1fr 1fr}.la-controls{grid-template-columns:1fr 1fr}.la-statgrid{grid-template-columns:1fr 1fr}}@media(max-width:600px){.la-groups,.la-controls,.la-statgrid{grid-template-columns:1fr}.la-canvaswrap canvas{height:500px}.la-canvaswrap{min-height:500px}}
    `;document.head.appendChild(st);
  }

  function csv(text){
    const rows=[];let row=[],field='',q=false;
    for(let i=0;i<text.length;i++){
      const c=text[i];if(q){if(c==='"'){if(text[i+1]==='"'){field+='"';i++}else q=false}else field+=c;continue}
      if(c==='"'){q=true;continue}if(c===','){row.push(field);field='';continue}if(c==='\n'){row.push(field);rows.push(row);row=[];field='';continue}if(c!=='\r')field+=c;
    }
    if(field.length||row.length){row.push(field);rows.push(row)}
    const h=rows.shift()||[];return rows.filter(r=>r.length&&r.some(x=>x!=='')).map(r=>Object.fromEntries(h.map((k,i)=>[k,r[i]??''])));
  }
  async function loadText(path){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw new Error(`${r.status} ${path}`);return r.text();}
  function pairKey(a,b){return a<b?a+'|'+b:b+'|'+a;}
  function getPair(a,b){return atlas.pairMap.get(pairKey(a,b));}
  function dirSupport(p,from,to){if(!p)return null;return p.iso_a===from?+p.a_to_b_direct_mass:+p.b_to_a_direct_mass;}

  function install(){
    if($('languageAtlas'))return;addCSS();const sec=document.createElement('section');sec.className='section wrap';sec.id='languageAtlas';sec.innerHTML=`
      <h2>Language Relationship Atlas</h2>
      <p class="lead">Which languages actually behave alike inside the phonetic bridge? This atlas maps every canonical WikiPron language pair using the gate relationships already measured by the full benchmark.</p>
      <div class="la-explain"><b>Compatibility percentage <span class="la-help" title="Jaccard overlap: shared stable gate types divided by all distinct stable gate types used by either language. 100% means the two languages use exactly the same stable gate set in this benchmark; 0% means no stable gate types overlap.">?</span></b> = the percentage of stable 4×4 gate types shared by both languages out of their combined set. This is deliberately separate from <b>A→B direct support</b>, which measures how much of one language's observed transition mass the other language can directly support.</div>
      <div id="laStatus" class="status">Loading full relationship data…</div>
      <div id="laStats" class="la-statgrid"></div>
      <div class="la-controls">
        <div class="la-control"><label for="laLanguage">Explore one language</label><select id="laLanguage"></select></div>
        <div class="la-control"><label for="laTopK">Links per language <span class="la-help" title="For the full network, each language keeps only its strongest few relationships so the graph stays readable. The underlying matrix still contains every pair.">?</span></label><select id="laTopK"><option>2</option><option>3</option><option selected>4</option><option>5</option><option>6</option><option>8</option></select></div>
        <div class="la-control"><label for="laMinCompat">Minimum visible compatibility</label><input id="laMinCompat" type="range" min="0" max="80" step="1" value="20"><div class="la-note"><span id="laMinCompatLabel">20%</span></div></div>
        <div class="la-control"><label>Colour/group view</label><div class="la-modebtns"><button class="btn active" data-la-mode="cluster" type="button">Data groups</button><button class="btn" data-la-mode="family" type="button">Families</button></div></div>
      </div>
      <div class="la-grid">
        <div class="la-panel"><h3>All-language relationship network <span class="la-help" title="Every dot is a language. Lines connect each language to its strongest compatible neighbours above the threshold. Data-derived groups are communities found from those strongest measured relationships, not assumed historical families.">?</span></h3><div class="la-canvaswrap"><canvas id="laNetwork"></canvas><div id="laNetworkTip" class="la-tooltip"></div></div><p class="la-note">Click a language node to make it the active language. Hover a node or line for details.</p></div>
        <div class="la-panel"><h3>Closest matches</h3><div id="laSelected"></div><div id="laRanking"></div></div>
      </div>
      <h3 style="margin-top:28px">Data-derived compatibility groups</h3>
      <p class="small">These groups are produced from mutual strongest gate-overlap relationships. They are experimental phonetic-network communities and should not be confused with historical language families.</p>
      <div id="laGroups" class="la-groups"></div>
      <h3 style="margin-top:28px">All languages × all languages</h3>
      <div class="la-legend"><span>Lower gate overlap</span><span class="la-grad"></span><span>Higher gate overlap</span><span>· hover for exact pair</span></div>
      <div class="la-matrixwrap"><canvas id="laMatrix"></canvas><div id="laMatrixTip" class="la-tooltip"></div></div>
      <details class="panel" style="margin-top:16px"><summary><b>How are the groups calculated?</b></summary><p>The atlas builds a sparse undirected graph from each language's strongest compatibility relationships, keeping mutual or very strong neighbour links. It then repeatedly propagates community labels until they stabilise. The matrix itself always retains every measured pair; changing the visible network threshold does not alter the underlying compatibility values.</p><p>The primary compatibility measure is stable-gate Jaccard overlap. Cosine similarity, Jensen–Shannon divergence, and directional direct-support values remain available in hover details so one percentage is never mistaken for the whole story.</p></details>`;
    const anchor=$('magic')||$('status');if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(sec,anchor);else document.querySelector('main')?.appendChild(sec);
    const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#languageAtlas"]')){const a=document.createElement('a');a.href='#languageAtlas';a.textContent='Language atlas';nav.insertBefore(a,nav.querySelector('a[href="#magic"]')||null);}
    $('laTopK').addEventListener('change',()=>{atlas.edgeTopK=+$('laTopK').value;deriveGroups();renderAll();});
    $('laMinCompat').addEventListener('input',()=>{$('laMinCompatLabel').textContent=$('laMinCompat').value+'%';drawNetwork();});
    $('laLanguage').addEventListener('change',()=>{renderSelected($('laLanguage').value);drawNetwork();});
    document.querySelectorAll('[data-la-mode]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-la-mode]').forEach(x=>x.classList.remove('active'));b.classList.add('active');atlas.mode=b.dataset.laMode;drawNetwork();}));
    load();
  }

  async function load(){
    try{
      const [lt,pt]=await Promise.all([loadText('data/phonetic-benchmark-languages.csv?v=atlas1'),loadText('data/phonetic-benchmark-pairs.csv?v=atlas1')]);
      const langs=csv(lt).filter(r=>String(r.canonical).toLowerCase()==='true').map(r=>({iso:r.iso,name:r.name||r.iso,family:r.family||'Unclassified',macroarea:r.macroarea||'',file:r.file||''}));
      const wanted=new Set(langs.map(x=>x.iso));
      const pairs=csv(pt).filter(p=>wanted.has(p.iso_a)&&wanted.has(p.iso_b)).map(p=>({...p,jaccard:+p.jaccard,cosine:+p.cosine,jsd_bits:+p.jsd_bits,a_to_b_direct_mass:+p.a_to_b_direct_mass,b_to_a_direct_mass:+p.b_to_a_direct_mass,shared_stable_gates:+p.shared_stable_gates,union_stable_gates:+p.union_stable_gates}));
      atlas.langs=langs;atlas.pairs=pairs;atlas.byIso=new Map(langs.map(x=>[x.iso,x]));atlas.pairMap=new Map(pairs.map(p=>[pairKey(p.iso_a,p.iso_b),p]));atlas.mode='cluster';
      deriveGroups();atlas.loaded=true;populate();renderAll();
      $('laStatus').className='status ok';$('laStatus').innerHTML=`Loaded <b>${langs.length}</b> canonical languages and <b>${pairs.length.toLocaleString()}</b> measured language relationships.`;
    }catch(e){$('laStatus').className='status error';$('laStatus').textContent='Could not load the relationship atlas: '+e.message;}
  }

  function neighbours(iso){
    const arr=[];for(const l of atlas.langs){if(l.iso===iso)continue;const p=getPair(iso,l.iso);if(p)arr.push({iso:l.iso,p,compat:p.jaccard,support:dirSupport(p,iso,l.iso),reverse:dirSupport(p,l.iso,iso)});}arr.sort((a,b)=>b.compat-a.compat||b.support-a.support);return arr;
  }
  function sparseEdges(){
    const chosen=new Map();for(const l of atlas.langs){const ns=neighbours(l.iso).slice(0,atlas.edgeTopK);chosen.set(l.iso,new Set(ns.map(n=>n.iso)));}
    const out=[];for(const p of atlas.pairs){const a=chosen.get(p.iso_a)?.has(p.iso_b),b=chosen.get(p.iso_b)?.has(p.iso_a);if(a&&b || (a||b)&&p.jaccard>=.55)out.push(p);}return out;
  }
  function deriveGroups(){
    if(!atlas.langs.length)return;const edges=sparseEdges(),adj=new Map(atlas.langs.map(l=>[l.iso,[]]));for(const p of edges){adj.get(p.iso_a).push([p.iso_b,p.jaccard]);adj.get(p.iso_b).push([p.iso_a,p.jaccard]);}
    let lab=new Map(atlas.langs.map(l=>[l.iso,l.iso]));for(let iter=0;iter<30;iter++){let changed=0;for(const l of atlas.langs.slice().sort((a,b)=>a.iso.localeCompare(b.iso))){const score=new Map();for(const [n,w] of adj.get(l.iso)){const z=lab.get(n);score.set(z,(score.get(z)||0)+w);}if(!score.size)continue;const best=[...score].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])))[0][0];if(best!==lab.get(l.iso)){lab.set(l.iso,best);changed++;}}if(!changed)break;}
    // Collapse tiny groups into their strongest neighbouring group.
    for(let pass=0;pass<3;pass++){const count=new Map();for(const v of lab.values())count.set(v,(count.get(v)||0)+1);for(const l of atlas.langs){const g=lab.get(l.iso);if((count.get(g)||0)>=3)continue;const scores=new Map();for(const [n,w] of adj.get(l.iso)){const ng=lab.get(n);if(ng!==g)scores.set(ng,(scores.get(ng)||0)+w);}if(scores.size)lab.set(l.iso,[...scores].sort((a,b)=>b[1]-a[1])[0][0]);}}
    const gm=new Map();for(const l of atlas.langs){const g=lab.get(l.iso);if(!gm.has(g))gm.set(g,[]);gm.get(g).push(l.iso);}let groups=[...gm.values()].sort((a,b)=>b.length-a.length);
    atlas.groups=groups.map((members,i)=>{let sum=0,n=0,max={v:-1,a:null,b:null};for(let x=0;x<members.length;x++)for(let y=x+1;y<members.length;y++){const p=getPair(members[x],members[y]);if(p){sum+=p.jaccard;n++;if(p.jaccard>max.v)max={v:p.jaccard,a:members[x],b:members[y]};}}return{id:i+1,members,mean:n?sum/n:0,strongest:max};});atlas.groupOf=new Map();for(const g of atlas.groups)for(const iso of g.members)atlas.groupOf.set(iso,g.id);
  }

  function populate(){const opts=atlas.langs.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(l=>`<option value="${esc(l.iso)}">${esc(l.name)} · ${esc(l.iso)}</option>`).join('');$('laLanguage').innerHTML=opts;const current=state?.languages?.get?.($('sourceLanguage')?.value)?.ISO;if(current&&atlas.byIso.has(current))$('laLanguage').value=current;}
  function renderAll(){renderStats();renderSelected($('laLanguage').value||atlas.langs[0]?.iso);renderGroups();drawNetwork();drawMatrix();}
  function renderStats(){const vals=atlas.pairs.map(p=>p.jaccard).sort((a,b)=>a-b),mean=vals.reduce((a,b)=>a+b,0)/(vals.length||1),median=vals[Math.floor(vals.length/2)]||0,strong=vals.filter(x=>x>=.5).length;$('laStats').innerHTML=`<div class="la-stat"><b>${atlas.langs.length}</b><span>languages mapped</span></div><div class="la-stat"><b>${atlas.pairs.length.toLocaleString()}</b><span>pair relationships</span></div><div class="la-stat"><b>${pct(mean)}</b><span>mean gate compatibility</span></div><div class="la-stat"><b>${atlas.groups.length}</b><span>data-derived groups</span></div>`;}
  function renderSelected(iso){const l=atlas.byIso.get(iso);if(!l)return;const ns=neighbours(iso);const best=ns.slice(0,20);$('laSelected').innerHTML=`<h4>${esc(l.name)} <span class="la-badge">${esc(l.iso)}</span></h4><div class="small">${esc(l.family)} · ${esc(l.macroarea||'macroarea unlisted')} · data group ${atlas.groupOf.get(iso)||'—'}</div><p class="small">Its strongest measured partner is ${best[0]?`<b>${esc(atlas.byIso.get(best[0].iso)?.name)}</b> at <b class="la-compat">${pct(best[0].compat)}</b>`:'—'}.</p>`;$('laRanking').innerHTML=`<table class="la-table"><thead><tr><th>#</th><th>Language</th><th>Compatibility <span class="la-help" title="Shared stable-gate Jaccard overlap.">?</span></th><th>${esc(l.iso)}→other <span class="la-help" title="Fraction of this language's observed gate-transition mass directly supported by the other language.">?</span></th><th>other→${esc(l.iso)}</th></tr></thead><tbody>${best.map((n,i)=>{const o=atlas.byIso.get(n.iso);return`<tr><td class="la-rank">${i+1}</td><td><button class="btn" style="padding:4px 7px" data-la-pick="${esc(n.iso)}">${esc(o?.name||n.iso)}</button><div class="la-note">${esc(o?.family||'')}</div></td><td class="la-compat">${pct(n.compat)}</td><td>${pct(n.support)}</td><td>${pct(n.reverse)}</td></tr>`;}).join('')}</tbody></table>`;document.querySelectorAll('[data-la-pick]').forEach(b=>b.onclick=()=>{$('laLanguage').value=b.dataset.laPick;renderSelected(b.dataset.laPick);drawNetwork();});}
  function renderGroups(){$('laGroups').innerHTML=atlas.groups.map(g=>{const names=g.members.map(x=>atlas.byIso.get(x)?.name||x).sort();return`<div class="la-group"><h4>Group ${g.id} <span class="la-badge">${g.members.length} languages</span></h4><div class="small">mean internal compatibility <b>${pct(g.mean)}</b></div><div class="small">strongest pair ${g.strongest.a?`${esc(atlas.byIso.get(g.strongest.a)?.name)} ↔ ${esc(atlas.byIso.get(g.strongest.b)?.name)} · ${pct(g.strongest.v)}`:'—'}</div><div class="la-members">${names.map(n=>esc(n)).join(' · ')}</div></div>`;}).join('');}

  function palette(i){const h=(i*137.508)%360;return `hsl(${h} 68% 62%)`;}
  function familyIndex(){const fams=[...new Set(atlas.langs.map(l=>l.family))].sort();return new Map(fams.map((f,i)=>[f,i]));}
  function networkData(w,h){const n=atlas.langs.length,cx=w/2,cy=h/2,R=Math.min(w,h)*.42,famIdx=familyIndex();return atlas.langs.map((l,i)=>{const g=atlas.groupOf.get(l.iso)||1;const ring=(g-1)%5;const ang=2*Math.PI*(i/n)+(g*.37);const rr=R*(.42+.12*ring);return{...l,x:cx+Math.cos(ang)*rr,y:cy+Math.sin(ang)*rr,vx:0,vy:0,r:4+(neighbours(l.iso)[0]?.compat||0)*4,color:atlas.mode==='family'?palette(famIdx.get(l.family)||0):palette(g-1)};});}
  function drawNetwork(){if(!atlas.loaded)return;const canvas=$('laNetwork'),wrap=canvas.parentElement,dpr=window.devicePixelRatio||1,w=Math.max(600,wrap.clientWidth),h=canvas.clientHeight||620;canvas.width=w*dpr;canvas.height=h*dpr;canvas.style.width=w+'px';canvas.style.height=h+'px';const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const nodes=networkData(w,h),by=new Map(nodes.map(n=>[n.iso,n])),edges=sparseEdges().filter(p=>p.jaccard*100>=+$('laMinCompat').value),selected=$('laLanguage').value;
    // lightweight force relaxation
    for(let it=0;it<70;it++){for(const p of edges){const a=by.get(p.iso_a),b=by.get(p.iso_b);if(!a||!b)continue;let dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1,target=35+95*(1-p.jaccard),f=(d-target)*.018;a.x+=dx/d*f;a.y+=dy/d*f;b.x-=dx/d*f;b.y-=dy/d*f;}for(const n of nodes){n.x=clamp(n.x,16,w-16);n.y=clamp(n.y,16,h-16);}}
    ctx.clearRect(0,0,w,h);for(const p of edges){const a=by.get(p.iso_a),b=by.get(p.iso_b);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=`rgba(130,180,195,${.08+.55*p.jaccard})`;ctx.lineWidth=.4+2.2*p.jaccard;ctx.stroke();}
    for(const n of nodes){ctx.beginPath();ctx.arc(n.x,n.y,n.iso===selected?n.r+3:n.r,0,Math.PI*2);ctx.fillStyle=n.color;ctx.fill();if(n.iso===selected){ctx.lineWidth=3;ctx.strokeStyle='#fff';ctx.stroke();}}
    canvas._la={nodes,edges,by,w,h};attachNetworkEvents(canvas);
  }
  function attachNetworkEvents(c){if(c._bound)return;c._bound=true;const tip=$('laNetworkTip');c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,d=c._la;let node=d.nodes.map(n=>[n,Math.hypot(n.x-x,n.y-y)]).sort((a,b)=>a[1]-b[1])[0];if(node&&node[1]<12){const n=node[0],best=neighbours(n.iso)[0];tip.style.display='block';tip.style.left=(x+14)+'px';tip.style.top=(y+14)+'px';tip.innerHTML=`<b>${esc(n.name)}</b> · ${esc(n.iso)}<br>${esc(n.family)}<br>Group ${atlas.groupOf.get(n.iso)||'—'}${best?`<br>Best match: ${esc(atlas.byIso.get(best.iso)?.name)} · ${pct(best.compat)}`:''}`;return;}tip.style.display='none';});c.addEventListener('mouseleave',()=>tip.style.display='none');c.addEventListener('click',e=>{const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,d=c._la;const z=d.nodes.map(n=>[n,Math.hypot(n.x-x,n.y-y)]).sort((a,b)=>a[1]-b[1])[0];if(z&&z[1]<14){$('laLanguage').value=z[0].iso;renderSelected(z[0].iso);drawNetwork();}});}

  function drawMatrix(){if(!atlas.loaded)return;const ordered=atlas.groups.flatMap(g=>g.members.slice().sort((a,b)=>(atlas.byIso.get(a)?.name||a).localeCompare(atlas.byIso.get(b)?.name||b))),n=ordered.length,cell=3,size=n*cell+120,c=$('laMatrix'),dpr=window.devicePixelRatio||1;c.width=size*dpr;c.height=size*dpr;c.style.width=size+'px';c.style.height=size+'px';const ctx=c.getContext('2d');ctx.scale(dpr,dpr);ctx.fillStyle='#0b0f16';ctx.fillRect(0,0,size,size);const off=110;for(let i=0;i<n;i++)for(let j=0;j<n;j++){const v=i===j?1:(getPair(ordered[i],ordered[j])?.jaccard||0);const t=clamp(v,0,1);const lum=15+70*t;ctx.fillStyle=`hsl(187 70% ${lum}%)`;ctx.fillRect(off+j*cell,off+i*cell,cell,cell);}ctx.fillStyle='#aab1c5';ctx.font='9px sans-serif';for(let i=0;i<n;i+=Math.max(1,Math.floor(n/18))){const name=atlas.byIso.get(ordered[i])?.name||ordered[i];ctx.save();ctx.translate(off+i*cell+2,off-4);ctx.rotate(-Math.PI/3);ctx.fillText(name,0,0);ctx.restore();ctx.fillText(name,2,off+i*cell+3);}c._la={ordered,cell,off};attachMatrixEvents(c);}
  function attachMatrixEvents(c){if(c._bound)return;c._bound=true;const tip=$('laMatrixTip'),wrap=c.parentElement;c.addEventListener('mousemove',e=>{const r=c.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,d=c._la,i=Math.floor((y-d.off)/d.cell),j=Math.floor((x-d.off)/d.cell);if(i<0||j<0||i>=d.ordered.length||j>=d.ordered.length){tip.style.display='none';return;}const a=d.ordered[i],b=d.ordered[j],la=atlas.byIso.get(a),lb=atlas.byIso.get(b),p=a===b?null:getPair(a,b);tip.style.display='block';tip.style.left=(x+14)+'px';tip.style.top=(y+14)+'px';tip.innerHTML=a===b?`<b>${esc(la?.name)}</b><br>same language · 100%`:`<b>${esc(la?.name)} ↔ ${esc(lb?.name)}</b><br>compatibility <b>${pct(p?.jaccard)}</b><br>${esc(a)}→${esc(b)} direct support ${pct(dirSupport(p,a,b))}<br>${esc(b)}→${esc(a)} direct support ${pct(dirSupport(p,b,a))}<br>cosine ${p?.cosine?.toFixed(3)??'—'} · JSD ${p?.jsd_bits?.toFixed(3)??'—'}`;});c.addEventListener('mouseleave',()=>tip.style.display='none');}

  function boot(){install();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();