DeepThorT 35% resource-cap update (2026-11-25)

Close the application and all model workers. Back up state. Extract the source overlay over the existing installation, preserving the executable, model files, state, node_modules, cache, references and projects. Use START DEEPTHORT.cmd to launch the updated source supervisor, rather than a potentially frozen old executable. The shared CPU ceiling is 35% of total CPU; aggregate private committed memory is capped at up to 35% of installed physical RAM, lowered when free memory is insufficient, retaining the existing 10% reserve. No changes to models, ONNX runtime or approvals. These are not per-process allowances or physical working-set/disk hard caps. Actual Windows enforcement must be checked locally. Historical 30% descriptions in release notes refer to the old versions.

---

# DeepThorT v60 for Windows

On the independent PE request, the local planner can now assemble the fitted asteroid into a new ship component. It offers the model upper-rear offsets with verified visual surface contact, screened against measured cockpit, elevator, dock, weapon, turret and engine connections. The resulting source bundle includes the registered macro and component, four visual detail levels on the benchmark ship, a resized collision XMF and an OBJ preview showing both main shapes together. In the project sidebar choose **Export latest draft mesh**, then save the component draft with a .zip filename.

# DeepThorT v59 for Windows

The indexed X4 planner can now measure a vanilla PE hull and ore asteroids from native LOD0 vertices. For the independent PE hull request, the local model selects an inspected rock and DeepThorT records a uniformly fitted visual mesh in the draft. Use **Export latest draft mesh** in the project sidebar to save XMF or Wavefront OBJ to a new file. The OBJ contains positions and triangle faces in native axes.

# DeepThorT v58 for Windows

The indexed X4 planner can recover when the local model picks the original ship as the destination for an independent variant. It asks the model to choose a fresh identifier and records a paired ship definition and index entry. An approved Build can derive those two files from the inspected vanilla XML. The static checker resolves each new registration to the on-disk declaration.

In the Windows PE benchmark, the model reviewed all three specification sections and proposed four files. Ten planning checks remained open. A separate two-file test verified the generated variant against the real PE. See TEST_RESULTS_V58.md for the comparison with the existing OpenCode extension.

# DeepThorT v57 for Windows

The indexed X4 planner now brings inspected game references into its file proposals and checks whether proposed paths belong inside an extension. Retrying a legacy draft keeps the original specification and an archive of incompatible proposals. The Processes tab's **Run latest test** reports the selected project's pending sections, incompatible paths and open planning checks.

JANUS can answer a literal reply request in the instruction inbox. Planning advice remains staged until a completed implementation-model exchange contains the full advice. See PROJECT_CONTEXT_V57.md for the Windows replay and TEST_RESULTS_V57.md for release evidence.

# DeepThorT v56 — visible JANUS instruction retry (23 November 2026)

**Usability fix:** Chats → Retry failed reply retries only an ordinary failed conversation, NOT a JANUS instruction. The earlier documentation incorrectly told the user to select an inbox row and click Retry failed interpretation, even though the fixed-size popup could hide its bottom-row buttons on a scaled display.

The JANUS & Sentinel tab now has an always-visible **Retry latest failed JANUS instruction** button, adjacent to **Instruction inbox…** and separate from the Chats retry button. The action finds the most recent FAILED neural interpretation for the selected project and atomically requeues read-only JANUS/Sentinel inference. It preserves the exact message, other projects' instructions, already staged advice, original chat requests, approved builds, game files and source files. If no failed instruction exists in the selected project, it explains the distinction instead of silently doing nothing.

The inbox popup now places retry/review controls ABOVE the file list and details, uses an adaptive window size and scrollbar, preselects the most recent instruction, and shows its project, state and original text. If the current workspace has no instructions but a different workspace does, it shows those other entries read-only until explicitly selected. No changes to the 30% shared Windows cap, models or underlying council inference were made. No live Windows model run is claimed; GUI and persistence regressions are tested under Xvfb.

**Upgrade:** Close DeepThorT; back up `D:\deepthort\state`; extract the v56 source overlay over the v55 installation. Preserve DeepThorT.exe, ONNX models, state, node_modules, references and projects. In JANUS & Sentinel click **Retry latest failed JANUS instruction**, then monitor the inbox and use **Run latest test**. The user does not need to select a row merely to retry the latest failed interpretation.

---

# DeepThorT v55 — verified JANUS handoff status and bounded neural JSON recovery

The 23 Nov 22:18/22:23 Windows diagnostics revealed a false positive: the JANUS inbox probe reported passed when a saved instruction had actually failed Qwen JSON interpretation. `Run latest test` now classifies a failed neural translation as BLOCKED, staged advice or pending instructions as INCONCLUSIVE, and only actual delivered-to-planner advice as PASSED. It never exports the original instruction text.

JANUS and Sentinel each get one bounded structure-only retry if their Qwen reply is malformed or a fenced JSON object. Unsafe, invalid or unapproved changes remain prohibited. The nine Xenon PE planning gaps are still unresolved; no claim of a working mod or game playtest. No model, executable, RAM or CPU-cap changes.

**Upgrade:** back up `D:\deepthort\state`, close DeepThorT, extract v55 source overlay over the v54 Windows installation. Preserve the exe, models, node_modules, state, references and all projects. See `PROJECT_CONTEXT_V55.md`.

---

# DeepThorT v54 — JANUS coordinator diagnostic and pause-safe Sentinel

The Windows v53 acceptance ZIP (23 Nov 18:06) passed all six checks for shared Job Object, two ready supervised ONNX models, real council inference and simultaneous inference. Separately, 11-core JANUS showed cycle 1473 unchanged since 21 Nov. v54 distinguishes an intentional safety pause from a truly stale cycle in `Run latest test`, includes the pause flag in diagnostics and prevents Sentinel from reporting paused JANUS as a hung worker. No automatic unsafe resume or worker replay.

# DeepThorT v53 — one-click evolving acceptance tests

**New Processes controls:** **Run latest test** and **Stop latest test**. The latest packaged `LATEST_TEST.json` selects a fixed, audited suite of local, bounded checks. New releases can update the manifest or add a separately tested adapter without adding another button. Manifest values cannot execute model-created commands, download software, change project files, start a game, or override permissions.

**Current v53 suite:** verify Windows capped-supervisor membership, primary Qwen ONNX readiness and PID, secondary JANUS/Sentinel Qwen readiness and supervised PID, durable inbox readability, one bounded local advisory model health inference, and whether simultaneous main/council inference was actually observed. The suite never interrupts an active implementation request or steals an occupied JANUS worker. An idle primary model produces an **inconclusive** concurrency check, not a fabricated success. A council load may take up to 180 seconds; user can cancel the remaining checks. Verification of a Windows Job Object does not independently measure an actual 30% CPU rate.

**Automatic evidence:** no Save As dialog. Each run writes `D:\deepthort\state\latest-tests\LatestTest-*.json` and `latest.json`, plus a verified ZIP at `D:\deepthort\diagnostics\DeepThorT-LatestTest-*.zip`. `state\last-diagnostic-export.json` records its location/hash; **Processes → Locate latest diagnostics** can open the folder. The ZIP excludes raw chat input and model weights, but still inspect before sharing.

**Limitations:** This release adds a repeatable Windows acceptance harness, not automated X4 gameplay or a guaranteed functional second ONNX model. Source checks are covered by Linux tests; real Windows memory, 30% Job rate, dual-model performance and the parent Windows executable require your local run.

**Upgrade:** Close DeepThorT; back up `D:\deepthort\state`; extract the source overlay over the existing v52 installation, preserving `DeepThorT.exe`, models, node modules, state, cache, references and user projects.

---

# DeepThorT v52 — verified diagnostics and JANUS wait-state visibility

- Export diagnostics now verifies ZIP/summary and retains a second copy in `D:\deepthort\diagnostics`, even when Save As selects another location; `state/last-diagnostic-export.json` records both exact paths and SHA-256. The success dialog can open the selected folder. Processes > Locate latest diagnostics also works after restart.
- JANUS secondary ONNX now reports whether it awaits primary model readiness, shared cap verification, sufficient free RAM, model load completion or a completed inference. Processes > Retry JANUS model resets exhausted startup attempts without interrupting an ongoing council reply. The council refuses any unmanaged service occupying port 8766.
- User instructions remain durable. JANUS/Sentinel proposals remain advisory; approved jobs remain untouched. Two Qwen ONNX workers still share one 30% supervisor budget. The original Windows executable, models and state are retained.
- No Windows telemetry from this reported failed export was uploaded: the exact prior path and secondary-worker cause remain unknown. Please verify on Windows after updating.

**Install:** Close DeepThorT; back up `D:\deepthort\state`; extract the source overlay into `D:\deepthort`. Never delete existing executable, models, state, node_modules or projects.

---

# DeepThorT v51 — parallel JANUS instruction processing (23 November 2026)

**Hardware context:** user reports 40 GB of system RAM. DeepThorT can now start **two copies of the SAME local Qwen2.5-Coder-1.5B ONNX weights**, as two Node child processes on 127.0.0.1:8765 (implementation) and :8766 (JANUS/Sentinel advisory). No cloud endpoint or separate Llama/Ollama process is introduced. The secondary worker starts only when the primary is ready, genuine capped Windows Job membership is confirmed and available RAM is sufficient. When missing/unavailable, new instructions remain queued. The two workers **share one Windows Job Object 30% system CPU hard cap and at-most-30% physical-RAM-sized committed-memory cap**, not 30% each. Under foreground RAM pressure the launch cap may be smaller to retain the reserve. The existing launcher sources enforce the new caps and MUST be installed; real Windows verification of the original `DeepThorT.exe` invoking the upgraded scripts remains outstanding.

**New workflow:** Select a project, type a message in Chats and click **Instruction to JANUS** (or Ctrl+Shift+Enter). The message is saved immediately to `state/janus-instruction-inbox-v51.sqlite3` with its exact original text; it does not cancel or alter the main model's in-flight request or any approved build job. The second Qwen worker performs a JANUS next-action translation followed by a separate Sentinel critical acceptance check. Their output is advice, not authorization. The main model receives a small **translated next action and test requirement**, rather than a second copy of the original user message, **only at a NEW unapproved planning checkpoint** (subsequent indexed section/revision or a newly drafted plan). Approved stages, execution, separate milestones and tool UAC still require the existing approvals; changing existing scope requires explicit review. JANUS & Sentinel > **Instruction inbox…** shows original text, proposal, evidence, status, review, retry and dismissal. Messages longer than the model input window are saved intact and flagged for indexed planning rather than silently truncated into an incorrect decision.

**Limitations:** No independent higher-capacity neural models: JANUS and Sentinel each perform a separate Qwen inference turn, sharing the council instance sequentially while the primary implementation model can be busy. Real live Windows/ONNX dual-model performance and caps require physical-PC diagnostics. Advice does not rewrite an already approved job, start a new milestone, install tools, or change source without consent. The 40-call progress-based planning batches and all existing tool/game safety boundaries remain. GPU, disk and physical cache activity are not percentage hard-capped.

**Upgrade:** Close DeepThorT; back up `D:\deepthort\state`; extract the v51 source overlay to `D:\deepthort` replacing source files. Preserve `DeepThorT.exe`, models, node_modules, cache, references, state and user projects. If the original Windows launcher does not load the updated `desktop_launcher.py` from disk, the 30% change must NOT be treated as effective: check actual Job Object CPU rate with native Windows diagnostics before invoking both models. See `PROJECT_CONTEXT_V51.md` and `TEST_RESULTS_V51.md`.

---

# DeepThorT v50 — active JANUS/Sentinel neural consultation and X4 source workset (23 November 2026)

**First:** JANUS and Sentinel's eleven-core Fano societies remain independent deterministic persistent coordinators; v50 adds real sequential reasoning consultations by the *same* already-capped local Qwen ONNX model for a stuck X4 plan. JANUS proposes concrete alternative hypotheses; Sentinel challenges the evidence; neither can approve, execute or fabricate success. Only the actual X4 validator and an approved build can establish progress. New responses are persisted and visible as recommendations. They are **not separate trained neural models**.

**Project files:** `D:\x4mods` is a mod **output workspace**, not the installed X4 game's source. X4 has already supported automatic Steam/GOG installation and extracted-reference detection, but previous versions kept verified vanilla XML invisible in the sidebar. v50 auto-discovers references for selected X4 workspaces, displays only a small useful set of hash-verified vanilla XML in a separately labelled **read-only** tree group, and lets the user preview or hide references without altering X4. The new **Show all workspace files** toggle defaults off in X4 folders; files explicitly named by a local plan or approved job stay in the editable project list, unrelated files are not shown until toggled. Choose **Auto-discover X4 sources** if necessary; missing extracted XML still requires approved extraction. There is no guessing/modification of game files or automatic filing of fictitious project files.

**Safety and limits:** Same Qwen2.5-Coder-1.5B ONNX, same Windows 20% aggregate cap, original launcher, JANUS/Sentinel societies, eight Tk tabs, game prioritization, versioned checkpoints, no arbitrary autonomous installations or model swap, no approval bypass. Two additional neural council calls per qualifying X4 stall use the same supervised model worker; this may be slow but is bounded and persistence-backed. Council hypotheses remain unverified until genuine tests. No actual live Qwen or native Windows X4 playtest is claimed. See `PROJECT_CONTEXT_V50.md` and `TEST_RESULTS_V50.md`.

**Install:** Close DeepThorT, back up `D:\deepthort\state`, and extract this verified source overlay over your existing v49 Windows install. Preserve `DeepThorT.exe`, `models`, `state`, `reference`, `cache`, `node_modules` and all projects. Source overlay is not a standalone installer.

---

# DeepThorT v49 — productive long-running X4 planning (23 November 2026)

**Evidence:** The 23 November 2026 14:43 diagnostics showed an indexed Xenon PE request running for approximately 79 minutes. All 40 correction calls completed, but all **9 X4 plan validator checks remained unsatisfied**, with no authorized files produced. The local Qwen model was still operating at about 18.4% CPU with ~2.2 GiB resident memory; extending this failed correction loop alone would not have created a mod.

**v49 corrections:**
- Desktop indexed planning now automatically continues into additional **40-model-call batches** if the previous batch verified *real progress*: a source section reviewed or an X4 acceptance check closed. The 40 counter measures **one batch**, not the permitted project lifetime or file count. All original specification text and reviewed sections remain in SQLite between launches. Cancellation remains available.
- After **eight consecutive unproductive X4 corrections**, the current active run pauses with a specific status instead of burning hours/days rewriting the same unresolved requirements. A user-requested retry may resume saved proposals; unsuccessful calls are never presented as completed work.
- Progress is measured by previously unmet acceptance checks that actually close, not by tokens generated or descriptions rewritten. Audit records survive app restarts. Corrections may not reopen satisfied X4 requirements, including by adding new assets without their matching registration entries.
- The focused ONNX correction input now shows only one missing acceptance goal, up to three related saved file descriptions, and **one exact unchanged original specification section**, rather than nine competing objectives in one reply.
- GUI startup version marker now reads 49.

**Scope and limitations:** This is automatically continued **planning** of indexed large requirements, *not* unrestricted multi-month unattended application development. Existing explicit build/milestone approvals, file backups, resource constraints and game testing limitations remain. If the 1.5B local model cannot solve even one acceptance check, progress-based control deliberately stops and the model, evidence or strategy must change. A completed plan remains unbuilt until actually approved and executed. No new cloud model, inference engine or Windows resource allowance is introduced.

**Upgrade:** Close DeepThorT; back up `D:\deepthort\state`; extract this source overlay into `D:\deepthort`. Keep `DeepThorT.exe`, ONNX `models`, `state`, `node_modules`, `cache`, references and projects.

