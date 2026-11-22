# DeepThorT v41 engineering handover — 23 November 2026

## Baseline / identity

Continues v40 source at GitHub commit `fc2772327454dc0916d5085f9481ce3678bc1d35`.
Same local `Qwen2.5-Coder-1.5B-Instruct` ONNX/Transformers.js inference,
JANUS/Sentinel 11-core supervisors, Tk eight-tab desktop, and existing
Windows 20%-resource supervision. NO Scratch Chat integration, cloud fallback,
external general agent loop, arbitrary tool invocation, or change to the model.

## Implemented in v41

1. `deepthort_local/development_cycle.py` adds a durable SQLite ledger at
   `state/development-cycles.sqlite3`. Each job is tied to the original
   approved project path, original stage/plan fingerprint and a bounded
   `test -> failure evidence -> one-file ONNX repair -> retest` state machine.
   At most **3** tests and **2** repairs can occur for one job. Separate
   events record started, diagnosed, repairing, saved, verified and blocked.
   Exit 0 alone is *not* accepted: existing source-snapshot, nonzero-test and
   independent engine/static acceptance evidence still governs completion.
2. Existing v40 project authority is extended with `authorize_repair_context`,
   `authorize_repair` and `record_repair`. Only an already-saved file in the
   exact approved plan is editable. A pre-repair SHA-256 check, the existing
   atomic writer and timestamped backup apply on EACH replacement. Saved
   SHA-256 receipts are updated only after real writes. Off-plan paths,
   changed files, symlinks, executable/install targets, revoked grants and
   expired authority fail closed. No project-wide permission is inferred.
3. On a failing real recognized Python/Godot/.NET/npm/X4 local check, the
   diagnostic must show evidence of a source/test problem before a repair is
   considered. Environment/installer failures and ambiguous output block for
   inspection, not arbitrary model editing. The small ONNX model receives an
   intentionally bounded excerpt of original requirements, failed test tail,
   and at most **two complete small approved source files**. There is no
   hidden truncation pretending to be a complete source. It must respond with
   one exact JSON object containing one approved path and a complete file.
   Only replacements <=1,800 characters are eligible. Bad JSON, no-op output,
   missing model, changed files, exhausted budgets or cancellation block
   automatic continuation without guessing.
4. Desktop `Work queue` now shows durable phase, test/repair counters and
   short actual diagnostics/event history. `Processes` identifies the active
   cycle; exported support snapshots include summary counts only, not raw
   project code or test-output secrets. The new workflow is triggered by
   the existing explicit plan approval and visible v40 standing policy, not
   by casual conversation or pasted model instructions.
5. Global queue pause, JANUS pause, game activity, WinGet operations and
   other process gates still prevent NEW automatic actions. User cancellations
   of a test do not trigger repairs, and cancelling a running verification
   does not accidentally terminate the ONNX model. Uncertain in-flight tests
   or model repairs after a crash are marked **needs_attention** on restart,
   never silently replayed or labelled successful.
6. Python `unittest discover` runs under a **new private bytecode cache prefix**
   for every verification attempt. This prevents a same-size, rapid source
   rewrite from loading stale timestamp-matched `.pyc` and giving a false
   retest result. No user source or existing bytecode cache is deleted.
7. The original JANUS/Sentinel roles remain separate. Both completed tests
   and blocked/awaiting repair states are visible as actual work evidence.

## Limitations (important)

- This implements **a bounded, job-scoped development cycle**, NOT the full
  general autonomous task/dependency graph. Each new hierarchical milestone
  still needs its own approval. It cannot yet autonomously acquire every new
  tool, edit arbitrary large source files, publish products or test live games.
- Verification executes generated project code under your normal Windows
  account; recognized test commands are **not a sandbox**. This is stated in
  the plan approval dialog. Existing normal Windows UAC stays active and is
  never bypassed.
- Model output quality is unverified on the physical machine. Integration
  tests use a *fake model at the ONNX interface* but real desktop, backups,
  SQLite state and a real Python unittest subprocess. This proves glue logic,
  not Qwen's ability to independently debug real software or gameplay.
- A file successfully written and a test that exits zero prove different
  things. X4 gameplay/save compatibility, Android APK deployment, Godot
  playability and real Windows WinGet/UAC all still need actual acceptance.
- Backups are per-file, NOT full atomic multi-file Git checkpoint/rollback.
  An interruption between file replacement and receipt persistence blocks
  automation for manual reconciliation instead of redoing the write.

## Windows installation and first acceptance test

1. Back up `D:\deepthort\state` and close DeepThorT.
2. Overlay the v41 **source-update** ZIP on `D:\deepthort`.
   **Do not remove** `DeepThorT.exe`, `models`, `state`, `node_modules`,
   `cache`, `reference` or any user project.
3. Restart and open Work queue. The v40 checkbox for unattended approved
   file/test work also controls bounded v41 repairs; disable it before a plan
   if you want manual approvals. Approve only a disposable test project you
   trust; generated tests execute with your user rights.
4. Observe a deliberately failing Python test. The cycle should record an
   actual failed process, local ONNX repair attempt, exact source write with
   backup, and subsequent test (or a clear blocked reason). No new file or
   arbitrary command is permitted. Stop a test in Processes and confirm that
   no automatic repair starts. Pause the queue and confirm no new action.
5. Export diagnostics on failure. Check Work queue/Processes logs and
   `state/development-cycles.sqlite3` (local only). Do not send credentials or
   unreviewed source files in diagnostic bundles.

## Next development passes

- **v42:** durable requirement/dependency DAG, bounded task selection,
  component-level multi-file checkpoints and safe undo/rollback.
- **v43:** verified installed-tool executables and real versions, PATH reload,
  appropriate project task unblock/resume rather than trusting WinGet exit.
- Later: engine-specific adapters and genuinely playable project acceptance.

See `NEXT_STEPS.md` for full priorities and `TEST_RESULTS_V41.md` for test
scope. Preserve the v40 GitHub source baseline, not a speculative rewrite.
