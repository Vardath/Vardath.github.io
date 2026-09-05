// Page-wide interaction affordances and tutorial for the phonetic bridge.
// Additive only: does not change experiment calculations.
(function(){
  const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
  function addCSS(){
    if($('#phoneticGuideStyles'))return;
    const st=document.createElement('style');st.id='phoneticGuideStyles';st.textContent=`
      :root{--guide:#5ce1e6;--guide2:#8583ff;--guideGlow:rgba(92,225,230,.22)}
      .guidebox{margin:24px auto 8px;padding:18px;border:1px solid #3a5061;border-radius:16px;background:linear-gradient(180deg,rgba(17,25,38,.96),rgba(12,17,27,.96));box-shadow:0 0 0 1px rgba(92,225,230,.05) inset}
      .guidebox h3{margin:0 0 8px}.guidesteps{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}.guidestep{padding:13px;border:1px solid #303a50;border-radius:12px;background:#101621;cursor:pointer;transition:.16s}.guidestep:hover{border-color:var(--guide);transform:translateY(-2px);box-shadow:0 0 18px var(--guideGlow)}.guidestep b{display:block;color:var(--guide);margin-bottom:4px}.guidekey{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.guidechip{display:inline-flex;align-items:center;gap:6px;border:1px solid #3b465f;border-radius:999px;padding:5px 9px;background:#111722;font-size:.8rem;color:#cbd2e3}.guidechip i{width:8px;height:8px;border-radius:50%;background:var(--guide);display:inline-block}.guidechip.result i{background:#80e7a8}.guidechip.audio i{background:#ffd37a}.guidechip.test i{background:#8583ff}
      .interactive-hint{position:relative;box-shadow:0 0 0 1px rgba(92,225,230,.16) inset}.interactive-hint::after{content:attr(data-interact);position:absolute;right:8px;bottom:7px;font-size:.67rem;letter-spacing:.04em;text-transform:uppercase;color:#72edf0;opacity:.78;pointer-events:none}.control select,.btn,button,a[href^="#"],summary,.cell,.g,.bmcell,.r345sq{transition:.15s ease}.control select:hover,.control select:focus,.btn:hover,button:hover,summary:hover,.cell:hover,.g:hover,.bmcell:hover,.r345sq:hover{outline:none;box-shadow:0 0 0 2px rgba(92,225,230,.16),0 0 20px rgba(92,225,230,.12);border-color:#5ce1e6!important}.control select:focus-visible,.btn:focus-visible,button:focus-visible,a:focus-visible,summary:focus-visible,.cell:focus-visible,.g:focus-visible,.bmcell:focus-visible,.r345sq:focus-visible{outline:2px solid #ffd37a;outline-offset:3px}
      .section-guide{margin:10px 0 16px;padding:10px 12px;border-left:3px solid #5ce1e6;background:#0e141e;border-radius:7px;color:#bfc7d9;font-size:.88rem}.section-guide b{color:#eafcff}.result-label{display:inline-block;margin-bottom:8px;border:1px solid #315749;background:#0f1716;color:#80e7a8;border-radius:999px;padding:4px 8px;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}.control-label{display:inline-block;margin-bottom:8px;border:1px solid #36556a;background:#0f161c;color:#5ce1e6;border-radius:999px;padding:4px 8px;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}.audio-label{display:inline-block;margin-bottom:8px;border:1px solid #6a5831;background:#19160f;color:#ffd37a;border-radius:999px;padding:4px 8px;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}
      @media(max-width:900px){.guidesteps{grid-template-columns:1fr 1fr}}@media(max-width:600px){.guidesteps{grid-template-columns:1fr}}
    `;document.head.appendChild(st);
  }
  function sectionHint(id,text){const s=document.getElementById(id);if(!s||s.querySelector('.section-guide'))return;const h=s.querySelector('h2');if(!h)return;const d=document.createElement('div');d.className='section-guide';d.innerHTML=text;h.insertAdjacentElement('afterend',d)}
  function tutorial(){
    if($('#howToUse'))return;const hero=$('.hero');if(!hero)return;
    const box=document.createElement('div');box.id='howToUse';box.className='guidebox';box.innerHTML=`<h3>How to use this page</h3><p class="small">You do not need to understand the maths first. Pick two languages, click or change anything that glows cyan, and listen where a speaker icon appears. The page updates the experiment live.</p><div class="guidesteps"><div class="guidestep" data-jump="#experiment"><b>1 · Pick languages</b>Choose a source language, target language and source phoneme.</div><div class="guidestep" data-jump="#correspondence"><b>2 · Compare sounds</b>See which target sound is closest, why, and hear both sides.</div><div class="guidestep" data-jump="#resolution345"><b>3 · Try the pyramid</b>Force 3×3, 4×4 or 5×5, or let Adaptive mode choose.</div><div class="guidestep" data-jump="#benchmark"><b>4 · Test the theory</b>Use the benchmark and full-inventory tests to compare outcomes rather than relying on one example.</div></div><div class="guidekey"><span class="guidechip"><i></i>interactive control</span><span class="guidechip audio"><i></i>playable audio</span><span class="guidechip test"><i></i>run a test</span><span class="guidechip result"><i></i>result/output</span></div>`;
    hero.appendChild(box);box.querySelectorAll('[data-jump]').forEach(x=>x.addEventListener('click',()=>document.querySelector(x.dataset.jump)?.scrollIntoView({behavior:'smooth',block:'start'})));
  }
  function labelPanels(){
    const exp=$('#experiment .experiment');if(exp&&!exp.querySelector('.control-label'))exp.insertAdjacentHTML('afterbegin','<div class="control-label" style="grid-column:1/-1">Interactive controls — choose languages and source sound</div>');
    const mr=$('#matchResults');if(mr&&!mr.querySelector('.result-label'))mr.insertAdjacentHTML('afterbegin','<span class="result-label">Live result</span> ');
    const cg=$('#correspondenceGrid');if(cg&&!cg.previousElementSibling?.classList?.contains('audio-label'))cg.insertAdjacentHTML('beforebegin','<span class="audio-label">Click 🔊 to hear available sounds</span>');
    const br=$('#benchmarkMatrix');if(br&&!br.previousElementSibling?.classList?.contains('result-label'))br.insertAdjacentHTML('beforebegin','<span class="result-label">Benchmark output — hover cells for gate details</span>');
  }
  function affordances(){
    $$('.control select').forEach(el=>{el.classList.add('interactive-hint');el.dataset.interact='select';el.title=el.title||'Interactive: choose an option'});
    $$('.cell').forEach(el=>{el.classList.add('interactive-hint');el.dataset.interact='click';el.tabIndex=0;el.title=el.title||'Interactive: click this bridge cell'});
    $$('.g').forEach(el=>{el.classList.add('interactive-hint');el.dataset.interact='hover';el.tabIndex=0});
    $$('.bmcell').forEach(el=>{el.classList.add('interactive-hint');el.dataset.interact='hover';el.tabIndex=0});
    $$('button,.btn').forEach(el=>{el.title=el.title||'Interactive button'});
    $$('summary').forEach(el=>{el.title=el.title||'Click to expand explanation'});
  }
  function hints(){
    sectionHint('grid','<b>Try it:</b> change the Overlay menu, then click any of the 16 cells to inspect which real PHOIBLE sounds occupy it.');
    sectionHint('experiment','<b>Start here:</b> choose source language → inventory → phoneme, then choose the target language. The result below updates automatically.');
    sectionHint('correspondence','<b>Listen and inspect:</b> each row is a source sound → target sound. Click 🔊 where available and open “Why this maps this way” for the feature explanation.');
    sectionHint('gates','<b>Explore:</b> the 16×16 matrix represents all 256 directed state transitions. Hover/click cells to inspect individual gates.');
    sectionHint('benchmark','<b>Read this as evidence:</b> brighter/higher-percentage cells are gates shared by more languages. Hover cells for exact prevalence and powers-of-3 information.');
    sectionHint('resolution345','<b>Experiment:</b> pick a sound, switch Adaptive / 5×5 / 4×4 / 3×3, hear the result, then run the whole inventory test to compare average loss and coverage.');
    sectionHint('magic','<b>Run the control:</b> click the 5,000-comparison button. This checks whether the magic-square ordering behaves unusually or just like random orderings.');
  }
  function run(){addCSS();tutorial();hints();labelPanels();affordances();setTimeout(()=>{labelPanels();affordances()},1200);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();