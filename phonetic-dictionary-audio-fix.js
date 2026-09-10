(()=>{
'use strict';
const clean=s=>String(s||'').trim().replace(/^\/+|\/+$/g,'').normalize('NFC');
const pairs=[['t͡ʃ','ch'],['d͡ʒ','j'],['tʃ','ch'],['dʒ','j'],['aɪ','eye'],['aʊ','ow'],['ɔɪ','oy'],['eɪ','ay'],['oʊ','oh'],['əʊ','oh'],['ɪə','ear'],['eə','air'],['ʊə','oor']];
const p={'ɑ':'ah','ɒ':'o','ɔ':'aw','æ':'a','ə':'uh','ɚ':'er','ɝ':'er','ɛ':'eh','ɜ':'er','ɞ':'uh','ɪ':'ih','i':'ee','ʊ':'oo','u':'oo','ʌ':'uh','e':'eh','o':'oh','ø':'er','œ':'er','y':'ee','ɐ':'uh','ɘ':'uh','ɤ':'uh','ɯ':'oo','ɨ':'ih','ʉ':'oo','ɶ':'a','ʃ':'sh','ʒ':'zh','θ':'th','ð':'th','ŋ':'ng','ɲ':'ny','ɳ':'n','ɴ':'n','ɱ':'m','ç':'hy','x':'kh','χ':'kh','ɣ':'gh','ʁ':'r','ʀ':'r','ɹ':'r','ɾ':'r','ɽ':'r','ɻ':'r','ʎ':'ly','ɬ':'hl','ɮ':'zl','ʋ':'v','β':'v','ɸ':'f','ʂ':'sh','ʐ':'zh','ɕ':'sh','ʑ':'zh','ʔ':'','q':'k','ɢ':'g','ɖ':'d','ʈ':'t','ɟ':'g','c':'k','j':'y','ː':'','ˑ':'','̆':'','̯':'','̃':'','̥':'','̬':'','̩':'','̪':'','̺':'','̻':'','̚':'','ˈ':'','ˌ':'','.':' ','-':' '};
function respell(raw){let s=clean(raw);for(const [a,b] of pairs)s=s.split(a).join(b);let o='';for(const c of s)o+=Object.hasOwn(p,c)?p[c]:c;return o.replace(/[^A-Za-z' ]+/g,' ').replace(/\s+/g,' ').trim()||clean(raw);}
let voice=null;
function pick(){const v=speechSynthesis?.getVoices?.()||[];voice=v.find(x=>/^en-AU$/i.test(x.lang))||v.find(x=>/^en-GB$/i.test(x.lang))||v.find(x=>/^en/i.test(x.lang))||v[0]||null;return voice;}
if(window.speechSynthesis){pick();speechSynthesis.addEventListener?.('voiceschanged',pick);}
function speak(raw,slow){if(!window.speechSynthesis)return;const text=respell(raw);if(!text)return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.rate=slow?.58:.82;u.pitch=.96;u.volume=1;u.voice=voice||pick();speechSynthesis.speak(u);}
function bind(){document.querySelectorAll('#originalLanguageDictionary [data-play],#originalLanguageDictionary [data-slow]').forEach(b=>{if(b.dataset.humanSpeech==='1')return;b.dataset.humanSpeech='1';b.onclick=null;b.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();const raw=b.closest('.oldict-card')?.querySelector('.oldict-word')?.textContent||'';speak(raw,b.hasAttribute('data-slow'));},true);});}
// Dictionary rerenders on search/sort/page changes, so continually replace its legacy
// oscillator click handlers with speech handlers. This touches dictionary buttons only.
const mo=new MutationObserver(bind);mo.observe(document.documentElement,{childList:true,subtree:true});
bind();
document.addEventListener('click',e=>{const b=e.target.closest?.('#originalLanguageDictionary [data-play],#originalLanguageDictionary [data-slow]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();const raw=b.closest('.oldict-card')?.querySelector('.oldict-word')?.textContent||'';speak(raw,b.hasAttribute('data-slow'));},true);
})();
