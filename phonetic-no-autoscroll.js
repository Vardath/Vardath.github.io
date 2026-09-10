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
  od.src='phonetic-original-language-dictionary.js?v=20260910-grid4col16';
  od.defer=true; document.head.appendChild(od);

  if(location.hash){ try{ history.replaceState(null,'',location.pathname+location.search); }catch(_){ } }
  let userNavigated=false;
  addEventListener('click',e=>{ const a=e.target.closest?.('a[href^="#"]'); if(a) userNavigated=true; },{capture:true});
  const top=()=>{ if(userNavigated)return; requestAnimationFrame(()=>scrollTo({top:0,left:0,behavior:'auto'})); };
  top();
  addEventListener('DOMContentLoaded',top,{once:true});
  addEventListener('load',()=>{ top(); setTimeout(top,120); setTimeout(top,500); },{once:true});
  addEventListener('pageshow',e=>{ if(e.persisted) top(); });
})();