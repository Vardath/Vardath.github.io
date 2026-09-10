// Keep the phonetic experiment stable on load, lock refreshes to the top, and permanently protect the dictionary layout.
(()=>{
  'use strict';

  try{
    const me=document.currentScript;
    document.querySelectorAll('script[src*="phonetic-no-autoscroll.js"]').forEach(s=>{if(s!==me)s.remove();});
  }catch(_){ }

  if(!window.__VARDATH_PHONETIC_LAYOUT_GUARD__){
    window.__VARDATH_PHONETIC_LAYOUT_GUARD__=true;
    const st=document.createElement('style');
    st.id='vardath-phonetic-layout-lock';
    st.textContent=`
#originalLanguageDictionary{grid-column:1/-1!important;min-width:0!important;width:auto!important;max-width:none!important;justify-self:stretch!important}
#originalLanguageDictionary .oldict-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;min-width:0!important}
@media(max-width:700px){#originalLanguageDictionary .oldict-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:430px){#originalLanguageDictionary .oldict-grid{grid-template-columns:1fr!important}}
`;
    document.head.appendChild(st);
    const enforce=()=>{
      const d=document.getElementById('originalLanguageDictionary');
      if(d){
        d.style.setProperty('grid-column','1 / -1','important');
        d.style.setProperty('min-width','0','important');
        d.style.setProperty('width','auto','important');
        d.style.setProperty('max-width','none','important');
        d.style.setProperty('justify-self','stretch','important');
      }
      document.querySelectorAll('#originalLanguageDictionary .oldict-grid').forEach(g=>{
        const cols=innerWidth<=430?1:(innerWidth<=700?2:4);
        g.style.setProperty('grid-template-columns',`repeat(${cols},minmax(0,1fr))`,'important');
        g.style.setProperty('width','100%','important');
        g.style.setProperty('min-width','0','important');
      });
    };
    new MutationObserver(enforce).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});
    addEventListener('resize',enforce,{passive:true});
    addEventListener('DOMContentLoaded',enforce,{once:true});
    enforce();
  }

  try{ if('scrollRestoration' in history) history.scrollRestoration='manual'; }catch(_){ }
  document.documentElement.style.overflowAnchor='none';
  if(document.body) document.body.style.overflowAnchor='none';

  // Refresh/navigation must always start at the very top. Explicit in-page clicks still work after load.
  try{
    if(location.hash) history.replaceState(null,'',location.pathname+location.search);
  }catch(_){ }
  let userNavigated=false;
  const forceTop=()=>{ if(userNavigated)return; window.scrollTo(0,0); };
  forceTop();
  requestAnimationFrame(forceTop);
  addEventListener('DOMContentLoaded',()=>{forceTop();setTimeout(forceTop,0);setTimeout(forceTop,80);},{once:true});
  addEventListener('load',()=>{forceTop();setTimeout(forceTop,120);setTimeout(forceTop,500);setTimeout(forceTop,1200);},{once:true});
  addEventListener('pageshow',()=>{forceTop();setTimeout(forceTop,100);});
  addEventListener('click',e=>{const a=e.target.closest?.('a[href^="#"]');if(a)userNavigated=true;},{capture:true});

  const wc=document.createElement('script');
  wc.src='phonetic-word-connect-localize.js?v=20260905-connect1';
  wc.defer=true; document.head.appendChild(wc);

  const wr=document.createElement('script');
  wr.src='phonetic-word-table-research.js?v=20260905-table2';
  wr.defer=true; document.head.appendChild(wr);

  const fl=document.createElement('script');
  fl.src='phonetic-full-localize.js?v=20260905-full1';
  fl.defer=true; document.head.appendChild(fl);

  const vs=document.createElement('script');
  vs.src='phonetic-validation-status.js?v=20260905-validation1';
  vs.defer=true; document.head.appendChild(vs);

  const lab=document.createElement('script');
  lab.src='phonetic-345-magic-page.js?v=20260906-coordinate2';
  lab.defer=true; document.head.appendChild(lab);

  const hv=document.createElement('script');
  hv.src='phonetic-holdout-results.js?v=20260906-holdout1';
  hv.defer=true; document.head.appendChild(hv);

  const ex=document.createElement('script');
  ex.src='phonetic-coordinate-explainer.js?v=20260906-explain1';
  ex.defer=true; document.head.appendChild(ex);

  const cc=document.createElement('script');
  cc.src='phonetic-conclusions-20260906.js?v=20260906-conclusions1';
  cc.defer=true; document.head.appendChild(cc);

  const ml=document.createElement('script');
  ml.src='phonetic-mirror-lab.js?v=20260909-mirror1';
  ml.defer=true; document.head.appendChild(ml);

  const mg=document.createElement('script');
  mg.src='phonetic-manuscript-grid.js?v=20260909-grid1';
  mg.defer=true; document.head.appendChild(mg);

  const pr=document.createElement('script');
  pr.src='phonetic-proto-reconstruction.js?v=20260909-proto2';
  pr.defer=true; document.head.appendChild(pr);

  const pa=document.createElement('script');
  pa.src='phonetic-proto-audio.js?v=20260909-audio1';
  pa.defer=true; document.head.appendChild(pa);

  const pw=document.createElement('script');
  pw.src='phonetic-proto-word-lab.js?v=20260909-wordproto1';
  pw.defer=true; document.head.appendChild(pw);

  const dp=document.createElement('script');
  dp.src='phonetic-cross-family-proto.js?v=20260909-deep1';
  dp.defer=true; document.head.appendChild(dp);

  const hp=document.createElement('script');
  hp.src='phonetic-hidden-proto-word.js?v=20260909-hidden2';
  hp.defer=true; document.head.appendChild(hp);

  const od=document.createElement('script');
  od.src='phonetic-original-language-dictionary.js?v=20260910-fourcol-lock20';
  od.defer=true; document.head.appendChild(od);

  const nc=document.createElement('script');
  nc.src='phonetic-nearest-current-results.js?v=20260910-nearest3';
  nc.defer=true; document.head.appendChild(nc);
})();