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
