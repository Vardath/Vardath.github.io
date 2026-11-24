# DeepThorT v42 handover — evidence-backed dependency graph and source revisions

23 November 2026 — builds on verified v41 commit `63fbcbb1620ee84a718a00a883dba98bc4e0ba9c`.

## Architecture unchanged

- Sole coding/conversation LLM: **Qwen2.5-Coder-1.5B-Instruct ONNX** via Transformers.js. No Scratch Chat, other local model, Ollama, cloud endpoint or paid model fallback.
- Original 8-tab Tk UI, JANUS coordinator, Sentinel watchdog, Windows Job Object gaming cap, process gates, v39 software policy, v40 job-bound authorization and v41 three-test/two-repair cycle remain intact.
- `D:\deepthort\state`, project files, models, local references and original Windows launcher are preserved by source overlays.

## New v42 capabilities

### 1. Durable local dependency DAG

`deepthort_local/task_graph.py` owns `state/task-graph.sqlite3`. A DAG is created only for a **real approved build** with a v40 grant. Its nodes represent the *observed* plan approval, individual approved source artifacts, an observed fixed verification executable, actual verification and accepted source/test evidence. The exact planned source stage order is preserved; no hardcoded game plan or fabricated file paths are introduced. The approved job, project, plan and original prompt SHA-256 are bound to the graph.

Hierarchical milestones can additionally link their already-indexed requirement IDs, original source-checksum evidence, file intentions and **declared** file dependencies. This is a source-to-file *scope trace*, **not proof that a requirement has been implemented**. A dependency that contradicts the approved order fails rather than being silently reordered. For huge original prompts, a bounded graph does not re-read/re-hash a multi-million-character source on the GUI thread; the original indexed hierarchy remains available separately.

Before a fixed automatic test, the graph checks that all approved artifact hashes still match disk, and that the recognized test executable is actually locatable. Presence is not capability verification; real tool version checks remain v43 work. A passing result must include the existing accepted test/source evidence to reach `evidence: recorded`; it never means Android/X4 gameplay is independently proven.

### 2. Crash-safe execution leases

An immutable randomly identified action lease is written to SQLite before each **new v42** unattended file write, ONNX repair or local verification subprocess. Only one live lease may exist per approved job. On restart unfinished leases are marked interrupted, corresponding nodes become `needs_attention`, and the job is **not** silently replayed. Existing v41 development-cycle interruption and retry limits still apply. A repaired file resets graph verification/acceptance to unverified.

### 3. Multi-file, content-addressed source checkpoints

`deepthort_local/source_checkpoints.py` writes to `state/source-checkpoints/job-N/`. The exact source set (up to 24 files and 4 MB of bounded UTF-8 source per revision) is recorded **before initial generation** and after each authorized source save and repair. Immutable revision manifests refer to SHA-256-addressed source blobs, with no redundant copies of unchanged blobs. Maximum 60 revisions per job; a full quota blocks further unattended source saves rather than dropping older checkpoints. These are private local project sources; they are NOT included in diagnostic exports.

The Work queue shows graph progress and checkpoint revisions. **Restore source checkpoint…** requires explicit user selection and confirmation. The entire current source scope must match its most recent recorded snapshot; external edits or corrupt/missing blobs refuse rollback *before* any file changes. A pre-restore emergency revision is created. Old files are restored with the original atomic writer and backups; files newly created since the chosen revision are **quarantined, not deleted**. Existing approvals, graph progress and prior test results become invalid, and the old plan cannot be re-queued. Re-approve a **new** plan to resume development. Multi-file restore is sequential, not a guaranteed atomic transaction; an interrupted restore needs manual recovery from its emergency checkpoint.

### 4. Original interface and help preserved

The eight original tabs and controls remain; Work queue gains a checkpoint restore control and task-graph/checkpoint evidence in job details. Passive hover help, F1 illustrated guide, `NEXT_STEPS.md`, diagnostics and existing subprocess controls remain.

## Safety/evidence boundaries

- Untrusted model output, web pages, test logs and project files **cannot** authorize new commands, off-plan writes, new requirements or new graph edges.
- Generated tests run with the user's ordinary Windows account and are **not sandboxed**. Normal UAC remains active, with no elevation bypass.
- A source checksum records what was saved, not successful compilation, gameplay or fulfilment of the entire original specification.
- Rollback is explicit; **no automatic undo** on a model-suggested failure. A rollback can intentionally invalidate a previously successful milestone. All user state/backup directories must survive updates.
- Legacy v41 grants without a v42 baseline continue their v41 controls; a new v42 source-restore feature requires a v42 approval/baseline. Missing graph or checkpoint metadata is never invented or treated as verified.

## Validation and next work

New modules: `tests/test_task_graph_v42.py`, `tests/test_source_checkpoints_v42.py`, `tests/test_task_graph_gui_v42.py`. Focused tests include dependency prerequisites, real GUI plan-to-test-to-rollback, tamper/revocation, source hash conflicts, explicit rollback, missing blobs and restart lease interruption. Full isolated Linux Xvfb regression and a source-overlay artifact are required on GitHub Actions before declaring the release complete. Physical Windows 10, UAC, 20% gaming limits, ONNX quality and X4/Android gameplay remain untested until user acceptance.

Next **v43:** real post-install executable/version/capability probes and durable tool-task unblocking. Later: multi-milestone scheduling under explicit approvals, richer task adaptation, signed provenance/safer downloads, game-specific build/acceptance adapters and real device/game verification.
