(()=>{
'use strict';
const cleanWord=s=>String(s||'').trim().replace(/^\/+|\/+$/g,'').replace(/[ˈˌ.]/g,'').trim();
function speakWord(word,slow){
  const text=cleanWord(word);
  if(!text)return;
  const ss=window.speechSynthesis;
  if(!ss){return;}
  ss.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.rate=slow?0.62:0.92;
  u.pitch=1;
  u.volume=1;
  ss.speak(u);
}
// Capture before the dictionary's old WebAudio click handlers. This prevents
// the old abstract gate-tone synthesis from firing and removes its startup lag.
document.addEventListener('click',e=>{
  const b=e.target.closest?.('#originalLanguageDictionary [data-play],#originalLanguageDictionary [data-slow]');
  if(!b)return;
  e.preventDefault();
  e.stopImmediatePropagation();
  const card=b.closest('.oldict-card');
  const reconstructed=card?.querySelector('.oldict-word')?.textContent||'';
  speakWord(reconstructed,b.hasAttribute('data-slow'));
},{capture:true});
})();