---

# DeepThorT v48 — repair incomplete indexed X4 plans (23 November 2026)

**Fix for `REPLY FAILED` after retrying a fully reviewed large X4 specification:** Previously, once a 7,422-character request had been indexed and its sections reviewed, the hierarchical roadmap validator could reject missing `content.xml`, `md/*.xml`, asset/equipment XML and ship-behaviour coverage **without making another Qwen model request**. A retry raised the same failure in seconds. v48 now re-opens exact saved section evidence, asks the local ONNX model for a focused JSON correction, validates and persists new model-authored proposals, then rechecks the complete original X4 specification. The existing 40-call budget applies; incomplete corrections are retained for future retries. No generated mod files are written before explicit plan approval.

**Diagnostics correction:** The v47 release inherited a stale `desktop_init` version marker of `46`. A v47 application could therefore log version `46`. v48 records `48`; check release files/commit, not the old marker, to determine installed source version.

**Resource policy unchanged:** local Qwen ONNX; no alternate model, no cloud fallback, 20% Windows process-tree CPU cap; long planning sessions permitted. v48 does not purport to resolve ONNX worker exits not observed in the new 12:04 diagnostics.

---

# DeepThorT v47 — historical recovery and ONNX transport safeguards (23 November 2026)

**Planning attempt counters:** Standard project planning uses at most **40 model-generation passes per invocation**. These are attempts to find and repair missing pieces in a plan, NOT a maximum of 40 source files. Oversized imported specifications are divided into numbered source-preserving sections, using **up to 40 model calls per processing batch**; unfinished sections can continue in another batch without modifying the stored specification. The counters show model effort, not proven output or completion. No new limit on long sessions or workspace file size was introduced.

**Pre-v46 history recovery:** If `D:\deepthort\state\sessions.sqlite3` still contains complete old Qwen responses, v47 can reuse a reply only if its full model input matches exactly AND the original request, selected workspace, chat, and attachment scope match an existing durable conversation. This includes older per-pass planning sessions and the original single-session format. Large-document reviewed sections can also be inherited from the old `specification_index.sqlite3` when every source-section hash matches. All restored fragments face the CURRENT safe-file parser, X4 plan validator, and unchanged user approval. A diagnostic ZIP contains no model replies and CANNOT recover data that was never saved, overwritten, or deleted.

**ConnectionResetError recovery:** If the local ONNX server connection fails while planning, the request remains pending rather than being marked permanently failed. DeepThorT does not dispatch new inference while the previous local worker is busy. An unexpected *previously ready* model process exit triggers up to two supervised restarts within the same Windows 20% CPU and commit-memory Job Object. Explicit Stop AI, closing the app and worker startup failures do not initiate an unattended restart. Up to two transport interruptions are tolerated per conversation before it becomes a visible error. Completed identical model exchanges are reused, avoiding unnecessary model calls. Uncertain in-flight replies may need regeneration; they are NOT recorded as successful answers. A crash can result from memory pressure, process restart or another cause; WinError 10054 alone is not proof of memory exhaustion.

**What did not change:** Qwen2.5-Coder-1.5B-Instruct ONNX remains the only language model. JANUS/Sentinel, eight Tk tabs, Windows UAC, 20% cap, project file exclusions, 40 model passes, backups, test budgets and explicit build approval remain intact. No generic app/game launch or X4 playtest was claimed. See `PROJECT_CONTEXT_V47.md` and `TEST_RESULTS_V47.md`.

---

# DeepThorT v45 — isolated Windows GUI smoke tests

Work queue now has **Isolated GUI smoke test…** and **Stop isolated GUI test**. You can explicitly approve a trusted, project-local Windows `.exe` to launch on a separate Win32 desktop without changing your foreground focus or sending keyboard/mouse input. The process is low priority, limited to 25 seconds and runs under DeepThorT.exe’s existing **shared** 20% CPU Job Object with a nested cleanup job. The app can still produce sound and use GPU; it is NOT a VM/security sandbox, nor an automated gameplay or graphical correctness proof. The Processes tab and diagnostic receipts show actual project-window titles, geometry, responsiveness and exit status. Unclear or unsupported Win32 desktop operations fail closed. Native Windows testing is still required.

**Update**: Close DeepThorT, back up `D:\deepthort\state`, then extract the v45 source overlay over your existing v44 Windows install. Keep `DeepThorT.exe`, ONNX model, state, node_modules, cache, references and all projects untouched. Read `PROJECT_CONTEXT_V45.md` for first-use acceptance.

---

## v44 — Quiet background Godot scene simulation

DeepThorT can now launch a project's declared Godot main scene **headlessly** from Work queue → **Quiet Godot scene test**, while the user works in other programs or plays a foreground game. It uses no display, audio or interactive input, starts under the existing **shared** Windows Job Object resource cap and is throttled by IDLE priority and a pressure preemption guard. Select **Stop quiet test** to cancel; receipts appear in diagnostics and Processes.

This only executes the Godot scene and examines exit status/output; it **does not** confirm graphics, input, physics correctness, actual playability, X4/RimWorld behaviour, or Android emulation. It requires a locally installed Godot executable and a `run/main_scene` in `project.godot`. It does not install games or stage mods. Generated scene scripts run with normal user permissions, not inside a sandbox. Never assume a 20% GPU or disk cap.

# DeepThorT v43 — independent post-install tool verification (23 November 2026)

**Continues the v42 ONNX + JANUS/Sentinel project workflow, without introducing another model.** After a fixed-catalog WinGet installation exits, v43 finds real executables, checks bounded known command-line version output, saves durable evidence and makes newly verified CLI tools available to the *current desktop process* for previously authorized project tests. Registry-only installed-app entries no longer count as usable tools. GUI applications are located but are **not automatically opened** for probing. Inspect `Computer & Tools` and the `Processes` log; receipts live at `state/tool-verification-v43.json`. See `PROJECT_CONTEXT_V43.md` and `PLAYTEST_ACCEPTANCE_V43.md`.

**Important:** A successful version probe is not proof that an app is playable, that a mod works in-game, or that the publisher is trusted. A true install/launch/playtest adapter is still a subsequent development target. Keep your existing Windows UAC, project approval gates, resource caps, model and game profiles. This is a **SOURCE OVERLAY** for an existing v42 Windows install; preserve `DeepThorT.exe`, `state`, `models`, `node_modules`, `cache`, `reference` and user projects.

---

# DeepThorT v42 — evidence-backed task dependencies and source rollback (23 November 2026)

**Local Qwen ONNX only; original JANUS, Sentinel, eight-tab desktop and Windows gaming constraints preserved.** After an explicitly approved plan, a persisted task graph records linked requirements, exact source artifacts, observed verification tools and real test evidence without fabricating success. Source checkpoints preserve the approved baseline and successive generated/ONNX-repaired file revisions under `state/source-checkpoints`. Work queue has a deliberately explicit **Restore source checkpoint…** action which safely quarantines newly created files and invalidates the old plan approval, graph and tests. External edits and corrupt/missing checkpoint blobs block restoration. Job-bound action leases prevent silent replay after interruption.

**Install as an overlay over an existing v41 install**; preserve `DeepThorT.exe`, `models`, `state`, `node_modules`, `cache`, `reference`, projects and user files. The ZIP is NOT a standalone Windows installer. Tests run as the user and are not sandboxed. Read `PROJECT_CONTEXT_V42.md` and `TEST_RESULTS_V42.md`. Windows end-to-end acceptance remains outstanding.

---

# DeepThorT v41 — bounded local diagnose/repair/retest development cycle

Version 41 adds a durable per-approved-job build/test/failure/repair/retest
loop on top of v40's scoped file grants. After a recognized fixed project
test fails with source-level diagnostics, DeepThorT can ask its **existing
local Qwen ONNX model** to replace ONE small approved project file, save
that file through the existing backup writer with SHA-256 conflict checks,
and retest. Each job permits up to **3 tests and 2 repairs**. Ambiguous
diagnostics, model errors, unsafe paths, stop/pause/revocation, and interrupted
uncertain work require review rather than automatically guessing.

The Work queue and Processes tab report real attempts, not synthetic token
progress. The original JANUS/Sentinel, Windows resource budget, eight-tab UI,
model and v39 WinGet safety behavior are preserved. Recognized local project
tests still execute project code under your Windows account and are **NOT
sandboxed**. Separate milestones, arbitrary external software, installer
permissions and publishing are not authorized by this cycle.

This release is a **source overlay** for an existing v40/v39 installation,
not a complete Windows installer. Back up `D:\deepthort\state`; overlay the
ZIP, preserving `DeepThorT.exe`, `models`, `state`, `node_modules`, `cache`,
`reference` and project files. Inspect `PROJECT_CONTEXT_V41.md` for the exact
first Windows test. Physical PC, Qwen code quality and gameplay are not proven
by GitHub CI. See `TEST_RESULTS_V41.md` and `NEXT_STEPS.md`.

---

# DeepThorT v40 — approved project work without repeated file/test prompts (23 November 2026)

**Sole coding model: local Qwen2.5-Coder ONNX.** Original JANUS/Sentinel, gaming
limits, eight-tab interface, Windows launcher and installed state are preserved.

An explicit approval of a draft, legacy plan or hierarchical milestone may now
issue a durable, exact-file **project authority grant** when Work queue >
**Continue approved file steps and fixed tests without repeated prompts** is
enabled (default on, visible and revocable). Each grant binds the job ID,
project directory, full planned file list, plan digest and pre-write SHA-256
fingerprints. Source writes still use atomic replace and timestamped backups.
Changed files, protected paths, revoked/expired/missing grants, or incompatible
plans fail closed and return to manual file review.

After every planned file is saved and its SHA-256 recorded, DeepThorT may run a
known local Python/Godot/X4/npm/.NET verification command without another
dialog, provided the project, file receipts, queue, JANUS, game and process
gates permit it. These tests execute project code with your normal Windows
user permissions; they are not sandboxed. Tests running before a preference
change or grant revocation may need to be stopped separately. A failed test
requires inspection, not a blind automatic retry.

Unknown software installs, arbitrary learned recipes, generated script
execution outside fixed tests, destructive operations and publishing do NOT
inherit this grant. The separate v39 curated WinGet routine-tool policy and
native Windows UAC remain unchanged.

**Do not replace or delete the existing `DeepThorT.exe`, ONNX models, state,
node_modules, references, caches or projects.** Install v40 as a source overlay
over an existing v39 Windows installation unless a separately verified full
bundle is provided. See `PROJECT_CONTEXT_V40.md` and
`tests/test_project_authority_v40.py`. Live Windows execution and genuine
game acceptance remain unverified until the owner's tests.

---

# DeepThorT v39 — routine tools without repeated prompts (23 November 2026)

**Inference remains local Qwen through ONNX.** JANUS, Sentinel, the Windows launcher,
local inference server, resource priorities and existing projects are unchanged.

## Routine software management

**Computer & Tools → Automatically manage routine project tools** is enabled on
first use of this v39 package, reflecting the owner's stated preference for
uninterrupted job execution. The switch is persistent in
`state/routine-software-policy.json` and can be disabled at any time. A second
switch controls automatic upgrades. These are standing local preferences, not
an opportunity for model output or web text to run arbitrary commands.

After a **real build plan is approved and queued**, DeepThorT uses its local
heuristic tool inventory and a fixed, reviewed WinGet ID catalog to queue up to
three relevant installs/upgrades. Only one installation runs at a time.
Automatic upgrades are attempted at most once per package every 14 days; other
attempts are throttled. The program avoids installations while a configured
game is running, the queue is paused, a tool process is busy, or disk free space
is below 1 GiB. It records `state/last-routine-software.json` and a bounded
`state/routine-software-history.json` before launch and after completion.
A WinGet exit code of zero is recorded as `completed_unverified`; it is not a
verified working tool. Interruption on restart cannot be mistaken for success.

The command uses exact local WinGet package IDs with no shell, no `--all`,
`--force`, `--override`, `--ignore-security-hash`, `--silent` or `--scope user`.
DeepThorT does **not** attempt to elevate itself, bypass Windows UAC or block
normal system elevation confirmation. The Windows installer can still ask for
other interaction or fail; that outcome is logged, not silently overridden.

WinGet packages from outside the curated catalog can be searched and inspected
using the existing controls. With routine management enabled, clicking
**Install inspected package…** after a fresh validated exact-ID inspection
uses the standing preference and **the explicit button click** instead of
another Yes/typed phrase. An audit correctly records that authorization source.
With routine management disabled, the older two-step manual review remains.
Unknown packages are **not** automatically selected or executed from model/web
search results. WinGet catalog metadata and its SHA are untrusted, not
independent publisher identity or malware proof. Always apply ordinary system
security judgment before choosing an unknown package.

**A project plan, source file edit, or arbitrary generated script is not yet
silently approved**: these retain established review boundaries. Reducing those
repeated gates using project-scoped, reversible task permissions is a top item
in `NEXT_STEPS.md`.

The user guide (`USER_GUIDE.html`, F1), development roadmap (`NEXT_STEPS.md`)
and diagnostic tests (`TEST_RESULTS_V39.md`) are included with the Windows ZIP.
Keep `state`, `models`, `node_modules`, `cache`, `reference` and existing project
folders when updating; back up `state` first. No actual Windows install/UAC
acceptance test has yet been performed for v39. See `PROJECT_CONTEXT_V39.md`.

---

# DeepThorT v38 — supervised exact-version installation of inspected software (23 November 2026)

DeepThorT's **only coding-language model** remains local Qwen running under **ONNX** via its existing loopback inference server. No cloud model, separate training pipeline or external conversational AI has been added. JANUS and Sentinel coordinate and supervise; they are not a replacement inference engine.

## New functionality (Computer & Tools)

1. **Search packages online…** — user-authorized WinGet community catalog lookup (v36).
2. **Inspect package ID…** — separate approved `winget show --id vendor.package --exact --source winget` request, saving metadata from the exact package (v37).
3. **Review inspected install…** — NEW: in the same desktop session, a successful recent exact-ID inspection with a valid HTTPS publisher page and installer URL, a complete manifest SHA-256, a pinned version, and no unsafe URL flags can be reviewed for installation. The user sees the exact package name, catalog-claimed publisher, URL, license, hash, pinned version and fixed WinGet command. Clicking **Yes** is NOT enough: the user must separately type `INSTALL vendor.package`. Only then is an audit written and a single WinGet installation launched.

The installation command is fixed, not generated by the model. It pins `--id`, `--exact`, `--version`, `--source winget`, requests `--scope user`, forbids upgrades with `--no-upgrade`, disables WinGet interaction, and does not bypass hash checking. The review warns that WinGet accepts repository and package agreements, may still require UAC, and that the publisher is **not independently authenticated**. A successful exit is stored as `completed_unverified`, not as proof the software is installed, authentic or usable. No install permission is reused after restart.

The new audit lives in `state/last-reviewed-install.json`. The original `state` data, installed models, caches and projects are not included in the ZIP and are preserved on extraction. Offline guide and development backlog: `USER_GUIDE.html` and `NEXT_STEPS.md`. The original `DeepThorT.exe`, `inference_server.mjs` and model files were not changed. The v38 code has not executed a real WinGet installation on Windows; testing uses synthetic local fixtures on Linux.

**Remaining security limitations:** WinGet catalog metadata and its installer SHA are from the same catalog, not independent publisher verification. Requested user scope does not guarantee absence of elevation. There is no Windows installer sandbox, independently verified Authenticode trust chain, quarantined direct downloads, automatic rollback, or confirmed post-install executable capability test. Users must review publisher and licensing independently and should test new installers in a disposable environment first. Arbitrary internet search, custom installer URLs and hands-free installs are not supported. See `NEXT_STEPS.md`.

