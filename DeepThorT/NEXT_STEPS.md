# DeepThorT next steps — after v49 (23 November 2026)

**Verified v49 scope:** Long indexed specifications can traverse multiple 40-call review/correction batches while *objective* coverage progresses, and pause on 8 consecutive correction calls without a closed acceptance check. Durable per-call acceptance receipts, original sections and model-authored file proposals are retained across restart and explicit retry. There is still no newly approved source file, game process, or test until the user authorizes the relevant milestone. The diagnostics prompting this change had 40 actual correction requests, 9 persistent missing checks and zero generated files.

**High priority v50:** Improve the local 1.5B model's X4 planning correctness, not merely its retry budget: test actual source-specific model outputs, durable per-criterion contracts and conditional narrowing, report which of the 9 checks stay unresolved, verify real PE macro/connection references against installed X4. Add a fallback to smaller independent subplans with explicit requirement coverage; never fabricate X4 identifiers or allow incomplete proposals to masquerade as a working mod. After completion, build and validate a real extension in `D:\x4mods` under explicit approval.

**Long-project roadmap:** Plan a *project-scoped* autonomous task scheduler that carries approved design → code → test → diagnosis → repair → retest across restarts, with evidence, milestones, resource monitoring, backups and bounded retries. Currently **automated continuation is only for indexed planning**, not autonomous approval of later milestones or unattended X4/RimWorld/Android playtesting. The user's 20% Windows CPU/commit cap and foreground-game priority must remain enforced across all spawned children; GPU usage still needs a separate guard.

**Windows acceptance:** Run v49 on the actual 20% capped Windows installation with Qwen ONNX. Look for "batch 2" only after measurable progress. If it pauses after 8 zero-gain corrections, compare before/after missing-check lists and capture logs. Check Stop reply/cancel, app restart, original spec hashes, no unauthorized files, and absence of false project-approval states.

---

# DeepThorT next steps — after v48 (23 November 2026)

v48 closes a blocking path in indexed X4 planning: when all source sections have been reviewed but the combined roadmap is still missing mandatory X4 files/behaviours, retry runs model-authored, scope-bound corrections instead of failing instantly from unchanged cached proposals. Source sections remain exact and indexed; structurally safe corrections are persisted and still require current full-domain validation and individual approval. v48 also corrects the stale startup version field.

**Next acceptance:** Install the v48 overlay, retry the existing 7,422-character Xenon PE request in `D:\x4mods`, observe actual model correction passes and whether Qwen can supply X4-valid XML file intentions. The local test suite uses scripted model replies; it does not prove the actual 1.5B model will satisfy every missing requirement. Export new diagnostics if still blocked. The 20% Windows process-tree CPU cap and original 40-call budget remain unchanged.

**Other priorities:** Instrument a real ONNX process exit with exit code and memory-commit telemetry, verify GPU/contention behavior, and build end-to-end X4 mod execution/playtest after reliable model plans and approvals. No source files may be fabricated to make a validator pass; full original specifications must remain preserved.

---

# DeepThorT next steps — after v47 (23 November 2026)

v47 restores eligible, exact-input old planning replies and exact-hash large-document sections from surviving local SQLite state; pauses local ONNX transport failures rather than losing them; prevents busy-worker duplicate submission and performs at most two supervised crash restarts, all under the existing 20% cap. Complete model-output loss remains unrecoverable without a user-provided source: older redacted diagnostic logs contain no reply text. 40 is a per-batch inference-attempt budget, not a file limit or maximum runtime.

**Next:** Verify root cause of repeated process exits using actual Windows Event Viewer fault data, memory-commit utilization and ONNX worker exit codes from an updated diagnostics ZIP. Test v47 with a reissued PE project plan and check original reply/section reuse. Benchmark 40-pass plan completion and improve local Qwen's X4 JSON validity without substituting hardcoded intentions. Continue engine-specific X4/RimWorld acceptance profiles and real gameplay tests. Keep the 20% CPU/committed-memory policy.

---

# DeepThorT next steps — after v45 (23 November 2026)

