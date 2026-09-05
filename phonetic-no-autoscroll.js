// Keep the phonetic experiment at the top on initial load while preserving explicit nav-link scrolling.
(()=>{
  'use strict';
  try{ if('scrollRestoration' in history) history.scrollRestoration='manual'; }catch(_){ }
  document.documentElement.style.overflowAnchor='none';
  if(document.body) document.body.style.overflowAnchor='none';

  // Remove stale/deep-link hashes on initial page load so the page does not jump automatically.
  // Clicking a navigation link after load still works normally.
  if(location.hash){
    try{ history.replaceState(null,'',location.pathname+location.search); }catch(_){ }
  }

  let userNavigated=false;
  addEventListener('click',e=>{
    const a=e.target.closest?.('a[href^="#"]');
    if(a) userNavigated=true;
  },{capture:true});

  const top=()=>{
    if(userNavigated) return;
    requestAnimationFrame(()=>scrollTo({top:0,left:0,behavior:'auto'}));
  };

  // Counter browser restoration and layout shifts caused by dynamically injected sections.
  top();
  addEventListener('DOMContentLoaded',top,{once:true});
  addEventListener('load',()=>{ top(); setTimeout(top,120); setTimeout(top,500); },{once:true});
  addEventListener('pageshow',e=>{ if(e.persisted) top(); });
})();
