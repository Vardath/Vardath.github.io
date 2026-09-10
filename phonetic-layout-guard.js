(()=>{
'use strict';
if(window.__VARDATH_PHONETIC_LAYOUT_GUARD__) return;
window.__VARDATH_PHONETIC_LAYOUT_GUARD__=true;

function enforce(){
  const dict=document.getElementById('originalLanguageDictionary');
  if(dict){
    dict.style.setProperty('grid-column','1 / -1','important');
    dict.style.setProperty('min-width','0','important');
    dict.style.setProperty('width','auto','important');
    dict.style.setProperty('max-width','none','important');
    dict.style.setProperty('justify-self','stretch','important');
  }
  document.querySelectorAll('#originalLanguageDictionary .oldict-grid').forEach(grid=>{
    const w=window.innerWidth;
    const cols=w<=430?1:(w<=700?2:4);
    grid.style.setProperty('grid-template-columns',`repeat(${cols},minmax(0,1fr))`,'important');
    grid.style.setProperty('width','100%','important');
    grid.style.setProperty('min-width','0','important');
  });
}

const style=document.createElement('style');
style.id='vardath-phonetic-layout-lock';
style.textContent=`
#originalLanguageDictionary{grid-column:1/-1!important;min-width:0!important;width:auto!important;max-width:none!important;justify-self:stretch!important}
#originalLanguageDictionary .oldict-grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;min-width:0!important}
@media(max-width:700px){#originalLanguageDictionary .oldict-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:430px){#originalLanguageDictionary .oldict-grid{grid-template-columns:1fr!important}}
`;
document.head.appendChild(style);

const mo=new MutationObserver(enforce);
mo.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['style','class']});
addEventListener('resize',enforce,{passive:true});
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enforce,{once:true});
enforce();
})();
