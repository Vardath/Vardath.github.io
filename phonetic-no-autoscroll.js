// Keep the phonetic experiment stable on load, lock refreshes to the top, permanently protect the dictionary layout, and keep site navigation available on the bridge itself.
(()=>{
  'use strict';
  const installSiteNav=()=>{
    const top=document.querySelector('.wrap.top');
    if(!top||document.getElementById('vardath-site-nav'))return;
    try{
      top.style.flexWrap='wrap';
      top.style.alignItems='center';
      const brand=top.querySelector('.brand');
      if(brand)brand.textContent='VARDATH · PHONETICS';
      top.querySelectorAll(':scope > a.back').forEach(a=>a.remove());
      const nav=document.createElement('div');
      nav.id='vardath-site-nav';
      nav.innerHTML='<a href="index.html">Vardath Home</a><a href="vardath-cosmology.html">Vardath Cosmology</a><a href="https://paypal.me/vardath" target="_blank" rel="noopener noreferrer">Buy me a coffee if you found any value here</a>';
      top.appendChild(nav);
      if(!document.getElementById('vardath-site-nav-style')){
        const st=document.createElement('style');
        st.id='vardath-site-nav-style';
        st.textContent=`#vardath-site-nav{display:flex;gap:9px;flex-wrap:wrap;justify-content:flex-end;align-items:center;max-width:100%}#vardath-site-nav a{color:#aab1c5;text-decoration:none;border:1px solid #30374c;border-radius:999px;padding:6px 10px;background:#151925;font-size:.85rem}#vardath-site-nav a:hover{color:#5ce1e6;border-color:#5ce1e6}@media(max-width:600px){.wrap.top{justify-content:center!important}.wrap.top>.brand{width:100%;text-align:center}#vardath-site-nav{width:100%;justify-content:center}#vardath-site-nav a{text-align:center}}`;
        document.head.appendChild(st);
      }
    }catch(_){}
  };
  if(document.readyState==='loading')addEventListener('DOMContentLoaded',installSiteNav,{once:true});else installSiteNav();
  try{const me=document.currentScript;document.querySelectorAll('script[src*="phonetic-no-autoscroll.js"]').forEach(s=>{if(s!==me)s.remove();});}catch(_){}
  if(!window.__VARDATH_PHONETIC_LAYOUT_GUARD__){window.__VARDATH_PHONETIC_LAYOUT_GUARD__=true;const st=document.createElement('style');st.id='vardath-phonetic-layout-lock';st.textContent=`#originalLanguageDictionary{grid-column:1/-1!important;min-width:0!important;width:auto!important;max-width:none!important;justify-self:stretch!important}#originalLanguageDictionary .oldict-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;min-width:0!important}@media(max-width:700px){#originalLanguageDictionary .oldict-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}@media(max-width:430px){#originalLanguageDictionary .oldict-grid{grid-template-columns:1fr!important}}`;document.head.appendChild(st);const enforce=()=>{const d=document.getElementById('originalLanguageDictionary');if(d){d.style.setProperty('grid-column','1 / -1','important');d.style.setProperty('min-width','0','important');d.style.setProperty('width','auto','important');d.style.setProperty('max-width','none','important');d.style.setProperty('justify-self','stretch','important');}document.querySelectorAll('#originalLanguageDictionary .oldict-grid').forEach(g=>{const cols=innerWidth<=430?1:(innerWidth<=700?2:4);g.style.setProperty('grid-template-columns',`repeat(${cols},minmax(0,1fr))`,'important');g.style.setProperty('width','100%','important');g.style.setProperty('min-width','0','important');});};new MutationObserver(enforce).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});addEventListener('resize',enforce,{passive:true});addEventListener('DOMContentLoaded',enforce,{once:true});enforce();}
  try{if('scrollRestoration' in history)history.scrollRestoration='manual';}catch(_){}document.documentElement.style.overflowAnchor='none';if(document.body)document.body.style.overflowAnchor='none';try{if(location.hash)history.replaceState(null,'',location.pathname+location.search);}catch(_){}let userNavigated=false;const forceTop=()=>{if(userNavigated)return;window.scrollTo(0,0);};forceTop();requestAnimationFrame(forceTop);addEventListener('DOMContentLoaded',()=>{forceTop();setTimeout(forceTop,0);setTimeout(forceTop,80);},{once:true});addEventListener('load',()=>{forceTop();setTimeout(forceTop,120);setTimeout(forceTop,500);setTimeout(forceTop,1200);},{once:true});addEventListener('pageshow',()=>{forceTop();setTimeout(forceTop,100);});addEventListener('click',e=>{const a=e.target.closest?.('a[href^="#"]');if(a)userNavigated=true;},{capture:true});
  const scripts=[['phonetic-word-connect-localize.js','20260905-connect1'],['phonetic-word-table-research.js','20260905-table2'],['phonetic-full-localize.js','20260905-full1'],['phonetic-validation-status.js','20260905-validation1'],['phonetic-345-magic-page.js','20260906-coordinate2'],['phonetic-holdout-results.js','20260906-holdout1'],['phonetic-coordinate-explainer.js','20260906-explain1'],['phonetic-conclusions-20260906.js','20260906-conclusions1'],['phonetic-historical-drift-conclusions.js','20260911-drift2'],['phonetic-mirror-lab.js','20260909-mirror1'],['phonetic-manuscript-grid.js','20260911-sequence3'],['phonetic-man-grid-mobile-center-fix.js','20260911-center1'],['phonetic-proto-reconstruction.js','20260909-proto2'],['phonetic-proto-audio.js','20260909-audio1'],['phonetic-proto-word-lab.js','20260909-wordproto1'],['phonetic-cross-family-proto.js','20260909-deep1'],['phonetic-original-language-dictionary.js','20260910-fourcol-lock21'],['phonetic-dictionary-audio-fix.js','20260910-wordaudio3'],['phonetic-nearest-current-results.js','20260910-nearest3']];for(const [src,v] of scripts){const s=document.createElement('script');s.src=`${src}?v=${v}`;s.defer=true;document.head.appendChild(s);}
})();