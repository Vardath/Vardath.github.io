# DeepThorT v54 — local regression results

Based on exact v53 source overlay + targeted JANUS coordinator fix. Initial 653 cases across all 80 modules passed in isolated Xvfb subprocesses (the first 20/21 were counted once). One additional GUI acceptance test was added and passed in the focused rerun: **654 total local tests / 80 modules**, all green.

Added tests verify exported `janus_status.paused`, Sentinel distinguishes intentionally paused JANUS from a hung worker, v54 manifest includes read-only `janus_core`, and the GUI generates a blocked result plus diagnostics for paused JANUS. V53 six existing probes and ONNX programs remain unchanged.

Real Windows recheck is necessary to establish why the coordinator is stalled or paused. This update has NOT been merged to GitHub and has not received GitHub Actions validation. Windows 30% aggregate throughput remains unmeasured.
