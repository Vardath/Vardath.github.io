(()=>{
'use strict';
if(window.__VARDATH_MAN_GRID_LOADER_V3__)return;window.__VARDATH_MAN_GRID_LOADER_V3__=true;
function load(src){return new Promise((ok,fail)=>{const s=document.createElement('script');s.src=src;s.defer=true;s.onload=ok;s.onerror=fail;document.head.appendChild(s)})}
load('phonetic-man-grid-engine-core.js?v=20260911-engine3').then(()=>load('phonetic-man-grid-engine-ui.js?v=20260911-engine3')).catch(e=>console.error('Man Grid engine failed to load',e));
})();