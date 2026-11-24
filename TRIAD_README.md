# DeepThorT Triad — native OpenVINO test edition

Three separate, concurrently resident native IR CPU workers, no model swapping, cloud inference, ONNX Runtime, llama.cpp or Ollama for text inference. The original DeepThorT remains unchanged. Models: implementation OpenVINO/Qwen2.5-Coder-7B-Instruct-int4-ov (4.51 GB, Apache-2.0); JANUS OpenVINO/Phi-4-mini-instruct-int4-ov (2.39 GB, MIT); Sentinel OpenVINO/LFM2.5-1.2B-Instruct-int4-ov (683 MB, LFM1.0, review model license). Each publisher revision is fixed in triad_profiles.py. No Python from model repositories is downloaded or run. Native GenAI version 2026.4.1.0 in private runtime/openvino-env.

Close original DeepThorT. Start START TRIAD.cmd, click Install AI and approve ~7.58 GB of native IR downloads plus runtime. Installer probes CPU numerical inference before weights, verifies file hashes from exact revision metadata, then individually loads and generates a synthetic answer from each model (smallest first). Interrupted files resume when server supports Range. Existing GGUF files and old CPU runtime are unused but not deleted. Existing state and projects preserved. Start AI requires all three installed and resident in separate capped native OpenVINO Python workers; installation tests are sequential only. Run latest test checks three PIDs and actual exact replies, not coding reliability. Optional old Florence ONNX vision subsystem remains separate and is not used by text workers.

The original Windows Job Object remains shared: 30% CPU and 30% aggregate committed memory; no GPU. Native IR non-mapped load requested, two threads, one stream per role; prompt + output limited to 4096 actual tokens. Initial weight sizes leave estimated headroom, not proof that actual combined allocations fit. No runtime fallback or silent model substitution. A native failure terminates the broker and its nested model jobs. Logs are retained for diagnosis. Host CI tests only source contracts unless explicitly running real models on Windows. Native runtime and real model accuracy remain unverified until installation smoke tests and concurrent acceptance pass.

Old Qwen release history/manuals and previous benchmark files are inherited historical artifacts, not this edition's acceptance results. 

The root Job Object now has a random name and is checked by actual membership and limit values even inside a nested cleanup job. A Windows virtual-environment launcher can have a different PID from the real serving interpreter; health must identify a PID belonging to the exact child job. Windows CI runs a real native OpenVINO numerical preflight under the shared cap, not a full three-model inference benchmark.


### Python compatibility repair
OpenVINO GenAI 2026.4.1.0 has no Python 3.15 Windows wheel. The installer now checks x64 Python 3.10–3.13, prefers the current supported interpreter or the explicit Python launcher selectors (3.13 first), and preserves incompatible private environments with an `openvino-env-incompatible-` name before creating a new one. Install Python 3.13 x64 from python.org if no supported Python is installed. No change to the selected models, shared Job Object cap, or original DeepThorT. Windows real model acceptance is still required.


### Automatic runtime bootstrap
Install AI now provisions private CPython 3.13.17 x64 from the official pinned CPython NuGet package if no compatible interpreter exists. It checks the catalog SHA-512, extracts only the tools directory with bounded path validation, tests the interpreter, and builds the isolated OpenVINO environment. No global Python or PATH changes. Previous incompatible environments are preserved. A runtime-only preflight is available under the shared Windows job. No production model or cap changes.
