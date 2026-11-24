import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

export async function runProjectBenchmark(root, generate, report, save) {
  function oracle(request) {
    const child = spawnSync(process.env.DEEPTHORT_BENCH_PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
      ['-B', join(root, 'model_benchmark_project.py')], {
        input: JSON.stringify(request), encoding: 'utf8', timeout: 15000, maxBuffer: 128000
      });
    if (child.status !== 0) throw new Error('Project oracle failed: ' + (child.error || child.stderr));
    return JSON.parse(child.stdout);
  }
  const spec = oracle({op: 'spec'});
  const rows = [];
  report.project = {stages: rows, complete: false};
  let built = {};
  for (const stage of ['build', 'amend', 'repair']) {
    const before = stage === 'build' ? {} : stage === 'amend' ? built : spec.seed;
    if (stage === 'amend' && !rows[0].passed) {
      rows.push({stage, passed:false, skipped:'Initial project failed behavioral verification'});
      save();
      continue;
    }
    let prompt = spec[stage];
    if (stage !== 'build') prompt += '\nCurrent files:\n' + JSON.stringify(before);
    if (stage === 'repair') prompt += '\nObserved test failure: ' + spec.seed_failure;
    const row = {stage, passed:false, attempts:[]};
    rows.push(row);
    const messages = [{role:'user', content:prompt}];
    for (let i=0; i<2; i++) {
      const began = Date.now();
      const answer = await generate(messages);
      const verdict = oracle({op:'judge', stage, before, answer});
      row.attempts.push({answer, diagnostic:verdict.diagnostic, elapsed_ms:Date.now()-began});
      row.passed = verdict.passed;
      save();
      if (verdict.passed) {
        if (stage === 'build') built = verdict.files;
        break;
      }
      messages.push({role:'assistant',content:answer},{role:'user',content:'Independent verification failed: '+verdict.diagnostic+'. Correct your answer. Return the complete requested JSON.'});
    }
  }
  report.project.complete = true;
  save();
}
