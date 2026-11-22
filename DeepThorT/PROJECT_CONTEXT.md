## v28 — Acceptance contracts and approved test evidence (22 November 2026)

**Current packaged release: DeepThorT v28.** Based strictly on the packaged v27 source. GitHub now includes both v27's previously uncommitted files and the v28 changes. The Windows launcher, GUI arrangement, offline ONNX model, JANUS/Sentinel topology, 40-pass planning limit, user-approval controls and existing state layout are preserved.

Implemented source: `deepthort_local/acceptance_contracts.py` supports model-declared `provides: Symbol`, `uses: path.py::Symbol`, and `verifies: REQ-N` intentions. These must refer to actually proposed files and exact user-written requirement labels. Static AST inspection checks source that exists without importing/running it; missing planned files are pending, not verified. The hierarchical roadmap and milestone approval dialog report contract state; concrete missing exports/imports or empty declared test source block verification until repaired and a fresh test is approved. User ambiguity flags are advisory only.

`deepthort_local/verification_evidence.py` now analyzes bounded actual output from an **already user-approved** verification process. `unittest discover` / `dotnet test` success with zero evidenced passing tests fails the verification gate; Godot editor loading is labelled editor-load only, not gameplay. Successful process checks attach separate assurance metadata and command/output hashes to v27's source-file snapshots. Legacy snapshots remain readable without retroactive test-level claims. A later source edit invalidates verification.

**Tests:** 329 tests passed over 43 isolated Python test modules under Xvfb, including 18 v28 tests. The monolithic run had one repeat of the pre-existing asynchronous X4 GUI test race; do not call that run fully green. The v28 ZIP contains 104 files and passed its CRC/integrity check. All 14 changed/new v27+v28 source, test and documentation files were verified against the GitHub version. Live Windows inference, X4 gameplay and Android/Godot game execution are unverified.

**Next architecture:** Turn explicit accepted requirements into engine-specific executable acceptance harnesses (Godot/GDScript, Android builds, X4 XML and MD fixtures), record actual artifact- and behavior-level evidence, and evaluate model-produced code rather than source declarations alone. Do not change user specifications or invent any default Xenon PE plan. Continue from v28, maintaining per-milestone approval and verified progress.

---

## v25 — Hierarchical development foundation (22 November 2026)

**Current packaged release: DeepThorT v25.** Built from the verified v24 Windows ZIP with the executable, desktop launcher, model, JANUS/Sentinel, approval controls, resource restrictions and original UI preserved. New source: `deepthort_local/hierarchical_planning.py`; tests: `test_hierarchical_planning_v25.py`, `test_hierarchical_gui_v25.py`; reference: `HIERARCHICAL_DEVELOPMENT.md`.

v24 reviewed large specifications in exact sections but failed after merging more than 24 model-proposed file stages. v25 closes that post-review blocker: once all source sections are model-reviewed, a durable roadmap groups **only model-authored** file proposals into independent milestones (default <=12 files, max 24 per job), with source section SHA-256 traceability. The aggregate plan is validated before staging. Conflicting paths, missing trace links, changed source or model proposals, and overly large exact source scopes block approval. Roadmaps persist separately in `state/hierarchical_plans.sqlite3`. No roadmap creation queues work.

The **existing** `Approve plan & queue` control now explicitly confirms only the next milestone in the same chat/project. Each generated file retains individual review; later milestones remain locked until the prior approved build job has recorded both saved file stages and a successful, explicitly approved verification run. Restart/idempotency checks reject wrong job identities and repeated approvals. Each model request receives unmodified, numbered source-section excerpts within the inference limit; the full original remains preserved in the existing specification database. Sequential dependencies are conservative verification gates, not learned software architecture. Very large shared-file scopes remain blocked for model reconciliation; this release is not evidence of game correctness.

A Faction Command / Android game citing X4 as inspiration is no longer misclassified as an X4 extension requiring extracted source assets; actual X4 mods remain subject to existing source verification.

**Validation:** 263 local Python tests passed under Xvfb (including 28 new hierarchical/desktop integration tests); the 92-file v25 ZIP passed CRC check; the Windows executable and desktop launcher are byte-for-byte unchanged from v24. GitHub CI and actual Windows ONNX inference, Android building and X4 gameplay have not yet been verified. No test result can be promoted into a claim of a working game.

