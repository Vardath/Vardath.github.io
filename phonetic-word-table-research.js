(()=>{
'use strict';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>String(s||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[‐‑‒–—]/g,'-').trim();
const LANG_NAME={en:'English',de:'Deutsch',fr:'Français',es:'Español',it:'Italiano',pt:'Português',nl:'Nederlands',sv:'Svenska',no:'Norsk',da:'Dansk',fi:'Suomi',is:'Íslenska',pl:'Polski',cs:'Čeština',uk:'Українська',ru:'Русский',el:'Ελληνικά',tr:'Türkçe',ar:'العربية',he:'עברית',fa:'فارسی',hi:'हिन्दी',zh:'中文',ja:'日本語',ko:'한국어',sw:'Kiswahili',yo:'Yorùbá',non:'Old Norse',ang:'Old English',gem:'Proto-Germanic',ine:'Proto-Indo-European'};
const VOICE_LANG={en:'en-GB',de:'de-DE',fr:'fr-FR',es:'es-ES',it:'it-IT',pt:'pt-PT',nl:'nl-NL',sv:'sv-SE',no:'nb-NO',da:'da-DK',fi:'fi-FI',is:'is-IS',pl:'pl-PL',cs:'cs-CZ',uk:'uk-UA',ru:'ru-RU',el:'el-GR',tr:'tr-TR',ar:'ar-SA',he:'he-IL',fa:'fa-IR',hi:'hi-IN',zh:'zh-CN',ja:'ja-JP',ko:'ko-KR',sw:'sw-KE',yo:'yo-NG',non:'is-IS',ang:'en-GB',gem:'de-DE',ine:'en-GB'};
const NUM_WORD={zero:0,one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,thirteen:13,fourteen:14,fifteen:15,sixteen:16,seventeen:17,eighteen:18,nineteen:19,twenty:20,ogdoad:8,octo:8,'ogdo-':8};
const STATUS={green:['Established','#80e7a8'],blue:['External / semantic','#7fc9ff'],orange:['Experimental','#ffd37a'],red:['Unsupported','#ff9292']};
let seed=null,pilot=null,numerals=null;

function css(){if($('#wcResearchStyle'))return;const s=document.createElement('style');s.id='wcResearchStyle';s.textContent=`
.wc-hear{border:1px solid #46526b;background:#121824;color:#eef1f8;border-radius:9px;padding:6px 9px;cursor:pointer;white-space:nowrap}.wc-hear:hover{border-color:#5ce1e6}.wc-research-row{background:#0d151d}.wc-evidence{display:inline-block;margin-left:6px;padding:2px 7px;border-radius:999px;border:1px solid currentColor;font-size:.7rem;white-space:nowrap}.wc-research-label td{padding:8px 13px!important;background:#0b1119;color:#aab1c5;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}.wc-mini{font-size:.76rem;color:#aab1c5}.wc-score{font-family:Consolas,monospace;color:#5ce1e6}@media(max-width:600px){.wc-table th:nth-child(4),.wc-table td:nth-child(4){display:none}.wc-hear{padding:6px 7px}}
`;document.head.appendChild(s);}

async function load(){try{const [a,b,c]=await Promise.all([
 fetch('data/phonetic-word-explorer-seed.json?v=20260905-wordexplorer1').then(r=>r.ok?r.json():null),
 fetch('data/word-transmission-pilot.json?v=20260905-word1').then(r=>r.ok?r.json():null),
 fetch('data/phonetic-numeral-sounds.json?v=20260905-num1').then(r=>r.ok?r.json():null)
]);seed=a;pilot=b;numerals=c;}catch(e){console.warn('word-table research data',e);}}

function speak(word,lang){if(!('speechSynthesis' in window))return;const u=new SpeechSynthesisUtterance(word.replace(/^\*/,'').replace(/\//g,''));u.lang=VOICE_LANG[lang]||lang||'en-US';const voices=speechSynthesis.getVoices();const base=u.lang.toLowerCase().split('-')[0];const v=voices.find(x=>x.lang.toLowerCase()===u.lang.toLowerCase())||voices.find(x=>x.lang.toLowerCase().startsWith(base));if(v)u.voice=v;speechSynthesis.cancel();speechSynthesis.speak(u);}
function hearButton(word,lang){const b=document.createElement('button');b.className='wc-hear';b.type='button';b.textContent='🔊 Hear';b.title=`Hear ${word}`;b.onclick=()=>speak(word,lang);return b;}

function wikiFor(word,lang){const clean=word.replace(/^\*/,'').trim();const modern=/^[a-z]{2}$/.test(lang||'')?lang:'en';if(['ine','gem','ang','non'].includes(lang)||word.startsWith('*'))return `https://en.wiktionary.org/wiki/${encodeURIComponent(word)}`;return `https://${modern}.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(clean)}`;}
function langFromWord(w){const s=norm(w.language);if(s.includes('yoruba'))return'yo';if(s.includes('old norse'))return'non';if(s.includes('old english'))return'ang';if(s.includes('proto-germanic'))return'gem';if(s.includes('proto-indo-european'))return'ine';if(s.includes('greek'))return'el';if(s.includes('english'))return'en';return'en';}

function addHearColumn(table){if(!table||table.dataset.hearDone)return;table.dataset.hearDone='1';const hr=table.tHead?.rows?.[0];if(hr){const th=document.createElement('th');th.textContent='Hear';hr.appendChild(th);} [...(table.tBodies[0]?.rows||[])].forEach(row=>addHearCell(row));}
function addHearCell(row){if(row.querySelector('.wc-hear'))return;const badge=row.querySelector('.wc-badge');const lang=badge?.textContent.trim()||row.dataset.lang||'en';const word=row.querySelector('.wc-word')?.textContent.trim()||row.dataset.word||'';const td=document.createElement('td');if(word)td.appendChild(hearButton(word,lang));row.appendChild(td);}

function numberFromQuery(q){const n=Number(q);if(Number.isInteger(n)&&n>=0&&n<=20)return n;return NUM_WORD[norm(q)]??null;}
function selectedCore(){return $('#wcTargetSet')?.value!=='all';}
function existingKeys(tbody){return new Set([...tbody.rows].map(r=>`${norm(r.querySelector('.wc-word')?.textContent)}|${r.querySelector('.wc-badge')?.textContent.trim()||r.dataset.lang||''}`));}
function relationClass(status){const [label,color]=STATUS[status]||STATUS.blue;return `<span class="wc-evidence" style="color:${color}">${esc(label)}</span>`;}

function researchRelations(q){if(!seed?.words||!seed?.edges)return[];const nq=norm(q);const words=new Map(seed.words.map(w=>[w.id,w]));const hits=seed.words.filter(w=>norm(w.form)===nq||norm(w.form).replace(/^\*/,'')===nq);
 const out=[];for(const h of hits){for(const e of seed.edges.filter(e=>e.from===h.id||e.to===h.id)){const other=words.get(e.from===h.id?e.to:e.from);if(!other)continue;out.push({word:other.form,lang:langFromWord(other),language:other.language,relation:e.label||e.type,status:e.status||'blue',score:e.score??e.phonetic??null});}}
 // Pilot adds calibrated directional candidates/controls even when seed graph is narrower.
 if(pilot){for(const e of [...(pilot.positive_controls||[]),...(pilot.candidates||[])]){if(norm(e.from)===nq||norm(e.to)===nq){const word=norm(e.from)===nq?e.to:e.from;const status=(e.status||'').includes('attested')||(e.status||'').includes('morphological')?'green':'orange';out.push({word,lang:guessHistoricalLang(word),language:guessHistoricalName(word),relation:e.verdict||e.status||'word-transmission test',status,score:e.combined??e.phonetic??null});}}}
 return dedupe(out).slice(0,14);
}
function guessHistoricalLang(w){if(/àṣẹ|ṣẹ/i.test(w))return'yo';if(/Æsir|áss/i.test(w))return'non';if(/ansuz|ahtō/i.test(w))return'gem';if(/oḱt/i.test(w))return'ine';if(/eahta/i.test(w))return'ang';if(/okt|ógd|ogdo/i.test(w))return'el';if(/eight/i.test(w))return'en';return'en';}
function guessHistoricalName(w){return LANG_NAME[guessHistoricalLang(w)]||'Historical form';}
function dedupe(arr){const seen=new Set();return arr.filter(x=>{const k=norm(x.word)+'|'+x.lang+'|'+norm(x.relation);if(seen.has(k))return false;seen.add(k);return true;});}

function numeralRows(q){const n=numberFromQuery(q);if(n==null||!numerals?.forms)return[];let a=numerals.forms.filter(x=>x.number===n);if(selectedCore()){const core=new Set(['en','de','fr','es','it','pt','nl','sv','no','da','fi','is','pl','cs','uk','ru','el','tr','ar','he','fa','hi','zh','ja','ko','sw','yo']);a=a.filter(x=>core.has(x.iso));}
 // one form per language id, capped so table stays compact
 const seen=new Set(),out=[];for(const x of a){const k=x.language_id;if(seen.has(k))continue;seen.add(k);out.push({word:x.form,lang:x.iso||'en',language:x.language,relation:`Number ${n} · numeral corpus`,status:'blue',score:null});if(out.length>=24)break;}return out;
}

function appendResearchRows(table,q){const tbody=table?.tBodies?.[0];if(!tbody||tbody.dataset.researchDone===q)return;tbody.dataset.researchDone=q;const keys=existingKeys(tbody);const rows=[...researchRelations(q),...numeralRows(q)];if(!rows.length)return;
 const label=document.createElement('tr');label.className='wc-research-label';const td=document.createElement('td');td.colSpan=5;td.textContent='Research connections · phonetics, etymology, semantics and numeral data';label.appendChild(td);tbody.appendChild(label);
 for(const r of rows){const k=`${norm(r.word)}|${r.lang}`;if(keys.has(k))continue;keys.add(k);const tr=document.createElement('tr');tr.className='wc-research-row';tr.dataset.lang=r.lang;tr.dataset.word=r.word;const score=r.score==null?'':` <span class="wc-score">${Math.round(r.score*100)}%</span>`;const url=wikiFor(r.word,r.lang);tr.innerHTML=`<td class="wc-lang">${esc(r.language||LANG_NAME[r.lang]||r.lang)} <span class="wc-badge">${esc(r.lang)}</span></td><td><a class="wc-word" target="_blank" rel="noopener" href="${esc(url)}">${esc(r.word)}</a></td><td>${esc(r.relation)}${score} ${relationClass(r.status)}</td><td><a target="_blank" rel="noopener" href="${esc(url)}">Wiki ↗</a></td>`;addHearCell(tr);tbody.appendChild(tr);}
}

function enhance(){const table=$('#wcResults .wc-table');if(!table)return;addHearColumn(table);const q=$('#wcInput')?.value.trim()||'';appendResearchRows(table,q);}
function install(){css();load().then(enhance);const out=$('#wcResults');if(out)new MutationObserver(()=>setTimeout(enhance,0)).observe(out,{childList:true,subtree:true});else{const mo=new MutationObserver(()=>{const x=$('#wcResults');if(x){mo.disconnect();install();}});mo.observe(document.documentElement,{childList:true,subtree:true});}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install();
})();
