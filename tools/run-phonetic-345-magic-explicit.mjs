#!/usr/bin/env node
import fs from 'node:fs/promises';
import * as Core from '../phonetic-345-magic-core.mjs';
const ROOT=new URL('../',import.meta.url),read=async p=>fs.readFile(new URL(p,ROOT),'utf8');
const all=Core.parseCSV(await read('data/phonetic-benchmark-languages.csv')).filter(x=>String(x.canonical).toLowerCase()==='true');
const topology=JSON.parse(await read('data/phonetic-group-comparison.json'));
const alphabetFile=JSON.parse(await read('data/phonetic-alphabet-orders.json'));
const rows=all.filter(x=>alphabetFile.orders?.[x.iso]);
const permutations=240,maxWords=5000;
console.log(`Running exact shared engine on ${rows.length} curated alphabet orders`);
const result=await Core.runExperiment({metas:rows,topologyData:topology,alphabetPresets:alphabetFile.orders||{},permutations,maxWords,concurrency:5,onProgress:x=>{if(x.done%5===0||x.done===x.total)console.log(`${x.done}/${x.total}`)}});
result.generatedUtc=new Date().toISOString();result.source='same shared engine as page; curated explicit alphabet benchmark';result.scope='explicit curated alphabet orders';
await fs.writeFile(new URL('data/phonetic-345-magic-results-explicit.json',ROOT),JSON.stringify(result,null,2));
console.log(JSON.stringify({counts:result.counts,global:result.global,topology:result.groups.topology.slice(0,8),families:result.groups.families.slice(0,8),scripts:result.groups.scripts.slice(0,8),languages:result.languages.slice(0,15).map(x=>({name:x.name,z:x.z345,strength:x.strength,g3:x.layers[3].magicGain,g4:x.layers[4].magicGain,g5:x.layers[5].magicGain,orderZ:x.layers[4].alphabetOrderZ,powerZ:x.power4.z}))},null,2));