**Next priorities:** Pass 5 benchmarks and semantic requirement IDs, model-authored dependency/API interfaces, safe reuse of earlier verified code and real-engine acceptance tests. Preserve the original specification and explicit approval boundaries.

---

## v24 update — 22 November 2026: million-word input, Pass 3 approved evidence

**Packaged v24:** DeepThorT_Desktop_v24_Windows.zip; 88 files; SHA-256 `41c895f6893dab747b22998db22921b98916e41a0e7d413c1d9e43669303250b`. Built from v23 with the exact original Windows launcher (byte-for-byte unchanged). All 235 local Linux virtual-display tests passed; Tkinter/SQLite cleanup warnings remain. Live Windows model, X4 gameplay and game-engine builds are not yet validated.

**Large input architecture:** `ConversationStore` and `JobStore` accept prompts up to 120,000,000 characters instead of 250,000. `deepthort_local/specification_library.py` stores a hash-checked, lossless section index in `state/specification_index.sqlite3`, with original text still stored in `state/conversations.sqlite3`. Exact numbered sections are passed individually to the 7,500-character model prompt; completed valid model-origin file proposals are tracked per section and resumed on retry/restart. This DOES NOT enlarge Qwen's inference context, prove semantic coverage, or allow approval of incomplete section reviews. Review batches remain capped at 40 model calls and the current single execution plan at 24 source-file stages. Huge game plans will need hierarchical milestone planning (Pass 4). Changed source hashes cannot reuse prior progress; malformed model proposals do not count as reviewed.

**Import and rendering:** `deepthort_local/large_input.py` imports user-selected UTF-8 TXT/MD/RST/JSON/YAML into the conversation (right-click editor or Ctrl+Shift+O), verifying SHA-256 again before submission; additional instructions from the editor are appended with an explicit marker. Huge texts render in Chats as labelled previews, but full text remains in SQLite. Existing interface dimensions/layout are preserved. No scripts/attachments are silently executed.

**Verified-procedure evidence:** `deepthort_local/tool_evidence.py` reads already user-approved JANUS verification records read-only, tracking exit results and SHA-256 fingerprints of logs. It does not run tests or automatically promote procedures. `CapabilityLibrary.verify_workflow` may explicitly associate a current checked artifact and an approved, successful test action from the same project (strict known GUI test profiles only; unrelated commands rejected). Evidence is invalidated if the artifact, action status or log changes. Evidence scope is artifact + test exit code, NOT game correctness or end-to-end completion. CLI `verify-workflow` exists for explicit linking. Data remains local.

**GitHub:** v24's 12 modified/added source, tests and docs files committed to existing `DeepThorT/` folder and fetched back byte-equal to packaged sources. No manual design changes or JANUS/Sentinel/model rewrites. CI status should be checked separately.

**Next pass:** Pass 4 hierarchical project planning, milestone-specific requirements traceability, cross-section proposal conflict reconciliation, scope-aware retrieval for huge specifications, and staged approval/build beyond 24 files. Performance benchmarks on Windows should measure actual tokens/sec, section review cost, and success against Xenon PE and eventually Faction Command; do not infer speed improvements from unit tests.

---

## v23 update — 22 November 2026: Capability Library Pass 2 local reference learning

**Current packaged release: v23.** Built from the exact v22 ZIP, with seven changes/additions only: `deepthort_local/reference_learning.py` (new), `tests/test_reference_learning_v23.py` (new), `deepthort_local/capability_library.py`, `desktop_app.py`, `README.md`, `START HERE.txt`, and `CAPABILITY_LIBRARY.md`. The untouched Windows executable and all other package entries match v22. Full local Xvfb regression: **212 tests passed** (197 prior, 15 new), with the preexisting Tk/SQLite teardown warnings. Windows ONNX inference, actual game builds, self-directed discovery of online references, and autonomous workflow verification are **NOT proven**.

**Implemented:** The selected workspace's bounded existing scan (200 eligible paths) now indexes up to 20 local documentation/example text files, maximum 48 KB each, with hash and source provenance in the existing `state/capabilities.sqlite3`. No document body is persisted. Retrieval reopens/re-hashes sources and returns limited relevant lines, attributed by path, line number, hash prefix, and optional user-provided version label (explicitly UNVERIFIED). Credential-like and clear instruction-override lines are omitted; all excerpts are untrusted source data. It reads sources only and does not execute tools, alter project files, or approve unverified procedures. CLI: `python -m deepthort_local.capability_library --db state\capabilities.sqlite3 inspect <project>`, `references <project>`, `reference-context <project> "<request>"`, `index-reference <project> <relative-file> --version <label>`.

