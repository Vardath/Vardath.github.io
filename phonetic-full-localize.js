(()=>{
'use strict';

// Whole-page localization controller for the phonetic experiment.
// The existing wcUiLang selector is the single language control.
// Google Website Translator handles prose/UI; scientific tokens are protected.

const SUPPORTED=['en','de','fr','es','it','pt','nl','sv','no','da','fi','is','pl','cs','uk','ru','el','tr','ar','he','fa','hi','zh','ja','ko','sw','yo'];
const RTL=new Set(['ar','he','fa']);
const GOOGLE_CODE={he:'iw',zh:'zh-CN'};
const FROM_GOOGLE={'iw':'he','zh-CN':'zh','zh-TW':'zh'};
const PROTECT='code,pre,kbd,samp,.formula,.bigipa,.ipa-cloud,.corrsound,.node,.g,.magic-square,.benchmatrix,.featureline,[data-no-translate],[translate="no"]';
let current='en', ready=false, applying=false, mutationTimer=0;

function uiCodeToGoogle(code){return GOOGLE_CODE[code]||code;}
function googleCodeToUi(code){return FROM_GOOGLE[code]||code||'en';}
function savedLanguage(){
  const saved=localStorage.getItem('phoneticUiLang');
  if(SUPPORTED.includes(saved)) return saved;
  const guessed=(navigator.language||'en').toLowerCase().split('-')[0];
  return SUPPORTED.includes(guessed)?guessed:'en';
}
function setDirection(code){
  document.documentElement.lang=code;
  document.documentElement.dir=RTL.has(code)?'rtl':'ltr';
}
function protect(root=document){
  try{
    root.querySelectorAll(PROTECT).forEach(el=>{
      el.classList.add('notranslate');
      el.setAttribute('translate','no');
    });
  }catch(_){ }
}
function addStyle(){
  if(document.getElementById('fullLocaleStyle')) return;
  const s=document.createElement('style');
  s.id='fullLocaleStyle';
  s.textContent=`
    #google_translate_element{position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;clip:rect(0 0 0 0)!important;white-space:nowrap!important;opacity:.001!important;pointer-events:none!important}
    .goog-te-banner-frame.skiptranslate,.goog-te-banner-frame{display:none!important}
    body{top:0!important}
    .skiptranslate iframe{max-height:0!important}
    .wc-wholepage{font-size:.72rem;color:var(--cyan);margin-top:3px}
  `;
  document.head.appendChild(s);
}
function addHiddenWidget(){
  if(document.getElementById('google_translate_element')) return;
  const d=document.createElement('div');d.id='google_translate_element';d.setAttribute('aria-hidden','true');document.body.appendChild(d);
}
function annotateSelector(){
  const wrap=document.querySelector('.wc-locales');
  if(wrap&&!wrap.querySelector('.wc-wholepage')){
    const n=document.createElement('div');n.className='wc-wholepage';n.textContent='Whole page';wrap.appendChild(n);
  }
}
function findCombo(){return document.querySelector('#google_translate_element .goog-te-combo')||document.querySelector('.goog-te-combo');}
function dispatchCombo(code){
  const combo=findCombo(); if(!combo) return false;
  const g=uiCodeToGoogle(code);
  if(combo.value!==g){
    combo.value=g;
    combo.dispatchEvent(new Event('change',{bubbles:true}));
  }
  return true;
}
function clearTranslateCookies(){
  try{
    const domains=['',location.hostname,'.'+location.hostname];
    for(const domain of domains){
      const suffix=domain?`;domain=${domain}`:'';
      document.cookie=`googtrans=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/${suffix}`;
    }
  }catch(_){ }
}
function setLanguage(code,{fromUser=false}={}){
  if(!SUPPORTED.includes(code)) code='en';
  current=code; localStorage.setItem('phoneticUiLang',code); setDirection(code); protect(); annotateSelector();
  const selector=document.getElementById('wcUiLang'); if(selector&&selector.value!==code) selector.value=code;
  if(!ready) return;
  if(code==='en'){
    const combo=findCombo();
    if(combo){
      // The widget normally accepts the source language as a reset target.
      combo.value='en';combo.dispatchEvent(new Event('change',{bubbles:true}));
      // If Google leaves a translated cookie behind, clear it for the next load.
      clearTranslateCookies();
    }
  }else{
    applying=true;dispatchCombo(code);setTimeout(()=>{applying=false;protect();setDirection(code);},250);
  }
  if(fromUser) history.replaceState(null,'',location.pathname+location.search+location.hash);
}

window.phoneticGoogleTranslateInit=function(){
  try{
    new google.translate.TranslateElement({
      pageLanguage:'en',
      includedLanguages:SUPPORTED.filter(x=>x!=='en').map(uiCodeToGoogle).join(','),
      autoDisplay:false,
      multilanguagePage:true,
      layout:google.translate.TranslateElement.InlineLayout.SIMPLE
    },'google_translate_element');
    let tries=0;
    const wait=setInterval(()=>{
      tries++;
      if(findCombo()){
        clearInterval(wait);ready=true;setLanguage(current);
      }else if(tries>40) clearInterval(wait);
    },125);
  }catch(e){console.warn('Whole-page translator init failed',e);}
};

function loadTranslator(){
  if(window.google?.translate?.TranslateElement){window.phoneticGoogleTranslateInit();return;}
  if(document.getElementById('phoneticGoogleTranslateScript')) return;
  const s=document.createElement('script');
  s.id='phoneticGoogleTranslateScript';
  s.src='https://translate.google.com/translate_a/element.js?cb=phoneticGoogleTranslateInit';
  s.async=true;
  document.head.appendChild(s);
}

function bindSelector(){
  const selector=document.getElementById('wcUiLang');
  if(!selector) return false;
  selector.value=current;
  if(!selector.dataset.fullPageBound){
    selector.dataset.fullPageBound='1';
    selector.addEventListener('change',()=>setLanguage(selector.value,{fromUser:true}),true);
  }
  annotateSelector();return true;
}

function observe(){
  const mo=new MutationObserver(muts=>{
    for(const m of muts){for(const n of m.addedNodes){if(n.nodeType===1) protect(n);}}
    bindSelector();
    if(current!=='en'&&ready&&!applying){
      clearTimeout(mutationTimer);
      mutationTimer=setTimeout(()=>dispatchCombo(current),700);
    }
  });
  mo.observe(document.body,{childList:true,subtree:true});
}

function start(){
  current=savedLanguage();addStyle();addHiddenWidget();protect();setDirection(current);
  let tries=0;const bind=setInterval(()=>{tries++;if(bindSelector()||tries>60)clearInterval(bind);},100);
  observe();loadTranslator();
}

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start,{once:true}); else start();
})();
