// Production baseline workers in two isolated Node processes sharing the parent Windows job.
import { fork } from 'node:child_process';
import { Worker } from 'node:worker_threads';
import { fileURLToPath } from 'node:url';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const root = dirname(fileURLToPath(import.meta.url));
if (process.argv[2] === 'worker') {
  const worker = new Worker(new URL('./inference_worker.mjs', import.meta.url));
  worker.on('message', m => process.send(m));
  worker.on('error', e => process.send({kind:'fatal', error:String(e)}));
  process.on('message', m => worker.postMessage(m));
  process.on('disconnect', () => worker.terminate());
} else {
  const cases = JSON.parse(readFileSync(join(root, 'benchmarks/cases.json')));
  const children = [];
  const report = {profile:'baseline', test:'Concurrent production inference workers', answers:[], complete:false};
  const file = join(root, 'benchmark-local/results/baseline-dual.json');
  function save() { writeFileSync(file, JSON.stringify(report, null, 2)); }
  function receive(child, kind) {
    return new Promise((resolve, reject) => {
      function cleanup() {
        clearTimeout(timer);
        child.off('message', message);
        child.off('error', fail);
        child.off('exit', fail);
      }
      function fail(problem) { cleanup(); reject(new Error(String(problem))); }
      function message(m) {
        if (m.kind === 'fatal' || m.kind === 'request_error') fail(m.error);
        else if (m.kind === kind) { cleanup(); resolve(m); }
      }
      const timer = setTimeout(() => fail('Worker timeout'), 20*60*1000);
      child.on('message', message);
      child.once('error', fail);
      child.once('exit', fail);
    });
  }
  try {
    const started = Date.now();
    for (let i=0; i<2; i++) {
      const child = fork(fileURLToPath(import.meta.url), ['worker'], {windowsHide:true});
      children.push(child);
      await receive(child, 'ready');
    }
    report.both_ready_ms = Date.now()-started;
    const tasks = ['tool_read','scope'].map(id => cases.find(c => c.id === id));
    const requests = children.map((child, i) => {
      const task=tasks[i], began=Date.now();
      const answer=receive(child,'answer');
      child.send({kind:'generate', messages:[{role:'user', content:task.prompt}], id:i+1, max:768});
      return answer.then(m => ({role:i===0?'JANUS tool selection':'Sentinel scope review',
        id:task.id, answer:m.output, began_ms:began-started, ended_ms:Date.now()-started}));
    });
    report.answers = await Promise.all(requests);
    report.complete = true;
  } catch (e) {
    report.failure = String(e);
    process.exitCode = 1;
  } finally {
    save();
    for (const child of children) child.kill();
  }
}
