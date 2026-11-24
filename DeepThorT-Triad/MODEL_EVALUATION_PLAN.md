# Local coding model evaluation (proposal, not a model change)

Current baseline: Qwen2.5-Coder-1.5B-Instruct ONNX, existing dual worker architecture, pinned Transformers.js, CPU only. Keep current model and state intact until an alternative passes acceptance. ONNX is a runtime/model format, not the neural model.

Candidates: Qwen2.5-Coder-3B-Instruct ONNX Q4 (https://huggingface.co/onnx-community/Qwen2.5-Coder-3B-Instruct), Qwen3-4B ONNX (https://huggingface.co/onnx-community/Qwen3-4B-ONNX), and Qwen3.5-4B (https://huggingface.co/Qwen/Qwen3.5-4B; compatible export/runtime must be checked independently). Qwen2.5-Coder-7B may be a later candidate if memory permits. Qwen3-Coder-Next has 80B total parameters despite 3B active per token; it is not a 3B memory-footprint model.

Acceptance: compare same quantization/runtime where possible, on fixed independent coding tasks, original-spec and amendment interpretation, exact JSON tool requests, project planning, multi-file changes, behavioral test validity, repair and evidence rejection. Record pass rates, time to verified result, peak aggregate committed memory, working set, startup, token rate, failures, gaming preemption and both-worker resource usage. Reject candidate if shared 30% caps, offline-only operation or existing Windows compatibility fail. Do not silently download, activate or migrate model weights. A separate approved evaluation build is required; no change to pinned runtime in this pass.


## Evaluation priority — first-stage real inference

The owner explicitly prioritizes reliable correctness over speed. The experimental runner uses the same Transformers.js 3.8.1, CPU, one intra/inter-op thread, deterministic greedy decode, 768-token output limit as the production worker. No production file, port, or state changes. Three pinned public profiles: baseline Qwen2.5-Coder 1.5B Q4, Coder 3B Q4 (external weight data), Qwen3 4B Q4F16 (different quantization, CPU compatibility unproven, /no_think request). GitHub Actions loads actual weights and generates synthetic answers; no user projects or secrets are sent to hosted runners. Download and initialization are separate from offline generation; no remote inference API.

14 fixed tasks: algorithm implementation/repair, amendment adherence, tool JSON, planning dependency structure, untrusted evidence, behavioral test oracle and long instructions. Python scoring uses a bounded AST interpreter, not execution of model code; unsupported syntax is a separate result. Raw answers and fixed-oracle scores are saved, with startup, elapsed time and sampled RSS. This is an initial screen, not end-to-end coding acceptance. Hosted RSS is not Windows committed memory.

On the actual updated Windows installation, close DeepThorT and both workers first. Run one profile at a time from the DeepThorT directory:

    py -3 model_benchmark_prepare.py baseline --download
    py -3 model_benchmark_windows.py baseline
    py -3 model_benchmark_score.py benchmark-local/results/baseline.json

Repeat with coder3b and qwen3-4b. The download verifies pinned file hashes and stores experimental files separately. Offline Windows inference uses the existing Job Object 30% CPU/commit limits. Single-worker test does not establish dual-worker feasibility. Do not run simultaneously with production or games. No automatic model activation. Next: compare actual results, troubleshoot load failures, add realistic multi-file project and autonomous repair tests, verify both-worker Windows resource feasibility before promotion.


### First hosted attempt
Run 45487080395 failed before model inference for all three profiles: ONNX Runtime 1.21.0 installer attempted to fetch unnecessary Linux CUDA binaries and received HTTP 404. Normal source CI 45487080483 passed 927 tests across 147 modules. Benchmark-only installation now explicitly skips CUDA using the installer-recommended option; production dependencies unchanged. Rerun all three profiles; no model scores yet.