**Implemented:** User-approved project-local Windows `.exe` runs on a new **non-input Win32 desktop**, limited to 25 seconds, low priority, *same parent job-wide 20% CPU cap* and nested kill-on-close cleanup. Read-only window metadata and outcome receipts; pressure preemption and stop controls; no global keyboard/mouse simulation. Program executable hashes must match at launch; the test is not automatically replayed after crash. Project code runs with the current Windows account permissions. Native Windows acceptance remains outstanding; the implementation does not cap GPU, mute arbitrary GUI audio or guarantee rendering on the alternate desktop.

**Next v46:** Godot native scripted gameplay probe adapter: physics/scene assertions, simulation-time bounded steps, telemetry on player interactions and collision, optional offscreen screenshots only if supported without foreground changes, reversible test profiles; no fabricated graphical assertions. Explicit, fixed test contracts, not model-provided arbitrary commands.

**Then:** Isolated emulator (ADB APK install/launch with owned AVD), X4/RimWorld disposable mod/profile staging with log capture and save restoration, visual window automation only in an actually isolated session/VM. Protect the user's currently running Steam/game process and never commandeer input or assume X4/RimWorld are headless. Guard GPU/audio budgets with actual evidence before allowing graphics-heavy unattended launches. Avoid silent UAC bypass, unknown binaries, cloud inference, or replacing ONNX/JANUS/Sentinel architecture.

---

# DeepThorT next steps — after v44 (23 November 2026)

**Delivered v44:** An explicit, quiet Godot scene-simulation action under Work queue, backed by persisted run receipts and bounded resource pressure checks. It uses a fixed Godot `--headless --path ... --quit-after 360` command for a declared main scene; no game window, dummy audio, no input/focus injection. Starts from an existing `DeepThorT.exe` capped Windows Job Object, so the headless game shares the SAME aggregate 20% CPU and RAM-commit budgets; it does **not** get its own 20%. Child is idle priority. Safe real scene results are clearly labelled `headless_smoke_passed`, not verified interactive gameplay. Foreground game workloads are allowed, but the test is automatically preempted if system RAM reserve drops below 10% or system CPU exceeds 90% for three consecutive samples while a game is detected. OS cannot enforce a simple aggregate 20% GPU-use cap here. Tests execute project scripts as the current Windows user; they are **not sandboxed**.

**Next v45:** Implement bounded, actively supervised launch of generated Windows GUI programs with test-account isolation and explicit permission to interact with windows. Use window-handle identity, foreground focus checks, screenshot/process/log evidence, process-tree stopping and failure classification. Never control keyboard/mouse globally while the user is working or gaming. For actual hidden graphical scenes use a separate session/virtual display or an engine-provided offscreen harness; a hidden window alone is not a safe isolation technique.

**Next v46:** Godot gameplay-specific scripted probes and scene telemetry (actual collision/movement logic) with assertion logs and reversible saves. Android emulator isolated instances and X4/RimWorld disposable test profiles follow. Real game builds, install/staging and reboot-safe game testing need independent receipts and version checks. Do not playtest X4 and RimWorld invisibly by merely suppressing the window; they can require rendering, Steam or interactive input and cannot be assumed to work headlessly.

**Validation still required:** Real Windows 10/11 and GPU contention, actual Godot executable and game scenes, parent/child Windows Job cap membership, user input focus while playing, RAM pressure and alternate game process detection; CI mocks and a simulated process do not establish those outcomes. Keep the original model, state, launcher, WinGet UAC and project permissions.

---
# DeepThorT next steps — after v43 (23 November 2026)

**Implemented in v43:** durable independent detection of known installed CLI
executable versions following approved catalog WinGet installations; bounded,
fixed flags and version parsing; serial game-aware background probes; current-
session PATH recovery and stale-file detection; separate `located_only` for
GUI applications; registry entries alone no longer count as executables. This
is an evidence probe, not app signature verification or gameplay.

**Priority v44:** one real, instrumented project run/launch acceptance adapter,
prefer Godot and Windows programs. Verify real artifact, approved safe staging,
process/window identity, bounded input and observation, crash/output logs,
retry/stop and restore checkpoint. An app simply opening is not playtested.

**Priority v45+:** Android SDK/Gradle/device readiness after installations,
APK build and ADB/emulator playtest; X4/RimWorld disposable mod staging,
actual game startup/log and save-interaction checks; separate Blender etc.
Explicitly preserve originals and keep game performance caps. Build tests
are not a security sandbox and must not be treated as in-game acceptance.