---

# DeepThorT v37 — exact WinGet inspection receipts (23 November 2026)

**Base:** Full v36 Windows release. This pass adds `Inspect package ID…` under
Computer & Tools to make user-approved online discovery more precise. An exact,
validated WinGet `vendor.package` ID is inspected using `winget show --id ...
--exact --source winget --locale en-US`. Network consent is obtained separately
for every inspection. The process has a 90-second timeout and a 64 KiB output
budget, and it cannot download or install anything.

The inspection result is parsed conservatively: expected ID, unambiguous package
header, claimed publisher/version, optional manifest SHA256 and HTTPS-only
informational URLs. Invalid fields or conflicting reports are not accepted.
A privacy-reduced receipt is saved to `state/last-package-inspection.json` and
shown in the UI, labelled **UNVERIFIED CATALOG METADATA — NOT INSTALL
AUTHORIZATION**. Installer SHA256 supplied by the same catalog is not an
independent checksum. Non-English CLI output may fail closed and can still be
reviewed in Processes.

The regression runner also now terminates the isolated Linux test process
**group** after a timeout; previously grandchildren could keep pipes open and
hang an otherwise isolated suite. This is test-runner hardening, not an
autonomous worker or production Sentinel change.

The fixed eight-package installer catalog, separate installation consent,
JANUS/Sentinel, local Qwen worker and other UI behavior are preserved. Newly
inspected package IDs are **never** passed to the installer in v37. Existing
user-approved script execution is not sandboxed. No actual WinGet requests,
Windows installation, real X4 mod or Android build has been verified by the
synthetic Linux tests. See `USER_GUIDE.html`, `NEXT_STEPS.md`,
`PROJECT_CONTEXT_V37.md` and `TEST_RESULTS_V37.md`.

---

# DeepThorT v36 — consented online package lookup and cross-platform regression repair (22 November 2026)

**Base:** Complete v35 release (illustrated offline manual, hover tooltips and fixed publisher-source lookup). v36 adds a read-only online catalog lookup and corrects two preexisting Linux CI test fixtures without relaxing tool executable validation. Original local Qwen model, JANUS/Sentinel, UI geometry, all state, gaming/resource limits and explicit source/command approvals are unchanged.

- **Computer & Tools → Search packages online…:** asks for a bounded software name, displays consent describing network/catalog access, then runs `winget search --query ... --source winget --count 20` through the existing supervised desktop process log. The query cannot install or download. It does not automatically trust catalog results, allow arbitrary URLs or add installable package IDs. A search result requires further independent review before any future generalized install implementation.
- `deepthort_local/online_tool_search.py` produces only a fixed command vector, rejects control characters/option-like input, and requires a real available winget executable. No model-generated shell code, script execution or automatic cloud model use.
- `tests/test_execution_safety_v34.py` and `tests/test_generated_scripts_v33.py` now resolve `sys.executable` in their fixtures: GitHub's setup-python binary can be a symlink and DeepThorT correctly refuses to enroll symlink tools. This is a test-environment repair, not a weakening of the production guard.
- New `tests/test_online_tool_search_v36.py`, updated tooltip and `USER_GUIDE.html`. Install over `D:\deepthort` without deleting models, state, cache, references, node_modules or projects. See `NEXT_STEPS.md` for the prioritized capability backlog.

**Validation:** full isolated regression and GitHub Actions status must be checked and reported separately; neither substitutes for live Windows winget/tool/game acceptance.

---

# DeepThorT v35 — user guidance and reviewed publisher links (22 November 2026)

**Base:** unmodified v34 Windows launcher, JANUS/Sentinel, offline local Qwen inference,
resource limits, source-backed approval controls and persisted project state.

- Added passive, delayed hover explanations for existing desktop controls and major
  interface areas, including per-tab Notebook help. The **User guide** button and
  **F1** open the offline `USER_GUIDE.html` (schematic + genuine GUI screenshot).
- Included `NEXT_STEPS.md` with prioritized capability backlog and Windows acceptance
  plan. No assets load from the web to display the guide.
- Added a reviewed official publisher page lookup for the eight fixed winget catalog
  entries, with a separate confirmation before opening a browser. This **does not**
  download or install anything. Existing fixed-package winget installation still
  requires its own explicit review and authorization.
- Expanded passive tool inventory and task category hints for documents, audio/video,
  graphics and CAD. These categories are **not** enrolled as executable recipes or
  automatic installers.
- The original desktop geometry, local model, persistent plans, JANUS/Sentinel and
  approval policy are unchanged. v35 does not offer autonomous internet tool research,
  sandboxing, full GUI control or guaranteed end-to-end game delivery.

**Installation:** Close the application; back up `D:\deepthort\state`, then extract
`DeepThorT_Desktop_v35_Windows.zip` over `D:\deepthort`, preserving all `models`,
`state`, `node_modules`, `cache`, `reference` and project folders. Press F1 for guide.

**Verification and gaps:** See `NEXT_STEPS.md` and `PROJECT_CONTEXT_V35.md` for the
current isolated regression report, Windows acceptance checklist and unfinished work.

---

# DeepThorT v34 — defensive execution preflight and recovery (22 November 2026)

**Source base:** v33; user requested proactive safeguards before a Windows test. See [APPROVAL_SAFETY_V34.md](APPROVAL_SAFETY_V34.md) for detailed risk matrix and test steps.

- New approved learned-tool actions pin the detected executable, generated script, selected input and expected output file state. JANUS revalidates these before launch; changed inputs leave the action at `needs_attention` without execution. Existing queued legacy actions are not retroactively pinned.
- Generated-script review is bound to the actual draft and preexisting file hashes; a changed proposal or external file edit must be reviewed again before write. Source review explicitly warns that Python/GDScript are **not sandboxed**.
- JANUS processes now have conservative elapsed-time and output-log budgets (tool 60 minutes; verification 120 minutes; 8 MB log); less than 150 MB free disk space blocks a new launch. These limits do not guarantee absence of partial changes.
- Project writes use unique exclusive temporary files and retain backups. Internal symlink edit targets are rejected. Export diagnostics now contains read-only bounded SQLite `quick_check`/free-disk metadata without raw database rows.
- `regression_cli.py` isolates GUI test modules, handles stale Linux display settings and offers an optional JSON report. It does not cure the old combined-process Tkinter race.
- JANUS/Sentinel topology, offline Qwen, resource caps, original interface layout, 40-attempt planning process and approval gates are unchanged. Real Windows app/tool execution and X4/Godot/Android acceptance require on-PC tests.

---

# DeepThorT v33 — model-authored automation scripts with separate file and command approvals (22 November 2026)

**Base:** v32. This release closes the script-authoring gap in local tool acquisition, without adding another UI panel, replacing JANUS/Sentinel, changing the ONNX model or permitting autonomous command execution.

- **Learn procedure…** can now accept an optional local-model-authored `script` object (`path`, full `source`) in addition to the CLI recipe. The program persists the candidate source and SHA-256 in `state/tool_acquisition.sqlite3`. It does **not** write the script when the model replies. The local small model is given up to 768 output tokens for this bounded draft; longer scripts may still fail and should use the existing staged source-workflow instead.
- **Run learned procedure…**, first selection: a **scrollable, full-source/diff review** offers **Approve WRITE ONLY** or Cancel. Approving writes just the project-relative `.py`/`.gd` source via the existing atomic writer with backups, and returns without scheduling an application. The source can be reviewed again in project files.
- **Run learned procedure…**, second selection: separately show the exact installed executable and command-line arguments; only affirmative user confirmation queues the supervised JANUS operation. Script and output artifact cannot be the same file.
- Generated Python is syntax-parsed before it can become a candidate. Supported script types are Python/Blender `.py` and Godot `.gd`; arbitrary shell scripts, external paths, model-proposed shell expressions, code-execution flags, missing scripts, symlink escapes and unapproved/changed source are rejected or require reapproval. Static syntax checks do **not** establish that a script is safe or correct: project scripts run with the user's operating-system permissions when explicitly approved.
- Previously installed v32 SQLite recipes are retained and migrated in place; legacy command-only recipes still operate without new steps. Replacing a candidate or changing its executable/script invalidates earlier evidence.
- Existing JANUS gaming pause, process limits, cancellation, artifact/procedure evidence and user-controlled approval remain intact. This is not GUI-only app automation and has not operated Blender or Godot on the user's Windows machine.

**Validation:** 408 regression tests passed across 50 separate test modules under a Linux virtual desktop, including 9 new generated-script and desktop approval tests, plus a real approved Python script generating an artifact. Single-process Tkinter teardown remains a known unresolved issue; Windows UI/model/script quality and full game integration are not confirmed.

**Install:** Exit the application, back up state, extract the ZIP over `D:\deepthort`, and keep existing models, `state`, `node_modules`, `cache`, `reference` and project folders. Scripts already staged in a workspace are not removed. See `TOOL_ACQUISITION.md` and `PROJECT_CONTEXT_V33.md`.

---

# DeepThorT v32 — supervised tool acquisition and reusable command recipes (22 November 2026)

**Base:** v31. This release fills the first operational gap between detecting installed apps and using their actual interfaces. It adds `deepthort_local/tool_acquisition.py`, a durable per-project local recipe registry, and three controls in the existing Computer & Tools toolbar. No external service, general-purpose shell, new model, or automatic tool permission was added.

- Real installed CLI executables are enrolled from scans; registry-only hints are not treated as runnable programs.
- Per-app bounded help is queried through explicitly approved JANUS processes. Limited adjacent documentation is read without launching a tool.
- The local ONNX model can create a compact recipe *candidate* for a concrete task; it is saved, not executed.
- Actual commands run only after reviewing the exact argv and confirming; existing JANUS worker supervision, gaming priority and cancel controls apply.
- A successful approved command must have a new or changed project artifact and intact action/log/tool fingerprints before its narrowly scoped result is retained. Zero-exit without an artifact is not a verified production workflow.
- Only current artifact-level results are surfaced to future planning. No blanket claim of application capability, generated code correctness, game behavior or autonomous unrestricted GUI operation.
- The original v31 interface layout, JANUS/Sentinel architecture, model, 40-attempt planning workflow, source approvals and Windows launcher are otherwise unchanged.

**Validation:** 399 automated tests passed across 48 isolated modules. These include one *real* JANUS-supervised Python help command and one user-approved local Python script that produced a file, with evidence checked after execution. GUI behavior was tested under a virtual display. Live Windows tool execution, model-generated recipe quality, Blender export and game-engine acceptance remain unverified. The existing combined-process Tkinter teardown race remains.

See `TOOL_ACQUISITION.md` for operation, constraints and test scope. Real Windows CLI probes/operation and game-engine testing remain outstanding.

---

# DeepThorT v31 — inspection evidence in diagnostics (22 November 2026)

**Source base:** v30. The 21:28 Windows export confirmed a healthy local Qwen worker but only a generic “X4 reference candidates found” activity message. It did not export PE macro/component/slot evidence or project engine readiness; `desktop_init` had also retained the old version 27 label. v31 corrects those diagnostic blind spots without changing inference, planning, approval, installed tool execution, JANUS/Sentinel or the window.

- X4 source inspections record and persist bounded evidence: PE macro and component verification, actual connection slot tags, weapon/turret candidate file identifiers and hashes, paired catalog count, readiness and explicit blockers.
- Computer & Tools scans record project engine status and missing prerequisites in a privacy-reduced, project-scoped snapshot.
- Export diagnostics adds both snapshots to `summary.json`. Results are tied to the selected project and remain available after restart, but are not revalidated during export; changed assets still need a fresh scan.
- Paths are reduced to their basename and a fingerprint; no model weights, raw source XML, chat prompts or entire machine inventory are newly copied into the support ZIP.
- `desktop_init` now records version 31 rather than the stale version 27.
- Five new regression tests; **373 tests passed across 46 isolated modules**. The existing monolithic Tkinter teardown crash remains. No live Windows ONNX, Xenon PE mod, or gameplay test occurred.

Install v31 over `D:\deepthort` while preserving `state`, `models`, `reference`, `cache`, `node_modules` and projects. Run the two existing scans in the correct X4 project before exporting fresh diagnostics. See `DIAGNOSTIC_INSPECTION_V31.md`.

---

# DeepThorT v30 — installed-engine preflight and X4 source-link evidence (22 November 2026)

**Source base:** v29, preserving the original Windows launcher, JANUS, Sentinel,
local ONNX worker, project approvals, existing interface and 40-attempt plan
limit. This pass adds read-only discovery and source-backed X4 registration
checks rather than asserting successful live gameplay.

- Existing **Computer & Tools → Scan this computer** now reports discovered
  X4/Godot/Android prerequisites from real local paths. The scan remains
  background/read-only, and no program is run or installed automatically.
- Godot verification can use a genuine `GODOT_EXECUTABLE` path, an existing
  PATH program or a discovered concrete executable. A registry install hint
  or folder no longer counts as a runnable engine.
- Full new X4 asset macro/component definitions require explicit local index
  registration. Extracted vanilla macro/component indexes can be consulted
  for explicit `ref` identifiers, with unknown DLC/mod references left
  unresolved—not invented or falsely declared invalid.
- `engine_environment_cli.py` provides a read-only local readiness report.
  Its findings are observational, not runtime/gameplay acceptance evidence.
- **Validation:** 368 automated tests across 45 isolated modules passed.
  The monolithic Tkinter run still crashed in the established cross-thread
  teardown path, so it was not counted as green. No live Windows Godot, X4,
  Android APK or save-game test was performed.

**Install:** Close DeepThorT; extract this ZIP over `D:\deepthort`, preserving
`state`, `models`, `node_modules`, `cache`, `reference` and every project. Select
your X4 project, use **Scan this computer**, and export diagnostics to inspect
actual engine/source readiness. See `ENGINE_ENVIRONMENT.md` for scope.

---

# DeepThorT v29 — engine-aware static audits and tested-result guards (22 November 2026)

**Source base:** v28, retaining its original interface, desktop launcher, Qwen
ONNX model, JANUS/Sentinel, gaming limits, full original specification, 40-pass
planner, cancellation, versioned milestone store and explicit approval controls.

- New `deepthort_local/engine_acceptance.py`: bounded read-only X4 XML/index and
  local macro/component registration validation; Godot main-scene/resource
  validation; Android Gradle manifest checks. Existing XML in earlier milestones
  is included; external vanilla/DLC references are not falsely treated as local.
- The existing approved **Verify build** flow prefers actual Python project
  tests for X4 when present, otherwise uses the static X4 auditor. Godot uses
  an installed GUT runner when actual test scripts exist, with an explicit
  nonempty passing-suite requirement. Editor loading remains editor-only.
- Model-described `verifies: REQ-N` test contracts now recognize local GUT/GDScript
  test functions and Kotlin/Java `@Test` annotations without executing them.
- Successful approved checks bind their engine artifact fingerprints into the
  milestone's verification snapshot, so changes to previously inspected index,
  scene or manifest files invalidate stale evidence.
- All tests run against synthetic files and mocked process output. There is no
  claim of completed Xenon PE gameplay, an exported Android game, engine-level
  acceptance, free-form JANUS conversation, or improvement to live ONNX latency.

See `ENGINE_ACCEPTANCE.md` for exact checks, supported paths, CLI usage and
remaining work. No new installer, UI button, external service or model is added.

**Verification:** 351 tests passed across 44 isolated test modules under Xvfb.
The single-process run still hits the old X4 GUI worker timing race; its result
is **not** counted as passed. Live Windows and CI verification remain outstanding.