**Planning:** Draft planning may include small hash-verified relevant excerpts in the first model input when the 7,500-character budget permits; it never truncates original requirements or verified X4 preflight evidence. Later revision passes do not yet independently retrieve new excerpts. This is **Pass 2**, not autonomous tool mastery. Original JANUS/Sentinel, 40-pass limit, UI, approvals and offline ONNX inference are unchanged.

**Next priority: Pass 3** — integrate only explicitly approved/supervised build/test tools with actual exit statuses, tool versions and artifact hashes, then promote scoped procedures only when tests genuinely pass. After that: Pass 4 dependency-aware hierarchical planning for games; Pass 5 on-PC performance and acceptance benchmarks. Do not claim a working X4 mod or Android game without actual verification.

---

## v22 update — 22 November 2026: Capability Library foundation (first of several passes)

**Current packaged release: v22.** New read-only `deepthort_local/capability_library.py`, `CAPABILITY_LIBRARY.md`, test module and a small draft-plan handler integration in the existing `desktop_app.py`. All six changed/added files were verified by Git blob SHA against `DeepThorT_Desktop_v22_Windows.zip`; the original Windows launcher is unchanged. 197 local tests passed using Xvfb. Live Windows inference, GitHub CI, game-engine builds and full autonomous learning have not been demonstrated.

**Implemented:** Selected-project manifest/configuration observations, SHA-256 source fingerprints, bounded scanning, installed tool presence (no execution), local `state/capabilities.sqlite3` persistence, stale evidence exclusion, bounded model context injection if it fits behind all original user requirements and X4 evidence, unverified procedure candidates, and deterministic file-artifact XML/JSON/existence checks explicitly labelled as artifact checks rather than verified workflows. No downloaded documentation, commands, automatic project edits, pretrained model changes, interface redesign or automatic game build features have been added.

**Planned next passes:** (1) securely ingest and retrieve bounded relevant project/installed-tool documentation, with provenance and source instructions quarantined as untrusted data; (2) integrate authorized actual build/test execution, versioned test receipts and verified workflow promotion with the existing job/approval system; (3) hierarchical project/subsystem planning with safe dependency resolution and repeatable Faction Command acceptance benchmarking. These stages are *not yet implemented*. Do not claim that v22 autonomously learns all new software or builds games. Do not alter JANUS/Sentinel or release numbering to implement these.

See `CAPABILITY_LIBRARY.md` and `tests/test_capability_library_v22.py`. **Do not overwrite local `state`, `models`, `node_modules`, `reference`, `cache` or projects during installation.**

---

## v16 update — 21 November 2026 (17:22 diagnostics)

**Current packaged release: v16.** Built strictly from the v15 Windows ZIP, preserving UI geometry, launcher, installed ONNX model, JANUS, Sentinel, existing approval gates and saved state.

The new diagnostics show conversation #15 began X4 model planning at 16:05 local time. Six calls completed in roughly 8–10 minutes each. Its seventh request began 17:00:26 local time, then `LocalModelClient` raised `TimeoutError` at exactly 900 seconds (17:15:26), while the ONNX worker returned its answer at 17:15:41 — 15 seconds after the HTTP client disconnected. A manual retry at 17:21 dispatched conversation #15 again, but v15's in-memory planner did not reuse the six completed passes. No approved X4 jobs or finished mod were present.

v16 fixes exactly this class of failure: `deepthort_local/client.py` increases its local inference socket timeout from 900 to 3600 seconds and exposes `completed_exchange(session,prompt)` for a matching, fully saved local model answer in the existing `state/sessions.sqlite3`. `deepthort_local/agent_plan.py` replays only exact prior completed pass inputs on a retry/restart, rebuilding its accumulated model-authored plan; any new/changed source evidence or user prompt forces fresh inference. A pass that timed out before its answer was saved must still be regenerated. This does not guarantee successful planning, prevent all future timeouts or create a prewritten fallback.

Source diff from v15 is restricted to `deepthort_local/client.py`, `deepthort_local/agent_plan.py`, `tests/test_inference_recovery_v16.py`, `README.md`, and `START HERE.txt`. The Windows launcher and all other files are unchanged. Five targeted tests passed; 158 tests passed in the successful full Xvfb suite. One earlier full-suite run was affected by a pre-existing GUI temporary-folder cleanup race. Archive CRC and byte-for-byte GitHub source hashes were verified. **Live Windows ONNX inference, generated Xenon PE XML, X4 gameplay and GitHub Actions green status are not established by these tests.**

