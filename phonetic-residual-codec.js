// Reversible residual-memory experiment for the three-square pyramid bridge.
// Additive only: does not alter the existing bridge or benchmarks.
(function(){
  const $=id=>document.getElementById(id);
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const codecModes=[{id:'plain',label:'Plain nearest'},{id:'5',label:'5×5'},{id:'4',label:'4×4'},{id:'3',label:'3×3'},{id:'adaptive',label:'Adaptive 5→4→3'}];

  function install(){
    if($('residualCodec'))return;
    const css=document.createElement('style');css.textContent=`
      .rc-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:16px 0}.rc-card{border:1px solid #30384d;border-radius:12px;padding:14px;background:#10151f}.rc-card b{display:block;color:#5ce1e6}.rc-loss{font-size:1.25rem;font-weight:700}.rc-good{color:#80e7a8}.rc-warn{color:#ffd37a}.rc-flow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:10px 0}.rc-flow span{border:1px solid #3c465d;border-radius:9px;padding:7px 9px;background:#0d111a}.rc-flow .arrow{border:0;background:transparent;color:#5ce1e6}.rc-packet{border:1px dashed #5ce1e6;border-radius:10px;padding:10px 12px;background:#0d1619;margin:10px 0}.rc-features{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.rc-feature{border:1px solid #3b465f;border-radius:999px;padding:3px 7px;font-size:.78rem;background:#111722}.rc-table{width:100%;border-collapse:collapse}.rc-table th,.rc-table td{padding:10px;border-bottom:1px solid #30384d;text-align:left}.rc-table th{color:#aab1c5;font-size:.8rem;text-transform:uppercase}@media(max-width:900px){.rc-grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){.rc-grid{grid-template-columns:1fr}}`;
    document.head.appendChild(css);
    const sec=document.createElement('section');sec.className='section wrap';sec.id='residualCodec';sec.innerHTML=`
      <h2>Residual-memory codec: can lost sound detail be carried through translation?</h2>
      <p class="lead">When a target language cannot express every source distinction, the audible output may need to compress the sound. This experiment stores the feature difference separately as a residual packet, then uses that packet on the return trip.</p>
      <div class="notice"><b>Important:</b> the listener still hears only a real target-language sound. The residual packet is hidden bridge metadata used only to test whether the original pronunciation can be reconstructed more accurately later.</div>
      <div class="panel"><h3>Example logic</h3><div class="rc-flow"><span>source sound</span><span class="arrow">→</span><span>target sound</span><span class="arrow">+</span><span>lost feature packet</span><span class="arrow">→</span><span>better return reconstruction?</span></div><p class="small">Example: if /g/ must be rendered as /k/, the audible target is /k/ while the residual can retain the lost voicing distinction.</p></div>
      <div style="margin-top:18px"><button id="rcRun" class="btn" type="button">Run residual-memory benchmark</button> <button id="rcRandom" class="btn" type="button">Show random residual example</button></div>
      <div id="rcStatus" class="status">Choose a language pair above, then run the test.</div>
      <div id="rcSummary" class="rc-grid"></div>
      <div id="rcResults" class="panel" style="margin-top:14px"></div>
      <h3 style="margin-top:30px">Residual example</h3><div id="rcExample" class="panel">Run the test first.</div>
      <details class="panel" style="margin-top:16px"><summary><b>What would support this idea?</b></summary><p>If residual-assisted round trips consistently reduce return feature loss or increase exact IPA reconstruction compared with ordinary round trips, then the pyramid can act more like a reversible multiresolution codec. If residual memory does not improve reconstruction, it adds complexity without benefit and should be rejected.</p></details>`;
    const anchor=$('magic')||$('status'); if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(sec,anchor); else document.querySelector('main')?.appendChild(sec);
    const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#residualCodec"]')){const a=document.createElement('a');a.href='#residualCodec';a.textContent='Residual codec';nav.insertBefore(a,nav.querySelector('a[href="#magic"]')||null);}
    $('rcRun')?.addEventListener('click',run);$('rcRandom')?.addEventListener('click',randomExample);
  }

  function srcPhones(){const ids=state.inventorySegments.get($('sourceInventory')?.value)||[];return ids.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY');}
  function targetIds(){return state.inventorySegments.get($('targetInventory')?.value)||[];}
  function sourceIds(){return state.inventorySegments.get($('sourceInventory')?.value)||[];}
  function plain(p,ids){const r=nearest(p,ids,false).ranked[0];return r?{best:r,covered:true}:{best:null,covered:false};}
  function route(p,ids,m){if(m==='plain')return plain(p,ids);return window.phonetic345?.resultForMode(p,ids,m)||{best:null,covered:false};}

  function vector(p){const v={};for(const f of FEATURE_NAMES)v[f]=fnum(p[f]);return v;}
  function residual(a,b){const av=vector(a),bv=vector(b),r={};for(const f of FEATURE_NAMES){if(f==='tone'&&classify(a)!=='PROSODY'&&classify(b)!=='PROSODY')continue;const d=av[f]-bv[f];if(Math.abs(d)>.001)r[f]=d;}return r;}
  function residualMagnitude(r){let sum=0,w=0;for(const f of FEATURE_NAMES){if(!(f in r))continue;const wt=PRIMARY_FEATURES.has(f)?2:1;sum+=Math.abs(r[f])/2*wt;w+=wt;}return w?sum/w:0;}
  function reconstructVector(target,res){const tv=vector(target),out={};for(const f of FEATURE_NAMES)out[f]=Math.max(-1,Math.min(1,(tv[f]||0)+(res[f]||0)));return out;}
  function distanceToVector(candidate,v,referenceClass){let sum=0,wSum=0;for(const f of FEATURE_NAMES){if(f==='tone'&&referenceClass!=='PROSODY'&&classify(candidate)!=='PROSODY')continue;const wt=PRIMARY_FEATURES.has(f)?2:1;sum+=Math.abs(fnum(candidate[f])-(v[f]||0))/2*wt;wSum+=wt;}return wSum?sum/wSum:1;}
  function decodeResidual(target,res,ids,sourceClass){const goal=reconstructVector(target,res);let pool=ids.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY');if(sourceClass==='PROSODY')pool=ids.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)==='PROSODY');const ranked=pool.map(p=>({p,distance:distanceToVector(p,goal,sourceClass)})).sort((a,b)=>a.distance-b.distance);return ranked[0]||null;}
  function topResidual(r){return Object.entries(r).sort((a,b)=>Math.abs(b[1])-Math.abs(a[1])).slice(0,8);}

  let last=null;
  function run(){
    if(typeof state==='undefined'||!state.loaded||!window.phonetic345){$('rcStatus').className='status error';$('rcStatus').textContent='PHOIBLE or pyramid codec has not loaded yet.';return;}
    const src=srcPhones(),tids=targetIds(),sids=sourceIds();if(!src.length||!tids.length)return;
    const rows=codecModes.map(m=>{let forward=0,ordinaryReturned=0,residualReturned=0,ordinaryExact=0,residualExact=0;const ordinaryLoss=[],residualLoss=[],packet=[];for(const p of src){const f=route(p,tids,m.id);if(!f.best)continue;forward++;const t=f.best.p;const ord=route(t,sids,m.id);if(ord.best){ordinaryReturned++;const d=featureDistance(p,ord.best.p).distance;ordinaryLoss.push(d);if(ord.best.p.Name===p.Name)ordinaryExact++;}const rp=residual(p,t),dec=decodeResidual(t,rp,sids,classify(p));if(dec){residualReturned++;const d=featureDistance(p,dec.p).distance;residualLoss.push(d);if(dec.p.Name===p.Name)residualExact++;packet.push(residualMagnitude(rp));}}
      return {...m,forward,ordinaryReturned,residualReturned,ordinaryExact,residualExact,ordinaryMean:ordinaryLoss.length?ordinaryLoss.reduce((a,b)=>a+b,0)/ordinaryLoss.length:null,residualMean:residualLoss.length?residualLoss.reduce((a,b)=>a+b,0)/residualLoss.length:null,packetMean:packet.length?packet.reduce((a,b)=>a+b,0)/packet.length:null};});
    last={rows,src,tids,sids};const sl=state.languages.get($('sourceLanguage')?.value),tl=state.languages.get($('targetLanguage')?.value);$('rcStatus').className='status ok';$('rcStatus').innerHTML=`Residual-memory test completed for <b>${esc(sl?.Name||'source')}</b> → <b>${esc(tl?.Name||'target')}</b> across ${src.length} source sounds.`;
    $('rcSummary').innerHTML=rows.map(r=>{const improved=r.ordinaryMean!==null&&r.residualMean!==null&&r.residualMean<r.ordinaryMean-1e-9;return`<div class="rc-card"><b>${esc(r.label)}</b><div class="small">ordinary return loss</div><div class="rc-loss">${r.ordinaryMean===null?'—':r.ordinaryMean.toFixed(4)}</div><div class="small">with residual memory</div><div class="rc-loss ${improved?'rc-good':''}">${r.residualMean===null?'—':r.residualMean.toFixed(4)}</div><div class="small">exact return ${r.ordinaryExact} → ${r.residualExact}</div>${improved?'<div class="rc-good">reconstruction improved</div>':''}</div>`;}).join('');
    $('rcResults').innerHTML=`<table class="rc-table"><thead><tr><th>Strategy</th><th>Forward outputs</th><th>Ordinary exact</th><th>Residual exact</th><th>Ordinary return loss</th><th>Residual return loss</th><th>Mean packet size</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${esc(r.label)}</b></td><td>${r.forward}/${src.length}</td><td>${r.ordinaryExact}/${src.length}</td><td>${r.residualExact}/${src.length}</td><td>${r.ordinaryMean===null?'—':r.ordinaryMean.toFixed(4)}</td><td>${r.residualMean===null?'—':r.residualMean.toFixed(4)}</td><td>${r.packetMean===null?'—':r.packetMean.toFixed(4)}</td></tr>`).join('')}</tbody></table><p class="small">Residual memory is only useful if the improved return accuracy is large enough to justify carrying the extra feature packet.</p>`;
    randomExample();
  }

  function randomExample(){if(!last)run();if(!last)return;const {src,tids,sids}=last;const p=src[Math.floor(Math.random()*src.length)];const cards=codecModes.map(m=>{const f=route(p,tids,m.id);if(!f.best)return`<div class="rc-card"><b>${esc(m.label)}</b><div class="rc-warn">no forward output</div></div>`;const t=f.best.p,rp=residual(p,t),ord=route(t,sids,m.id),dec=decodeResidual(t,rp,sids,classify(p)),tops=topResidual(rp);const od=ord.best?featureDistance(p,ord.best.p).distance:null,rd=dec?featureDistance(p,dec.p).distance:null;return`<div class="rc-card"><b>${esc(m.label)}</b><div class="rc-flow"><span>/${esc(p.Name)}/</span><span class="arrow">→</span><span>/${esc(t.Name)}/</span></div><div class="rc-packet"><b>Residual packet</b><div class="rc-features">${tops.length?tops.map(([f,v])=>`<span class="rc-feature">${esc(f)} ${v>0?'+':''}${v.toFixed(2)}</span>`).join(''):'<span class="small">no lost features</span>'}</div></div><div class="small">ordinary return: ${ord.best?'/'+esc(ord.best.p.Name)+'/':'—'} · loss ${od===null?'—':od.toFixed(4)}</div><div class="small">with residual: ${dec?'/'+esc(dec.p.Name)+'/':'—'} · loss ${rd===null?'—':rd.toFixed(4)} ${dec&&dec.p.Name===p.Name?'<span class="rc-good">· exact recovery</span>':''}</div>${typeof audioButton==='function'?`<div style="margin-top:8px" class="small">source ${audioButton(p.Name)} target ${audioButton(t.Name)} ${dec?'recovered '+audioButton(dec.p.Name):''}</div>`:''}</div>`;}).join('');$('rcExample').innerHTML=`<h4>Source /${esc(p.Name)}/</h4><div class="rc-grid">${cards}</div>`;}

  function boot(){install();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();