**Install:** Close DeepThorT; extract v29 over `D:\deepthort` preserving
`models`, `state`, `reference`, `cache`, `node_modules` and project folders.
Back up `state` before updating. This ZIP does not include model or user data.

---

# DeepThorT v28 — requirement-linked source contracts and real test-output guards (22 November 2026)

**Source base:** v27. Original window layout, offline Qwen ONNX model and resource profile, JANUS/Sentinel, original user requirements, milestone approval, stop/close chat controls, and Windows launcher are unchanged.

- `deepthort_local/acceptance_contracts.py` adds explicit, auditable model-declared Python `provides:` / `uses:` and test `verifies: REQ-N` intentions, always linked to actual source requirement labels. Missing labels, unsafe/non-test verification claims or missing planned providers are rejected. Present Python source/test files are parsed without importing/executing them. An absent planned file remains pending. Unlinked labelled requirements and ambiguous source phrases remain visible rather than being treated as implemented or silently interpreted.
- Hierarchical roadmap creation checks contract declarations; approved verification reconciliation blocks confirmed missing exports/imports or empty test stubs. Repair requires a fresh approved test. The existing milestone approval dialog reports counts without adding any controls.
- `deepthort_local/verification_evidence.py` inspects bounded output from user-approved verification operations. An exit-zero `unittest discover` or `dotnet test` with **zero evidenced passing tests** is not accepted. Godot editor loading is explicitly labelled editor validation, not gameplay proof. Approved check summaries are hash-linked to existing file snapshots; older snapshots remain readable.
- Large specification storage, exact source sections, 40 planning attempts, milestone limits and explicit approvals are unchanged. No built-in X4 plan, fake acceptance tests, cloud dependencies or autonomous process permissions were added.

Read `ACCEPTANCE_CONTRACTS.md` for the read-only audit command, precise evidence levels and remaining limitations.

**Validation:** 18 focused v28 tests pass. Full-suite results are reported separately after a complete run. Live Windows ONNX/X4 gameplay/Android validation is not established by local tests.

**Install:** Close DeepThorT, extract v28 over `D:\deepthort`, retain the existing `state`, `models`, `node_modules`, `cache`, `reference` and game/project folders. Back up `state` first.

---

# DeepThorT v27 — conservative semantic reconciliation and fresh verification evidence (22 November 2026)

**Source base:** v26, preserving the original desktop interface, Windows launcher, local ONNX model, JANUS/Sentinel, state and approval controls. No external service or new model dependency was added.

- New `semantic_reconciliation.py` identifies narrowly provable conflicts between explicit mandatory requirements and impossible matching numeric bounds in the *original exact specification*. It rejects a new hierarchical roadmap when these source demands contradict, rather than inventing a resolution or approving both.
- Explicit `REQ-N: ...; depends-on: REQ-M` declarations are validated for unknown references, duplicate IDs and cycles. No semantic dependencies are guessed from prose. Model-declared **file** dependencies retain the v26 scheduling behavior.
- An inspectable acceptance checklist preserves exact source wording and anchored offsets, labels each criterion `unverified`, and does not mistake a linked plan file for successful implementation.
- Read-only Python AST inspection flags syntax errors or missing local exports in files actually present in the approved workspace. This check never executes code and explicitly distinguishes pending sources and uncheckable external/dynamic APIs.
- On desktop-approved verification exit 0, SHA-256 fingerprints of the actual planned files are attached to the job's verification result. Edited/deleted sources invalidate that evidence; verified milestones and dependent later stages are conservatively demoted and require a fresh explicitly approved test. Legacy verification records remain supported but cannot retroactively gain snapshots.
- Broken static local Python interfaces return an approved job to `waiting_verification` instead of silently accepting a previously green test. A repair requires re-running the test, not merely changing files.
- A read-only command-line inspector is available: `python -m deepthort_local.semantic_reconciliation requirements <file>` and `python -m deepthort_local.semantic_reconciliation interfaces <project> <plan.json>`.
- Full specification storage, incremental section review, 40 model attempts and immediate stop on validated plans are unchanged. No hardcoded X4 mod plan has been introduced.

**Verification:** 311 tests passed in the local Python/Xvfb regression suite, including 32 new v27 tests. ZIP integrity and launcher comparison were checked. Windows ONNX runtime, real X4 gameplay and Android compilation are **not** verified by these results. See `SEMANTIC_RECONCILIATION.md` for exact scope and remaining limitations.

**Install:** Exit DeepThorT, extract v27 over `D:\deepthort`; keep `state`, `models`, `node_modules`, `cache`, `reference` and projects. Back up `state` before upgrades. Do not treat acceptance candidates or static checks as proof that the complete game works.

---

# DeepThorT v26 — Pass 5, requirement candidates and explicit dependency intelligence (22 November 2026)

**Source base: v25.** This pass retains the existing Windows launcher, desktop geometry, local ONNX model and resource caps, JANUS/Sentinel, 40 planning attempts, source-fingerprint guards and approval/verification workflow.

- Added exact-source, hash-checked candidate requirement IDs to hierarchical roadmaps. Explicit list entries and headings are distinguished from retained unstructured text; no source is shortened or discarded. Candidate-to-file links mean **review scope**, not semantic proof of correct implementation.
- Model-authored descriptions can optionally declare `; depends-on: path/to/file.ext`; missing or self-referential paths and cycles are rejected, and roadmap milestones are ordered topologically without inventing dependencies. The section-review prompt teaches this optional syntax. Existing v25 roadmaps remain readable.
- Added a read-only `python -m deepthort_local.planning_metrics PATH_TO_STATE_LOGS` performance report for earlier locally logged inference/planning activity; no user prompts, generated answers, secrets or paths are included in the reported metrics.
- Optimized the file dependency sorter for thousands of model-authored proposals using a stable heap-based topological algorithm. **This does not prove any speed improvement in actual local-model inference.**
- No new interface elements, cloud calls, autonomous execution permissions or fake success/fallback plans.

Implementation details, measured historical reference data, limitations, and the next development priorities: `PLANNING_INTELLIGENCE.md`.

**Verification:** Tests run locally under an X virtual display. Actual Windows inference, X4 gameplay, Android compilation and GitHub Actions CI remain independently unverified until checked on the target environment.

**Installation:** Close DeepThorT, extract this release over `D:\deepthort`, and preserve `state`, `models`, `node_modules`, `cache`, `reference` and all project directories. Existing saved specifications and roadmaps remain intact.

---

# DeepThorT v25 — hierarchical project milestones with exact source traceability (22 November 2026)

**Source base:** v24. The original interface, Windows launcher, Qwen2.5-Coder ONNX model, gaming resource limits, JANUS/Sentinel, chat cancellation, user confirmation and stored state remain intact. This is Pass 4 of the Capability Library/development roadmap.

**What changed:** `deepthort_local/hierarchical_planning.py` persists a complete-section roadmap in SQLite. After the local model has reviewed every numbered section of an imported large specification, the system combines only **model-authored** file proposals, validates the aggregate plan, traces each file to its original section hashes, detects contradictory descriptions of shared files and groups the output into independently approved milestones. A milestone normally holds at most 12 files; it never bypasses the existing 24-file stage cap. Model input uses exact, labelled source-section excerpts, rather than cutting or overwriting the full original specification.

**Approval and verification:** A complete roadmap appears in Chats without queuing work. `Approve plan & queue` now offers one milestone at a time when the current chat has an active roadmap. Each milestone requires explicit user confirmation, individual file review and a separately approved test run. The next milestone is blocked until the prior milestone's actual job is verified (successful approved test exit and saved files). A successful command exit is not proof that an entire game works.

**Data integrity:** Existing or changed specifications and model responses cannot silently reuse a stale roadmap. Every indexed specification section must have a model-proposed file trace. Conflicts, missing section reviews, unbound files, changed fingerprints, wrong job identities and excessive inference scopes stop approval. Roadmap state survives application restart. Sequential gates are cautious scheduling, not independent AI discovery of complete software dependencies.

**Game project classification:** An Android/Faction Command game which refers to X4 as inspiration is no longer incorrectly routed into X4 extension preflight. Actual X4 mod projects retain the existing source inspection and validation gates.

**Local verification:** 263 Python tests passed under Xvfb, including 28 new hierarchical and GUI integration tests. Tests use scripted model outputs and controlled verification records; real Windows ONNX planning, Android compilation, X4 mod execution and gameplay remain unverified. Tkinter/SQLite teardown warnings from older releases remain in test output.

**Installation:** Close DeepThorT; extract v25 over `D:\deepthort`; preserve `state`, `models`, `node_modules`, `reference`, `cache` and your projects. For very large specifications, use **Ctrl+Shift+O** to import the full local text. Once all sections are reviewed and the roadmap is ready, approve the next milestone in the existing Chats panel; verify each before proceeding. No blanket multi-milestone execution permission is granted.

**Details and limitations:** See `HIERARCHICAL_DEVELOPMENT.md`. This is a working hierarchical execution foundation, not a verified autonomous game developer. Performance benchmarking, semantic requirement extraction and deliberate subsystem dependency planning are future work.

---

# DeepThorT v24 — large specifications + verified procedure evidence (22 November 2026)

**Source base:** v23 (Capability Library Pass 2). The original desktop layout, Windows launcher, JANUS/Sentinel architecture, locally installed ONNX model, resource limits, cancellation controls, explicit draft approval and 40-attempt limit remain intact. This release implements the first evidence-backed part of Pass 3 while removing the previous small text-storage and immediate-inference-input rejection behavior.

**Long-form instructions:** The former 250,000-character caps in `ConversationStore` and `JobStore` are replaced by a **120,000,000-character practical local storage ceiling** (roughly many millions of ordinary-language words). This is a local disk/RAM protection threshold, **not** the model context. The unaltered full specification is saved in SQLite. A separate durable index (`state/specification_index.sqlite3`) stores exact character offsets, section hashes, model review attempts and model-authored file proposals. It does not replace the original. Sections cover every original character without omission. Mismatched hashes fail closed and cannot reuse old progress.

**Large plan processing:** Specifications too large for the single 7,500-character inference prompt are reviewed by Qwen in numbered, exact sections of at most 3,200 characters, using up to **40 model calls per processing batch**. Already completed sections are saved and can resume on a retry without replaying prior calls. Malformed JSON does not advance coverage. An incomplete review or unresolved/contradictory plan is never approved or queued for execution. Once all sections have been reviewed, the accumulated model-origin file proposals must still pass the existing domain validator, and a single approved implementation plan is still limited to 24 file stages. Large games therefore require Pass 4's hierarchical milestone planner before automatic implementation. **This is not a claim that the model can understand millions of words simultaneously, or that every requirement has been semantically verified.**

**Large-spec import:** In the existing chat editor, right-click → **Import large specification**, or press **Ctrl+Shift+O**. Select a user-authored UTF-8 TXT, MD, RST, JSON or YAML file. Its length and SHA-256 are recorded; it is checked again at submission, with any additional instructions typed in the editor appended under an explicit heading. The original local file is never changed. Copy/paste into the editor remains supported, but import avoids trying to render millions of words in Tk. The chat timeline shows only a clearly marked display preview for messages over 12,000 characters, while SQLite retains their full contents. Imported files are read only; no external services or executables are invoked.

**Pass 3 — actual test evidence:** A new read-only `ToolEvidenceIndex` records successful and failed **user-approved JANUS verification** outcomes from `state/janus.sqlite3`, including action ID, fixed verification label, exit status and SHA-256 of the process log. It records **no command execution**, and never auto-promotes an observed action to a proved workflow. Saved observations are checked for action/log changes before reuse. The Capability Library can now explicitly elevate a candidate with a current hash-checked artifact only when paired with an eligible user-approved JANUS project-test action from the same workspace whose exit code is 0 and whose log remains intact. Eligible command profiles are Python unittest discovery, npm test, dotnet test, or Godot headless project validation; an unrelated `python -V` or `git status` is not enough. The resulting evidence level is **checked artifact + approved project test passed**, not end-to-end engine/game acceptance. Procedure evidence is invalidated when test status, log, artifact or procedure changes.

**Offline CLI:** Use the existing `python -m deepthort_local.capability_library --db state\capabilities.sqlite3` commands to inspect evidence, add a candidate and check its XML/JSON artifact. To associate a completed JANUS test, run `verify-workflow <procedure-id> <project-folder> state\janus.sqlite3 <JANUS-action-id>`. This is a read-only evidence association; actual test execution still requires GUI approval.

**Verification:** Linux virtual-display full suite: **235 tests passed**, including 23 new long-input, import, source-hash, resume, cancellation, evidence-reconciliation and verification-scope tests. Existing Tkinter/SQLite cleanup warnings remain. The ZIP and Windows launcher are integrity-checked separately. **No live Windows ONNX test, completed Xenon PE modification, actual Godot/Android build, or timing improvement is claimed.** Large inputs will take many model calls and significant disk space; faster hierarchical summarization/requirements traceability is the next pass.

**Installation:** Close DeepThorT, extract v24 over `D:\deepthort` and preserve `state`, `models`, `node_modules`, `cache`, `reference` and all project folders. The two new SQLite indexes initialize automatically. Back up `state` before importing very large specifications.

**Next pass (Pass 4):** Hierarchical milestone planning, scoped requirements traceability, staged builds beyond the 24-file limit, and repair/reconciliation of conflicting section proposals. Then benchmark performance and correctness on the real Windows machine.

---

# DeepThorT v23 — Capability Library Pass 2: local reference learning (22 November 2026)

**Source base:** verified v22 Windows package. This release preserves the desktop interface, launcher, JANUS/Sentinel, local ONNX model, 40-attempt plan approval rules, resource profile and existing local state. No new download, arbitrary command execution, cloud request or autonomous project file write is introduced.

**Implemented:** `deepthort_local/reference_learning.py` adds a separate hash-locked SQLite index of local project documentation and examples. `CapabilityLibrary.inspect_project` automatically indexes at most 20 qualifying text documents or code examples among the existing bounded workspace scan (up to 200 eligible project files); an explicit offline CLI command may select an additional allowed source from the selected project. Document bodies are **not saved** in SQLite. On retrieval, each source is reopened from the selected workspace, checked against its saved SHA-256 and read-only size/type restrictions, and ranked against the user's request. At most one short relevant passage per source is quoted with its path, line number, SHA prefix, and unverified version label. Credential-looking lines and obvious instruction-override text are omitted. Every excerpt is labelled **untrusted quoted reference data** and is never mistaken for validated instructions or a proved workflow.

**Planning integration:** v22's existing pre-plan discovery now finds these references and includes small, relevant excerpts in the optional capability context of the **initial draft-plan request** when sufficient space remains. It always preserves the complete original project requirements, the X4 preflight evidence and the 7,500-character planning limit. Unverified procedure candidates remain excluded. No new fields or controls appear in the window. The later 40-pass correction prompts do not yet have independent document retrieval; this is intentionally left to the hierarchical-planning pass.

**Offline developer CLI:** `python -m deepthort_local.capability_library --db state\capabilities.sqlite3 references D:\x4mods`; `reference-context D:\x4mods "Mission Director XML"`; and `index-reference D:\x4mods docs\api.md --version 1.0`. Version is a user-supplied, unverified label. See `CAPABILITY_LIBRARY.md` for full examples and limitations.

**Verification:** Full local Xvfb regression suite: **212 tests passed**, comprising the v22 baseline's 197 and 15 new reference-index tests. The tests cover persistence, project isolation, bounded discovery, staleness, path/symlink guards, secret/instruction filtering, context budget, offline mode and version provenance. The suite has pre-existing Tkinter/SQLite teardown warnings. Live Windows inference, model plan success, engine builds, and independent workflow verification remain untested. This release is **Pass 2 only**, not a claim that the agent can autonomously build games.

