# DeepThorT v52 — trustworthy diagnostics and observable JANUS model state

Baseline: verified v51 source; offline Qwen2.5-Coder-1.5B-Instruct with two possible supervised instances sharing the same Windows CPU/job memory cap; original eight-tab Tk desktop and unchanged JANUS/Sentinel systems.

User report: Export diagnostics said the ZIP was saved but could not be found; a JANUS conversation/instruction stayed at “waiting for local model.” No newly exported diagnostic was attached, so the cause of that specific missing ZIP or secondary startup has **not been established**.

## Implemented

- Export now builds an atomic temporary ZIP, verifies CRC and readable summary.json, replaces the selected ZIP only after verification, and rechecks it. A failed verification leaves an earlier file intact rather than reporting success.
- Store a second SHA-256-identical copy in `D:\deepthort\diagnostics\` regardless of the Save As location, with a path/hash receipt at `state/last-diagnostic-export.json`. The success dialogue prints both full paths and can open the selected folder. Processes > **Locate latest diagnostics** verifies and finds either copy after restart.
- Show why the secondary model is waiting in Processes and JANUS & Sentinel: primary ONNX starting/stopped, cap not verified, Windows RAM below 6 GiB free, secondary starting/loading, busy inference, or exhausted restart attempts. The existing health response supplies concrete loading stage and elapsed time when available.
- Add **Retry JANUS model** without interrupting an active model call. Detect ANY process binding port 8766, including an unmanaged or mismatched server, rather than launching into an occupied port and exhausting restarts.
- Add bounded secondary-model status into diagnostics metadata, without recording raw instructions or model responses.

## Boundary and acceptance

This release does not assert that the original missing file was created anywhere, or that the user's council ONNX successfully loaded. Those claims require the new Windows diagnostics or live Windows observation. There is no extra ONNX worker, no cloud fallback, no reduced security or CPU cap and no change to file approvals.

For Windows acceptance, use Start AI, then send an instruction with Ctrl+Shift+Enter; open Processes/JANUS for the specific council state. Export diagnostics and use **Locate latest diagnostics**. Check ZIP in the chosen directory and retained `D:\deepthort\diagnostics`; inspect `state/last-diagnostic-export.json`; verify no approved job is modified or paused. If the council worker fails, the logs in the retained ZIP should show the port, PID and model-load or failure stages.
