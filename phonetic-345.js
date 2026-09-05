// Experimental 3–4–5 adaptive resolution codec.
// This file is additive: it does not alter the established 4×4 classifier.
(function(){
  const $=id=>document.getElementById(id);
  const ROWS=['A','B','C','D'];
  const CELL4=['A1','A2','A3','A4','B1','B2','B3','B4','C1','C2','C3','C4','D1','D2','D3','D4'];
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const html=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  // The existing 4×4 cell is the invariant anchor. Residual PHOIBLE features
  // create a small within-cell offset, never large enough to change the 4×4 cell.
  function latentPoint(p){
    const c=classify(p); if(!c||c==='PROSODY')return null;
    const ri=ROWS.indexOf(c[0]), ci=Number(c[1])-1;
    let dx=0,dy=0;
    if(c[0]==='A'){
      dx=clamp((fnum(p.back)-fnum(p.front))/2,-1,1);
      dy=clamp((fnum(p.low)-fnum(p.high))/2,-1,1);
    }else{
      const lab=fnum(p.labial),cor=fnum(p.coronal),dor=fnum(p.dorsal);
      // Fine place residual: front/labial negative, dorsal/deep positive.
      dx=clamp((dor-lab + .35*(dor-cor))/2,-1,1);
      // Fine manner residual inside B/C/D using continuous feature detail.
      dy=clamp((fnum(p.continuant)-fnum(p.sonorant)+.35*fnum(p.delayedRelease))/2,-1,1);
    }
    const micro=.42; // stays inside the original 4×4 cell
    return {x:(ci+.5+micro*dx)/4,y:(ri+.5+micro*dy)/4,cell4:c,dx,dy};
  }
  function qcell(pt,n){
    if(!pt)return null;
    const col=Math.min(n-1,Math.floor(clamp(pt.x,0,.999999)*n));
    const row=Math.min(n-1,Math.floor(clamp(pt.y,0,.999999)*n));
    return {row,col,id:String.fromCharCode(65+row)+(col+1),index:row*n+col};
  }
  function sameCellCandidates(source,targetIds,n){
    const sp=latentPoint(source); if(!sp)return [];
    const sq=qcell(sp,n);
    return targetIds.map(id=>state.parameters.get(id)).filter(Boolean)
      .filter(p=>classify(p)!=='PROSODY')
      .map(p=>({p,pt:latentPoint(p)})).filter(x=>x.pt&&qcell(x.pt,n).index===sq.index)
      .map(x=>({p:x.p,pt:x.pt,...featureDistance(source,x.p)}))
      .sort((a,b)=>a.distance-b.distance);
  }
  function adaptive(source,targetIds){
    const levels=[5,4,3];
    const evidence={};
    for(const n of levels)evidence[n]=sameCellCandidates(source,targetIds,n);
    let chosen=levels.find(n=>evidence[n].length>0)||null;
    let best=null,mode='global fallback';
    if(chosen){best=evidence[chosen][0];mode=chosen===5?'fine direct':chosen===4?'contract once':'contract twice';}
    else{const r=nearest(source,targetIds,false).ranked[0];if(r)best={...r,pt:latentPoint(r.p)};}
    return {chosen,best,evidence,mode};
  }
  function gridHTML(p){
    const pt=latentPoint(p); if(!pt)return '';
    return [3,4,5].map(n=>{const q=qcell(pt,n);return `<div class="r345box"><b>${n}×${n}</b><span>${q.id}</span><small>${n*n} states · ${n*n*n*n} directed gates</small></div>`}).join('<div class="r345arrow">↔</div>');
  }
  function render(){
    if(typeof state==='undefined'||!state.loaded)return;
    const sid=$('sourceSegment')?.value,tid=$('targetInventory')?.value;
    const source=state.parameters.get(sid),targetIds=state.inventorySegments.get(tid)||[];
    const out=$('resolution345Result'); if(!out||!source)return;
    const result=adaptive(source,targetIds),pt=latentPoint(source);
    if(!pt){out.innerHTML='<p class="small">This source is prosodic or cannot be projected into the 3–4–5 experiment.</p>';return;}
    const counts=[5,4,3].map(n=>`${n}×${n}: ${result.evidence[n].length} target sound${result.evidence[n].length===1?'':'s'}`).join(' · ');
    let route='';
    if(result.chosen===5)route='5×5 fine region already contains a target sound: no contraction required.';
    else if(result.chosen===4)route='5×5 was empty in the target inventory, so the codec contracts to the existing 4×4 bridge, then resolves to the nearest real target sound inside that region.';
    else if(result.chosen===3)route='Neither the 5×5 nor 4×4 region exists in the target inventory. The codec contracts to the broader 3×3 region, then expands back to the nearest real target sound represented there.';
    else route='No target sound shares even the 3×3 coarse region, so the codec falls back to ordinary PHOIBLE feature-nearest matching.';
    const b=result.best;
    const targetPart=b?`<div class="r345target"><div><span class="bigipa">/${html(source.Name)}/</span> <span class="r345flow">→</span> <span class="bigipa">/${html(b.p.Name)}/</span></div><div class="corrmeta"><span class="pill">${html(result.mode)}</span><span class="pill">feature distance ${b.distance.toFixed(4)}</span><span class="pill">source 4×4 ${html(pt.cell4)}</span><span class="pill">target 4×4 ${html(classify(b.p))}</span></div>${typeof audioButton==='function'?`<div class="small">Source ${audioButton(source.Name)} &nbsp; Target ${audioButton(b.p.Name)}</div>`:''}</div>`:'<p>No target candidate.</p>';
    out.innerHTML=`<div class="r345levels">${gridHTML(source)}</div>${targetPart}<div class="metric"><b>Target occupancy by resolution</b><span>${html(counts)}</span></div><p>${html(route)}</p><details><summary>How the adaptive codec decides</summary><p>The same PHOIBLE feature vector is projected into one latent point. The current 4×4 classifier fixes its broad cell; residual features only provide within-cell position. The codec tests the target inventory at 5×5 first, then 4×4, then 3×3. It contracts only as far as necessary to find a legal target region, then chooses the closest real target phoneme by full PHOIBLE feature distance. This makes contraction a controlled loss of distinction rather than an arbitrary substitution.</p></details>`;
  }
  function renderSelectedInventorySummary(){
    if(typeof state==='undefined'||!state.loaded)return;
    const targetIds=state.inventorySegments.get($('targetInventory')?.value)||[];
    const ps=targetIds.map(id=>state.parameters.get(id)).filter(Boolean).filter(p=>classify(p)!=='PROSODY');
    const box=$('resolution345Inventory');if(!box)return;
    const cells=n=>new Set(ps.map(p=>qcell(latentPoint(p),n)?.index).filter(x=>x!==undefined)).size;
    box.innerHTML=`<span><b>${cells(3)}/9</b>3×3 regions used</span><span><b>${cells(4)}/16</b>4×4 regions used</span><span><b>${cells(5)}/25</b>5×5 regions used</span><span><b>${ps.length}</b>target phonemes</span>`;
  }
  function update(){render();renderSelectedInventorySummary();}
  function boot(){
    ['sourceSegment','sourceLanguage','sourceInventory','targetLanguage','targetInventory'].forEach(id=>$(id)?.addEventListener('change',()=>setTimeout(update,0)));
    const t=setInterval(()=>{if(typeof state!=='undefined'&&state.loaded){clearInterval(t);update();}},250);
  }
  document.addEventListener('DOMContentLoaded',boot);
  window.phonetic345={latentPoint,qcell,adaptive,render:update};
})();