**Next:** Pass 3 attaches authorized build/test results and tool-version evidence to procedures before qualifying any workflow as verified. Pass 4 adds hierarchical, dependency-aware planning; Pass 5 measures real inference and game-engine outcomes.

---

# DeepThorT v22 — local Capability Library foundation (22 November 2026)

**Source base:** v21. No GUI layout change, no JANUS/Sentinel replacement, no model or inference changes, no automatic project writes, no extra cloud dependencies. Original approval and 40-attempt planning safeguards remain in place.

**New working foundation:** `deepthort_local/capability_library.py` maintains a local SQLite database (`state/capabilities.sqlite3`) for bounded observations of a selected project's manifests/configuration, file hashes and explicitly marked candidate procedures. The Draft project plan handler now performs read-only project discovery before model inference and can add small source-grounded references to the *first* planning prompt when the existing 7,500-character budget permits. The user's full specification and existing X4 evidence always take priority. Discovered project files are observations, **not** proof that a workflow works. A read-only XML/JSON/existence check can mark a procedure `artifact_checked`, but not as an execution-tested workflow. Nonverified candidates are never inserted into the model prompt. This stage does not automatically learn how to operate arbitrary tools or produce a game.

**Privacy and safety:** No project document body is copied into planning context, no tool is automatically launched, no project file is changed, and no observed candidate is silently promoted to working. Evidence is checked for staleness at retrieval. Local SQLite state should be preserved during updates and excluded from Git. Command-line developer inspection is documented in `CAPABILITY_LIBRARY.md`.

**Tests:** The new `test_capability_library_v22.py` covers discovery, persistence, offline behavior, scope, stale evidence, rejection of unverified procedures, deterministic artifact checks and prompt-budget preservation. A full regression run under Xvfb reported 197 tests passed; known preexisting Tkinter/SQLite cleanup warnings remain. Windows live ONNX speed/plan quality, full game engine execution and end-to-end autonomous learning remain unverified.

**Next passes:** (1) bounded retrieved documentation excerpts with source provenance, (2) authorized real build/test execution and workflow verification receipts, (3) hierarchical, dependency-aware game planning and measured performance. See `CAPABILITY_LIBRARY.md`.

---

# DeepThorT v21 — malformed-JSON planning recovery (22 November 2026)

**Source base:** v20. This is a narrow fix for `DeepThorT-Diagnostics-20261122-162725.zip` and does not alter the desktop layout, JANUS/Sentinel, ONNX worker, gaming limits, project approval, or the user's stored state.

**Observed:** In a live resumed Xenon PE draft request, the first pass yielded 7 model-authored files, but the following 9 passes generated structurally invalid JSON and retained no additional valid files. The number of missing requirements remained at 10. The Python planner limited all of these ~7,000-character input prompts to 384 output tokens. Its supposed increase to 640 tokens was gated on the input being shorter than 5,000 characters and therefore never applied here. A fixed output cap may truncate generated JSON, although raw model output is absent from the export, so truncation is plausible rather than proven.

**Correction:** On a malformed response, the planner now requests exactly one complete, short JSON file entry on the next revision, keeps the entire original specification, and increases the output allowance to 640 tokens for the first consecutive format failure and 768 for repeated failures. Input length no longer blocks that correction. Repeated malformed answers remain format failures, rather than resetting the output budget. A valid partial proposal resets the escalation; all valid model-authored files stay in the retained plan. This does not manufacture X4 file steps or grant execution permission. The 40-pass maximum and early stop upon complete validation remain unchanged.

**Privacy-safe diagnostics:** Each pass now records its requested token budget and consecutive format-failure count without saving the model's private answer text. Historical cached responses may be replayed when their exact prompt matches; a changed recovery prompt requires fresh inference.

**Verification:** 185 Python tests passed under Xvfb (`xvfb-run -a python -m unittest discover -s tests -q`), including 4 new budget/format/recovery tests. Pre-existing Tkinter/SQLite teardown warnings remain in test output. Tests do not prove that the model can produce a fully valid X4 plan or that live Windows inference is faster; larger token budgets can also increase individual generation time.

**Installation:** Exit DeepThorT before extracting into `D:\deepthort`. Preserve `models`, `state`, `node_modules`, `cache`, `reference` and project folders. Test the current failed draft via Retry if desired; completed passes can be reused only when their exact prompts match. Do not approve a plan until the application has validated it.

---

# DeepThorT v20 — JANUS local Interface + planning-revision reliability (22 November 2026)

**Source:** v19, retaining the original desktop interface and Windows launcher. This release does **not** add a second neural model, change the 20% gaming CPU profile, or give JANUS permission to approve/execute work.

**JANUS while Qwen is occupied:** In the existing Chats input, address a message explicitly to `JANUS` or `@JANUS` (e.g. `JANUS, report status`). JANUS now replies immediately using its saved Front/Interface status, Sentinel oversight state, existing approved-job counts and ONNX availability. It does not wait for Qwen and does not interrupt another chat. These are **read-only factual reports, not free-form AI language generation**. Ordinary chat still queues for Qwen; JANUS cannot independently explain arbitrary subjects or write complete project plans with its current deterministic architecture. Actions still require existing explicit approval controls.

**Planning:** The 40-pass limit, early stop on validated success and the complete original specification on **every** planning request remain intact. Revision requests now include the purpose/description of a few relevant previously model-authored files, target a missing criterion for more than one pass before rotating, and reject a rewrite that would remove previously satisfied criteria. Smaller model output budgets (384 tokens normally rather than 640; up to 640 after suitable malformed-JSON failures) and shorter fixed prompt instructions can reduce unnecessary inference, but no Windows speedup or valid Xenon PE plan has been demonstrated. No fixed or fabricated PE plan is substituted.

**Tests:** 181 tests passed in a Linux virtual-display run (`xvfb-run -a python -m unittest discover -s tests -q`). Tkinter/SQLite teardown warnings still occur. No live Windows inference, cancellation, X4 gameplay, Android build, or GitHub CI success is asserted by this test result.

**Install:** Exit DeepThorT, extract the package to `D:\deepthort` with application files overwritten; keep `state`, `models`, `node_modules`, `reference`, `cache` and project directories. Test an addressed JANUS reply while Qwen plans, then request a fresh draft plan to assess actual speed/quality.

---

# DeepThorT v19 — JANUS worker runtime correction (22 November 2026)

**Source base:** v18. This is a minimal diagnostics-driven correction, not a change to the existing interface, planning system, model, approvals, or JANUS topology.

- Fixed a JANUS idle-loop race observed as `ValueError: sleep length must be non-negative`: calculate remaining delay from one monotonic reading and skip sleep when the deadline has passed.
- Optional JANUS model counsel no longer sends a background request to the sole Qwen ONNX worker while an interactive request is already in progress. Deterministic JANUS observation continues independently.
- JANUS does not yet serve free-form chat replies; a separate response-routing architecture is required to do that without the busy model.
- Added targeted regression tests for these conditions. The 22 November 13:10 export showed planning pass 35/40 completed, pass 36 in progress, and one chat-mode request pending in the same thread. No approved implementation job was queued.
- Package deliberately leaves the desktop GUI and launch executable untouched. Keep all local models, caches, state and project files when installing.

---

# DeepThorT v18 — close chats and genuinely stop their local inference (22 November 2026)

**Source base:** v17. No changes to the existing JANUS/Sentinel architecture, model choice, planner criteria, 40-pass limit, explicit plan approval, project file generation, or window layout. The original button rows remain where they were.

**Observed problem:** Retrying an old planning conversation occupied the only ONNX model worker, leaving a new chat queued. v17 had no Close Chat or Stop Reply control; Stop AI paused an unfinished request for automatic retry, so it was not equivalent to cancelling it. The model server is single-flight.

**Repairs:**

- **Close chat** button in the existing chat toolbar. It asks for confirmation, cancels that chat's unfinished replies, hides its tab and **preserves** conversation history and drafts. Right-click the chat tabs to reopen a closed chat. It does not erase approved build jobs.
- **Stop reply** button in the existing lower chat-action row. Cancels pending/running/waiting-source conversation requests only in the selected chat. They remain cancelled after restart; they are not silently requeued.
- A running ONNX generation cannot be cancelled simply by disconnecting an HTTP request. DeepThorT terminates its **supervised** ONNX server/worker process, waits for process-exit notification, then automatically restarts a new supervised model for the next queued conversation. The original model initialization time is still required. Model weights, job queue and source files remain intact.
- Completed replies or network errors arriving after cancellation cannot overwrite a cancelled conversation or clear the next chat's current reply. The planning loop checks for cancellation between model passes, ensuring a cancelled 40-pass request does not continue making new calls.
- Existing session state remains in its SQLite files. Closing a tab is an archive action, **not deletion**; approval and execution jobs retain their existing separate controls.

**Verification:** 170 Python tests passed when run in isolated modules under Xvfb, including seven new chat/cancellation tests. The monolithic GUI test discovery run encountered the earlier Tkinter teardown / async-cleanup crash; therefore do not claim that particular run was green. Tests use mocked model processes; a real Windows worker termination and reload still need an on-PC test. The interface is unchanged except for two buttons and a right-click archive/reopen menu; a screenshot-sized (1138×765) geometry test confirmed action buttons remain visible.

**Installation:** Close DeepThorT and extract `DeepThorT_Desktop_v18_Windows.zip` over `D:\deepthort`. Preserve `models`, `state`, `node_modules`, `cache`, `reference` and all project directories. No new installs, cloud service or source-editing permission is introduced.

**How to recover from an old running chat:** Open that chat, click **Stop reply** or **Close chat**, then open/select the other chat. Cancelling an active ONNX response causes a real model worker restart; the new chat can run once the model is ready. **Stop AI** remains a global pause; use **Stop reply** for permanent cancellation of the selected request. To stop already-approved jobs, use Work queue → Cancel selected or Processes → Cancel running job.

---

# DeepThorT v17 — targeted model-authored plan revisions (22 November 2026)

**Source base:** v16; original v10.9 interface geometry, approval rules, JANUS/Sentinel, offline Qwen ONNX inference, local state, resource settings and Windows launcher are unchanged.

**Observed failure:** The 07:57 diagnostic ZIP from 22 November records another 40 completed local model planning calls for the Xenon PE project without a validated plan. The model responded to each request, but the validator still listed missing X4 deliverables. No work was approved, queued or generated. The export intentionally omits the raw proposals, so it cannot establish which individual replies were malformed. Raising the timeout or attempt limit again would not solve this result.

**Repairs (model remains solely responsible for proposing files):**

- The first request asks the model for up to two short, concrete file descriptions, rather than up to five. Each subsequent repair asks for **one or two files**, reducing the chance of incomplete JSON within the existing 640-token output allowance.
- The unchanged project validator identifies the current unmet criteria. Later requests explicitly focus on **one missing criterion at a time**, rotating even when no model output has been accepted. All instructions and original specifications remain in the model's input; previously proposed file paths and source candidates are preserved and included where the context window permits.
- Accept a single structurally valid JSON plan object embedded in a model response with prefatory prose. Reject malformed, ambiguous or multiply embedded objects. No plan step is fabricated or inferred from text.
- Record privacy-safe planning telemetry in `state/logs/planner.jsonl`: pass number, reply length, number of retained/new/revised files, remaining validation gaps, duplicate/JSON rejection and current focus. No raw private prompt, model reply or file contents are written to diagnostic logs.
- The 40-attempt maximum and **immediate stop once a complete plan validates** remain unchanged. An unsuccessful plan cannot be approved or executed, and no hardcoded Xenon PE plan is substituted.
- An existing GUI test now waits until its background planner finishes before deleting its temporary test fixture, correcting a non-production test cleanup race.

**Local tests:** `xvfb-run -a python -m unittest discover -s tests -q` -> **163 tests OK**, including five new targeted-planning tests. Tests use scripted replies; **actual 1.5B model success is still unverified**. This release does not claim to have built the PE mod, loaded it in X4 or implemented an autonomous game developer. If the model continues to fail, the new safe planning diagnostics identify whether output formatting, repeats or missing requirements are the blocker.

**Installation:** Fully close DeepThorT, extract `DeepThorT_Desktop_v17_Windows.zip` over `D:\deepthort`, keeping all `models`, `state`, `node_modules`, `reference`, `cache` and project files. The 40-pass run already failed, so request a **new draft plan** (not a stale replay). For a genuinely interrupted and incomplete run, `Retry failed reply` may recover completed identical passes from SQLite.

---

# DeepThorT v16 — avoid lost long-running inference and resume interrupted plans (21 November 2026)

**Source base:** v15, with the v10.9 interface geometry unchanged. No new panels,
model providers, approval rules, JANUS/Sentinel changes or canned X4 plans.

The 17:22 diagnostic export showed a planning inference timed out after 900 seconds
at 17:15:26 Brisbane time. The local ONNX worker returned a valid response only
15 seconds later, but Python's HTTP client had already disconnected and the
model answer was discarded. Earlier passes had each taken 8½–10 minutes.

**Corrections:**

- Local HTTP inference read timeout is now **3600 seconds**, not 900 seconds.
  The desktop still reports elapsed inference time and Stop AI remains available.
- During 40-pass planning, completed local-model exchanges are recovered from
  the **existing** `state/sessions.sqlite3` database on retry/restart. They are
  reused only if their exact preceding prompt matches, so changed requirements
  or source evidence force new inference. Unfinished passes are generated anew.
- The approved-work queue and generated files remain untouched. There is still
  no hardcoded PE plan, no synthetic success and no execution without approval.
- No additional persistence copies of user prompts, model output or credentials.

**Verification:** 158 Python tests passed on a local Xvfb run, including five
new timeout/restart recovery regression tests. One initial full-suite run hit
an existing asynchronous Tkinter temporary-folder cleanup race; the subsequent
full-suite run passed. This verifies code paths, **not** live Windows ONNX
inference, the Xenon PE mod or X4 gameplay.

**Installation:** Close DeepThorT, extract this ZIP into `D:\deepthort`, and
retain `models`, `state`, `cache`, `node_modules`,
`reference` and project files. Restart and **Retry failed reply** on the
original Xenon PE conversation to reuse previously completed pass data when
its exact saved prompts match. If the conversation had already reached all
40 failed passes, submit a new draft request instead.

---

# DeepThorT v15 — allow up to 40 self-correction passes (21 November 2026)

**Source base:** v14. No UI layout changes, no JANUS/Sentinel modifications, no new cloud/model providers, no resource-limit changes. The same standalone Windows launcher, chat/approval boundary, local ONNX model and user-state folders remain in place.

**Observed failure:** `DeepThorT-Diagnostics-20261121-155708.zip` and the 15:57 screenshot show a real 41-minute local planning run that exhausted four attempts. All four model requests finished; none passed the X4 plan validator. The desktop passed `max_rounds=4`, and the planning module rejected limits above 8. No approved X4 execution job was created.

**Repair:** Normal model planning now allows **up to 40 attempts**, displays the pass count in the existing activity status, and **returns immediately** when a complete plan passes validation. An identical *invalid* model answer no longer causes premature termination; instead, specific corrective feedback is sent for the next pass. When a fragment would exceed 24 distinct files, it is rejected transactionally without corrupting prior model-proposed steps, giving later passes a chance to succeed. The original user request remains unmodified and must fit into each model prompt. No prewritten Xenon PE plan is ever inserted; actual job execution still requires explicit user approval. If 40 attempts fail, the saved request remains retryable and no plan or job is automatically approved.

