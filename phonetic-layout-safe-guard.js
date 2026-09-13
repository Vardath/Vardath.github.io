// Static layout guard for the phonetics page. This deliberately avoids MutationObserver
// so the layout lock cannot create a style/class mutation feedback loop.
(()=>{
  'use strict';
  if(window.__VARDATH_PHONETIC_LAYOUT_GUARD__)return;
  window.__VARDATH_PHONETIC_LAYOUT_GUARD__=true;
  if(document.getElementById('vardath-phonetic-layout-lock'))return;
  const st=document.createElement('style');
  st.id='vardath-phonetic-layout-lock';
  st.textContent=`#originalLanguageDictionary{grid-column:1/-1!important;min-width:0!important;width:auto!important;max-width:none!important;justify-self:stretch!important}#originalLanguageDictionary .oldict-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;min-width:0!important}@media(max-width:700px){#originalLanguageDictionary .oldict-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}@media(max-width:430px){#originalLanguageDictionary .oldict-grid{grid-template-columns:1fr!important}}`;
  document.head.appendChild(st);

  // Additive evidence/presentation section for the completed 3×3→21×21 test.
  // Kept as a separate script so it cannot change the established bridge or test engines.
  if(!document.querySelector('script[data-vardath-square-sequence]')){
    const seq=document.createElement('script');
    seq.defer=true;
    seq.dataset.vardathSquareSequence='1';
    seq.src='phonetic-square-sequence-section.js?v=20260913-sequence1';
    document.head.appendChild(seq);
  }
})();