On Windows, close the application, extract v16 over `D:\deepthort` without deleting `state`, `models`, `reference`, `cache`, `node_modules` or project folders; restart and use **Retry failed reply** on the original Xenon PE request. If identical saved source references/prompt are present, the first six completed model passes should be replayed without another expensive inference; the unrecorded seventh must be generated again.

Do not weaken the model-authored plan validator, 40-pass allowance or explicit approval. Preserve sequential version naming: next genuine repair release is v17.

---

## v15 update — 21 November 2026 (15:57 diagnostic)
The user explicitly required **at least 40 independent local-model attempts** for generating/revising an X4 plan, **stopping immediately when validation succeeds**. Screenshot 467 and `DeepThorT-Diagnostics-20261121-155708.zip` confirm v14 made four complete, unsuccessful ONNX inference calls in approximately 41 minutes and then stopped at the hard-coded desktop limit. The parser also rejected max_rounds >8. v15 sets the planner and desktop to 40, does not prematurely abort upon an identical invalid reply, and avoids poisoning the retained plan with an oversized (more than 24 file) candidate. The initial user specification and explicit approval boundary remain unchanged. No canned plan was inserted. Five new tests pass; total local headless tests **153, OK**. This verifies control flow only, not the model's ability to invent a technically sound plan or produce a working mod. Existing v14 GUI design and JANUS/Sentinel code are untouched. A 40-pass run may take several hours on the user's CPU; persistence across UI exit is not established. GitHub CI remains unverified until an actual check conclusion is inspected.

# DeepThorT — verified project context and continuity handover

## v20 — JANUS Interface and planning changes (22 November 2026)

- Source baseline: v19. The desktop geometry, ONNX implementation, JANUS/Sentinel core processors, 20% gaming CPU design, 40-pass bound and explicit work-approval gates remain unchanged.
- Address an ordinary chat message explicitly to JANUS or @JANUS to obtain a read-only report from current JANUS Front/Interface, Sentinel, queue and ONNX status even when Qwen is busy. This is a deterministic factual Interface, **not general-purpose free-form language generation or permission to execute work**; unaddressed chat is still handled by Qwen.
- Model-authored plan revisions now show purposes of selected existing proposed files, hold a specific unmet criterion briefly before rotating, and reject rewrites of existing steps that would lose previously satisfied validator criteria.
- Full original user specifications remain included in every planning inference. Regular plan-generation token budget is 384 instead of 640, with a bounded longer retry for certain invalid JSON. Any speedup on Windows must be measured; none has been confirmed.
- Eight new tests, 181 total local tests passed under Linux X virtual display. The launcher is identical to v19. Real Windows operation, a successful Xenon PE mod, and GitHub CI remain unverified at release packaging. A prior v19 diagnostic showed 35/40 model passes and nine remaining X4 planning gaps.
- Local artifact: DeepThorT_Desktop_v20_Windows.zip. Install only while the old desktop process is closed; preserve state, models, references and user projects.

Last reviewed: 21 November 2026 (Australia/Brisbane). Updated for v14.

## Read before editing
DeepThorT is the user's **local Windows autonomous project developer**, descended from the JANUS/Mindcore work. It is NOT merely an X4 mod generator, and the standalone **Vardath Scratch Chat** language-model project is separate. The Xenon PE assignment is a small but technically demanding acceptance test before the larger *Faction Command* Android game.

**Do not rebuild, rename, redesign, or alter working code based on a summary.** Read the original v10.9 source, the current v14 files, the diagnostic export, and the specific screenshot/log before any changes. Audit the actual call paths, UI geometry and tests. Historical assistant assertions are not proof.

Original JANUS reference (read-only): `D:\vardath work`. Mindcore predecessor: `D:\mindcore`. Current DeepThorT installation: `D:\deepthort`. X4 test project: `D:\x4mods`. GitHub source: `Vardath/Vardath.github.io/DeepThorT`. Preserve these boundaries; do not modify original JANUS to repair DeepThorT.