**Verification:** `xvfb-run -a python -m unittest discover -s tests -q` → **153 tests, OK** (five new v15 tests covering 40 attempts, early success, repeated failures, source-plan overflow recovery and desktop budget wiring). Full source compiles. Tkinter/SQLite cleanup warnings remain in the headless test output. Actual Windows inference success, valid model-authored X4 plan, game XML generation and in-game behavior are **not verified**. The existing local Qwen ONNX model took approximately 9–12 minutes per planning request in the reported diagnostic run; 40 failures could therefore take hours if allowed to continue. The user can close/retry as before, but a running draft-planning thread is not claimed to survive application shutdown.

**Installation:** Close DeepThorT, extract v15 over `D:\deepthort`, preserve all local `models`, `state`, `node_modules`, `cache`, `reference` and project workspaces, then use **Retry failed reply**. No re-extraction of the game's reference data is required if existing data is valid.

---

# DeepThorT v14 — bounded planning revision context (21 November 2026)

**Source base:** v13, retaining the original v10.9 interface, JANUS/Sentinel, local ONNX model, resource limits, chat/work-queue approval boundary and all user state. No new application features or UI layout changes.

**Repair:** The 15:07 diagnostics and screenshot showed `build_revision_prompt` throwing `PlanError: Existing plan paths cannot fit alongside the complete original specification` on the first correction after a model-generated plan. The old implementation allocated prompt space for verified evidence and verbose existing-step descriptions, then aborted when the accumulated paths would not fit the 7,500-character request window. This rejected the planning attempt **before the local model could attempt a correction**.

v14 preserves the full original user specification on every planning pass and keeps every previously model-proposed step in local accumulated state. Only the **revision request's auxiliary context** is budgeted: it supplies complete existing file paths that fit, marks how many were omitted from that model context, rotates the path selection across passes, and fits source evidence only in the remaining space. All saved steps still merge and face the normal full-plan validator; no predefined PE plan or unrequested file is inserted. A genuinely overlarge complete specification still fails safely without truncation.

**Observed validation:** `xvfb-run -a python -m unittest discover -s tests -q` → 148 tests, OK; four new v14 regression cases reproduce oversized path context, verified evidence budgeting, successful model-revision continuation, and safe rejection of genuinely oversized full specifications. Some pre-existing Tkinter/SQLite cleanup warnings occur during headless GUI tests. No live Windows inference, user-side layout, independently adequate Xenon PE plan, approved executable mod job or X4 gameplay has been verified. Future acceptance tests must establish those separately.

**Installation:** Close DeepThorT and extract v14 over `D:\deepthort`, preserving local `models`, `state`, `node_modules`, `cache`, `reference` and project workspaces. User approval is still mandatory before any planned job executes.

---

# DeepThorT v13 — model-authored plans, bounded self-correction (21 November 2026)

**Source base:** v12 (which preserved the original v10.9 interface). This release does not add controls, rearrange panes, replace JANUS/Sentinel, change local ONNX inference, or alter the CPU/memory supervisor. It retains existing user state, model files and approved-job boundaries.

**Why v13:** The 21 November 14:07 diagnostics showed a *hardcoded Xenon PE fallback draft* was substituted after the actual model-generated draft failed validation. That is NOT evidence the AI can plan software by itself. The v11/v12 fallback has therefore been removed, not renamed or disguised.

**Planner changes:** Every source path and description in a new draft must originate in actual local model output. Incomplete proposals can be extended or corrected over at most four separate model calls, using validator feedback and actual verified X4 source candidate information. Each pass uses its own inference context to avoid exceeding the small ONNX model's message limit. A repeated identical answer stops early, not after multiple wasted attempts. The complete original specification remains preserved and included in revision requests; genuinely oversized requirements fail explicitly instead of being silently trimmed. If a valid plan is not produced, the request remains retryable and **no draft or executable job is substituted**. Approval is still required before any work is queued.

**Safety and technical validation:** Legacy *source-grounded fallback* drafts from v11/v12 cannot be approved; their chat records are retained. X4 plans now require appropriate asset registration and independent projectile definitions for the per-hit PE test, reject obvious L/XL equipment candidates on the M-class PE, and require component registration if proposing a new component. The read-only evidence scan ranks M-class candidates before L-class destroyer candidates, but filename class remains *a hypothesis*, not proven equipment compatibility. Initial model-generated Android/game plans are checked for real source files, build configuration, gameplay, interface and test coverage, not a single generic stub. The new validator does not guarantee a project will work; actual source inspection, code generation and build/game tests are still required.

**Observed evidence:** 144 Python regression tests pass locally under Xvfb, including the pre-existing v12 GUI layout tests, multi-pass model-authored draft tests, X4 source-ranking checks, Android game planning checks, and old fallback approval prevention. The live Windows Qwen ONNX model and installed X4 game are unavailable in this test environment: **no real AI plan or Xenon PE mod has yet been produced/verified by this build**. The 1.5B model may remain slow or incapable of a complex plan. Model quality and long specifications are still limits.

**Install:** Fully close DeepThorT, then extract over `D:\deepthort`. Preserve all existing `state`, `models`, `node_modules`, `cache`, `reference`, and project directories. Restart the usual `DeepThorT.exe`. The old source-grounded PE draft will be rejected if you try to approve it; request a fresh draft so the actual model must plan. The existing reply activity appears in the original status row. No local game data or user files were included in this release ZIP.

---

# DeepThorT v12 — restore original v10.9 window layout

The extra v11 reply-status banner was removed because it clipped the bottom action buttons at Windows display sizes. Waiting, generation, validation, and failure notices now appear in the **existing** status row, preserving the original vertical geometry. No new controls or tabs were added. All v11 safeguards and X4 planning fixes remain.

# DeepThorT Desktop v11 — repairs based on the original v10.9

This package is rebuilt from the **original v10.9 Windows ZIP**. This v11 release keeps v10.9 as its code baseline. The original workflow and model backend are retained.

**Diagnosis from the 2026-11-21 12:40 Brisbane diagnostics:** The original Xenon PE plan request entered ONNX inference at 12:30:28 and answered about 10 minutes later; the model generated a proposal missing required X4 extension files, equipment coverage and ownership monitoring. It was correctly rejected. The local model was functioning, but its 1.5B parameter capacity/CPU cap make such output slow and unreliable. The screenshot showed the idle `AI: ready` label after the request had already failed.

**Repair:** Chats now has a separate always-visible *reply activity* line. It shows queued/waiting requests, preflight stages, local ONNX generation with real elapsed wall time, draft validation, completion and failure. Model readiness stays separate and cannot replace reply-activity status. No imagined token percentages are displayed.

For the exact PE task, a failed model proposal is retained in local model-session history; **only if extracted vanilla PE macro, component slots and weapon/turret XML are verified** will DeepThorT produce a source-grounded replacement DRAFT for explicit approval. No project file changes, model downloads or execution jobs are authorized by draft recovery. Without verified sources it remains a clear failed/retryable request. The planned file-generation prompt retains the original user specification and current-file description within the 7,500-character local prompt budget, and rejects genuinely oversized requests rather than silently truncating them.

**Important limitations:** The fallback is a reviewable file-stage plan, not a finished or game-tested X4 extension. The real 1.9 GB Qwen model and the X4 installation are on your Windows machine and were not available for a complete live end-to-end test in this build environment. The 20% CPU / committed-memory supervision remains unchanged.

**Installation:** Close DeepThorT. Back up `D:\deepthort\state` if desired. Extract this ZIP over the existing `D:\deepthort` application files. Keep `state`, `models`, `node_modules`, `cache`, `reference`, and project folders intact. Restart with `DeepThorT.exe`; retry the failed PE draft. The new reply banner will show the real stage and elapsed time. The ZIP carries no state database or model weights.

**Validation:** 129 local Python automated tests passed under a virtual graphical display: 121 original v10.9 tests and 8 new regression checks for reply status and source-verified draft recovery. Python compiled successfully; no actual X4 in-game verification was performed.

---

# DeepThorT Desktop v10.9 — X4 planning input-budget fix (21 November 2026)

**Diagnosis from `DeepThorT-Diagnostics-20261121-122349.zip`:** DeepThorT correctly detected the installed X4 game, ran the previously approved XML extraction, and reported verified PE macro/component and weapon/turret reference candidates. It resumed the original draft-plan request, but the app built a **7,566-character inference prompt**, 66 characters above its own 7,500-character cap. The conversation then failed before the model was called. It did **not** create an executable job or an X4 mod. This is an input-assembly bug, not a failure of the user's specification or a reason to extract the assets again.

## Changes

- In X4 planning, preserve **the complete original request** and prioritize the verified PE connection tags and actual ship, weapon and turret reference identifiers. If the attached inspection details make the combined prompt too long, fit complete reference lines into the remaining space instead of rejecting the entire request or truncating an identifier. Short provenance SHA snippets can be omitted from the model's context; the complete inspected files and their hashes remain intact in the local reference directory.
- Ensure inspected-reference summaries prefer the PE connections and at least one example of each essential macro class before optional candidates. No partial XML path or ID is sent as evidence.
- Fail closed with a specific message if even the complete user request plus essential reference lines cannot fit. This fix does **not** silently summarize, cut or drop user requirements. Very large instructions still need a future multi-pass context-management system.
- Record that the original user specification was preserved and the final bounded model-input size in the automatic diagnostic log.
- Keep X4 source preflight, extraction approval, chat/plan separation, and the user's separate **Approve plan & queue** step unchanged.

## Install and retry without retyping

1. Fully close DeepThorT. Optionally back up `D:\deepthort\state` first.
2. Extract this ZIP directly into `D:\deepthort`, replacing **application code** and `DeepThorT.exe`.
3. Keep `state`, `models`, `node_modules`, `cache`, and `reference` folders. The game XML references already extracted should be reused; do not extract them again unless DeepThorT identifies missing files.
4. Open `DeepThorT.exe`, select your existing X4 project and chat, then click **Retry failed reply**. The original full prompt was saved by v10.8; no need to paste it again. The existing plan is not automatically approved.
5. Review any proposed X4 extension plan carefully. A valid plan needs extension metadata, ship/equipment XML, respawn MD logic, 50,000 damage/hit, 4× speed, 10× cargo, handling improvements, and a 60-second ownership check. **Only** click Approve plan & queue if the plan is technically credible and meets your requirements.
6. If it still produces an invalid proposal, export diagnostics and send the ZIP. The 1.5B local model's ability to create a correct complete mod is not established by passing these infrastructure tests.

**Verification:** 121 automated tests passed, including a GUI test of the previously-failing combined prompt boundary and preservation of source references. Python compilation and ONNX JavaScript syntax checks passed. Real inference on the user's Windows PC and X4 mod generation were not performed in the test environment. Existing 20% CPU/committed-memory settings are unchanged; no hard 20% disk-activity ceiling is claimed.

---

# DeepThorT Desktop v10.8 — Automatic X4 inspection from the first prompt

**Repair based on `DeepThorT-Diagnostics-20261121-120413.zip`:** The game was not being inspected by the chat workflow when the user asked DeepThorT to examine it. v10.7 offered a separate Computer & Tools button, and blocked the project plan with instructions to press it. That is not an autonomous source inspection.

**v10.8 changes**
- An X4 request now starts a bounded **read-only** inspection as soon as the user submits the initial chat or draft-plan prompt, *even before the local model is ready*. It lists the selected project files, detects known Steam/GOG installations, paired CAT/DAT files, and previously extracted vanilla XML references.
- The conversational worker repeats the inspection and uses verified PE macro, component connection, weapon and turret references rather than asking the model to invent or inspect them. Follow-ups like **"examine it"** inherit the selected `x4mods` project and recent X4 chat context; explicit inspection questions get a real local report without calling Qwen.
- If CAT/DAT archives are present but extracted XML is missing, the app finds an already-installed official `XRCatTool.exe`. If found, it **asks one explicit permission** to extract only relevant XML to `D:\deepthort\reference\x4`. After a successful extraction, DeepThorT verifies the actual references and **automatically resumes the original saved conversation or plan request**. The requested mod is never added to the execution queue without separate plan approval.
- If the game installation cannot be located, DeepThorT opens a folder chooser **as part of the original request** (not a separate inspect command). If the official extraction tool is absent, it asks for its path. Downloading/installing an extractor is NOT automatic and still requires the user's authorisation.
- Extraction is deferred while a configured game is running to respect gaming priority. An extraction denied by the user or interrupted by an app restart **does not silently execute or repeat**; the original request is retained for explicit retry.
- The new source-discovery, tool-consent, worker-state and conversation transitions are included in Export diagnostics.
- Existing chats, model weights, project files, approved work and JANUS/Sentinel states are preserved. There is **no installer and no cloud provider** in this update.

**Use it**
1. Close DeepThorT. Extract the ZIP directly into `D:\deepthort` and replace app code. Keep `state`, `models`, `node_modules`, `cache` and `reference` directories untouched.
2. Double-click `D:\deepthort\DeepThorT.exe`, select `D:\x4mods` on the left, and use Chats → **Draft project plan** with the original Xenon PE specification. You do NOT have to open Computer & Tools first. Even when the model is still loading, source discovery begins immediately.
3. If asked, permit a specific **read-only catalog extraction to separate reference files** (not a game modification). If X4 or the official tool cannot be located, the app will ask for the missing location, not tell you to inspect it yourself.
4. Once verified sources are available, the saved plan request is submitted to the local model. Review any draft carefully. Only **Approve plan & queue** can authorise a mod-building job.
5. If inspection fails, click Export diagnostics and send the ZIP; X4 preflight events should show what was found and what was missing.

**Validation:** 117 local automated tests pass (including GUI tests using a virtual display). Real X4 catalog extraction and PE equipment inspection on the owner's Windows PC still require validation. The existing resource limits remain; a strict universal 20% disk busy ceiling is still not implemented. The local 1.5B model's ability to produce a correct full extension is not yet demonstrated.

---

# DeepThorT Desktop v10.7 — X4 source discovery and approved extraction

**Why this update exists:** the submitted `DeepThorT-Diagnostics-20261121-114522.zip` and screenshot show that Qwen finished the X4 planning request, but the resulting plan lacked actual X4 ship/equipment definitions. v10.6 correctly prevented a bad approval; it did not know how to locate the missing source data.

**Changes implemented:**
- **Computer & Tools → Inspect X4 sources** searches only named Steam/GOG game locations and bounded XML folders (no full-drive scan, no installer, no game writes). It distinguishes CAT/DAT catalog *indexes* from usable extracted XML sources.
- **Choose X4 game folder** lets you select the installed X4 directory containing `X4.exe` and numbered `.cat`/`.dat` archives when automatic discovery is insufficient.
- **Choose extracted X4 XML** lets you point to a pre-existing reference directory with `assets/`, `index/`, and `libraries/`. It is read-only.
- **Extract X4 XML (approval required)** accepts the official Egosoft `XRCatTool.exe` only after you explicitly select or locate it. Shows the full read location, output directory and tool path; waits for explicit approval, then filters extracted XML to ship, equipment, libraries, indexes and MD. Output is under `D:\deepthort\reference\x4`, never into the X4 game installation. The app will not download a catalog tool on its own.
- Inspects the *actual extracted file content* for the Xenon PE ship macro `ship_xen_m_corvette_02_a_macro`, its referenced component's real weapon/turret connection tags, candidate weapon macros and turret macros. The published PE name is only used as a lookup hint; installed definitions must be verified before being trusted.
- Includes verified reference file paths, macro names and short SHA-256 fingerprints in an X4 project-planning request. **When the sources are missing, the app tells you what is needed instead of using Qwen to invent names or propose `src/main.py`.** A plan with insufficient verified sources also cannot be approved after restart.
- Existing chat history, unapproved drafts, JANUS/Sentinel records, local AI model and queued approved work are retained. No new mod was generated by this update.

