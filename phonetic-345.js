// Experimental 3–4–5 adaptive resolution codec.
// Additive only: it does not alter the established 4×4 classifier or benchmark.
(function(){
  const $=id=>document.getElementById(id);
  const ROWS=['A','B','C','D'];
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let currentMode='adaptive', exampleRequest=0;

  function installUI(){
    if($('resolution345'))return;
    const css=document.createElement('style');
    css.textContent=`
      .r345pyramid{display:grid;gap:10px;justify-items:center;margin:24px 0}.r345tier{display:grid;gap:6px;text-align:center}.r345tier5{grid-template-columns:repeat(5,46px)}.r345tier4{grid-template-columns:repeat(4,50px)}.r345tier3{grid-template-columns:repeat(3,56px)}.r345sq{aspect-ratio:1;display:grid;place-items:center;border:1px solid #3a4259;border-radius:7px;background:#111621;color:#9da6bf;font-size:.72rem;transition:.15s}.r345sq.src{border-color:#5ce1e6;box-shadow:0 0 0 2px rgba(92,225,230,.28) inset;color:#fff}.r345sq.tgt{border-color:#80e7a8;box-shadow:0 0 0 2px rgba(128,231,168,.28) inset;color:#fff}.r345sq.both{background:#17302e;border-color:#b8f5d0}.r345cap{width:100px;padding:9px;border:1px dashed #ffd37a;border-radius:9px;text-align:center;color:#ffd37a;background:#17140d}.r345levels{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:18px 0}.r345box{min-width:160px;text-align:center;padding:15px;border:1px solid #39435c;border-radius:12px;background:linear-gradient(180deg,#191f2d,#11151f)}.r345box b,.r345box span,.r345box small{display:block}.r345box b{color:#5ce1e6}.r345box span{font-size:1.55rem;font-family:Consolas,monospace;margin:4px 0}.r345box small{color:#aab1c5}.r345arrow,.r345flow{color:#5ce1e6;font-size:1.45rem}.r345target{border:1px solid #30384d;border-radius:13px;padding:16px;background:#11151f;margin:14px 0}.r345formula{text-align:center;font-family:Consolas,monospace;color:#5ce1e6;margin:12px 0}.r345explain{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:18px 0}.r345explain>div{border:1px solid #30384d;border-radius:12px;padding:14px;background:#11151f}.r345explain b{display:block;color:#5ce1e6;margin-bottom:5px}.r345toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:end;margin:16px 0}.r345toolbar .control{min-width:210px;flex:1}.r345modes{display:flex;gap:7px;flex-wrap:wrap}.r345mode,.r345action{border:1px solid #46506b;background:#151a27;color:#eef1f8;border-radius:999px;padding:8px 12px;cursor:pointer}.r345mode.active{border-color:#5ce1e6;background:#18303a;color:#fff}.r345action:hover,.r345mode:hover{border-color:#5ce1e6}.r345output{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center}.r345sound{text-align:center;border:1px solid #30384d;border-radius:12px;padding:14px;background:#0d111a}.r345sound .ipa{font-family:Georgia,serif;font-size:2.3rem}.r345written{font-size:1.45rem;font-weight:700;margin-top:7px}.r345compare{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}.r345compare>div{border:1px solid #30384d;border-radius:11px;padding:12px;background:#10141d}.r345compare b{display:block;color:#5ce1e6}.r345batch{overflow:auto}.r345batch table{width:100%;border-collapse:collapse}.r345batch th,.r345batch td{padding:9px;border-bottom:1px solid #30384d;text-align:left}.r345legend{display:flex;gap:14px;flex-wrap:wrap;color:#aab1c5;font-size:.85rem}.r345dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}.r345dot.src{background:#5ce1e6}.r345dot.tgt{background:#80e7a8}@media(max-width:900px){.r345compare{grid-template-columns:1fr 1fr}.r345output{grid-template-columns:1fr}.r345flow{text-align:center}}@media(max-width:800px){.r345explain{grid-template-columns:1fr}.r345tier5{grid-template-columns:repeat(5,34px)}.r345tier4{grid-template-columns:repeat(4,38px)}.r345tier3{grid-template-columns:repeat(3,42px)}}`;
    document.head.appendChild(css);

    const section=document.createElement('section');
    section.className='section wrap';section.id='resolution345';
    section.innerHTML=`
      <h2>Experimental 3–4–5 Pyramid Translation Lab</h2>
      <p class="lead">Treat the 5×5, 4×4 and 3×3 grids as three resolutions of one phonetic space. Choose a sound, force a layer or let the codec contract automatically, then inspect and hear the target result.</p>
      <div class="notice"><b>This remains additive.</b> The existing 4×4 bridge, benchmark, correspondence system and audio layer are unchanged. This lab tests whether controlled expansion/contraction improves practical sound translation.</div>
      <div class="r345pyramid" aria-label="3-4-5 pyramid layers">
        <div class="r345cap">? capstone<br><span class="small">unresolved</span></div>
        <div class="r345tier r345tier3">${Array.from({length:9},(_,i)=>`<div class="r345sq" data-n="3" data-i="${i}">3.${i+1}</div>`).join('')}</div>
        <div class="r345tier r345tier4">${Array.from({length:16},(_,i)=>`<div class="r345sq" data-n="4" data-i="${i}">4.${i+1}</div>`).join('')}</div>
        <div class="r345tier r345tier5">${Array.from({length:25},(_,i)=>`<div class="r345sq" data-n="5" data-i="${i}">5.${i+1}</div>`).join('')}</div>
      </div>
      <div class="r345legend"><span><i class="r345dot src"></i>source position</span><span><i class="r345dot tgt"></i>target position</span></div>
      <div class="r345formula">5×5 fine detail ⇄ 4×4 bridge ⇄ 3×3 coarse structure ⇄ ? capstone</div>
      <div class="r345explain"><div><b>5×5 — expand</b>25 fine regions. Best when the target language preserves the source distinction.</div><div><b>4×4 — bridge</b>The existing 16-state universal bridge remains the fixed middle layer.</div><div><b>3×3 — contract</b>9 broad regions. Useful when the target language lacks a finer equivalent.</div></div>

      <h3>Try a translation</h3>
      <div class="r345toolbar">
        <div class="control"><label>Source sound</label><select id="r345Sound"></select></div>
        <button class="r345action" id="r345Random" type="button">Random sound</button>
        <button class="r345action" id="r345Swap" type="button">⇄ Swap languages</button>
      </div>
      <div class="r345modes" aria-label="resolution mode">
        <button class="r345mode active" data-mode="adaptive" type="button">Adaptive 5→4→3</button>
        <button class="r345mode" data-mode="5" type="button">Force 5×5</button>
        <button class="r345mode" data-mode="4" type="button">Force 4×4</button>
        <button class="r345mode" data-mode="3" type="button">Force 3×3</button>
      </div>
      <div id="resolution345Inventory" class="stats" style="margin-top:16px"></div>
      <div id="resolution345Result" class="panel" style="margin-top:16px">Waiting for PHOIBLE…</div>
      <div id="r345WrittenExample" class="panel" style="margin-top:12px"><span class="small">A real written target-language example will appear here when WikIPA has one.</span></div>

      <h3 style="margin-top:28px">Compare all four strategies for this sound</h3>
      <div id="r345Compare" class="r345compare"></div>

      <h3 style="margin-top:28px">Test the whole source inventory</h3>
      <p class="small">This runs every non-prosodic source phoneme through 5×5, 4×4, 3×3 and adaptive routing. Coverage means the requested layer actually contained a legal target sound. Mean distance is PHOIBLE feature loss among matched sounds; lower is better, but coverage matters too.</p>
      <button id="r345BatchRun" class="btn" type="button">Run inventory-wide comparison</button>
      <div id="r345Batch" class="r345batch panel" style="margin-top:14px">Not run yet.</div>

      <details class="panel" style="margin-top:16px"><summary><b>What would count as evidence?</b></summary><p>The pyramid idea earns support if adaptive contraction gives high target coverage without increasing feature loss, if particular language pairs systematically prefer particular layers, and if those results remain stable across inventories and corpora. A 5×5 win means fine distinctions can be preserved; a 3×3 win means deliberate contraction can outperform a forced fine match. If adaptive routing performs no better than ordinary nearest-neighbour mapping, the pyramid codec should be revised or rejected.</p><p>The capstone still has no assigned linguistic meaning. It remains a placeholder for a higher-order invariant only if the data eventually demands one.</p></details>`;
    const anchor=$('magic')||$('status');
    if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(section,anchor);else document.querySelector('main')?.appendChild(section);
    const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#resolution345"]')){const a=document.createElement('a');a.href='#resolution345';a.textContent='3–4–5 lab';nav.insertBefore(a,nav.querySelector('a[href="#magic"]')||null);}
  }

  // Existing 4×4 classification fixes the broad cell. Residual PHOIBLE features
  // only move the sound inside that cell, preserving all prior work exactly.
  function latentPoint(p){
    const c=classify(p); if(!c||c==='PROSODY')return null;
    const ri=ROWS.indexOf(c[0]),ci=Number(c[1])-1;let dx=0,dy=0;
    if(c[0]==='A'){
      dx=clamp((fnum(p.back)-fnum(p.front))/2,-1,1);
      dy=clamp((fnum(p.low)-fnum(p.high))/2,-1,1);
    }else{
      const lab=fnum(p.labial),cor=fnum(p.coronal),dor=fnum(p.dorsal);
      dx=clamp((dor-lab+.35*(dor-cor))/2,-1,1);
      dy=clamp((fnum(p.continuant)-fnum(p.sonorant)+.35*fnum(p.delayedRelease))/2,-1,1);
    }
    const micro=.42;
    return {x:(ci+.5+micro*dx)/4,y:(ri+.5+micro*dy)/4,cell4:c,dx,dy};
  }
  function qcell(pt,n){if(!pt)return null;const col=Math.min(n-1,Math.floor(clamp(pt.x,0,.999999)*n)),row=Math.min(n-1,Math.floor(clamp(pt.y,0,.999999)*n));return{row,col,id:String.fromCharCode(65+row)+(col+1),index:row*n+col};}
  function sameCellCandidates(source,targetIds,n){const sp=latentPoint(source);if(!sp)return[];const sq=qcell(sp,n);return targetIds.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY').map(p=>({p,pt:latentPoint(p)})).filter(x=>x.pt&&qcell(x.pt,n).index===sq.index).map(x=>({p:x.p,pt:x.pt,...featureDistance(source,x.p)})).sort((a,b)=>a.distance-b.distance);}
  function fixed(source,targetIds,n){const candidates=sameCellCandidates(source,targetIds,n);return{chosen:n,best:candidates[0]||null,evidence:{[n]:candidates},mode:`forced ${n}×${n}`,covered:candidates.length>0};}
  function adaptive(source,targetIds){const levels=[5,4,3],evidence={};for(const n of levels)evidence[n]=sameCellCandidates(source,targetIds,n);const chosen=levels.find(n=>evidence[n].length>0)||null;let best=null,mode='global fallback';if(chosen){best=evidence[chosen][0];mode=chosen===5?'fine direct':chosen===4?'contract 5→4':'contract 5→4→3';}else{const r=nearest(source,targetIds,false).ranked[0];if(r)best={...r,pt:latentPoint(r.p)};}return{chosen,best,evidence,mode,covered:!!chosen};}
  function resultForMode(source,targetIds,mode){return mode==='adaptive'?adaptive(source,targetIds):fixed(source,targetIds,Number(mode));}
  function gridHTML(p){const pt=latentPoint(p);if(!pt)return'';return[5,4,3].map(n=>{const q=qcell(pt,n);return`<div class="r345box"><b>${n}×${n}</b><span>${q.id}</span><small>${n*n} states · ${(n*n)*(n*n)} directed gates</small></div>`}).join('<div class="r345arrow">→</div>');}

  function sourceSounds(){const ids=state.inventorySegments.get($('sourceInventory')?.value)||[];return ids.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY').sort((a,b)=>a.Name.localeCompare(b.Name));}
  function syncSoundPicker(){const sel=$('r345Sound');if(!sel||typeof state==='undefined'||!state.loaded)return;const current=$('sourceSegment')?.value;const ps=sourceSounds();sel.innerHTML=ps.map(p=>`<option value="${html(p.ID)}">/${html(p.Name)}/ · ${html(classify(p))}</option>`).join('');if(ps.some(p=>p.ID===current))sel.value=current;else if(ps[0]){$('sourceSegment').value=ps[0].ID;sel.value=ps[0].ID;}}
  function setSourceById(id){if(!$('sourceSegment'))return;$('sourceSegment').value=id;$('r345Sound').value=id;$('sourceSegment').dispatchEvent(new Event('change',{bubbles:true}));}

  function highlightPyramid(source,target){document.querySelectorAll('.r345sq').forEach(x=>x.classList.remove('src','tgt','both'));const mark=(p,cls)=>{const pt=latentPoint(p);if(!pt)return;[3,4,5].forEach(n=>{const q=qcell(pt,n),el=document.querySelector(`.r345sq[data-n="${n}"][data-i="${q.index}"]`);if(!el)return;if(el.classList.contains(cls==='src'?'tgt':'src'))el.classList.add('both');el.classList.add(cls);});};mark(source,'src');if(target)mark(target,'tgt');}

  function routeText(result){if(currentMode!=='adaptive')return result.covered?`The forced ${result.chosen}×${result.chosen} layer contains a legal target sound.`:`No target sound occupies the same ${result.chosen}×${result.chosen} region. This forced test deliberately returns no match rather than silently changing resolution.`;return result.chosen===5?'The target already has a compatible 5×5 fine-region sound, so maximum detail is preserved.':result.chosen===4?'The 5×5 region is empty, so the codec contracts once to the existing 4×4 bridge.':result.chosen===3?'The 5×5 and 4×4 regions are empty, so the codec contracts to the 3×3 layer before expanding to a real target sound.':'Even the 3×3 region is empty, so adaptive mode falls back to ordinary PHOIBLE feature-nearest matching.';}

  function renderCompare(source,targetIds){const box=$('r345Compare');if(!box)return;const modes=['5','4','3','adaptive'];box.innerHTML=modes.map(m=>{const r=resultForMode(source,targetIds,m),b=r.best;return`<div><b>${m==='adaptive'?'Adaptive':m+'×'+m}</b>${b?`<div class="ipa">/${html(b.p.Name)}/</div><div class="small">distance ${b.distance.toFixed(4)}</div><div class="small">${html(r.mode)}</div>`:`<div class="small warn">no same-region target</div>`}</div>`;}).join('');}

  async function renderWrittenExample(targetSound){const box=$('r345WrittenExample');if(!box)return;const token=++exampleRequest;if(!targetSound){box.innerHTML='<span class="small">No target sound to look up.</span>';return;}const lang=state.languages.get($('targetLanguage')?.value);box.innerHTML=`<span class="small">Looking for a real ${html(lang?.Name||'target-language')} written example containing /${html(targetSound.Name)}/…</span>`;if(typeof fetchWikipaLanguage!=='function'||typeof textVal!=='function'){box.innerHTML=`<b>Output sound:</b> /${html(targetSound.Name)}/ ${typeof audioButton==='function'?audioButton(targetSound.Name):''}<div class="small">Real written-word lookup is unavailable, but the isolated sound can still be heard above.</div>`;return;}try{const rows=await fetchWikipaLanguage(lang);if(token!==exampleRequest)return;const meta=typeof WIKIPA_META!=='undefined'?WIKIPA_META:null;const needle=String(targetSound.Name).normalize('NFC');let hit=null;for(const r of rows){const ipa=meta?textVal(r,meta.ipa):'',word=meta?textVal(r,meta.word):'';if(String(ipa).normalize('NFC').includes(needle)){hit={r,ipa,word,audio:typeof audioUrlFromRow==='function'?audioUrlFromRow(r):null};break;}}if(!hit){box.innerHTML=`<div><b>Output symbol:</b> /${html(targetSound.Name)}/ ${typeof audioButton==='function'?audioButton(targetSound.Name):''}</div><div class="small">No real written WikIPA example containing this exact sound was returned for ${html(lang?.Name||'the target language')}.</div>`;return;}box.innerHTML=`<div class="r345written">${html(hit.word||'written form unavailable')}</div><div><span class="pill">/${html(hit.ipa||targetSound.Name)}/</span> <span class="pill">contains /${html(targetSound.Name)}/</span></div><div style="margin-top:8px">${typeof audioButton==='function'?`Isolated sound ${audioButton(targetSound.Name)}`:''}</div>${hit.audio?`<audio controls preload="none" src="${html(hit.audio)}" style="width:100%;margin-top:10px"></audio>`:'<div class="small" style="margin-top:8px">The dataset row supplied the written word and IPA but no directly playable audio URL.</div>'}`;}catch(e){if(token!==exampleRequest)return;box.innerHTML=`<div><b>Output symbol:</b> /${html(targetSound.Name)}/ ${typeof audioButton==='function'?audioButton(targetSound.Name):''}</div><div class="small">Real-word lookup could not load: ${html(e.message)}</div>`;}}

  function render(){
    if(typeof state==='undefined'||!state.loaded)return;const source=state.parameters.get($('sourceSegment')?.value),targetIds=state.inventorySegments.get($('targetInventory')?.value)||[],out=$('resolution345Result');if(!out||!source)return;
    const result=resultForMode(source,targetIds,currentMode),pt=latentPoint(source);if(!pt){out.innerHTML='<p class="small">This source is prosodic or cannot be projected into the 3–4–5 experiment.</p>';return;}
    const b=result.best,target=b?.p||null;highlightPyramid(source,target);renderCompare(source,targetIds);
    const counts=[5,4,3].map(n=>`${n}×${n}: ${sameCellCandidates(source,targetIds,n).length} candidate${sameCellCandidates(source,targetIds,n).length===1?'':'s'}`).join(' · ');
    const sourceLang=state.languages.get($('sourceLanguage')?.value),targetLang=state.languages.get($('targetLanguage')?.value);
    const output=b?`<div class="r345output"><div class="r345sound"><div class="small">${html(sourceLang?.Name||'Source')}</div><div class="ipa">/${html(source.Name)}/</div>${typeof audioButton==='function'?audioButton(source.Name):''}</div><div class="r345flow">→</div><div class="r345sound"><div class="small">${html(targetLang?.Name||'Target')}</div><div class="ipa">/${html(b.p.Name)}/</div>${typeof audioButton==='function'?audioButton(b.p.Name):''}</div></div>`:`<div class="notice"><b>No output at this forced resolution.</b> Try another layer or Adaptive mode.</div>`;
    out.innerHTML=`<div class="r345levels">${gridHTML(source)}</div>${output}${b?`<div class="corrmeta" style="margin-top:12px"><span class="pill">${html(result.mode)}</span><span class="pill">feature distance ${b.distance.toFixed(4)}</span><span class="pill">source 4×4 ${html(pt.cell4)}</span><span class="pill">target 4×4 ${html(classify(b.p))}</span></div>`:''}<div class="metric"><b>Target candidates by resolution</b><span>${html(counts)}</span></div><p>${html(routeText(result))}</p>`;
    renderWrittenExample(target);
  }

  function renderInventory(){if(typeof state==='undefined'||!state.loaded)return;const targetIds=state.inventorySegments.get($('targetInventory')?.value)||[],ps=targetIds.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY'),box=$('resolution345Inventory');if(!box)return;const cells=n=>new Set(ps.map(p=>qcell(latentPoint(p),n)?.index).filter(x=>x!==undefined)).size;box.innerHTML=`<span><b>${cells(3)}/9</b>3×3 regions used</span><span><b>${cells(4)}/16</b>4×4 regions used</span><span><b>${cells(5)}/25</b>5×5 regions used</span><span><b>${ps.length}</b>target phonemes</span>`;}

  function runBatch(){if(typeof state==='undefined'||!state.loaded)return;const src=sourceSounds(),targetIds=state.inventorySegments.get($('targetInventory')?.value)||[],box=$('r345Batch');if(!box||!src.length)return;const modes=['5','4','3','adaptive'];const rows=modes.map(m=>{let covered=0,dist=0,outputs=0,layer5=0,layer4=0,layer3=0,fallback=0;for(const p of src){const r=resultForMode(p,targetIds,m);if(r.covered)covered++;if(r.best){outputs++;dist+=r.best.distance;}if(m==='adaptive'){if(r.chosen===5)layer5++;else if(r.chosen===4)layer4++;else if(r.chosen===3)layer3++;else fallback++;}}return{m,covered,outputs,mean:outputs?dist/outputs:null,layer5,layer4,layer3,fallback};});const best=rows.filter(x=>x.mean!==null).sort((a,b)=>a.mean-b.mean)[0];box.innerHTML=`<table><thead><tr><th>Strategy</th><th>Same-region coverage</th><th>Outputs</th><th>Mean feature distance</th><th>Adaptive route mix</th></tr></thead><tbody>${rows.map(r=>`<tr><td><b>${r.m==='adaptive'?'Adaptive 5→4→3':r.m+'×'+r.m}</b>${best===r?' <span class="pill good">lowest mean distance</span>':''}</td><td>${r.covered}/${src.length} (${(100*r.covered/src.length).toFixed(1)}%)</td><td>${r.outputs}/${src.length}</td><td>${r.mean===null?'—':r.mean.toFixed(4)}</td><td>${r.m==='adaptive'?`5×5 ${r.layer5} · 4×4 ${r.layer4} · 3×3 ${r.layer3} · fallback ${r.fallback}`:'—'}</td></tr>`).join('')}</tbody></table><p class="small">Interpretation: a useful strategy should combine high coverage with low mean feature distance. “Lowest mean distance” alone is not a win if it only covers a small fraction of the inventory.</p>`;}

  function swapLanguages(){const s=$('sourceLanguage'),t=$('targetLanguage');if(!s||!t)return;const a=s.value,b=t.value;s.value=b;t.value=a;if(typeof updateInventorySelectors==='function')updateInventorySelectors();s.dispatchEvent(new Event('change',{bubbles:true}));t.dispatchEvent(new Event('change',{bubbles:true}));setTimeout(()=>{syncSoundPicker();update();},50);}
  function randomSound(){const ps=sourceSounds();if(!ps.length)return;const p=ps[Math.floor(Math.random()*ps.length)];setSourceById(p.ID);}
  function update(){syncSoundPicker();render();renderInventory();}
  function boot(){installUI();$('r345Sound')?.addEventListener('change',e=>setSourceById(e.target.value));$('r345Random')?.addEventListener('click',randomSound);$('r345Swap')?.addEventListener('click',swapLanguages);$('r345BatchRun')?.addEventListener('click',runBatch);document.querySelectorAll('.r345mode').forEach(btn=>btn.addEventListener('click',()=>{currentMode=btn.dataset.mode;document.querySelectorAll('.r345mode').forEach(x=>x.classList.toggle('active',x===btn));render();}));['sourceSegment','sourceLanguage','sourceInventory','targetLanguage','targetInventory'].forEach(id=>$(id)?.addEventListener('change',()=>setTimeout(update,0)));const t=setInterval(()=>{if(typeof state!=='undefined'&&state.loaded){clearInterval(t);update();}},250);}
  document.addEventListener('DOMContentLoaded',boot);window.phonetic345={latentPoint,qcell,adaptive,fixed,resultForMode,render:update,runBatch};
})();