## Non-negotiable product requirements
- **Offline/local runtime** without Render, cloud inference, Ollama or llama.cpp; current local inference uses Qwen2.5-Coder-1.5B-Instruct ONNX through Transformers.js. No invented cloud fallback. The experimental Vardath Scratch Chat model remains a separate project.
- **JANUS and Sentinel**: preserve the existing 11-core, seven-faculty structures, persistent reasoning/monitoring and any functionality proven in source. Do not claim the historical full JANUS architecture or continuous intelligence is verified merely because modules exist.
- **Gaming first**: the configured CPU and committed-memory budgets are 20% each. The user also requires low disk impact, but a strict disk 20% limit is *not verified*. Do not weaken or silently advertise resource guarantees.
- **Chat is not a job**. Allow free conversation and multiple chat tabs/workspaces; draft a project plan on request; a plan goes into the executable work queue **only after explicit approval**. Any tools, installations and source extraction requiring permission must keep their approval gates.
- Durable user state, saved chat/specification, retry, model/worker status, work queues, process logs, watchdog, restart recovery and genuine execution/test evidence. These are product goals; verify each independently rather than claiming they all work end to end.
- Original v10.9 interface layout is the design baseline: left project/file pane, existing Chats/Work queue/File review/Tasks/Processes/JANUS & Sentinel/Computer & Tools/Files & Images tabs, and existing status/controls. Waiting/generating/validating/failed must be visible **without adding a banner that clips buttons**.
- Do not omit user requirements, invent file or game identifiers, quietly turn requests into generic Python apps, or mark work complete before validation. No new features or redesign when repairing log/screenshot defects.
- Release naming is sequential **v11, v12, v13**, etc. (not v11.0 or v10.9.1). Preserve `state`, `models`, `node_modules`, `cache`, `reference`, and user workspaces during installation.
- When the user supplies a screenshot/log, treat it as authorization for ordinary investigation and repair: inspect baseline, trace failure, make the smallest correct change, run regression tests, verify release and CI separately, supply result. Do not stop at diagnosis or repeatedly request approval for routine repairs.

## How the earlier work developed
The separate `mindcore setup.md` document records the JANUS/Mindcore objective and historical pre-DeepThorT conversation, including preservation of original JANUS, local persistence, truthful dashboard, model routing, code/test tools and Faction Command acceptance test. These requirements were refined in the November 20–21 `SoundCloud Top Tracks` conversation. The full earlier conversation is not reproduced here. Original v10.9 `README.md` carries release notes for v10 through v10.9.

- **v10:** Native desktop workspace with 11-core JANUS/Sentinel runtime, local ONNX model, queues and diagnostics. These structures were delivered; autonomous full-project completion was not proven.
- **v10.1–v10.3:** Fixed focus-stealing console processes, separated ONNX loading to keep health responsive, added persistent/automatic diagnostics and queue-dispatch repairs.
- **v10.4:** Fixed critical distinction between chat and approved execution jobs. Conversation, plan draft and approval are separate.
- **v10.5:** Chronological chat timeline and model inference status; a long local response may reflect CPU-limited generation rather than a dead queue.
- **v10.6:** Rejected generic `src/main.py` X4 plans and added game-specific plan guards.
- **v10.7–v10.8:** Found the actual game and XML extraction tools; inspection became part of the original request, with explicit permission required for extraction. Actual local extraction and source verification later succeeded.
- **v10.9:** Repaired combined X4 inference input exceeding the 7,500-character limit (7,566 characters). Preserve the full user specification and verified reference identifiers.
- **v11:** Rebuilt from the original v10.9, not the discarded v11.0 path. Added reply-lifecycle status and source-verified Xenon PE draft recovery. An added reply-status banner unexpectedly pushed action buttons below the Windows window.
- **v12 (historical packaged build):** Removes the extra banner, displays reply activity in the original status line, and adjusts prompt-editor height to keep original buttons accessible. **No user Windows screenshot verifying v12 yet.** Do not confuse local GUI tests with user acceptance.

Local archive inventory inspected: original `DeepThorT_Desktop_v10_9_Windows.zip` (67 entries), v11 (68), v12 (69). v12 differs from v10.9 in eight paths: `README.md`, `START HERE.txt`, `desktop_app.py`, `deepthort_local/agent_plan.py`, `janus_worker.py`, `tests/test_reply_activity_v11.py`, `tests/test_layout_v12.py`, `tests/test_janus_recursive_societies.py`. The JANUS worker change (first counsel timing) is unrelated to the visible UI defect; audit it separately, do not assume it was needed.

