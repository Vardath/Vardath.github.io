# DeepThorT — verified project context and continuity handover
Last reviewed: 21 November 2026 (Australia/Brisbane).

## Read before editing
DeepThorT is the user's **local Windows autonomous project developer**, descended from the JANUS/Mindcore work. It is NOT merely an X4 mod generator, and the standalone **Vardath Scratch Chat** language-model project is separate. The Xenon PE assignment is a small but technically demanding acceptance test before the larger *Faction Command* Android game.

**Do not rebuild, rename, redesign, or alter working code based on a summary.** Read the original v10.9 source, the current v12 files, the diagnostic export, and the specific screenshot/log before any changes. Audit the actual call paths, UI geometry and tests. Historical assistant assertions are not proof.

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
- **v12 (current packaged build):** Removes the extra banner, displays reply activity in the original status line, and adjusts prompt-editor height to keep original buttons accessible. **No user Windows screenshot verifying v12 yet.** Do not confuse local GUI tests with user acceptance.

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
