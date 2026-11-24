// Separate experimental runner: no production workers, ports or state.
import { readFileSync, writeFileSync, mkdirSync, renameSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { env, pipeline } from '@huggingface/transformers';
import { runProjectBenchmark } from './model_benchmark_project.mjs';
const root = dirname(fileURLToPath(import.meta.url));
const profiles = JSON.parse(readFileSync(join(root,'benchmarks','profiles.json'),'utf8'));
const cases = JSON.parse(readFileSync(join(root,'benchmarks','cases.json'),'utf8'));
const [profile, mode, suite = 'all'] = process.argv.slice(2);
if (!['all', 'project'].includes(suite)) throw Error('Unknown benchmark suite');
if (!Object.hasOwn(profiles,profile) || !['offline','prepare-hosted'].includes(mode)) throw Error('Usage: node model_benchmark.mjs PROFILE offline|prepare-hosted');
if (mode==='prepare-hosted' && process.env.GITHUB_ACTIONS!=='true') throw Error('Hosted mode is only for the synthetic GitHub benchmark');
const spec=profiles[profile];
const work=join(root,'benchmark-local');
const out=join(work,'results',profile+(suite === 'project' ? '-project' : '')+'.json');
mkdirSync(dirname(out),{recursive:true});
env.allowRemoteModels=mode==='prepare-hosted';
env.allowLocalModels=mode==='offline';
env.localModelPath=join(work,'models')+'/';
env.cacheDir=join(work,'cache');
const report={schema:'deepthort-model-benchmark-v1',profile,repo:spec.repo,revision:spec.revision,dtype:spec.dtype,
  node:process.version,platform:process.platform,mode,results:[],startup_ms:null,peak_rss_bytes:0,complete:false};
const start=Date.now();
let timer;
function save(){
  report.peak_rss_bytes=Math.max(report.peak_rss_bytes,process.memoryUsage().rss);
  writeFileSync(out+'.tmp',JSON.stringify(report,null,2));
  renameSync(out+'.tmp',out);
}
try {
  save();
  timer=setInterval(()=>{report.peak_rss_bytes=Math.max(report.peak_rss_bytes,process.memoryUsage().rss)},500);
  if(mode==='offline'){
    for(const file of spec.weights) if(!existsSync(join(env.localModelPath,spec.repo,file))) throw Error('Missing experimental weight '+file+'; prepare separately');
  }
  const gen=await pipeline('text-generation',spec.repo,{revision:spec.revision,device:'cpu',dtype:spec.dtype,
    use_external_data_format: spec.weights.length - 1,
    session_options:{intraOpNumThreads:1,interOpNumThreads:1,enableCpuMemArena:false}});
  env.allowRemoteModels=false;
  report.startup_ms=Date.now()-start; save();
  async function generate(messages) {
    const turns = messages.map((turn, i) => spec.no_think && i === messages.length-1
      ? {...turn, content:turn.content+'\n/no_think'} : turn);
    const generated = await gen(turns, {max_new_tokens:768, do_sample:false});
    const value = generated?.[0]?.generated_text;
    const answer = Array.isArray(value) ? value.at(-1)?.content : value;
    if (typeof answer !== 'string' || !answer.trim()) throw Error('No generated answer');
    return answer;
  }
  for(const item of suite === 'project' ? [] : cases){
    const began=Date.now();
    try{
      const answer = await generate([{role:'user', content:item.prompt}]);
      report.results.push({id:item.id,answer:answer.slice(0,16000),elapsed_ms:Date.now()-began});
    }catch(error){
      report.results.push({id:item.id,error:String(error?.message||error).slice(0,500),elapsed_ms:Date.now()-began});
    }
    save();
    console.log('BENCHMARK_CASE',profile,item.id,report.results.at(-1).error?'inference error':'generated',report.results.at(-1).elapsed_ms+'ms');
  }
  await runProjectBenchmark(root, generate, report, save);
  await gen.dispose();
  report.complete=true;
}catch(error){
  report.failure=String(error?.stack||error).slice(0,3000);
  console.error('BENCHMARK_LOAD_OR_RUN_FAILURE',profile,report.failure);
  process.exitCode=1;
}finally{
  clearInterval(timer);save();
}