## Real Xenon PE acceptance test, not a generic software demonstration
User requested a standalone, save-compatible X4 Foundations extension based on the installed vanilla Xenon PE M-class ship: **10× cargo**, **4× base speed**, improved acceleration/braking/handling, compatible best-performing high-rate forward weapons and turrets, **50,000 damage per successful weapon/turret hit** (not total DPS), correctly installed equipment, player ownership and **60-second replacement** whenever the player owns none (no duplicates), no new save and no accidental global weapon changes. Inspect installed vanilla PE/weapon/turret connection identifiers; produce actual `content.xml`, ship/equipment XML, Mission Director code, a complete installable extension ZIP, validation, instructions and explicit remaining in-game test limitations. First draft a technically valid plan; only execute after approval.

The 21 November diagnostic export `DeepThorT-Diagnostics-20261121-124052.zip` supports these observed facts: X4 was detected; source references extracted and verified; one combined inference prompt exceeded 7,500 characters; a later prompt fit (7,437 characters) and the local model generated approximately 1,544 characters over about ten minutes; its proposal was rejected for lacking necessary X4 extension files and requirements. There were **zero approved executable PE jobs** and **no completed mod**. A rejected plan is not a delivered mod.

## Verification status and cautions
- The original v10.9 suite passed **121 local tests**; v11 passed **130** and v12 **133 local automated tests** (v12 log records `Ran 133 tests` and `OK`). These tests ran in a Linux virtual display and are *not* verification of actual Windows layout, ONNX generation speed, autonomous mod coding, or X4 gameplay.
- Repository head when reviewed: `40faccc1bc3cc6561fafbc0a838165381e23f0b7` (v12 UI fix). GitHub API had no status checks to confirm v12 is green; historical DeepThorT workflow-failure notifications exist. **Never claim GitHub CI passed without examining the actual run and conclusion.**
- No demonstrated working Xenon PE mod or Faction Command APK. No demonstrated end-to-end days-long autonomy or uninterrupted worker after closing UI. No source-backed guarantee of free-model switching; v10's ONNX build explicitly described a single offline model with no fallback.
- `README.md` currently concatenates historical version notes, including an outdated v11 passage describing the extra banner. The top v12 note supersedes it. Do not treat historical changelog passages as current UI instructions.
- Installation is extraction into `D:\deepthort` **only after closing DeepThorT**; preserve all local state, models and project files. No one has remotely installed or game-tested v12 on the user's PC through this chat.

## Working discipline for the next repair
1. Reopen exact original/current source, screenshot and diagnostics; establish what the user is actually running.
2. Identify a specific, reproducible failing behavior and the smallest relevant code path.
3. Preserve user-visible geometry, existing feature set, code architecture and state. Do not add UI panels, invent fallback behavior or rename releases.
4. Run unit and GUI regression tests; separately verify on Windows when accessible, check real workflow and GitHub CI, and state every unverified limitation.
5. Keep this status document factual and up to date. Record what changed and what tests prove; preserve previous versions as rollback points.

This document is a continuity record **only**. It makes no changes to the application, and its statements must be checked against actual code and diagnostics before future implementation.


## v13 planning repair (21 November 2026)

**Historical packaged release: v13.** Built from v12 without changes to JANUS/Sentinel or the window geometry. Tested local ZIP: `DeepThorT_Desktop_v13_Windows.zip`. Exact source is committed to `Vardath/Vardath.github.io/DeepThorT`; latest repository code changes are v13.

The user explicitly rejected accepting the hardcoded Xenon PE fallback as evidence of independent planning. The v12 diagnostic export `DeepThorT-Diagnostics-20261121-140740.zip` confirmed that the eight-step plan was **substituted from source_grounded_pe_plan**, after the real local model output was rejected. The v13 code removes that fallback entirely.

v13 requires the local model to author every proposed source-file path and its description. The model can extend or correct its plan over up to four bounded inference calls. Structural/domain checks produce specific feedback; the full original specification and selected verified local X4 references are retained in revision calls. Old v11/v12 fallback drafts cannot be approved. If the model fails, the request fails truthfully and no substitute draft or execution job is created.

X4 planning validation now checks resource macro indexes, projectile/bullet definitions for the 50,000-per-hit PE test, component registration when creating new components, and obvious L/XL equipment mismatches with an M-class PE. X4 evidence candidate ordering now prefers M-class names rather than alphabetical L-class destroyer candidates; this ranking does not itself prove tag compatibility. For Android game planning, generic README-only plans are rejected in favor of native build configuration, gameplay code, user interface and test coverage. **These are validation requirements, NOT hardcoded file-stage plans.**

