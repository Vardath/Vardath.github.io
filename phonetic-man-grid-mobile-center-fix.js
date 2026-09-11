(()=>{
'use strict';
if(window.__VARDATH_MAN_GRID_CENTER_FIX__)return;
window.__VARDATH_MAN_GRID_CENTER_FIX__=true;
function center(){
  const box=document.querySelector('#manuscript-grid .mg-workbench');
  if(!box)return false;
  const max=Math.max(0,box.scrollWidth-box.clientWidth);
  box.scrollLeft=max/2;
  return true;
}
function run(){requestAnimationFrame(()=>{center();setTimeout(center,80);setTimeout(center,300);});}
document.addEventListener('vardath-man-grid-ready',run);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
addEventListener('resize',()=>setTimeout(center,50),{passive:true});
})();
