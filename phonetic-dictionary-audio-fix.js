(()=>{
'use strict';

// Browser TTS engines do not reliably understand raw IPA. Convert the displayed
// reconstructed IPA into a pronunciation-oriented spelling first, then speak
// that spelling. The English gloss is never sent to the speech engine.
const cleanIPA=s=>String(s||'').trim().replace(/^\/+|\/+$/g,'').normalize('NFC');

const multi=[
  ['t͡ʃ','ch'],['d͡ʒ','j'],['tʃ','ch'],['dʒ','j'],['aɪ','eye'],['aʊ','ow'],['ɔɪ','oy'],
  ['eɪ','ay'],['oʊ','oh'],['əʊ','oh'],['ɪə','ear'],['eə','air'],['ʊə','oor']
];
const phone={
  'ɑ':'ah','ɒ':'o','ɔ':'aw','æ':'a','ə':'uh','ɚ':'er','ɝ':'er','ɛ':'eh','ɜ':'er','ɞ':'uh',
  'ɪ':'ih','i':'ee','ʊ':'oo','u':'oo','ʌ':'uh','e':'eh','o':'oh','ø':'er','œ':'er','y':'ee',
  'ɐ':'uh','ɘ':'uh','ɤ':'uh','ɯ':'oo','ɨ':'ih','ʉ':'oo','ɶ':'a',
  'ʃ':'sh','ʒ':'zh','θ':'th','ð':'th','ŋ':'ng','ɲ':'ny','ɳ':'n','ɴ':'n','ɱ':'m',
  'ç':'hy','x':'kh','χ':'kh','ɣ':'gh','ʁ':'r','ʀ':'r','ɹ':'r','ɾ':'r','ɽ':'r','ɻ':'r',
  'ʎ':'ly','ɬ':'hl','ɮ':'zl','ʋ':'v','β':'v','ɸ':'f','ʂ':'sh','ʐ':'zh','ɕ':'sh','ʑ':'zh',
  'ʔ':'','q':'k','ɢ':'g','ɖ':'d','ʈ':'t','ɟ':'g','c':'k','j':'y','w':'w',
  'ː':'','ˑ':'','̆':'','̯':'','̃':'','̥':'','̬':'','̩':'','̪':'','̺':'','̻':'','̚':'',
  'ˈ':'','ˌ':'','.':' ','-':' '
};
function respell(raw){
  let s=cleanIPA(raw);
  for(const [a,b] of multi)s=s.split(a).join(b);
  let out='';
  for(const ch of s)out+=Object.prototype.hasOwnProperty.call(phone,ch)?phone[ch]:ch;
  // Separate awkward consonant piles just enough for TTS to articulate them,
  // without replacing the reconstructed form with its English meaning.
  out=out.replace(/[^A-Za-z' ]+/g,' ').replace(/\s+/g,' ').trim();
  return out||cleanIPA(raw);
}

let preferredVoice=null;
function chooseVoice(){
  const ss=window.speechSynthesis;if(!ss)return null;
  const vs=ss.getVoices?.()||[];
  preferredVoice=vs.find(v=>/^en-AU$/i.test(v.lang))||vs.find(v=>/^en-GB$/i.test(v.lang))||vs.find(v=>/^en/i.test(v.lang))||vs[0]||null;
  return preferredVoice;
}
if(window.speechSynthesis){chooseVoice();window.speechSynthesis.addEventListener?.('voiceschanged',chooseVoice);}

function speakWord(word,slow){
  const text=respell(word); if(!text)return;
  const ss=window.speechSynthesis;if(!ss)return;
  ss.cancel();
  const u=new SpeechSynthesisUtterance(text);
  u.rate=slow?0.58:0.82;
  u.pitch=0.96;u.volume=1;
  const v=preferredVoice||chooseVoice();if(v)u.voice=v;
  // A tiny pause after cancel avoids Chromium/Firefox occasionally swallowing
  // the replacement utterance while remaining effectively immediate.
  setTimeout(()=>ss.speak(u),12);
}

document.addEventListener('click',e=>{
  const b=e.target.closest?.('#originalLanguageDictionary [data-play],#originalLanguageDictionary [data-slow]');
  if(!b)return;
  e.preventDefault();e.stopImmediatePropagation();
  const reconstructed=b.closest('.oldict-card')?.querySelector('.oldict-word')?.textContent||'';
  speakWord(reconstructed,b.hasAttribute('data-slow'));
},{capture:true});
})();
