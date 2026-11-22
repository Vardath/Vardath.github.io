# DeepThorT v36 development handover — 22 November 2026

Base: full, complete v35 Windows ZIP and verified GitHub commit `83c49df4eb001c42851d3cb5c8aa0091cfcaa851`. Preserve JANUS/Sentinel topology, local ONNX Qwen model, 20%-CPU and RAM-commit budget, gaming priority, state and all approval gates.

An actual v35 GitHub Actions job failed in the preexisting v33 and v34 generated script and execution-safety test fixtures. The error was at `ToolAcquisition.authorize_probe` — `Tool not discovered as a real executable`: GitHub's Python executable was a symlink while the tool library intentionally rejects symlink tool paths. v36 corrects only the test fixtures using `Path(sys.executable).resolve(strict=True)` and retains the production rejection behavior. Do not claim the v35 CI job passed.

v36 additionally exposes a per-query, manually approved `winget search` lookup, bounded to 20 results from source winget, no shell, no installation or download. `deepthort_local/online_tool_search.py` is deterministic and validates queries; desktop wiring in `desktop_app.py` logs results through the existing Processes command runner. Query results are untrusted data and do not dynamically add package IDs to the fixed installer catalog. User-specific online search, network traffic and real Windows winget are unverified until on-PC acceptance.

Updated `USER_GUIDE.html`, hover tooltips and `NEXT_STEPS.md` are included in the installation root. The guide's screenshot is an actual virtual-display GUI capture; it does not demonstrate Windows model runtime. Next steps: confirm live user test, verified checksums/signatures before any arbitrary new installers, version-aware application adapters and behavioral acceptance for a real X4 mod and Android game. Existing script execution is not sandboxed and must remain expressly approved.

Package production and remote CI evidence are separate. The release ZIP must preserve original v35 models/state layout, scripts and launcher byte-for-byte apart from planned changes. Never override concurrent Scratch-Chat commits.
