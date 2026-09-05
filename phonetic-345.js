// Experimental 3–4–5 adaptive resolution codec.
// Additive only: it does not alter the established 4×4 classifier or benchmark.
(function(){
  const $=id=>document.getElementById(id);
  const ROWS=['A','B','C','D'];
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function installUI(){
    if($('resolution345'))return;
    const css=document.createElement('style');
    css.textContent=`
      .r345pyramid{display:grid;gap:10px;justify-items:center;margin:24px 0}.r345tier{display:grid;gap:6px;text-align:center}.r345tier5{grid-template-columns:repeat(5,46px)}.r345tier4{grid-template-columns:repeat(4,50px)}.r345tier3{grid-template-columns:repeat(3,56px)}.r345sq{aspect-ratio:1;display:grid;place-items:center;border:1px solid #3a4259;border-radius:7px;background:#111621;color:#9da6bf;font-size:.72rem}.r345cap{width:82px;padding:9px;border:1px dashed #ffd37a;border-radius:9px;text-align:center;color:#ffd37a;background:#17140d}.r345levels{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin:18px 0}.r345box{min-width:160px;text-align:center;padding:15px;border:1px solid #39435c;border-radius:12px;background:linear-gradient(180deg,#191f2d,#11151f)}.r345box b,.r345box span,.r345box small{display:block}.r345box b{color:#5ce1e6}.r345box span{font-size:1.55rem;font-family:Consolas,monospace;margin:4px 0}.r345box small{color:#aab1c5}.r345arrow,.r345flow{color:#5ce1e6;font-size:1.45rem}.r345target{border:1px solid #30384d;border-radius:13px;padding:16px;background:#11151f;margin:14px 0}.r345formula{text-align:center;font-family:Consolas,monospace;color:#5ce1e6;margin:12px 0}.r345explain{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:18px 0}.r345explain>div{border:1px solid #30384d;border-radius:12px;padding:14px;background:#11151f}.r345explain b{display:block;color:#5ce1e6;margin-bottom:5px}@media(max-width:800px){.r345explain{grid-template-columns:1fr}.r345tier5{grid-template-columns:repeat(5,34px)}.r345tier4{grid-template-columns:repeat(4,38px)}.r345tier3{grid-template-columns:repeat(3,42px)}}`;
    document.head.appendChild(css);

    const section=document.createElement('section');
    section.className='section wrap';section.id='resolution345';
    section.innerHTML=`
      <h2>Experimental 3–4–5 Pyramid Codec</h2>
      <p class="lead">A new hypothesis layered on top of the existing bridge: the 5×5, 4×4 and 3×3 grids may be three stacked resolutions of one phonetic space. The geometry is treated as three layers of a pyramid with the capstone deliberately left unresolved.</p>
      <div class="notice"><b>Nothing above this section has been changed.</b> The established 4×4 bridge remains the anchor. This section asks whether translation improves when sounds can contract to a coarser layer and expand again into a target language's available sound inventory.</div>
      <div class="r345pyramid" aria-label="3-4-5 pyramid layers">
        <div class="r345cap">? capstone<br><span class="small">unresolved</span></div>
        <div class="r345tier r345tier3">${Array.from({length:9},(_,i)=>`<div class="r345sq">3.${i+1}</div>`).join('')}</div>
        <div class="r345tier r345tier4">${Array.from({length:16},(_,i)=>`<div class="r345sq">4.${i+1}</div>`).join('')}</div>
        <div class="r345tier r345tier5">${Array.from({length:25},(_,i)=>`<div class="r345sq">5.${i+1}</div>`).join('')}</div>
      </div>
      <div class="r345formula">5×5 fine detail ⇄ 4×4 bridge ⇄ 3×3 coarse structure ⇄ ? capstone</div>
      <div class="r345explain"><div><b>5×5 — expansion layer</b>25 fine regions. Preserve distinctions when the target language supports them.</div><div><b>4×4 — bridge layer</b>The existing 16-state bridge. This remains the fixed middle reference and is not redefined by this experiment.</div><div><b>3×3 — contraction layer</b>9 coarse regions. Merge distinctions only when a target language has no viable finer equivalent.</div></div>
      <h3>Adaptive translation test</h3>
      <p class="small">Uses the source sound and target inventory already selected above. It tries the finest legal target region first. If none exists it contracts 5→4→3, then expands back to the nearest real target phoneme using the full PHOIBLE feature vector.</p>
      <div id="resolution345Inventory" class="stats"></div>
      <div id="resolution345Result" class="panel" style="margin-top:16px">Waiting for PHOIBLE…</div>
      <details class="panel" style="margin-top:16px"><summary><b>Why this could matter for translation</b></summary><p>A language may distinguish sounds that another language collapses together. A direct phoneme-for-phoneme map can therefore fail even when both languages occupy nearby articulatory territory. The pyramid codec models this as controlled resolution change: preserve detail when possible, contract only when necessary, then expand into the target inventory. The hypothesis is useful only if it lowers feature-distance or rerouting cost across real language pairs; if it does not, it should be rejected.</p><p>The capstone is intentionally not assigned a linguistic meaning yet. It is a placeholder for a possible higher-order invariant discovered from data, not a predetermined symbolic answer.</p></details>`;
    const anchor=$('magic')||$('status');
    if(anchor&&anchor.parentNode)anchor.parentNode.insertBefore(section,anchor);else document.querySelector('main')?.appendChild(section);
    const nav=document.querySelector('.nav');if(nav&&!nav.querySelector('a[href="#resolution345"]')){const a=document.createElement('a');a.href='#resolution345';a.textContent='3–4–5 codec';nav.insertBefore(a,nav.querySelector('a[href="#magic"]')||null);}
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
  function adaptive(source,targetIds){const levels=[5,4,3],evidence={};for(const n of levels)evidence[n]=sameCellCandidates(source,targetIds,n);const chosen=levels.find(n=>evidence[n].length>0)||null;let best=null,mode='global fallback';if(chosen){best=evidence[chosen][0];mode=chosen===5?'fine direct':chosen===4?'contract 5→4':'contract 5→4→3';}else{const r=nearest(source,targetIds,false).ranked[0];if(r)best={...r,pt:latentPoint(r.p)};}return{chosen,best,evidence,mode};}
  function gridHTML(p){const pt=latentPoint(p);if(!pt)return'';return[5,4,3].map(n=>{const q=qcell(pt,n);return`<div class="r345box"><b>${n}×${n}</b><span>${q.id}</span><small>${n*n} states · ${(n*n)*(n*n)} directed gates</small></div>`}).join('<div class="r345arrow">→</div>');}
  function render(){
    if(typeof state==='undefined'||!state.loaded)return;const source=state.parameters.get($('sourceSegment')?.value),targetIds=state.inventorySegments.get($('targetInventory')?.value)||[],out=$('resolution345Result');if(!out||!source)return;
    const result=adaptive(source,targetIds),pt=latentPoint(source);if(!pt){out.innerHTML='<p class="small">This source is prosodic or cannot be projected into the 3–4–5 experiment.</p>';return;}
    const counts=[5,4,3].map(n=>`${n}×${n}: ${result.evidence[n].length} target sound${result.evidence[n].length===1?'':'s'}`).join(' · ');
    let route=result.chosen===5?'The target has a compatible 5×5 fine-region sound, so the codec preserves maximum available detail.':result.chosen===4?'The fine 5×5 region is empty in the target, so the codec contracts one layer to the existing 4×4 bridge and resolves there.':result.chosen===3?'The target has no compatible 5×5 or 4×4 sound, so the codec contracts to the broader 3×3 layer before expanding to a real target phoneme.':'Even the 3×3 region is empty, so the codec falls back to ordinary PHOIBLE feature-nearest matching.';
    const b=result.best,targetPart=b?`<div class="r345target"><div><span class="bigipa">/${html(source.Name)}/</span> <span class="r345flow">→</span> <span class="bigipa">/${html(b.p.Name)}/</span></div><div class="corrmeta"><span class="pill">${html(result.mode)}</span><span class="pill">feature distance ${b.distance.toFixed(4)}</span><span class="pill">source 4×4 ${html(pt.cell4)}</span><span class="pill">target 4×4 ${html(classify(b.p))}</span></div>${typeof audioButton==='function'?`<div class="small">Source ${audioButton(source.Name)} &nbsp; Target ${audioButton(b.p.Name)}</div>`:''}</div>`:'<p>No target candidate.</p>';
    out.innerHTML=`<div class="r345levels">${gridHTML(source)}</div>${targetPart}<div class="metric"><b>Target occupancy by resolution</b><span>${html(counts)}</span></div><p>${html(route)}</p><details><summary>Decision rule</summary><p>One latent articulatory point is quantized at three resolutions. The 4×4 cell remains fixed by the existing classifier; finer residual features determine only within-cell position. Translation searches 5×5, then 4×4, then 3×3 and stops at the first layer containing a viable target sound. The final target is always a real PHOIBLE phoneme chosen by full feature distance.</p></details>`;
  }
  function renderInventory(){if(typeof state==='undefined'||!state.loaded)return;const targetIds=state.inventorySegments.get($('targetInventory')?.value)||[],ps=targetIds.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY'),box=$('resolution345Inventory');if(!box)return;const cells=n=>new Set(ps.map(p=>qcell(latentPoint(p),n)?.index).filter(x=>x!==undefined)).size;box.innerHTML=`<span><b>${cells(3)}/9</b>3×3 regions used</span><span><b>${cells(4)}/16</b>4×4 regions used</span><span><b>${cells(5)}/25</b>5×5 regions used</span><span><b>${ps.length}</b>target phonemes</span>`;}
  function update(){render();renderInventory();}
  function boot(){installUI();['sourceSegment','sourceLanguage','sourceInventory','targetLanguage','targetInventory'].forEach(id=>$(id)?.addEventListener('change',()=>setTimeout(update,0)));const t=setInterval(()=>{if(typeof state!=='undefined'&&state.loaded){clearInterval(t);update();}},250);}
  document.addEventListener('DOMContentLoaded',boot);window.phonetic345={latentPoint,qcell,adaptive,render:update};
})();