**Unchanged:** Sole local Qwen ONNX, no cloud fallback, original eight-tab GUI,
JANUS/Sentinel, offline project grants, original Windows launcher and models.
Real Windows deployment, WinGet/UAC and user GPU/CPU benchmarks remain untested
in Linux CI. See PROJECT_CONTEXT_V43.md and PLAYTEST_ACCEPTANCE_V43.md.

---

# DeepThorT next steps — after v42 (23 November 2026)

**Completed:** v42 adds an exact approved-job dependency DAG at `state/task-graph.sqlite3`, evidence-linked source/test/tool prerequisites, persisted source-hash/task progress, interrupted-action leases, bounded multi-file versioned checkpoints and explicit rollback with quarantine. The original ONNX-only v41 three-test/two-repair cycle, v40 project grants, JANUS/Sentinel and Windows gaming controls remain. Full details in `PROJECT_CONTEXT_V42.md`.

**Priority v43 — close the tool-bootstrap gap:** locate executables after curated WinGet installs, inspect real installed versions, check known low-impact command/API capabilities and PATH refresh requirements. Link probe evidence to each blocked approved graph node, with explicit non-arbitrary retry/unblock rules and no trust in WinGet exit codes alone. Preserve UAC and the v42 task-lease boundaries.

**Priority v44:** safely coordinate *multiple* separately approved hierarchical milestones, requirement trace propagation and observed prerequisites; multi-file crash reconciliation and optional Git snapshots/undo without re-writing history, per-commit conflict detection and source hash receipts. Do not auto-approve an unrelated milestone.

**Later:** vetted official software provenance and signature validation, sandboxed/permission-bounded untrusted project tests, Godot/Android SDK/Blender/X4/RimWorld adapters, verified artifact builds and real engine/device/gameplay acceptance, ONNX performance measurements with the gaming cap.

**Current limits:** A graph records approved intention and execution evidence, **not guaranteed semantic coverage** of a million-character specification. v42 only probes test-executable existence, not installed version/capability. Up to 24 source files/4MB per checkpoint and 60 revisions per job. Manual rollback quarantines newly created files but is sequential; an interruption requires emergency checkpoint inspection. No paid/cloud LLM, Scratch Chat substitution, silent elevation bypass, arbitrary downloaded installer/script or unauthorized publishing.

**Windows acceptance:** keep D:\deepthort\state, Qwen ONNX model, original launcher, user projects, reference/cache/node_modules. Back up state and test on a disposable project first. Use Work queue to see the task graph; confirm a tested job, choose its approval-baseline checkpoint, verify source restore and approval invalidation. Read full `PROJECT_CONTEXT_V42.md` before enabling on important projects.

---

# DeepThorT next steps — after v41 (23 November 2026)

**Implemented:** Durable approved-job test/diagnose/repair/retest loop, with
3-test/2-repair budget, exact file source receipts, ONNX-only repair proposals,
backup writes, shutdown interruption protection, queue/game/JANUS gates and
visible evidence. Source file size for unattended repair is deliberately
small to stay inside the 768-token local ONNX output ceiling. No general
autonomous task dependency graph yet. No cloud model or Scratch Chat.

**Priority v42:** Persistent DAG of requirements, tools, artifacts and test
acceptance contracts; versioned source checkpoints with rollback and approval
invalidations. Include a durable execution lease so subprocesses cannot be
silently replayed after interruption, and distinguish blocked dependencies
from actual source failures.

**Priority v43:** Post-WinGet executable discovery, real version/capability
checks, PATH reloading, and project-specific unblock/retry decisions. Do not
trust successful installer exit as proof of a working application.

**Then:** More capable but deterministic application adapters (Godot/Android,
X4/RimWorld, Blender, documents/media), evidence-backed launch/test tools,
reliable GUI automation, actual APK and game acceptance. Preserve all earlier
source and authorization constraints. Benchmark Qwen repair quality under
the Windows 20% resource cap; user test logs are still required.

**Constraints:** Max 768 new tokens per ONNX response; no arbitrary model
commands, silent elevation bypass or unsafe new installations. A complete
Python/Godot/X4 static test is not automatic proof of working gameplay. Always
keep `D:\deepthort\state`, original Windows launcher, models and projects.

---

# DeepThorT next steps — v40 (23 November 2026)

