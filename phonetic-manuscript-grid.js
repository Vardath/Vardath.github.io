(()=>{
'use strict';
if(window.__VARDATH_MAN_GRID_LOADER_V3__)return;window.__VARDATH_MAN_GRID_LOADER_V3__=true;
function load(src){return new Promise((ok,fail)=>{const s=document.createElement('script');s.src=src;s.defer=true;s.onload=ok;s.onerror=fail;document.head.appendChild(s)})}
load('phonetic-man-grid-engine-core.js?v=20260911-engine3')
 .then(()=>load('phonetic-man-grid-engine-ui.js?v=20260911-sequence2'))
 .then(()=>load('phonetic-man-grid-rebuild-v2.js?v=20260911-sequence2'))
 .then(()=>load('phonetic-man-grid-original-phonetics-exact-v3.js?v=20260911-exactphon1'))
 .then(()=>load('phonetic-man-grid-tests-2-3-exact-v3.js?v=20260911-tests23-1'))
 .then(()=>load('phonetic-man-grid-test5-dictionary.js?v=20260912-test5dict2'))
 .catch(e=>console.error('Man Grid corrected sequence failed to load',e));
})();