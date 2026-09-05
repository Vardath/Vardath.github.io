// Keep the phonetic experiment at the top on initial load while preserving explicit nav-link scrolling.
(()=>{
  'use strict';
  try{ if('scrollRestoration' in history) history.scrollRestoration='manual'; }catch(_){ }
  document.documentElement.style.overflowAnchor='none';
  if(document.body) document.body.style.overflowAnchor='none';

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

  // Browser-native full-dataset 3×3 → 4×4 → 5×5 ordered-symbol / phonetic / magic-square experiment.
  const lab=document.createElement('script');
  lab.src='phonetic-345-magic-page.js?v=20260906-full348-1';
  lab.defer=true; document.head.appendChild(lab);

  if(location.hash){ try{ history.replaceState(null,'',location.pathname+location.search); }catch(_){ } }
  let userNavigated=false;
  addEventListener('click',e=>{ const a=e.target.closest?.('a[href^="#"]'); if(a) userNavigated=true; },{capture:true});
  const top=()=>{ if(userNavigated)return; requestAnimationFrame(()=>scrollTo({top:0,left:0,behavior:'auto'})); };
  top();
  addEventListener('DOMContentLoaded',top,{once:true});
  addEventListener('load',()=>{ top(); setTimeout(top,120); setTimeout(top,500); },{once:true});
  addEventListener('pageshow',e=>{ if(e.persisted) top(); });
})();