**Current source:** local Qwen ONNX, JANUS/Sentinel, v39 curated routine
WinGet tool management plus **v40 job-scoped reversible file saves and fixed
test execution** after one explicit project-plan approval. Toggle in Work queue
(default enabled); revoke any selected job. Native Windows UAC remains active.
See `PROJECT_CONTEXT_V40.md` for exact scope and Windows test procedure.

## Implemented in this pass

- Durable exact-job grants with project directory, plan SHA, exact file paths,
  existing-target fingerprints, 30-day lifetime and revocation.
- Atomic project writes with timestamped backups, saved-artifact SHA receipts,
  conflict rejection and fallback to manual review for unsafe files.
- Fixed-profile local testing after all recorded files match on disk; no
  per-test dialog, no model-made shell invocation and no blind failure retry.
- Explicit game, queue, JANUS, running-tool and active-model gating.
- Existing milestone and user-approval boundaries remain unchanged.

## Highest priorities remaining

1. **Task graph v41:** persistent requirement -> files -> actual build -> tests
   -> bounded diagnosis -> repair -> retest; classify blocked/failed, prevent
   duplicate actions after restart, and make progress evidence prominent.
2. **Git/version snapshots and undo:** user-visible diffs, per-file and
   checkpoint rollback, multi-file transaction repair, and safe invalidation
   of authorization when the scope or selected project changes.
3. **Post-install tool verification:** locate the executable, inspect real
   version and capability, reconcile PATH changes/restarts, and link verified
   tools to the waiting project task rather than trusting a WinGet exit code.
4. **True dependency resolution:** infer engines/formats/versions from large
   specifications, compare project pins and installed software; move beyond
   simple keywords and fixed WinGet catalog.
5. **Trusted source acquisition:** official publisher identity, independent
   Authenticode/signature provenance, bounded quarantine, Defender checks,
   safe rollback and audited install/uninstall boundaries. Unknown software
   must not run just because a model says to download it.
6. **Versioned creation adapters and GUI automation:** Godot/Android, Blender,
   X4/RimWorld, books, graphics, audio/video, CAD; confirmed window identity
   and cancel/inspect controls rather than guessing screen coordinates.
7. **End-to-end acceptance:** actual APK in emulator/device, playable game,
   mod save compatibility, media rendering and source-backed requirements.
8. **Windows and CPU benchmarks:** test ONNX inference speed, UAC, installation
   controls, v40 grants, v39 catalogue, pause/restart and 20% resource limits.
   Linux CI is NOT proof of these hardware behaviors.

**Hard limits:** v40 still needs one approval for each separate milestone,
does not automatically repair arbitrary failures, and does not sandbox
generated project tests. No real Windows game/autonomous-build acceptance has
been demonstrated. Preserve `state`, `models`, `reference`, `cache`,
`node_modules`, original executable and all user projects during upgrade.

---

# DeepThorT next steps — v39 (23 November 2026)

**Current runtime:** local Qwen ONNX with JANUS coordinator/Sentinel watchdog.
No Scratch Chat integration or paid/cloud model fallback. User preference:
**do useful project work without interrupting for every routine action.**
Windows elevation, when required, must continue through the normal UAC prompt.

## Implemented through v39

- Eight-tab desktop, offline illustrated guide/F1, passive hover tooltips.
- Durable chat/work queue, indexed long specifications, JANUS/Sentinel status,
  engine/source inspection, exact project proposals and supervised tests.
- WinGet search and exact-ID metadata inspection, trusted fixed-ID catalog
  expanded to software for games, applications, literature, music/video, CAD
  and graphic design.
- **Standing routine software policy:** on by default for this requested
  release, visible and revocable in Computer & Tools. After actual **build
  plan approval**, known required tools can install/upgrade without further
  DeepThorT confirmations. Upgrades are throttled, UAC is not bypassed.
- **Inspected external packages:** user selects the exact ID and clicks
  **Install inspected package…** after inspection; standing policy avoids
  an additional Yes and typed phrase. Unknown packages are never chosen for
  installation automatically. Manual mode still offers v38 approvals.
- Audit records distinguish package-manager exit success from independent
  installation, authenticity and application-function verification.

## Priority 1 — Make project creation genuinely continuous

