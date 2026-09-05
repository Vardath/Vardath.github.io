(()=>{
'use strict';

const GREEN='goodtxt';
const ORANGE='warntxt';

function tooltip(text){
  const s=document.createElement('span');
  s.textContent=' ?';
  s.title=text;
  s.setAttribute('aria-label',text);
  s.style.cursor='help';
  s.style.color='var(--cyan,#5ce1e6)';
  s.style.fontWeight='700';
  return s;
}

function addRow(tbody,statement,status,tip){
  const tr=document.createElement('tr');
  const td1=document.createElement('td');
  const td2=document.createElement('td');
  td1.textContent=statement;
  if(tip) td1.appendChild(tooltip(tip));
  td2.textContent=status;
  td2.className=GREEN;
  tr.append(td1,td2);
  tbody.appendChild(tr);
}

function upgrade(){
  const section=document.querySelector('#status');
  if(!section) return false;
  const table=section.querySelector('table.compare');
  if(!table) return false;
  const tbody=table.tBodies[0]||table;

  // Upgrade the implementation-status row only. This does NOT claim optimality.
  [...table.rows].forEach(row=>{
    const txt=(row.cells?.[0]?.textContent||'').trim();
    if(txt.startsWith('The present rules assign non-prosodic segments to sixteen coarse bridge cells.')){
      const cell=row.cells[1];
      if(cell){
        cell.className=GREEN;
        cell.textContent='Implemented + benchmarked';
        cell.title='The 16-cell classifier is now exercised across the completed cross-language benchmark. This validates use of the implementation, not global optimality of sixteen cells.';
      }
    }
  });

  if(document.getElementById('evidence-status-divider')) return true;

  const divider=document.createElement('tr');
  divider.id='evidence-status-divider';
  const head=document.createElement('th');
  head.colSpan=2;
  head.textContent='New empirical findings from the completed analyses';
  head.style.paddingTop='24px';
  head.style.color='var(--cyan,#5ce1e6)';
  divider.appendChild(head);
  tbody.appendChild(divider);

  addRow(tbody,
    'Languages in the same Glottolog family are more bridge-similar on average than languages in different families.',
    'Supported in benchmark',
    'Observed mean stable-gate Jaccard: 0.5051 for same-family pairs versus 0.3731 for cross-family pairs; uplift +0.132.'
  );
  addRow(tbody,
    'Among different-family languages, present-day geographic distance is negatively associated with bridge similarity.',
    'Supported in benchmark',
    'Cross-family log-distance correlation is -0.1578. Nearby and regional pairs are more bridge-similar on average than pairs over 5,000 km apart. Geography is only a proxy for possible contact, not proof of contact.'
  );
  addRow(tbody,
    'Bridge compatibility can be strongly directional rather than symmetric.',
    'Observed in benchmark',
    'Directional direct-support measures differ substantially for some language pairs. This supports testing one-way adaptation/transmission separately from symmetric gate overlap.'
  );
  addRow(tbody,
    'Known historical sound changes can involve transformations as large as those allowed by the word-level pilot.',
    'Calibration established',
    'Positive controls include the independently attested eight/eight-family and octo/ogdo- developments. This validates the need for directional sound-change tolerance; it does not establish any proposed cross-family etymology.'
  );

  const note=document.createElement('div');
  note.className='notice';
  note.style.marginTop='22px';
  note.innerHTML='<b>Why some rows remain orange:</b> “16 cells are globally optimal,” “WikiPron lexical transitions equal continuous connected speech,” and “magic-square/powers-of-3 ordering has a phonetic relationship beyond chance” still require dedicated controls. They have deliberately not been promoted.';
  table.insertAdjacentElement('afterend',note);
  return true;
}

if(!upgrade()){
  const obs=new MutationObserver(()=>{if(upgrade()) obs.disconnect();});
  obs.observe(document.documentElement,{childList:true,subtree:true});
  setTimeout(()=>obs.disconnect(),10000);
}
})();