**How to use for your Xenon PE mod**

1. Close the app. Extract this ZIP over `D:\deepthort`, replacing code and launcher files, **but preserve the existing `state`, `models`, `node_modules`, `cache`, and any `reference` directory**.
2. Open `DeepThorT.exe`. Select the **Computer & Tools** tab and click **Inspect X4 sources**.
3. If no X4 installation is found, click **Choose X4 game folder** and select the folder containing `X4.exe`.
4. If it has game catalogs but no extracted XML, either select a previously extracted vanilla reference folder or click **Extract X4 XML (approval required)** and choose the Egosoft catalog tool. You can download X Tools from Steam or the official link below (registration/ownership may be required). Close games before extraction because 20% disk active time is NOT hard-enforced.
5. Inspect the report: it must verify the exact PE macro, its component connections, and real weapon/turret candidate XML. Then return to Chats and submit **Draft project plan** again. Review the proposal; do NOT approve anything inaccurate.
6. If it still reports a blockage or incorrect plan, click **Export diagnostics** and upload the ZIP. The app must not change game files or queue unapproved work.

Official tool: https://www.egosoft.com/download/x4/bonus_en.php. The X Catalog Tool can extract catalog XML. Command flags follow the public documentation at https://x4wiki.com/en/pages/tool-catalog .

**Limits:** This is a real reference-inspection and approval-gated extraction path. It is not proof that the 1.5B local model can correctly generate a custom ship extension, select the highest-firing-rate compatible weapons, install it, or test the final mod in X4. Those steps still require verification. A strict universal 20% disk active-time ceiling is unavailable. The original 20% Windows CPU and committed-memory caps remain unchanged and require device-level validation.

**Checks:** 105 Python regression tests passed in the headless GUI environment, including 9 tests for source inspection, extraction command restrictions and real GUI plan blocking. Windows GUI binary is present but actual extraction and game inspection are untested on your PC.

---

# DeepThorT Desktop v10.6 — Source-aware plan validation hotfix

**Issue investigated:** User's first X4 Xenon PE plan consisted only of `src/main.py` and was correctly rejected with No. The supplied diagnostic ZIP confirmed the local ONNX model actually loaded and produced that 130-character generic plan. The application must not treat valid JSON/path safety as evidence of an adequate engineering plan.

**Fixed:**
- Removed `src/main.py` from the planner's embedded JSON example; projects must use files relevant to their actual language/toolchain.
- Added specific X4 extension planning instructions: game-source inspection, `content.xml`, ship/equipment XML, Mission Director respawn logic, vanilla slot compatibility and explicit numeric requirements.
- Reject plans that don't cover X4 extension structure, the Xenon PE's cargo/weapons/turrets/speed/handling/ownership and any explicitly requested 50,000-per-hit, 4x speed, 10x cargo and 60-second replacement values.
- Require the model to identify missing X4 asset references rather than invent game identifiers. **This does not implement X4 CAT archive extraction. Actual game-file inspection still requires access to the game assets and possibly an extraction tool.**
- Validate both when generating a draft *and* when converting it into an executable queue job.
- Choosing No now discards the pending draft; previous invalid X4 drafts are automatically revoked on upgrade, without changing saved chats, model weights, or user project files.
- The proposal output cap is 640 tokens instead of 384 for complex JSON drafts; with an old CPU and 20% limit, planning will take longer.

**Installation:** Close DeepThorT, extract the entire update ZIP directly over `D:\deepthort` and preserve `models`, `node_modules`, `state` and `cache`. Launch `DeepThorT.exe`. Use Draft project plan again. An incomplete X4 proposal should now be marked **failed / needs source inspection**, not presented as a valid plan for approval. The rejection reason appears in chat and diagnostics.

**No guarantee:** The local 1.5B model has not been proven capable of independently inspecting X4's packed game definitions, creating the mod correctly, or running an in-game verification. No mod was generated in this update. The 20% CPU and RAM limits are unchanged; a universal hard disk activity limit remains unavailable.

---

# DeepThorT v10.5 — Chronological Chats & Observable Inference (21 November 2026)

**Fix for the user's latest diagnostic ZIP** (`DeepThorT-Diagnostics-20261121-105654.zip`): the offline Qwen 1.5B ONNX model reached **ready in 66 seconds** at approximately 00:55:01 UTC. The first migrated chat request was dispatched and a real model HTTP request began at approximately 00:55:02 UTC. It asked for up to **384 output tokens** and had **not finished** when the ZIP was exported at 00:57:00 UTC. This is not evidence of a dead queue or of a successful response; generation may be slow at the enforced 20% CPU cap. Two earlier pre-approval chat jobs were successfully migrated to non-executable conversation requests. None was approved work.

## Repairs

- **Oldest-first conversation display, newest at the bottom.** The GUI now merges historical self-diagnostics, the durable conversation inbox and approved build status messages by actual timestamps, rather than displaying *all* messages from the model-history database first. It also restores the original timestamps of old work-queue messages that v10.4 migrated, so messages written yesterday no longer appear as though first sent during migration.
- **No repeated messages.** Completed prompts that appear in both SQLite histories are deduplicated as full user/assistant pairs, not by matching all repeated text; separately repeated legitimate messages remain visible.
- **Faster ordinary chat requests.** New conversational answers use a maximum of 128 generated tokens rather than 384. Project planning remains at 384 tokens. Repeated local diagnostic dumps stay visible but are excluded from the model's input context, avoiding CPU-intensive reprocessing of multi-page telemetry with each response. Existing stored conversations are preserved and unchanged.
- **Actual inference activity.** The local-only server's `/health` now distinguishes `ready` (model initialized) from `inference_busy` (currently generating), reporting time elapsed and requested token cap. The desktop updates the Chats status banner and Processes tab while a request is running. A bounded `inference_still_running` log event is recorded approximately every 30 seconds; it does **not** invent token-by-token progress.
- **No repeated readiness log spam.** The `model_ready_event` is recorded only once on transition to ready, instead of at every subsequent health check.
- **Deterministic self-diagnosis.** It now reports whether a live generation request is in progress, separate from whether model startup finished.

## Upgrade

Close DeepThorT **fully** before changing its files. Optionally back up `D:\deepthort\state` first. Extract the entire v10.5 ZIP directly into `D:\deepthort`, replacing application source files and `DeepThorT.exe`. **Do not delete** your existing `state`, `models`, `node_modules`, or `cache` directories. Launch `D:\deepthort\DeepThorT.exe` normally. This package does not contain or re-download Qwen weights.

The current implementation's 20% CPU and committed-memory caps are unchanged. Universal disk-activity 20% hard enforcement is still not implemented. Inference speed and the first real completed model reply on the user's Windows PC remain to be measured. If chat does not finish, use **Export diagnostics** after the Processes tab displays a running inference duration, and submit the ZIP for diagnosis.

**Verification:** 89 Python tests passed in a Linux virtual desktop (including real GUI chronology tests, persistent-timestamp repair and model-history context filtering). A standalone Node.js test using a fake ONNX worker verified that `/health` reports an accepted request while it is being processed and returns to idle afterward. JavaScript syntax and Python compilation checks passed. These checks do not imply that the real model answered successfully on the user's machine.

---

# DeepThorT v10.4 — Chat-first workflow, approved jobs only, improved diagnostics

**Send message is conversation, NOT a work-queue submission.** Your large prompt is saved in a separate persistent conversation inbox while the local AI loads. JANUS answers it when the model becomes ready. Ordinary messages, including project discussions and uncertainty resolution, do not authorize code execution or file changes.

**Plan approval workflow**

1. In **Chats**, discuss the project. Use the **left Project Workspace panel** to choose a folder and inspect its files; it is not an approval control.
2. Click **Draft project plan** with your agreed specification. The draft stays in Chats, not in Work queue. The current local model attempts to produce a bounded, validated list of source-file stages; invalid results are reported, not executed.
3. If anything is wrong, discuss it and request another draft. Requesting a new draft invalidates the old unapproved proposal to prevent stale approval.
4. Click **Approve plan & queue** only after reviewing the displayed steps. A separate confirmation dialog requires your explicit approval. This is the **only normal GUI action that creates an executable project-build job**.
5. In **Work queue**, JANUS can then generate the approved files. Individual writes and execution of verification commands still require their own approvals. No download or installation is implicitly authorized.

**Existing user messages are preserved:** On the first v10.4 launch, old queued `chat`, `plan` and `edit` records from v10.3 are copied into `state/conversations.sqlite3` and their former work-queue entries are marked non-executable. This process is restart-safe and idempotent. Legacy unapproved build jobs without reviewed file steps are held for advice instead of being automatically launched. The other original databases are not deleted.

**Your first diagnostic ZIP** (`DeepThorT-Diagnostics-20261121-104159.zip`) showed two chat jobs stuck in the work queue and no active job. The ONNX service had reached file access `done: onnx/model_q4.onnx` but had not emitted a model-ready event; its last real stage event was 213 seconds earlier. The file-reading event is NOT proof of finished ONNX session initialization. This export does not establish a post-readiness queue-dispatch failure. The original user's model may subsequently have completed initialization, but that is not established by this ZIP.

**Better automatic logs:** The support ZIP now includes only safe conversation status/length metadata (no raw prompts), and 60-second per-process CPU and private/resident memory samples where Windows exposes them. Sentinel groups recurring “local AI still loading” warnings into one issue instead of creating a distinct record for each changing elapsed-second value. The exact reason the model takes several minutes to initialize remains unverified until the next PC diagnostic contains resource measurements and, ideally, a model-ready/error event.

**Upgrade:** Close DeepThorT and extract the entire v10.4 Windows ZIP directly over `D:\deepthort` so `DeepThorT.exe` and `desktop_app.py` sit in that root. Keep `D:\deepthort\state`, `models`, `node_modules` and `cache`; the ZIP omits those directories. Double-click **DeepThorT.exe**. No command prompt and no model re-download are required for this code update. Before an app update, copying `state` to a backup location is prudent.

**Verification:** 82 Python unit/GUI regression tests passed in the available Linux virtual display, including simulated offline model replies, draft-review-to-job dispatch, migration, persistent chats, diagnostic ZIP privacy and Sentinel warning deduplication. This validates the code paths but does **not** claim Qwen has initialized successfully or that long-running autonomous game development is verified on your specific Windows PC. The configured 20% CPU/committed-memory supervisor remains; a universal Windows 20%-disk-activity hard limit is still not implemented.

---

# DeepThorT v10.3 — Automatic diagnostics and queue-dispatch repair

**The diagnostic recorder now runs automatically.** It writes bounded, rotating diagnostic logs under `D:\deepthort\state\logs` whenever DeepThorT is open, including JANUS and Sentinel child processes, ONNX model startup stages, model request timings, queue transitions, scheduler blocking reasons, background exceptions, and resource snapshots. It does not send any data to an external service. Logs rotate at 3 MB per component with up to three older copies. The recorder is designed to avoid substantial disk activity.

## To send one diagnostic file

1. Start `DeepThorT.exe` normally. Wait for the issue to occur, or try one queued chat message.
2. Click **Export diagnostics** at the top of the application (works even if Qwen is not responding).
3. Save the ZIP, preferably in `D:\deepthort`. The suggested name starts `DeepThorT-Diagnostics-`.
4. Attach that **one ZIP** to your ChatGPT conversation. There is no need to copy PowerShell output or send multiple screenshots.

The ZIP contains application/queue/JANUS/Sentinel/ONNX logs, job states and transitions, selected process failures, and checks for required files. It does **not** include full conversations, model weights or copied SQLite databases. **Review it before sharing:** filenames, error messages and short excerpts from approved build commands may contain private project information. Do not use the ZIP as a backup of your conversations or model files.

## Queue repair

The job scheduler previously selected only the currently visible project. A saved task from another project could remain queued indefinitely even after the ONNX model became ready. It now dispatches the oldest eligible queued job across all projects. Logging also records whether dispatch is blocked by model readiness, a stopped process, paused queue, active work, or an installer. GUI callback exceptions no longer disappear into an invisible command window, and a failed scheduler iteration reschedules itself. This does not guarantee Qwen's response quality or that it will finish quickly at the 20% CPU limit.

**Installation:** Close the old app, extract the entire v10.3 ZIP directly into `D:\deepthort` over the existing program files, keep `state`, `models`, `node_modules` and `cache` intact, and double-click `DeepThorT.exe`. No new model download is needed. Actual Windows behavior and real Qwen model inference still require on-PC verification.

**Verification:** 74 automated tests passed in the available Linux virtual desktop, including a simulated loaded-model queue dispatch across projects, diagnostic ZIP privacy checks, and Node.js syntax checks. This is evidence for code paths, not a claim that we ran the full ONNX model on your machine.

---

# DeepThorT v10.2 — Local Model Loading and Focus-Stealing Fixes

This update preserves the existing 11-core JANUS/Sentinel runtimes, job queue, project data and offline Qwen2.5-Coder-1.5B model. It combines the v10.1 change that prevents `tasklist.exe` console flashes with the new **isolated ONNX loader worker thread**. The local HTTP server now responds to `/health` during the whole load, with the current model stage, elapsed time, time since a real model-loading event, and a four-minute no-progress warning. The desktop displays the real loading stage in Chats, Processes and its built-in self-diagnosis, instead of an unexplained loading indicator. When the ONNX worker exits with an error, the server exits with failure and shows the actual exception rather than silently hanging.

**Install:** Close DeepThorT completely, then extract this ZIP directly into `D:\deepthort`, replacing existing program files. Preserve the existing `state`, `models`, `node_modules` and `cache` folders. Open `D:\deepthort\DeepThorT.exe`. No model re-download is required. You can use **Diagnose AI** and the **Processes** tab to inspect real stage data; a model still loading after several minutes is not automatically presumed working. If the worker crashes, send the new diagnostic text or process log so the cause can be corrected.

**Verification:** 69 automated tests passed, including two real Node.js integration tests with a controlled mock model worker. The full 1.9 GB Qwen ONNX model was **not available** in the build environment. This update makes stalled initialization diagnosable and avoids the earlier console flashes, but it does **not guarantee faster inference** or prove the model starts on your particular Windows PC. The overall 20% CPU and committed-RAM supervision remains configured and a universal hard 20% disk-busy cap remains unsupported.

---

# DeepThorT v10.1 — Invisible Background-Process Fix

**Fix for repeated focus-stealing command prompt flashes.** The previous v10 game detector used `tasklist.exe` every few seconds to identify running games. In a GUI application, those spawned console processes could flash windows or take keyboard focus. v10.1 now uses native Windows Toolhelp32 process enumeration, which creates no new process/window. The resource-capped Python GUI process is also launched with `CREATE_NO_WINDOW`, and JANUS cancellation helpers hide any `taskkill.exe` process. Sentinel and JANUS remain enabled; their persistent state is unchanged.

Install: close DeepThorT; unzip this package directly into `D:\deepthort`, replacing program files. **Do not delete** your existing `state`, `models`, or `node_modules` directories. Launch `DeepThorT.exe` as usual. This update does not require a model re-download.

This patch was regression-tested in the build environment but has **not** been validated on your physical Windows desktop. If another process still steals focus, identify its executable name in Task Manager/Process Explorer and check the `Processes` tab for repeated restarts.

---

# DeepThorT Desktop v10 — dual recursive JANUS/Sentinel societies

