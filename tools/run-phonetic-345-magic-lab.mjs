#!/usr/bin/env node
import fs from 'node:fs/promises';
import * as Core from '../phonetic-345-magic-core-v2.mjs';

const ROOT=new URL('../',import.meta.url);
const read=async p=>fs.readFile(new URL(p,ROOT),'utf8');
const metas=Core.parseCSV(await read('data/phonetic-benchmark-languages.csv')).filter(x=>String(x.canonical).toLowerCase()==='true');
const topology=JSON.parse(await read('data/phonetic-group-comparison.json'));
const alphabetFile=JSON.parse(await read('data/phonetic-alphabet-orders.json'));
const presets=alphabetFile.orders||{};
const permutations=+(process.env.M345_PERMS||80);
const maxWords=+(process.env.M345_WORDS||2000);
const concurrency=+(process.env.M345_CONCURRENCY||5);
const scope=process.env.M345_SCOPE||'full';
const NON_ALPHA=/Han|Chinese|Japanese|Hangul|Canadian Aboriginal/i;

let rows=metas.filter(x=>presets[x.iso]||!NON_ALPHA.test(x.script||''));
if(scope==='explicit') rows=rows.filter(x=>presets[x.iso]);
if(scope==='quick'){
  const by=new Map();
  for(const r of rows){const k=r.family||r.script||'Other';if(!by.has(k))by.set(k,[]);by.get(k).push(r)}
  const q=[];
  for(let pass=0;q.length<72&&pass<12;pass++)for(const xs of by.values()){if(xs[pass])q.push(xs[pass]);if(q.length>=72)break}
  rows=q;
}

console.log(`Running exact page engine ${Core.VERSION_V2}: ${rows.length} languages, ${permutations} controls/layer, ${maxWords} words/language`);
const result=await Core.runExperimentFast({
  metas:rows,topologyData:topology,alphabetPresets:presets,permutations,maxWords,concurrency,
  onProgress:x=>{if(x.done%10===0||x.done===x.total)console.log(`${x.done}/${x.total} · ${x.results} completed · ${x.failures} skipped`)}
});
result.generatedUtc=new Date().toISOString();
result.source='exact same phonetic-345-magic-core-v2 engine as the page tool';
await fs.writeFile(new URL('data/phonetic-345-magic-results.json',ROOT),JSON.stringify(result,null,2),'utf8');
const top=(xs)=>xs.slice(0,12).map(x=>({group:x.group,strength:x.strength,z:+x.z.toFixed(3),q:+x.q.toPrecision(4),n:x.languages}));
console.log(JSON.stringify({counts:result.counts,global:result.global,topTopology:top(result.groups.topology),topFamilies:top(result.groups.families),topScripts:top(result.groups.scripts),topLanguages:result.languages.slice(0,15).map(x=>({name:x.name,strength:x.strength,z:+x.z345.toFixed(3),alphabet:x.alphabetConfidence}))},null,2));
