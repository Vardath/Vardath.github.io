# DeepThorT Triad — experimental three-resident-model copy

Independent copy of the Qwen source at 8b8ff17c. No original DeepThorT files or state changed. This fork replaces text inference with a pinned llama.cpp Windows CPU runtime (not the Llama neural model or Ollama). The three publisher Q4_K_M GGUF files are verified against fixed SHA256 values:

* Implementation: EssentialAI Rnj-1-Instruct 8B, 5.11 GB.
* JANUS: IBM Granite 4.2 3B, 2.24 GB.
* Sentinel: OpenBMB MiniCPM5 2B, 1.56 GB.

All three model processes must remain resident. No time-sharing of weights, automatic substitutions, cloud inference or independent resource budgets. Each has its own local inference endpoint and lock, allowing simultaneous requests. The existing desktop and both persistent coordinator stores remain; the broker maps named council roles to their assigned model. Long specification and draft planning use JANUS, implementation uses Rnj-1, Sentinel verdicts use MiniCPM5. Model roles remain subject to the original project authority and verification gates.

## Install and run

Copy this entire folder to a NEW directory, e.g. D:\deepthort-triad. Do not overlay the Qwen installation or copy its state. Close original DeepThorT first; both versions use the same desktop compatibility ports, 8765/8766. Run START TRIAD.cmd (Python 3.11+ x64 and Windows required). Click Install AI to approve download of approximately 9 GB; alternatively run install.ps1 explicitly. Start AI. All three must reach ready. Initial context is 4096 tokens per engine; existing text budgets are retained and actual context overflow is reported, not silently truncated by the broker.

## Resource and test boundaries

Original Windows Job Object launcher caps aggregate CPU and committed memory at 30%, with idle priority. Broker verifies inherited hard CPU and memory limits before launching; children start suspended, are assigned to nested kill-on-close jobs, then resumed. No GPU, memory mapping disabled, two CPU threads per model. Combined admission requires weight bytes plus 1.5 GiB estimated overhead and a 10% free-system-memory reserve. The OS may still reject allocations. If one model exits, broker exits and all three are stopped. No automatic eviction or single-model fallback. At 40 GB RAM this may be very tight. Real Windows load, simultaneous inference, CPU/commit enforcement, all model templates and task reliability are unverified. Focused source CI tests are not a Windows/model acceptance test.

Original Qwen-specific release manifests, manuals, benchmark history and old tests are inherited historical material, not Triad release validation. Do not run old ONNX startup scripts. The experimental copy is source, not a signed executable or packaged binary. Additional specialist instances not implemented in this pass.


## Startup repair 1
Windows diagnostics showed all three publisher downloads verified; implementation runtime exited before either other model loaded. Prior launcher suppressed native diagnostics, so memory exhaustion is not established. Native children now have valid redirected stdout/stderr handles, run with the DLL directory as working directory, log role and exit code, and run a capped version probe before weights load. Reduced inference batch and microbatch to lower avoidable temporary memory; all three models still resident, 4096 context and original hard cap retained. No weights/runtime changed. If a failure remains, the exact startup error is printed in Processes; native logs in `state/logs/triad-*-native.log` may contain private prompts after inference, so share only startup logs or review before sending. Apply source update without reinstalling models.