Verification: **144 local automated tests passed under Xvfb**, including the existing v12 UI layout checks. The ZIP integrity check passed. The nine changed GitHub files were compared by exact git blob hashes to the tested ZIP. **No actual Windows/Qwen inference or game-generated PE mod is proven; no live GitHub CI pass has been confirmed.** The original 1.5B local model may fail after bounded attempts. This release fixes misleading fallback behavior and planning orchestration; it does not prove autonomous development competence.

Next acceptance test: create a fresh X4 Xenon PE draft from the existing saved request, inspect the model-authored steps and confirm all model revision passes. Do not approve unless the plan is technically credible. Then execute after explicit approval, validate generated source, and finally verify in X4. Preserve the user specification, state and v10.9-based window layout. Next release naming is **v14**.


## v14 planning-context repair (21 November 2026)

**Current packaged release: v14.** Source base: v13 with the v10.9 layout, JANUS/Sentinel components, local offline ONNX model, resource budget, existing workflow and user state unchanged. ZIP: `DeepThorT_Desktop_v14_Windows.zip`.

The user's 15:07 diagnostic ZIP and screenshot show a **real v13 model planning attempt** (#13, original specification 3,839 characters) ran from 04:57 to 05:06 UTC and failed inside `build_revision_prompt` with `PlanError: Existing plan paths cannot fit alongside the complete original specification`. The model's earlier output was not saved as an approved draft. Zero executable X4 jobs were queued. The root cause was v13's attempt to include all model-proposed file paths and source evidence in every 7,500-character revision request; it aborted before another model correction.

v14 changes **only** the revision prompt budget in `deepthort_local/agent_plan.py` (plus README/install instructions and regression tests). It **always retains the full original specification**; prior proposed paths and descriptions remain in local accumulated state, subject to full validation. A bounded selection of complete paths is shown to the model and rotated on later passes, with an explicit omitted-count disclosure; verified source evidence is added only as space permits. No fallback plan is fabricated and approval remains explicit. Full specifications exceeding the limit still fail safely.

Tests: `xvfb-run -a python -m unittest discover -s tests -q` gave **148 passing tests** (144 previous plus 4 v14 regression tests). ZIP integrity passed; compared with v13, only `README.md`, `START HERE.txt`, `deepthort_local/agent_plan.py` changed and `tests/test_revision_context_v14.py` was added. Some Tkinter/SQLite ResourceWarnings persisted in the headless test output. **No Windows ONNX runtime/real model-plan acceptance, working Xenon PE mod or actual game validation has been demonstrated by v14.** Verify separately before claiming success. GitHub CI must also be checked independently.

The failure fixed here is in **context packing**, not in Qwen's ability to plan complicated software; the latter remains an open acceptance test. Do not substitute a hardcoded X4 blueprint or alter the UI to mask this.

## v17 targeted planning correction — 22 November 2026
The user supplied `Screenshot (468).png` and `DeepThorT-Diagnostics-20261122-075739.zip`. The export shows two sequential forty-pass planning requests: request 15 ran from roughly 16:05 on 21 November to 00:05 on 22 November (with interruption/retry), then request 16 ran from 00:05 to 06:14 on 22 November, Brisbane time. Both failed validation; neither yielded an approved Xenon PE plan. The approximately 14-hour interval covers both requests, not only the final forty passes. The Qwen ONNX worker remained alive and answered; there were no mod files or approved jobs. The export deliberately omits raw model-generated plan contents, so precise reply-format failures were not observable.

**v17** preserves the v16 GUI, JANUS/Sentinel, offline model, state, consent and 40-attempt policy. It changes only the iterative planning strategy: 1–2 model-authored file descriptions per request; rotate focus across actual unmet validator criteria; parse one complete JSON object even if surrounded by prose; preserve full original specification and model-authored accumulated paths; and record counts, reply sizes and rejection/focus categories (not private prompt text) into `state/logs/planner.jsonl`. The related GUI test fixture waits for its background planning thread before deletion. No canned X4 plan or automatic execution was introduced.