1. **Project-scoped standing permissions**: one explicit project decision
   authorizes bounded file writes, deterministic tests, format checks and
   specified build steps, instead of separate file/test confirmations. Keep
   source diffs, Git/versioned snapshots, undo/rollback and clear stop controls.
   Require elevated/restricted permissions only for meaningful boundaries:
   installation that triggers Windows UAC, destructive deletes, credential
   access, payments, publishing or changes outside the selected project.
2. **Durable autonomous task graph**: requirement -> artifact -> build -> test
   -> result, with minimal context passed to ONNX, dependency waits, bounded
   retries, stall detection, recovery after restart, and accurate on-screen
   active/blocked/completed evidence. Never claim completion merely because
   a script exits or a model proposes code.
3. **Tool bootstrap and verification**: after installing a package, locate
   its real executable and version; run low-impact capability probes, link it
   to the actual project, capture evidence and retry stalled plan steps.
   Detect PATH changes/restarts and show exactly what remains unavailable.
4. **Smarter requirements-to-tool resolution**: go beyond broad keyword
   matches. Infer target OS/engine, artifact format, license and resource
   needs, enumerate missing dependencies, choose verified adapters, compare
   installed versions and avoid changing a project's pinned toolchain.

## Priority 2 — Broader trusted software acquisition

5. Expand beyond the fixed WinGet catalog with read-only official docs,
   signed manifest metadata and trusted repository evidence. Match publisher
   identity against independently sourced provenance; store source citations
   and expiry. Treat the web/model as untrusted input, not commands.
6. Download to a quarantine with disk/time/size quotas. Independently check
   signed SHA-256 provenance/Authenticode where available; do not rely solely
   on a checksum claimed by the same catalog. Support Windows Defender and
   real UAC. No silent elevation bypass, force/hash overrides or arbitrary
   command templates. Maintain audit, cancellation and rollback plans.
7. Use safe package updates only when compatible with an existing project.
   Expose a user-visible **pause all automated work** control and scheduled
   maintenance windows; do not upgrade in the middle of a running build/game.

## Priority 3 — App-specific creation skills

8. Versioned adapters: Blender .blend/GLB/render; Godot scenes/build/export;
   X4 macro/XML and in-game behavior; RimWorld defs/assemblies; Android
   SDK/Gradle/ADB; Python/Node/.NET; LibreOffice/Pandoc book/EPUB/PDF;
   FFmpeg/Audacity media; Krita/GIMP/Inkscape art; FreeCAD CAD models.
9. GUI-only application controller with window identity, confirmed elements,
   screenshots, user-visible action logs and accessible cancellation. Never
   blindly click model-hallucinated screen coordinates.
10. Independent artifact acceptance: test playable games in the actual engine,
    APK on emulator/device, mod save compatibility, multimedia exports and
    geometry, document rendering, and source citations. Track unresolved bugs
    before declaring a job done.

## Priority 4 — Robustness and trust

11. Windows Job Objects and separate low-privilege task workers, resource
    budgets, game priority, logs, safe input/source hashing and recovery.
12. Add end-to-end Windows WinGet/UAC/package-signature tests and resolve
    intermittent Tkinter test teardown warnings. Complete `TEST_RESULTS_V39`.
13. Benchmark ONNX speed, prompt budget, JSON validity and multi-step task
    completion under 20% CPU/RAM limits. Optimize model use without changing
    the model family or sending prompts to an online LLM.

## Hard limits today

Routine automation currently knows a **fixed curated list of WinGet IDs** and
is activated only from approved build jobs or an explicit install button.
It does not browse arbitrary websites to find installers, verify independent
publisher signatures, choose unknown packages automatically, or operate most
third-party GUIs. The existing plan/file/test gates still interrupt long jobs.
No real Windows UAC, installation, application automation or full game
acceptance has been demonstrated in the Linux test environment. A successful
WinGet process exit is `completed_unverified` until app-level tests confirm.

## Testing later on the target PC

Close and back up `D:\deepthort\state`; install the full v39 ZIP over
`D:\deepthort` without deleting `models`, `state`, `cache`, `node_modules`,
`reference` or user projects. Open F1 and the new preference checkboxes.
Approve a disposable project's plan containing a missing recognised tool;
confirm no DeepThorT per-tool dialog, normal Windows elevation when required,
serial queue logs and persistent status. Test opt-out and upgrades separately.
Export a diagnostics ZIP for any failure. Use a VM for unknown packages.
