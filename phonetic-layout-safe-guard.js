// Static layout guard for the phonetics page. This deliberately avoids MutationObserver
// so the layout lock cannot create a style/class mutation feedback loop.
(()=>{
  'use strict';
  if(window.__VARDATH_PHONETIC_LAYOUT_GUARD__)return;
  window.__VARDATH_PHONETIC_LAYOUT_GUARD__=true;
  if(document.getElementById('vardath-phonetic-layout-lock'))return;
  const st=document.createElement('style');
  st.id='vardath-phonetic-layout-lock';
  st.textContent=`#originalLanguageDictionary{grid-column:1/-1!important;min-width:0!important;width:auto!important;max-width:none!important;justify-self:stretch!important}#originalLanguageDictionary .oldict-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;min-width:0!important}.vardath-site-nav{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.vardath-site-nav a{color:var(--muted);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:5px 9px;background:#151925;font-size:.82rem}.vardath-site-nav a:hover{color:var(--cyan);border-color:var(--cyan)}.vardath-site-nav.bottom{justify-content:center;margin:22px auto 0}@media(max-width:700px){#originalLanguageDictionary .oldict-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}.wrap.top{align-items:flex-start}.vardath-site-nav{max-width:72%}}@media(max-width:430px){#originalLanguageDictionary .oldict-grid{grid-template-columns:1fr!important}.vardath-site-nav{max-width:none}}`;
  document.head.appendChild(st);

  // Keep the four public Vardath pages cross-linked without restructuring the research page.
  const top=document.querySelector('.wrap.top');
  if(top&&!document.getElementById('vardath-site-nav')){
    const oldBack=top.querySelector('.back');
    if(oldBack)oldBack.remove();
    const nav=document.createElement('nav');
    nav.id='vardath-site-nav';
    nav.className='vardath-site-nav';
    nav.innerHTML='<a href="index.html">Home</a><a href="vardath-cosmology.html">Cosmology</a><a href="phonetic-bridge.html">Phonetic Bridge</a><a href="art.html">Art Archive</a>';
    top.appendChild(nav);
  }
  const footer=document.querySelector('footer');
  if(footer&&!document.getElementById('vardath-site-nav-bottom')){
    const nav=document.createElement('nav');
    nav.id='vardath-site-nav-bottom';
    nav.className='vardath-site-nav bottom';
    nav.innerHTML='<a href="index.html">Home</a><a href="vardath-cosmology.html">Cosmology</a><a href="phonetic-bridge.html">Phonetic Bridge</a><a href="art.html">Art Archive</a>';
    footer.parentNode.insertBefore(nav,footer);
  }

  // Additive evidence/presentation section for the completed 3×3→21×21 test.
  // Kept as a separate script so it cannot change the established bridge or test engines.
  if(!document.querySelector('script[data-vardath-square-sequence]')){
    const seq=document.createElement('script');
    seq.defer=true;
    seq.dataset.vardathSquareSequence='1';
    seq.src='phonetic-square-sequence-section.js?v=20260920-linked1';
    document.head.appendChild(seq);
  }

  // Follow-up presentation for the 20-fold held-out feature-birth test.
  // It waits for the successive-grid section, then inserts directly after it.
  if(!document.querySelector('script[data-vardath-feature-birth]')){
    const fb=document.createElement('script');
    fb.defer=true;
    fb.dataset.vardathFeatureBirth='1';
    fb.src='phonetic-feature-birth-section.js?v=20260913-birth1';
    document.head.appendChild(fb);
  }
})();