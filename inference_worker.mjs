// Local worker thread: model construction and inference never block the UI server.
// This thread creates no console window and makes no network requests.
import { parentPort } from 'node:worker_threads';
import { existsSync, statSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { env, pipeline } from '@huggingface/transformers';

const ROOT = dirname(fileURLToPath(import.meta.url));
const ID = 'onnx-community/Qwen2.5-Coder-1.5B-Instruct';
const ONNX = resolve(ROOT, 'models', ...ID.split('/'), 'onnx', 'model_q4.onnx');
const started = Date.now();
const stage = (message) => parentPort.postMessage({kind:'stage', message, elapsed_seconds: Math.round((Date.now()-started)/1000)});

if (!existsSync(ONNX) || statSync(ONNX).size < 1_700_000_000) {
  throw new Error('Local model is absent/incomplete. Click Install AI; existing conversations will be kept.');
}

env.allowRemoteModels = false;
env.allowLocalModels = true;
env.localModelPath = join(ROOT, 'models') + '/';
env.cacheDir = join(ROOT, 'cache');

stage(`Checking local model: ${(statSync(ONNX).size/1e9).toFixed(2)} GB (offline)`);
stage('Initializing tokenizer and ONNX graph on CPU; this is the expensive first phase.');
let generator;
try {
  generator = await pipeline('text-generation', ID, {
    device:'cpu', dtype:'q4',
    session_options:{ intraOpNumThreads:1, interOpNumThreads:1, enableCpuMemArena:false },
    progress_callback:(event) => {
      if (event && ['initiate','done','ready'].includes(event.status)) {
        stage(`${event.status}: ${event.file || event.name || 'local model component'}`);
      }
    },
  });
} catch (error) {
  parentPort.postMessage({kind:'fatal', error:String(error?.stack || error).slice(0,6000)});
  throw error;
}
stage(`ONNX model loaded in ${Math.round((Date.now()-started)/1000)}s`);
parentPort.postMessage({kind:'ready'});

// Explicit single-flight inference. Cancellation terminates the supervised node process.
let busy = false;
parentPort.on('message', async (message) => {
  if (message.kind !== 'generate' || busy) return;
  busy = true;
  try {
    const generated = await generator(message.messages, {max_new_tokens:message.max, do_sample:false});
    const value = generated?.[0]?.generated_text;
    const output = Array.isArray(value) ? value.at(-1)?.content : value;
    if (typeof output !== 'string' || !output.trim()) throw new Error('Local model produced no text');
    parentPort.postMessage({kind:'answer', id:message.id, output});
  } catch (error) {
    parentPort.postMessage({kind:'request_error', id:message.id, error:String(error?.message || error)});
  } finally { busy = false; }
});
