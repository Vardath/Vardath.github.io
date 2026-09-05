(()=>{
'use strict';

const LANGS=[
 ['en','English'],['de','Deutsch'],['fr','Français'],['es','Español'],['it','Italiano'],['pt','Português'],['nl','Nederlands'],['sv','Svenska'],['no','Norsk'],['da','Dansk'],['fi','Suomi'],['is','Íslenska'],['pl','Polski'],['cs','Čeština'],['uk','Українська'],['ru','Русский'],['el','Ελληνικά'],['tr','Türkçe'],['ar','العربية'],['he','עברית'],['fa','فارسی'],['hi','हिन्दी'],['zh','中文'],['ja','日本語'],['ko','한국어'],['sw','Kiswahili'],['yo','Yorùbá']
];
const RTL=new Set(['ar','he','fa']);
const L={
 en:{title:'Word connection explorer',lead:'Type a word or short phrase. The page resolves the concept through Wikipedia, then shows connected forms across languages. Each result links to the matching Wikipedia page.',ph:'Type a word, number, name or concept…',go:'Find connections',ui:'Page language',source:'Input language',targets:'Languages to show',lang:'Language',word:'Connected word',why:'Connection',wiki:'Wikipedia',translation:'Same concept / translation',sourceWord:'Resolved source concept',open:'Open',working:'Finding concept and language links…',none:'No matching Wikipedia concept was found. Try a more specific spelling or phrase.',note:'Wikipedia language links are concept links, not a claim that every title is a literal dictionary translation. Research sections that do not yet have a curated translation remain in English.'},
 de:{title:'Wortverbindungen',lead:'Gib ein Wort oder eine kurze Phrase ein. Die Seite löst den Begriff über Wikipedia auf und zeigt verbundene Formen in anderen Sprachen.',ph:'Wort, Zahl, Name oder Begriff…',go:'Verbindungen finden',ui:'Seitensprache',source:'Eingabesprache',targets:'Sprachen anzeigen',lang:'Sprache',word:'Verbundenes Wort',why:'Verbindung',wiki:'Wikipedia',translation:'Gleicher Begriff / Übersetzung',sourceWord:'Aufgelöster Ausgangsbegriff',open:'Öffnen',working:'Begriff und Sprachlinks werden gesucht…',none:'Kein passender Wikipedia-Begriff gefunden.',note:'Wikipedia-Sprachlinks verbinden Begriffe; sie sind nicht immer wörtliche Wörterbuchübersetzungen.'},
 fr:{title:'Explorateur de mots liés',lead:'Saisissez un mot ou une courte expression. La page résout le concept via Wikipédia puis affiche les formes liées dans plusieurs langues.',ph:'Mot, nombre, nom ou concept…',go:'Trouver les liens',ui:'Langue de la page',source:'Langue de saisie',targets:'Langues à afficher',lang:'Langue',word:'Mot lié',why:'Lien',wiki:'Wikipédia',translation:'Même concept / traduction',sourceWord:'Concept source résolu',open:'Ouvrir',working:'Recherche du concept et des liens linguistiques…',none:'Aucun concept Wikipédia correspondant.',note:'Les liens interlangues de Wikipédia relient des concepts; ils ne sont pas toujours des traductions littérales.'},
 es:{title:'Explorador de palabras conectadas',lead:'Escribe una palabra o frase corta. La página resuelve el concepto con Wikipedia y muestra formas conectadas en varios idiomas.',ph:'Palabra, número, nombre o concepto…',go:'Buscar conexiones',ui:'Idioma de la página',source:'Idioma de entrada',targets:'Idiomas a mostrar',lang:'Idioma',word:'Palabra conectada',why:'Conexión',wiki:'Wikipedia',translation:'Mismo concepto / traducción',sourceWord:'Concepto de origen',open:'Abrir',working:'Buscando concepto y enlaces de idioma…',none:'No se encontró un concepto de Wikipedia coincidente.',note:'Los enlaces entre idiomas de Wikipedia conectan conceptos; no siempre son traducciones literales.'},
 it:{title:'Esplora parole collegate',lead:'Digita una parola o una breve frase. La pagina risolve il concetto tramite Wikipedia e mostra forme collegate in più lingue.',ph:'Parola, numero, nome o concetto…',go:'Trova collegamenti',ui:'Lingua pagina',source:'Lingua input',targets:'Lingue da mostrare',lang:'Lingua',word:'Parola collegata',why:'Collegamento',wiki:'Wikipedia',translation:'Stesso concetto / traduzione',sourceWord:'Concetto sorgente',open:'Apri',working:'Ricerca del concetto e dei collegamenti linguistici…',none:'Nessun concetto Wikipedia corrispondente.',note:'I collegamenti interlingua di Wikipedia collegano concetti e non sono sempre traduzioni letterali.'},
 pt:{title:'Explorador de palavras conectadas',lead:'Digite uma palavra ou frase curta. A página resolve o conceito pela Wikipédia e mostra formas conectadas em vários idiomas.',ph:'Palavra, número, nome ou conceito…',go:'Encontrar conexões',ui:'Idioma da página',source:'Idioma de entrada',targets:'Idiomas a mostrar',lang:'Idioma',word:'Palavra conectada',why:'Conexão',wiki:'Wikipédia',translation:'Mesmo conceito / tradução',sourceWord:'Conceito de origem',open:'Abrir',working:'Buscando conceito e links de idioma…',none:'Nenhum conceito correspondente na Wikipédia.',note:'Links interlinguísticos da Wikipédia conectam conceitos; nem sempre são traduções literais.'},
 nl:{title:'Woordverbindingen',lead:'Typ een woord of korte zin. De pagina zoekt het Wikipedia-concept en toont verbonden vormen in meerdere talen.',ph:'Woord, getal, naam of begrip…',go:'Vind verbindingen',ui:'Paginataal',source:'Invoertaal',targets:'Talen tonen',lang:'Taal',word:'Verbonden woord',why:'Verbinding',wiki:'Wikipedia',translation:'Zelfde concept / vertaling',sourceWord:'Bronconcept',open:'Open',working:'Concept en taallinks zoeken…',none:'Geen passend Wikipedia-concept gevonden.',note:'Wikipedia-taallinks verbinden concepten en zijn niet altijd letterlijke vertalingen.'},
 sv:{title:'Ordanslutningar',lead:'Skriv ett ord eller en kort fras. Sidan hittar Wikipedia-begreppet och visar anslutna former på flera språk.',ph:'Ord, tal, namn eller begrepp…',go:'Hitta anslutningar',ui:'Sidspråk',source:'Inmatningsspråk',targets:'Språk att visa',lang:'Språk',word:'Anslutet ord',why:'Anslutning',wiki:'Wikipedia',translation:'Samma begrepp / översättning',sourceWord:'Källbegrepp',open:'Öppna',working:'Söker begrepp och språklänkar…',none:'Inget matchande Wikipedia-begrepp hittades.',note:'Wikipedias språklänkar kopplar begrepp och är inte alltid ordagranna översättningar.'},
 fi:{title:'Sanojen yhteydet',lead:'Kirjoita sana tai lyhyt ilmaus. Sivu tunnistaa Wikipedia-käsitteen ja näyttää siihen liittyvät muodot eri kielillä.',ph:'Sana, numero, nimi tai käsite…',go:'Etsi yhteydet',ui:'Sivun kieli',source:'Syöttökieli',targets:'Näytettävät kielet',lang:'Kieli',word:'Yhdistetty sana',why:'Yhteys',wiki:'Wikipedia',translation:'Sama käsite / käännös',sourceWord:'Lähdekäsite',open:'Avaa',working:'Haetaan käsitettä ja kielilinkkejä…',none:'Vastaavaa Wikipedia-käsitettä ei löytynyt.',note:'Wikipedian kielilinkit yhdistävät käsitteitä eivätkä aina ole kirjaimellisia käännöksiä.'},
 ru:{title:'Связи слов',lead:'Введите слово или короткую фразу. Страница найдёт понятие в Википедии и покажет связанные формы на разных языках.',ph:'Слово, число, имя или понятие…',go:'Найти связи',ui:'Язык страницы',source:'Язык ввода',targets:'Показывать языки',lang:'Язык',word:'Связанное слово',why:'Связь',wiki:'Википедия',translation:'То же понятие / перевод',sourceWord:'Исходное понятие',open:'Открыть',working:'Ищем понятие и языковые ссылки…',none:'Подходящее понятие Википедии не найдено.',note:'Межъязыковые ссылки Википедии связывают понятия и не всегда являются буквальными переводами.'},
 el:{title:'Συνδέσεις λέξεων',lead:'Πληκτρολόγησε μια λέξη ή σύντομη φράση. Η σελίδα βρίσκει την έννοια στη Βικιπαίδεια και εμφανίζει συνδεδεμένες μορφές σε πολλές γλώσσες.',ph:'Λέξη, αριθμός, όνομα ή έννοια…',go:'Εύρεση συνδέσεων',ui:'Γλώσσα σελίδας',source:'Γλώσσα εισόδου',targets:'Γλώσσες προβολής',lang:'Γλώσσα',word:'Συνδεδεμένη λέξη',why:'Σύνδεση',wiki:'Βικιπαίδεια',translation:'Ίδια έννοια / μετάφραση',sourceWord:'Έννοια πηγής',open:'Άνοιγμα',working:'Αναζήτηση έννοιας και γλωσσικών συνδέσμων…',none:'Δεν βρέθηκε αντίστοιχη έννοια.',note:'Οι διαγλωσσικοί σύνδεσμοι της Βικιπαίδειας συνδέουν έννοιες και δεν είναι πάντα κυριολεκτικές μεταφράσεις.'},
 tr:{title:'Kelime bağlantıları',lead:'Bir kelime veya kısa ifade yazın. Sayfa kavramı Vikipedi üzerinden çözümler ve farklı dillerdeki bağlı biçimleri gösterir.',ph:'Kelime, sayı, ad veya kavram…',go:'Bağlantıları bul',ui:'Sayfa dili',source:'Giriş dili',targets:'Gösterilecek diller',lang:'Dil',word:'Bağlı kelime',why:'Bağlantı',wiki:'Vikipedi',translation:'Aynı kavram / çeviri',sourceWord:'Kaynak kavram',open:'Aç',working:'Kavram ve dil bağlantıları aranıyor…',none:'Eşleşen Vikipedi kavramı bulunamadı.',note:'Vikipedi dil bağlantıları kavramları bağlar; her zaman kelimesi kelimesine çeviri değildir.'},
 ar:{title:'مستكشف ترابط الكلمات',lead:'اكتب كلمة أو عبارة قصيرة. تحل الصفحة المفهوم عبر ويكيبيديا ثم تعرض الأشكال المرتبطة بلغات متعددة.',ph:'كلمة أو رقم أو اسم أو مفهوم…',go:'ابحث عن الروابط',ui:'لغة الصفحة',source:'لغة الإدخال',targets:'اللغات المعروضة',lang:'اللغة',word:'الكلمة المرتبطة',why:'نوع الرابط',wiki:'ويكيبيديا',translation:'نفس المفهوم / ترجمة',sourceWord:'المفهوم المصدر',open:'فتح',working:'جارٍ البحث عن المفهوم وروابط اللغات…',none:'لم يتم العثور على مفهوم مطابق في ويكيبيديا.',note:'روابط اللغات في ويكيبيديا تربط المفاهيم وليست دائماً ترجمات حرفية.'},
 he:{title:'חוקר קשרי מילים',lead:'הקלידו מילה או ביטוי קצר. הדף מאתר את המושג בוויקיפדיה ומציג צורות מקושרות בשפות שונות.',ph:'מילה, מספר, שם או מושג…',go:'מצא קשרים',ui:'שפת הדף',source:'שפת הקלט',targets:'שפות להצגה',lang:'שפה',word:'מילה מקושרת',why:'קשר',wiki:'ויקיפדיה',translation:'אותו מושג / תרגום',sourceWord:'מושג מקור',open:'פתח',working:'מחפש מושג וקישורי שפה…',none:'לא נמצא מושג מתאים בוויקיפדיה.',note:'קישורי השפה של ויקיפדיה מחברים מושגים ואינם תמיד תרגום מילולי.'},
 hi:{title:'शब्द संबंध खोजक',lead:'एक शब्द या छोटा वाक्यांश लिखें। पृष्ठ विकिपीडिया से अवधारणा पहचानकर कई भाषाओं में जुड़े रूप दिखाता है।',ph:'शब्द, संख्या, नाम या अवधारणा…',go:'संबंध खोजें',ui:'पृष्ठ भाषा',source:'इनपुट भाषा',targets:'दिखाई जाने वाली भाषाएँ',lang:'भाषा',word:'जुड़ा शब्द',why:'संबंध',wiki:'विकिपीडिया',translation:'वही अवधारणा / अनुवाद',sourceWord:'स्रोत अवधारणा',open:'खोलें',working:'अवधारणा और भाषा लिंक खोजे जा रहे हैं…',none:'कोई मेल खाती विकिपीडिया अवधारणा नहीं मिली।',note:'विकिपीडिया के अंतरभाषा लिंक अवधारणाओं को जोड़ते हैं; वे हमेशा शाब्दिक अनुवाद नहीं होते।'},
 zh:{title:'词语连接探索器',lead:'输入一个词或短语。页面通过维基百科识别概念，并显示多种语言中的对应形式。',ph:'词、数字、名称或概念…',go:'查找连接',ui:'页面语言',source:'输入语言',targets:'显示语言',lang:'语言',word:'关联词',why:'连接',wiki:'维基百科',translation:'同一概念 / 翻译',sourceWord:'源概念',open:'打开',working:'正在查找概念和语言链接…',none:'未找到匹配的维基百科概念。',note:'维基百科跨语言链接连接的是概念，不一定是逐字翻译。'},
 ja:{title:'単語つながり探索',lead:'単語または短い語句を入力すると、Wikipediaで概念を特定し、複数言語の対応形を表示します。',ph:'単語・数字・名前・概念…',go:'つながりを探す',ui:'ページ言語',source:'入力言語',targets:'表示言語',lang:'言語',word:'つながる語',why:'つながり',wiki:'Wikipedia',translation:'同じ概念 / 翻訳',sourceWord:'元の概念',open:'開く',working:'概念と言語リンクを検索中…',none:'一致するWikipedia概念が見つかりません。',note:'Wikipediaの言語間リンクは概念を結ぶもので、必ずしも逐語訳ではありません。'},
 ko:{title:'단어 연결 탐색기',lead:'단어나 짧은 구를 입력하면 위키백과에서 개념을 찾고 여러 언어의 연결된 형태를 보여 줍니다.',ph:'단어, 숫자, 이름 또는 개념…',go:'연결 찾기',ui:'페이지 언어',source:'입력 언어',targets:'표시 언어',lang:'언어',word:'연결된 단어',why:'연결',wiki:'위키백과',translation:'같은 개념 / 번역',sourceWord:'원본 개념',open:'열기',working:'개념과 언어 링크를 찾는 중…',none:'일치하는 위키백과 개념을 찾지 못했습니다.',note:'위키백과의 언어 간 링크는 개념을 연결하며 항상 직역은 아닙니다.'},
 sw:{title:'Kichunguzi cha miunganisho ya maneno',lead:'Andika neno au kifungu kifupi. Ukurasa hutambua dhana kupitia Wikipedia na kuonyesha maumbo yanayolingana katika lugha mbalimbali.',ph:'Neno, nambari, jina au dhana…',go:'Tafuta miunganisho',ui:'Lugha ya ukurasa',source:'Lugha ya ingizo',targets:'Lugha za kuonyesha',lang:'Lugha',word:'Neno lililounganishwa',why:'Muunganisho',wiki:'Wikipedia',translation:'Dhana ileile / tafsiri',sourceWord:'Dhana ya chanzo',open:'Fungua',working:'Inatafuta dhana na viungo vya lugha…',none:'Hakuna dhana inayolingana iliyopatikana Wikipedia.',note:'Viungo vya lugha vya Wikipedia huunganisha dhana; si lazima viwe tafsiri za neno kwa neno.'},
 yo:{title:'Olùṣàwárí ìsopọ̀ ọ̀rọ̀',lead:'Tẹ ọ̀rọ̀ tàbí gbólóhùn kékeré. Ojúewé yóò rí èrò náà lórí Wikipedia, yóò sì fi àwọn ọ̀rọ̀ tó bá a mu ní èdè púpọ̀ hàn.',ph:'Ọ̀rọ̀, nọ́ńbà, orúkọ tàbí èrò…',go:'Wá àwọn ìsopọ̀',ui:'Èdè ojúewé',source:'Èdè ìwọlé',targets:'Àwọn èdè láti fi hàn',lang:'Èdè',word:'Ọ̀rọ̀ tó sopọ̀',why:'Ìsopọ̀',wiki:'Wikipedia',translation:'Èrò kan náà / ìtumọ̀',sourceWord:'Èrò orísun',open:'Ṣí',working:'Ń wá èrò àti àwọn ìjápọ̀ èdè…',none:'A kò rí èrò Wikipedia tó bá a mu.',note:'Àwọn ìjápọ̀ èdè Wikipedia ń so àwọn èrò pọ̀; wọn kì í ṣe ìtumọ̀ gangan ní gbogbo ìgbà.'}
};
// fallbacks for supported UI languages not yet fully curated
['no','da','is','pl','cs','uk','fa'].forEach(k=>{ if(!L[k]) L[k]=L.en; });

const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const wikiUrl=(lang,title)=>`https://${lang}.wikipedia.org/wiki/${encodeURIComponent(title.replace(/ /g,'_'))}`;
const api=(lang,params)=>`https://${lang}.wikipedia.org/w/api.php?origin=*&format=json&formatversion=2&${new URLSearchParams(params)}`;

let uiLang='en';
function t(k){return (L[uiLang]||L.en)[k]||L.en[k]||k;}
function optMarkup(selected='en'){return LANGS.map(([c,n])=>`<option value="${c}"${c===selected?' selected':''}>${n}</option>`).join('');}

function inject(){
 if(document.getElementById('wordConnect')) return;
 const hero=document.querySelector('header.hero');
 const box=document.createElement('section');
 box.id='wordConnect'; box.className='wordconnect wrap';
 box.innerHTML=`
  <div class="wc-head"><div><div class="eyebrow" data-wc="title"></div><h2 data-wc="title"></h2><p class="lead" data-wc="lead"></p></div>
  <div class="wc-locales"><label data-wc="ui"></label><select id="wcUiLang">${optMarkup()}</select></div></div>
  <div class="wc-search panel"><div class="wc-inputrow"><input id="wcInput" autocomplete="off" spellcheck="false"><button id="wcGo" class="btn" data-wc="go"></button></div>
  <div class="wc-options"><label><span data-wc="source"></span><select id="wcSourceLang">${optMarkup('en')}</select></label><label><span data-wc="targets"></span><select id="wcTargetSet"><option value="core">20+</option><option value="all">All available</option></select></label></div>
  <div id="wcStatus" class="small"></div><div id="wcResults"></div><p class="small wc-note" data-wc="note"></p></div>`;
 if(hero) hero.after(box); else document.body.prepend(box);
 const style=document.createElement('style');
 style.textContent=`.wordconnect{padding:6px 0 42px}.wc-head{display:flex;justify-content:space-between;gap:18px;align-items:end;flex-wrap:wrap}.wc-head h2{font-size:clamp(1.75rem,4vw,2.65rem);margin:.1em 0}.wc-locales,.wc-options label{display:flex;flex-direction:column;gap:5px;color:var(--muted);font-size:.82rem}.wc-locales select,.wc-options select,#wcInput{background:#0c1018;color:var(--text);border:1px solid #3d455d;border-radius:10px;padding:11px}.wc-search{margin-top:14px}.wc-inputrow{display:grid;grid-template-columns:1fr auto;gap:10px}.wc-options{display:flex;gap:12px;flex-wrap:wrap;margin-top:12px}.wc-options label{min-width:190px}.wc-tablebox{margin-top:16px;border:1px solid var(--line);border-radius:14px;overflow:auto}.wc-table{width:100%;border-collapse:collapse}.wc-table th,.wc-table td{padding:11px 13px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.wc-table th{background:#10141f;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}.wc-table tr:last-child td{border-bottom:0}.wc-word{font-size:1.08rem;font-weight:700;color:var(--cyan);text-decoration:none}.wc-lang{white-space:nowrap}.wc-source{background:#101820}.wc-note{margin:14px 0 0}.wc-badge{display:inline-block;padding:2px 7px;border:1px solid var(--line);border-radius:999px;font-size:.76rem;color:var(--muted)}@media(max-width:600px){.wc-inputrow{grid-template-columns:1fr}.wc-options label{min-width:140px;flex:1}.wc-table th:nth-child(3),.wc-table td:nth-child(3){display:none}}`;
 document.head.appendChild(style);
 bind(); applyLocale();
}

function applyLocale(){
 document.documentElement.lang=uiLang; document.documentElement.dir=RTL.has(uiLang)?'rtl':'ltr';
 document.querySelectorAll('[data-wc]').forEach(el=>el.textContent=t(el.dataset.wc));
 const input=document.getElementById('wcInput'); if(input) input.placeholder=t('ph');
 localStorage.setItem('phoneticUiLang',uiLang);
}

function bind(){
 const guessed=(navigator.language||'en').toLowerCase().split('-')[0];
 const saved=localStorage.getItem('phoneticUiLang'); uiLang=L[saved]?saved:(L[guessed]?guessed:'en');
 const ui=document.getElementById('wcUiLang'); ui.value=uiLang;
 ui.addEventListener('change',()=>{uiLang=ui.value;applyLocale();});
 document.getElementById('wcGo').addEventListener('click',run);
 document.getElementById('wcInput').addEventListener('keydown',e=>{if(e.key==='Enter')run();});
}

async function resolveConcept(lang,q){
 const url=api(lang,{action:'query',generator:'search',gsrsearch:q,gsrlimit:'1',gsrnamespace:'0',prop:'langlinks|info',inprop:'url',lllimit:'500'});
 const j=await fetch(url).then(r=>{if(!r.ok)throw Error(r.status);return r.json();});
 const p=j?.query?.pages?.[0]; if(!p) return null;
 return {title:p.title,url:p.fullurl||wikiUrl(lang,p.title),langlinks:p.langlinks||[]};
}

async function run(){
 const q=document.getElementById('wcInput').value.trim(); if(!q)return;
 const src=document.getElementById('wcSourceLang').value;
 const status=document.getElementById('wcStatus'), out=document.getElementById('wcResults');
 status.textContent=t('working'); out.innerHTML='';
 try{
  const p=await resolveConcept(src,q); if(!p){status.textContent=t('none');return;}
  const allowed=new Set(LANGS.map(x=>x[0]));
  let rows=[{lang:src,title:p.title,url:p.url,kind:t('sourceWord'),source:true}];
  for(const ll of p.langlinks){
   if(document.getElementById('wcTargetSet').value==='core'&&!allowed.has(ll.lang)) continue;
   rows.push({lang:ll.lang,title:ll.title,url:wikiUrl(ll.lang,ll.title),kind:t('translation')});
  }
  rows.sort((a,b)=>a.source?-1:b.source?1:(LANGS.findIndex(x=>x[0]===a.lang)+1000*(LANGS.findIndex(x=>x[0]===a.lang)<0))-(LANGS.findIndex(x=>x[0]===b.lang)+1000*(LANGS.findIndex(x=>x[0]===b.lang)<0)));
  status.textContent=`${p.title} · ${rows.length} ${t('lang').toLowerCase()}`;
  out.innerHTML=`<div class="wc-tablebox"><table class="wc-table"><thead><tr><th>${esc(t('lang'))}</th><th>${esc(t('word'))}</th><th>${esc(t('why'))}</th><th>${esc(t('wiki'))}</th></tr></thead><tbody>${rows.map(r=>`<tr class="${r.source?'wc-source':''}"><td class="wc-lang">${esc((LANGS.find(x=>x[0]===r.lang)||[r.lang,r.lang])[1])} <span class="wc-badge">${esc(r.lang)}</span></td><td><a class="wc-word" target="_blank" rel="noopener" href="${esc(r.url)}">${esc(r.title)}</a></td><td>${esc(r.kind)}</td><td><a target="_blank" rel="noopener" href="${esc(r.url)}">${esc(t('open'))} ↗</a></td></tr>`).join('')}</tbody></table></div>`;
 }catch(e){status.textContent=`Wikipedia lookup failed: ${e.message}`;}
}

document.readyState==='loading'?document.addEventListener('DOMContentLoaded',inject):inject();
})();
