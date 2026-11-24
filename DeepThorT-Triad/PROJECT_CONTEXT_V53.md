# DeepThorT v53 — one-click latest acceptance profile

Baseline: local v52 source overlay, dual supervised local Qwen ONNX 8765/8766, shared 30% Windows Job Object, JANUS/Sentinel original 11-core societies, original eight-tab Tk interface. No change to Windows launcher/model/permissions.

Implementation: `LATEST_TEST.json` strictly selects built-in test identifiers; `deepthort_local/latest_acceptance.py` validates profile, executes fixed registered probes and saves atomic JSON results; `desktop_app.py` exposes Processes -> Run latest test / Stop latest test. First profile: shared Windows job membership, primary PID/health, secondary PID/health with up to 180 seconds to load, JANUS inbox, one bounded 20-token local ONNX reply on the secondary model (while preserving real queued advice), and honest concurrent activity status. No arbitrary JSON-provided code, commands or URLs. No project-file edits or game starts.

Every run generates a per-run JSON report under state/latest-tests and a verified ZIP under diagnostics automatically. The ZIP carries the sanitized acceptance report in summary.json and saved logs; no raw prompts or credentials are added. The existing Locate latest diagnostics button finds the ZIP from the receipt. Cancellation prevents subsequent checks; an in-flight HTTP call has a finite timeout and is not forcibly killed.

QA: new manifest safety, editable profile, atomic result, cancellation and actual Tk integration tests; compile and existing regression suite. Native 30% Job CPU rate and real model accuracy are not proven by Linux CI. `is_capped_windows_process()` confirms Job membership, not Job rate; label accordingly.
