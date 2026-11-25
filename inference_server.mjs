// Offline localhost status and inference coordinator. Heavy ONNX work happens
// in a worker thread so /health responds throughout model initialization.
import http from 'node:http';
import { mkdirSync, appendFileSync, existsSync, renameSync, unlinkSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { Worker } from 'node:worker_threads';

const PORT = Number(process.env.DEEPTHORT_COUNCIL_PORT || process.env.DEEPTHORT_TEST_PORT || 8765);
const ROLE = process.env.DEEPTHORT_ROLE === 'council' ? 'council' : 'implementation';
if (ROLE === 'council' && PORT !== 8766) throw new Error('Council ONNX must run only on port 8766');
const MODEL = 'deepthort-qwen-coder-onnx';
const start = Date.now();
let ready = false;
let phase = 'starting';
let stage = 'Starting isolated ONNX worker';
let stageAt = Date.now();
let error = '';
let busy = false;
let serial = 0;
let activeInference = null; // Safe metadata only; never holds a prompt.
const pending = new Map();
// Durable, bounded model-only diagnostics. Do not log prompt text or generated replies.
const LOGDIR=join(process.cwd(),'state','logs');
const LOGPATH=join(LOGDIR, ROLE === 'council' ? 'onnx-council.jsonl' : 'onnx.jsonl');
function event(name, fields={}) {
  try {
    mkdirSync(LOGDIR,{recursive:true});
    if (existsSync(LOGPATH) && statSync(LOGPATH).size>3*1024*1024) {
      try { if (existsSync(LOGPATH+'.old')) unlinkSync(LOGPATH+'.old'); renameSync(LOGPATH,LOGPATH+'.old'); } catch { /* keep running */ }
    }
    appendFileSync(LOGPATH,JSON.stringify({utc:new Date().toISOString(),pid:process.pid,
      component:'onnx',event:name,...fields})+'\n');
  } catch { /* diagnostics cannot interrupt model */ }
}
event('model_server_start',{port:PORT,role:ROLE});

function reply(res, status, value) {
  res.writeHead(status, {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
  res.end(JSON.stringify(value));
}
function validate(body) {
  if (!body || typeof body !== 'object' || !Array.isArray(body.messages)) throw new Error('messages must be an array');
  if (body.model !== undefined && body.model !== MODEL) throw new Error('unsupported model');
  if (body.messages.length < 1 || body.messages.length > 12) throw new Error('1..12 messages required');
  let chars = 0;
  const messages = body.messages.map(m => {
    if (!m || !['system','user','assistant'].includes(m.role) || typeof m.content !== 'string') throw new Error('invalid message');
    chars += m.content.length;
    if (m.content.length > 8000 || chars > 15000) throw new Error('prompt exceeds gaming profile');
    return {role:m.role,content:m.content};
  });
  if (messages.at(-1).role !== 'user') throw new Error('final message must be user');
  const max = Number(body.max_tokens ?? 96);
  if (!Number.isInteger(max) || max < 1 || max > 768) throw new Error('max_tokens must be 1..768');
  if (body.stream === true) throw new Error('streaming not supported');
  return {messages,max};
}

const worker = new Worker(new URL('./inference_worker.mjs', import.meta.url));
let stopping = false;
function fatal(message) {
  if (stopping) return;
  stopping=true;
  error=String(message).slice(0,6000);
  phase='failed';ready=false;
  console.error('[AI LOAD FAILED]',error);
  event('model_start_failed',{error:error.slice(0,900)});
  for (const item of pending.values()) item.reject(new Error(error));
  pending.clear();
  // Exit with a failing code so the desktop displays an error dialog and does
  // not continue showing "AI: loading" with a dead model thread.
  setTimeout(() => process.exit(3), 200).unref();
}
worker.on('message', (m) => {
  if (m.kind==='stage') {
    stage=String(m.message || 'Loading');stageAt=Date.now();
    console.log(`[AI LOAD] ${stage} (${m.elapsed_seconds}s)`);
    event('model_load_stage',{stage,seconds:m.elapsed_seconds});
  } else if (m.kind==='ready') {
    ready=true;phase='ready';stage='Model ready for local chat';stageAt=Date.now();
    console.log(`[AI LOAD] Ready after ${Math.round((Date.now()-start)/1000)}s`);
    event('model_ready',{seconds:Math.round((Date.now()-start)/1000)});
  } else if (m.kind==='fatal') {
    fatal(m.error);
  } else if (m.kind==='answer' || m.kind==='request_error') {
    const item=pending.get(m.id);
    if (!item) return;
    pending.delete(m.id);
    if (m.kind==='answer') {event('inference_answer',{request_id:m.id,response_characters:String(m.output||'').length});item.resolve(m.output);}
    else {event('inference_error',{request_id:m.id,error:String(m.error||'Inference failed').slice(0,600)});item.reject(new Error(String(m.error||'Inference failed')));}
  }
});
worker.on('error',e=>fatal(e?.stack || String(e)));
worker.on('exit',code=>{if (!stopping) fatal(`ONNX worker exited (code ${code}); no local model is available`);});
const status = () => ({ready,offline:true,model:MODEL,role:ROLE,pid:process.pid,phase,stage,
  inference_busy:busy,
  inference_elapsed_seconds:activeInference ? Math.max(0,Math.floor((Date.now()-activeInference.started)/1000)) : 0,
  inference_max_tokens:activeInference?.max ?? null,
  inference_request_id:activeInference?.id ?? null,
  loading_seconds:Math.floor((Date.now()-start)/1000),
  seconds_since_progress:Math.floor((Date.now()-stageAt)/1000),
  stalled:!ready && !stopping && (Date.now()-stageAt)>240000,
  error:error || null});
const server = http.createServer(async(req,res)=>{
  if (req.url==='/health' && req.method==='GET') return reply(res,200,status());
  if (req.url!=='/v1/chat/completions' || req.method!=='POST') return reply(res,404,{error:'not found'});
  if (!ready) return reply(res,503,{error:'Model is not ready',...status()});
  if (busy) return reply(res,503,{error:'Model busy'});
  let raw='';
  try {
    for await (const chunk of req) {
      raw+=chunk.toString('utf8');
      if (raw.length>80000) throw new Error('request too large');
    }
    const {messages,max} = validate(JSON.parse(raw));
    busy=true;
    const id=++serial;
    activeInference={id,max,started:Date.now()};
    const result=new Promise((resolve,reject)=>pending.set(id,{resolve,reject}));
    event('inference_request',{request_id:id,message_count:messages.length,max_tokens:max,
       total_input_characters:messages.reduce((n,m)=>n+m.content.length,0)});
    worker.postMessage({kind:'generate',id,messages,max});
    const output=await result;
    return reply(res,200,{id:'offline-'+Date.now(),object:'chat.completion',model:MODEL,
      choices:[{index:0,message:{role:'assistant',content:output},finish_reason:'stop'}]});
  } catch(e) {
    console.error('Inference request failed:',e?.message||e);
    event('inference_http_error',{error:String(e?.message||e).slice(0,650)});
    if (!res.writableEnded) return reply(res,400,{error:String(e?.message||e)});
  } finally {busy=false;activeInference=null;}
});
server.on('error',e=>fatal(`Localhost server error: ${e?.message || e}`));
server.listen(PORT,'127.0.0.1',()=>{console.log(`[AI LOAD] Local diagnostic server listening at 127.0.0.1:${PORT}; model still loading`);event('health_endpoint_listening',{port:PORT});});
// Report elapsed status only: it is not evidence that model initialization progressed.
const beat=setInterval(()=>{
  if (busy && activeInference) event('inference_still_running',{request_id:activeInference.id,
    elapsed_seconds:Math.floor((Date.now()-activeInference.started)/1000),max_tokens:activeInference.max});
  if (!ready && !stopping) console.log(`[AI LOAD] ${status().loading_seconds}s total; phase=${phase}; last stage: ${stage}; ${status().seconds_since_progress}s since new model event`);
},30000);
beat.unref();
