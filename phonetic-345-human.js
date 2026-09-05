// Human-facing presentation layer for the 3–4–5 phonetic pyramid.
// Presentation only: does not alter classifier, matching, benchmark, or codec maths.
(function(){
  const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));

  function installStyles(){
    if(document.getElementById('r345HumanStyles'))return;
    const st=document.createElement('style');st.id='r345HumanStyles';st.textContent=`
      .r345-human-intro{max-width:820px;margin:18px auto 22px;padding:16px 18px;border:1px solid #355066;border-radius:14px;background:linear-gradient(180deg,#111925,#0d131d);text-align:left}
      .r345-human-intro h3{margin:0 0 8px;color:#eef1f8}.r345-human-intro p{margin:6px 0;color:#b8c1d4}.r345-human-steps{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:13px}.r345-human-step{padding:12px;border:1px solid #303a50;border-radius:10px;background:#0e141e}.r345-human-step b{display:block;color:#5ce1e6;margin-bottom:4px}.r345-human-step strong{color:#fff}
      .r345-no-cap{margin:4px 0 8px;color:#aab1c5;font-size:.84rem;text-align:center}.r345-no-cap b{color:#ffd37a}
      .r345-layer-label{width:100%;text-align:center;margin:9px 0 3px}.r345-layer-label b{display:block;color:#eef1f8;font-size:.98rem}.r345-layer-label span{color:#9da6bf;font-size:.8rem}.r345-layer-label .purpose{color:#5ce1e6}
      .r345sq{font-size:.82rem!important;font-weight:700;cursor:default}.r345sq.src::after,.r345sq.tgt::after,.r345sq.both::after{display:none!important}
      .r345legend{justify-content:center;margin-top:12px}.r345legend span{padding:5px 9px;border:1px solid #30384d;border-radius:999px;background:#10151e}.r345formula{max-width:820px;margin:17px auto!important;padding:12px 14px;border:1px solid #30384d;border-radius:10px;background:#0e141d;font-family:Arial,Helvetica,sans-serif!important;line-height:1.45}.r345formula b{color:#5ce1e6}
      .r345-route-help{margin:12px 0 0;padding:11px 13px;border-left:3px solid #5ce1e6;border-radius:7px;background:#0e141e;color:#bfc7d9}.r345-route-help b{color:#fff}
      @media(max-width:760px){.r345-human-steps{grid-template-columns:1fr}}
    `;document.head.appendChild(st);
  }

  function labelFor(n){
    if(n===3)return {title:'Broad sound families',purpose:'Most compressed view',desc:'9 broad regions — useful when two languages do not share the same fine distinction.'};
    if(n===4)return {title:'Translation bridge',purpose:'Middle working layer',desc:'16 bridge regions — the existing universal 4×4 phonetic map.'};
    return {title:'Fine sound detail',purpose:'Most detailed view',desc:'25 fine regions — preserves more detail when the target language supports it.'};
  }

  function humanize(){
    const section=document.getElementById('resolution345');if(!section)return false;
    installStyles();

    const lead=section.querySelector('.lead');
    if(lead)lead.textContent='The same sound can be viewed at three levels of detail. The pyramid lets you test whether translation works better by keeping fine detail, using the middle bridge, or temporarily grouping the sound into a broader family.';

    const notice=section.querySelector('.notice');
    if(notice)notice.innerHTML='<b>What this is testing:</b> some languages distinguish sounds that other languages merge together. The pyramid asks whether we can translate the sound more faithfully by changing resolution only when needed.';

    const pyr=section.querySelector('.r345pyramid');
    if(pyr&&!section.querySelector('.r345-human-intro')){
      const intro=document.createElement('div');intro.className='r345-human-intro';intro.innerHTML=`
        <h3>How to read the pyramid</h3>
        <p>Think of this as the <b>same phonetic space at three zoom levels</b>, not three different alphabets. A highlighted square shows where the selected sound sits at that level.</p>
        <div class="r345-human-steps">
          <div class="r345-human-step"><b>3×3 · zoomed out</b><strong>Broad sound family</strong><br><span class="small">Use when the target language lacks the exact fine distinction.</span></div>
          <div class="r345-human-step"><b>4×4 · middle</b><strong>Translation bridge</strong><br><span class="small">Our existing 16-state bridge between languages.</span></div>
          <div class="r345-human-step"><b>5×5 · zoomed in</b><strong>Fine sound detail</strong><br><span class="small">Use when both languages preserve the finer distinction.</span></div>
        </div>`;
      pyr.insertAdjacentElement('beforebegin',intro);
    }

    const cap=section.querySelector('.r345cap');
    if(cap){
      const note=document.createElement('div');note.className='r345-no-cap';note.innerHTML='<b>No capstone is assigned.</b> The current model stops at the three tested layers.';
      cap.replaceWith(note);
    }

    [3,4,5].forEach(n=>{
      const tier=section.querySelector('.r345tier'+n);if(!tier)return;
      if(!tier.previousElementSibling?.classList?.contains('r345-layer-label')){
        const d=labelFor(n),lab=document.createElement('div');lab.className='r345-layer-label';lab.innerHTML=`<b>${d.title} · ${n}×${n}</b><span class="purpose">${d.purpose}</span><br><span>${d.desc}</span>`;tier.insertAdjacentElement('beforebegin',lab);
      }
      tier.querySelectorAll('.r345sq').forEach((sq,i)=>{
        sq.textContent=String(i+1);
        const d=labelFor(n);sq.title=`${d.title}: region ${i+1} of ${n*n}. Cyan = source sound; green = target sound.`;
        sq.setAttribute('aria-label',`${d.title}, region ${i+1} of ${n*n}`);
      });
    });

    const legend=section.querySelector('.r345legend');
    if(legend)legend.innerHTML='<span><i class="r345dot src"></i><b>Source sound</b> — where you started</span><span><i class="r345dot tgt"></i><b>Target sound</b> — where the match landed</span>';

    const formula=section.querySelector('.r345formula');
    if(formula)formula.innerHTML='<b>Fine detail 5×5</b> ⇄ <b>Translation bridge 4×4</b> ⇄ <b>Broad sound families 3×3</b><br><span class="small">Adaptive mode starts detailed and only zooms out when the target language has no compatible sound at the finer level.</span>';

    const explain=section.querySelector('.r345explain');
    if(explain)explain.innerHTML='<div><b>5×5 — keep the detail</b>If the target language has a close sound in the same fine region, use it directly.</div><div><b>4×4 — use the bridge</b>If 5×5 is too specific, group the sound into the existing 16-state bridge and try again.</div><div><b>3×3 — broaden the family</b>If the target still has no equivalent, group it more broadly, then choose the closest real target sound from that family.</div>';

    const tryH=[...section.querySelectorAll('h3')].find(x=>x.textContent.trim()==='Try a translation');
    if(tryH&&!tryH.nextElementSibling?.classList?.contains('r345-route-help')){
      const help=document.createElement('div');help.className='r345-route-help';help.innerHTML='<b>Quick test:</b> choose a source sound below, then click <b>Adaptive 5→4→3</b>. Cyan marks the source position and green marks the chosen target. Use the speaker buttons in the result to hear both sounds. Force a layer only when you want to compare that layer directly.';tryH.insertAdjacentElement('afterend',help);
    }

    const modes=section.querySelector('.r345modes');
    if(modes){
      const names={adaptive:'Automatic — use finest match available','5':'Test fine detail only · 5×5','4':'Test bridge only · 4×4','3':'Test broad family only · 3×3'};
      modes.querySelectorAll('.r345mode').forEach(b=>{if(names[b.dataset.mode])b.textContent=names[b.dataset.mode];});
    }

    return true;
  }

  function boot(){
    if(humanize())return;
    const obs=new MutationObserver(()=>{if(humanize())obs.disconnect();});obs.observe(document.body,{childList:true,subtree:true});
    setTimeout(()=>{humanize();obs.disconnect();},5000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();