DeepThorT v10 is a **native-window desktop coding workspace** with a Windows GUI-subsystem `DeepThorT.exe` entry point. You do **not** need to type Python or PowerShell commands for normal use. It runs a locally installed Qwen2.5-Coder-1.5B-Instruct model with ONNX Runtime via Transformers.js, **not Meta Llama, llama.cpp or Ollama**. It makes no cloud-model inference calls and has no fallback model.

**Important distinction:** The GUI, job queue, project-file generation workflow, approval gates, computer inspection and real command/test verification have automated tests. Local Qwen/Florence/Diffusers inference performance and actual Windows launch have **not** been verified on your physical PC. A 1.5B model running on an old CPU under a 20% cap does not have ChatGPT/OpenCode-level reasoning or high-quality image-generation capacity; the app is a bounded project assistant, not an independently validated autonomous game factory.

## Installing over your existing setup (D:\\deepthort)

1. Close earlier DeepThorT or standalone server windows.
2. Download the **v10 Windows ZIP**. Extract **the entire ZIP directly into `D:\\deepthort`**, replacing program files if Windows asks. `DeepThorT.exe`, `desktop_app.py`, `install.ps1` and the `deepthort_local` folder must all sit together directly under `D:\\deepthort`, *not* a nested `DeepThorT_Desktop_v7` folder.
3. Keep your existing `models`, `node_modules` and `state` directories. This update's ZIP does not include or overwrite them, so your model download and conversations remain.
4. Double-click `D:\\deepthort\\DeepThorT.exe`. It opens an ordinary Windows desktop window without a command shell. The launcher uses the Python/Node.js already installed on your PC; it is not a self-contained runtime installer.
5. In the window, click **Install AI** if your local Qwen ONNX model is missing, then **Start AI**. Model installation involves an explicit approval and an initial download; inference afterwards is offline. Your current model cache can be reused.
6. An installed local model now starts automatically on launch; while it loads, messages can be queued. Click **Diagnose AI** in Chats or **Self-diagnose** in the title bar for an offline setup report if it does not become ready. In Chat, **Send message** submits your message and displays it immediately; replies appear when the model completes. Typed requests such as "Please diagnose DeepThorT" are answered from local system checks even if the AI cannot start. Click **Choose folder…** to select or create a local project workspace. **Chats** has a large scrollable input; use **Queue request**, **Plan project**, **Build project (staged)** or **Propose file edit**. `Ctrl+Enter` queues the prompt.
7. Use **Work queue** for queued/running/paused/failed work, staged build plans, cancellations and approval. Use **File review** to approve each proposed edit (backups are written). For a staged build, approve the plan, approve generated files as required, then explicitly approve **Verify build** to execute a locally detected real test/build command. Only a successful check may mark a build completed.
8. Use **Processes** to see actual supervised process IDs, sampled CPU/memory and live event logs. **Computer & Tools** scans CPU/GPU/RAM/drives/free storage and known development tools. Review any proposed tool installation; no program installs without approval.
9. Use **Files & Images** to attach documents/photos, analyze an image with an optionally installed local Florence ONNX vision model, and request images with an optionally installed local Stable Diffusion 1.5 CPU engine. The image capabilities require **separate optional model downloads**, explicit approvals, and substantial CPU/RAM/disk space; they are **not** supplied in the ZIP. Image creation under a 20% CPU ceiling may take an impractically long time, and results are not guaranteed to be high quality.

## Working components and constraints

- **Separate persistent chats** stored locally in SQLite, with names, history, large prompt editor and explicit full-prompt storage. The input editor can store long project briefs, but **the tiny model accepts a limited per-call context (~7,500 characters)**: the app does not pretend it can reason over a 250,000-character prompt in one request.
- **Durable jobs/steps** and explicit queue states. Crash-interrupted work is recovered as paused, not falsely marked finished. Pause/cancel controls terminate the supervised local model/tool process where applicable; partial tool writes cannot always be rolled back automatically.
- **Project planning**, strictly scoped local file writes and backup-before-edit. A staged multi-file build is verified by real local build/test commands when available; model-generated claims are not accepted as proof.
- **Local computer discovery** for common tools and drives. Install suggestions are drawn from a fixed reviewed catalogue and require confirmation. Scanning does not mean that every installed program is supported for automated use.
- **Document ingestion:** plain text/JSON/Markdown/code and DOCX; optional PDF reader installation from the GUI. Image reading uses separate Florence-2 ONNX weights; Qwen alone **cannot see pixels**. Image generation requires local diffusion weights; Qwen **orchestrates** the engine, rather than producing pixels itself.
- **Offline inference** after approved initial downloads. No external AI API and no fallback provider. External package/model installers, when approved, use the internet.

## Gaming-first resource rules and limitations

- The `DeepThorT.exe` GUI launcher installs a **Windows Job Object 20% aggregate CPU hard cap** on DeepThorT and the child processes it directly supervises. It uses idle process priority and fails closed if the cap cannot be established.
- The Windows Job Object also limits combined **committed memory** to 20% of installed physical RAM, with a launch-time free-RAM headroom check. This is **not** an absolute physical working-set measurement or all-cache/RAM ceiling; memory-mapped weights and OS file cache can behave differently.
- CPU inference does not use the RX 480 GPU by default, so the graphics card is left available for games.
- **No universal hard cap of 20% disk active time is implemented or guaranteed on Windows 10.** The game detector and cooperative disk gate defer bulk/project operations when configured game processes are found, but model paging, external installers, OS caching, and other I/O can still interfere with games. Do downloads/installations with games closed.
- Running installed programs and build commands may execute untrusted code: use projects you trust. The app asks before installing software, writing to project files and running verification commands.
- Resource limits and game responsiveness **need real Windows testing** on your system before trusting them for unattended operation.

## Troubleshooting

- If the window will not open, check `D:\\deepthort\\state\\launch-error.txt` for the launch exception, and make sure `DeepThorT.exe`, `desktop_launcher.py`, `desktop_app.py` and `deepthort_local` share the same parent folder. The GUI launcher will attempt a Windows error dialog rather than leaving a command shell.
- If you see “AI not installed”, use **Install AI** and wait for its output in **Processes**. If the runtime is already running independently at `127.0.0.1:8765`, close it: DeepThorT refuses to attach to a server outside its supervised resource budget.
- Use the **Processes** tab to inspect actual errors rather than retrying downloads blindly.
- Existing `state` is valuable history. Back it up before reinstallations, and do not delete it to troubleshoot.

## Test evidence

Under a Linux virtual-display harness, the Tk GUI rendered and the **27-source-test suite passed**, including a staged plan→approved file writes→real test execution→verified completion path using a **stubbed model response**. Python compile checks and Node JavaScript syntax checks passed; the `DeepThorT.exe` PE header identifies a Windows x64 GUI-subsystem executable. These checks **do not establish** physical Windows compatibility, ONNX model quality, image diffusion quality, or completion of a real autonomous game-building task.

## v8 — Chat and startup repair (21 November 2026)

**What the user observed:** A message appeared as a queue item and received no reply because the model had never been started. The Processes tab accurately showed `Model server PID: not running`. The queue is a storage mechanism, not a substitute for inference.

**Changes:**
- Automatically attempt to launch an already-installed, fully local Qwen ONNX model on GUI startup and when a message is sent. No downloads or remote inference without approval.
- Display the user's submitted message in Chats immediately; show the actual answer after local inference. Pending prompts remain persisted in the job queue.
- Label the send control **Send message** instead of **Queue request**. A connection-status banner shows whether the model is loading, ready, missing or failed.
- **Self-diagnose** top-bar control and **Diagnose AI** chat control work without a running neural model. They inspect Node, ONNX dependencies, the model-file size and the server program.
- An explicit typed request such as **Please diagnose DeepThorT** produces a persistent deterministic diagnostic, clearly labelled **not a generated AI response**.
- A failed model process shows its actual recent output in an error dialog and in Processes, rather than stopping without explanation.
- After successful approved AI installation, DeepThorT attempts to start the model and process queued work. Removed a duplicate installation-completed event.

**Upgrade existing installation:** Close DeepThorT. Extract the entire **v8** ZIP directly into `D:\deepthort`, overwriting application files. **Do not delete `state`, `models`, or `node_modules`**; the update ZIP deliberately excludes all three so existing conversation histories, weights and dependencies are retained. Double-click `D:\deepthort\DeepThorT.exe`. The executable is a GUI launcher and does not open a command shell. If the AI fails to start, click **Self-diagnose**, and inspect the Processes log.

**Verification boundary:** 35 automated tests passed under a headless GUI harness, including the real chat queue/UI pipeline with a **stubbed** model response, and deterministic offline diagnosis. The actual Qwen ONNX weights, loading performance and Windows CPU/RAM enforcement are not proven on the user's PC. Image generation remains optional and independently unverified.

## v8.1 — Model loading visibility

The model server now reports a startup notice, real loader events when available, and a best-effort 30-second heartbeat; its readiness message reports initialization elapsed time. The desktop shows elapsed load time instead of an indefinite `AI: loading…` label, and prompts a Processes-tab inspection after three minutes without declaring the model ready. The chat queue remains persisted; no CPU/RAM limits are relaxed and no remote inference is added.

If startup takes an unusually long time, open **Processes**, check that **Qwen inference** has a process ID and inspect the process log for `[AI LOAD FAILED]` or an exit code. **Stop AI** if it is clearly stalled. Replacing the model or allowing higher CPU use requires a separate decision.


## v9 — JANUS coordinator + independent Sentinel watchdog

This update introduces a **simplified original JANUS-style eleven-role coordinator**, not an import of the existing full JANUS system. Every ten-second cycle observes actual queued/running/failed tasks and approved subprocesses, reads the **previous Front state** and recent observations, then persists the next seven specialist projections, two hemispheres, Front and Interface to `state/janus.sqlite3`. It can work while the ONNX language model is offline and does not call the cloud or invent progress. It provides deterministic supervisory continuity, **not equivalent neural reasoning or validated autonomy**.

`JANUS & Sentinel` is the eighth workspace tab. It displays real JANUS cycles, Front focus, approved subprocess ledger, watchdog PID/health/restarts, and durable logs. **Pause JANUS** and **Resume JANUS** control dispatching of new approved work; **Cancel selected approved process** requests cancellation from the actual worker. Under `Computer & Tools`, explicit approval of a project check now queues a command for the JANUS worker, which records process ID, output log and exit status. Only approved known command vectors are accepted. User confirmation is still required for installs, file writes and verification commands.

`janus_sentinel.py` is a **separate local process**, supervised with JANUS and model inside the same Windows Job Object (20% aggregate CPU and 20% installed-RAM-sized committed-memory limit). It monitors the worker and desktop heartbeat. After a genuine JANUS worker exit, it retries with a maximum of three launches per ten-minute window, unless an interrupted approved action is detected—then it blocks automatic restart and asks for review. A live-but-stalled worker is never killed automatically, because it may be executing a real tool. If the desktop heartbeat goes stale, Sentinel pauses JANUS instead of continuing unattended work; resumption requires user action. It can warn when the ONNX model has spent more than four minutes loading, but **does not kill/reload a slow model automatically**.

**Not a duplicate commander.** Sentinel is a read-only observer of work with bounded failure recovery, not an independent JANUS personality or a second process authorized to modify project files. Two competing autonomous executors would risk repeated tasks and inconsistent state.

**Important limitations:** If the entire GUI or its Windows Job Object is terminated, this in-job watchdog does **not** keep running or restart the application. On restart, all in-progress JANUS approved processes are marked `needs_attention`, with no automatic retry. The model still needs to load; Qwen inference speed on the user's Windows machine is unverified, and this edition does not turn the small model into a ChatGPT/OpenCode-equivalent system. A universally enforced maximum of 20% disk busy-time is also **not supported by this package**. Windows 10 behavior still needs an on-device launch/response test before unattended operation can be considered reliable.

**Verification:** 49 tests passed under a Linux virtual-display harness, including UI tab creation, explicit approval, deterministic eleven-role cycles, persistent state, actual subprocess execution and exit-code capture, watchdog crash-restart limit, stale worker non-destructive alert, stale GUI heartbeat safety pause, and no replay of interrupted tools. The executable is still a Windows GUI-subsystem launcher and starts the packaged Python desktop application. No Node/Qwen weights or physical PC were available in the test container.

**Upgrade:** Close DeepThorT; extract v9 ZIP directly into `D:\deepthort` and replace application files. The ZIP intentionally excludes `state`, `models`, and `node_modules`; do not delete those folders. Open `DeepThorT.exe`, then `JANUS & Sentinel`. The application does not require command-shell interaction for normal use.

## v10 — Two persistent eleven-core recursive societies (21 November 2026)

**Core engine, not just eleven GUI labels.** DeepThorT now runs a dedicated JANUS
worker with 11 top-level cores in the owner's canonical order, each executing a
seven-faculty Fano processor. Every core retains state/weights, active faculty,
quiescence, peer revisions, bounded intuition and externalizable appraisal. The
seven specialist cores reconsider peer outputs; both hemispheres integrate all
seven specialist streams; Front receives the hemispheres; Interface receives
only Front. Prior Front and observations are recalled in the next sensory cycle,
never fed backwards from Interface as a direct new thought.

**Sentinel is also a full separate eleven-core society** with 77 internal
faculties, separate persisted cognition, and a supervisory goal. It monitors
JANUS cycles and worker health, actual queue states, project-task drift, stale
running work, model load health and approved-process outcomes. It keeps its own
observations, Front and revisions; it never masquerades as JANUS or gains its
file/tool execution privileges. On genuine worker crashes it uses bounded
restart policy; active unverified tool commands block automatic replay.

JANUS persists its own primary goal and generates alternatives when real jobs
fail. Both societies may occasionally consult the **same local Qwen ONNX model**
for suggestions when it is loaded, not during games. Advisory requests share a
lease to prevent concurrent background generation. Suggestions are saved in
SQLite, clearly marked as unverified, and **never execute themselves**.
Approval of installations, code writes and commands remains with the user.

In **JANUS & Sentinel**, use **Set primary goal…** to retain the specification
across restarts. Click **Inspect 22 core states** to see the actual two-society
readouts and each internal Fano processor. Evidence-based repair suggestions and
watchdog warnings appear in the same tab and in the bottom status area.

Cognitive state is stored in existing `state/janus.sqlite3` and
`state/sentinel.sqlite3` (additive migrations preserve v9 records). Local
advisory locking uses `state/janus-counsel.sqlite3`. Do **not** delete `state`
when upgrading. Work and model processes inherit the same capped Windows job.
Games slow the JANUS worker polling, defer tool execution and suppress new
background model advice. Actual 20% CPU/committed-memory Windows enforcement
still needs confirmation on the owner's machine; a universal hard 20% disk
busy-time cap is not implemented.

**Boundary:** This is a standalone *offline port of the JANUS 1|3|7 recursive
processing architecture*, adapted from `Vardath/JANUS-privatebuild`'s
`server_v2/topology.py`, `senses.py`, `recursive_core.py`, and `intuition.py`.
It is NOT a copy of the full original JANUS server/account/global federation,
nor proof of human-like conscious thought. The small Qwen model is not proven
capable of large unattended projects. If the desktop closes or Windows kills
its resource-constrained job, execution stops; only durable state survives.
A separate true background Windows service, robust model-loading on the user's
hardware, production-grade autonomous replanning, and independently verified
whole-project completion remain to be developed.

**Verification:** 60 Python regression tests passed in an X virtual desktop,
including 11x7 processing, Fano lines, storage persistence, goal retention,
peer routing, two independent societies, approval-only tool execution,
failure remediation proposals, restart limits, task-drift detection and
prolonged-work warnings. The Windows x64 GUI executable format is validated,
but physical-machine ONNX model inference and end-to-end autonomous coding
have not been verified.