**Verification:** 163 Linux/Xvfb local tests pass and the v17 ZIP integrity and JavaScript syntax checks pass. These are scripted tests; a technically complete model-authored Xenon PE draft, Windows inference success, X4 installability and gameplay remain unverified. The complete 40-pass run has already exhausted its cached responses; test the new strategy by requesting a **new draft plan** after installing v17. Do not increase the number of passes or claim success without analyzing the next planning telemetry.



## v18 — chat close and inference stop (22 November 2026)

The user reported that pressing Retry in an old chat occupied the single-flight local ONNX worker so a newly opened chat could not proceed, and there was no way to close a chat tab or cancel its running conversation. v18 was built from v17 **without altering** the original layout, 40-attempt planning rules, JANUS/Sentinel architecture or approval gates.

The Chats toolbar now has **Close chat**, which archives the tab, stops its pending/running/waiting-source conversation requests and preserves durable transcript/drafts. Right-click the chat tabs to reopen archived chats. The existing lower action row now has **Stop reply**, which cancels only the selected chat's outstanding conversation requests, not approved jobs or other chats. A cancelled request remains cancelled across restarts, rather than becoming pending automatically.

If the cancelled request owns the currently running ONNX model, the desktop terminates its supervised Node/worker process and restarts a fresh supervised model **after confirmed process exit**; another queued chat can run after the model reloads. The source planner checks for cancellation between passes and late HTTP errors/results are ignored when the original request is no longer active. This is a process-level cancellation, not instant asynchronous interruption of the ONNX pipeline. Existing work queue cancellation controls remain separate. Stop AI still pauses the model globally; use Stop reply for definitive per-chat cancellation.

**Validation:** 170 local Python tests passed when run as isolated modules under Xvfb (7 new cancellation tests). The single-process all-test run hit existing Tkinter asynchronous teardown crashes and is **not** claimed to have passed. Live Windows worker termination, automatic reload and subsequent successful reply have not been tested on the user's PC. The v18 ZIP was integrity-checked and packaged without model weights, state or user projects. GitHub is source-synchronized, with blob hashes checked against the ZIP. Do not claim Github CI is green without its actual status result.

Next real-world check: open two chats, start a long response in A, queue B, select A and press Stop reply (or Close chat); confirm A is cancelled, the old ONNX process exits, the new model reloads, and B progresses. Confirm closing/reopening chat retains the full transcript. If this fails, export diagnostics and inspect relevant events; do not silently increase retry limits or redesign the interface.


## v26 update — 22 November 2026 (Pass 5, first implementation)

v26 builds directly on the tested and committed v25 hierarchical roadmap without modifying the Windows executable, launcher, desktop layout, chat controls, local Qwen ONNX worker, JANUS/Sentinel, the 40-attempt maximum or explicit approval gates. Ten changed/new source, test and documentation files are committed in `DeepThorT/`.

- `deepthort_local/requirements_intelligence.py` creates stable, verbatim SHA-256-checked candidate requirement spans from the original fully indexed source. Explicit bullets/headings and unstructured prose are preserved; candidate-to-file links are review scope, never proof of correct implementation.
- Model file descriptions can optionally declare `depends-on: relative/path.ext`. Roadmap preparation rejects absent/self-referential/cyclic dependencies, orders files by a stable topological sort, and persists exact edges. Existing v25 roadmaps remain accessible. Missing or incorrect architecture cannot be inferred reliably from descriptions alone.
- `deepthort_local/planning_metrics.py` reports only numeric timing/progress from existing local rotating logs without reading raw prompts or responses. The prior 2026-11-22 16:27 diagnostics show historical median ~539.59s/model reply, 45 planner passes and only six adding files; not a controlled v26 speed benchmark.
- Stable heap-based dependency ordering improves CPU-side roadmap scalability. Live ONNX generation throughput and actual game-building correctness are unverified.
- `xvfb-run -a python -m unittest discover -s tests -q` passed **279 tests** locally. The 97-file ZIP archive passes integrity checks; the Windows executable and launcher are byte-identical to v25. Tkinter/SQLite cleanup warnings remain non-failing.
- Source package: `DeepThorT_Desktop_v26_Windows.zip`, docs: `PLANNING_INTELLIGENCE.md`. Preserve `state`, `models`, `reference`, `node_modules`, `cache` and project folders on install.

**Next priorities:** genuine semantic requirement reconciliation and acceptance criteria, interface/API dependency checks using actual project source and compiler evidence, measured Windows inference acceleration and an in-game Xenon PE acceptance test before Faction Command. Do not claim the model has built a verified game or proven semantic requirement coverage.
