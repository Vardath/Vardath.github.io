# DeepThorT — development handover and next steps (v35, 22 November 2026)

**Baseline:** `DeepThorT_Desktop_v34_Windows.zip` (134 files, ZIP CRC clean). This version adds contextual UI help and offline documentation; it does not replace the local Qwen runtime, JANUS/Sentinel topology or approval gates. Install to `D:\deepthort` without deleting `state`, `models`, `reference`, `cache`, `node_modules`, custom projects or existing launcher data. Back up `state` before upgrade. Read `USER_GUIDE.html` in the install root (F1 in the desktop).

## Completed in v35

- `deepthort_local/ui_help.py`: passive, delayed, non-focus-grabbing Tk hover tooltips on existing buttons, controls, main text areas, work/process trees and notebook tabs; no network or model activity. Existing UI retained; added `User guide` top button and F1 shortcut.
- `USER_GUIDE.html`: self-contained illustrated offline guide with a schematic layout, all eight tabs, permission flows, creation categories, tool acquisition and troubleshooting. Schematic illustration is *not* a live screenshot.
- `deepthort_local/tool_sources.py`: fixed, reviewed publisher URLs for existing `INSTALL_CATALOG` entries, with no arbitrary model-supplied download URLs; optional `Find official tool page…` asks before opening a browser. This is informational only, not a download or installation.
- Expanded read-only software inventory/advisory associations for documents/books, audio/video, graphics and CAD. Only original eight fixed Windows Package Manager package IDs remain eligible for an approved install.
- Tests in `tests/test_ui_help_v35.py` cover catalog source constraints, advisory categories and GUI help behavior under a virtual display. **Full isolated regression: 430 tests passed across 53 modules**; see `TEST_RESULTS_V35.md`/`.json`.

## Ordered, acceptance-gated development backlog

### P0 — Windows acceptance of v35, and rigorous GUI usability

1. Test actual Windows startup and 20%-resource/game priority with installed ONNX model; verify F1 guide and all tab/button tooltips at 1320×860 and 1138×765, including keyboard/screen-reader behavior. Fix clipping if necessary without removing original chat controls.
2. Verify source/ZIP parity, SHA-256 and GitHub CI status; fix any real failing workflows. Tkinter combined-process teardown remains an existing limitation even if isolated modules pass.
3. Run a small disposable project through local Qwen -> plan -> human approval -> source write -> authorized test -> persisted evidence -> restart. Collect diagnostics and observed runtimes.
4. If v35 tests are green, start next pass from v35, not from earlier source; do not overwrite unrelated GitHub `Scratch-Chat` updates.

### P1 — Safe *online* software/tool discovery and consent-controlled install (v36+)

1. Build a **capability resolver** from actual user requirements (artifact type, target OS, file formats, licenses, required tools, compatible versions and installed tool identity). Record a candidate dependency graph rather than keyword match only. Include resource needs (available disk/RAM and games running).
2. Add **explicit online-search consent** scoped to query/project, with independent **read-only research** using trusted upstream repositories, official documentation and package-manager metadata. Store source URL, version, publisher, retrieval time, license and evidence. Treat search results/pages as hostile data; never execute instructions from them. No browser takeover or unapproved network access.
3. Compare discovered packages to existing software. Validate package IDs and publisher identity against signed catalog data, official domains and independent provenance; disallow sponsored/mirrored/shortened/untrusted downloads as automatic installer candidates. Reject insecure URLs, redirects to unknown origins and mutable unpinned installers.
4. Present a detailed **download consent** review (publisher, exact URL, version, size, expected checksum/signature, destination, network use and potential data handling) before fetching. Download to a quarantined temporary directory with hard size/time/disk quotas, rate limiting and cancellation; verify SHA-256 when an independent trusted digest exists, Authenticode signature where applicable, and content type. A checksum from the same untrusted source is not strong provenance evidence. Unsigned/unverifiable installers need explicit exception or a blocked state.
5. Show a separate **installation authorization** with exact executable, arguments, elevation requirements, scope, expected writes/network effects and uninstall/rollback plan. Never silently elevate, run shell snippets from search results, or automatically accept arbitrary licensing terms. Enforce game priority and measured CPU/RAM/disk budgets; record post-install executable and capability probe, then source/evidence hashes.
6. Preserve reviewable local receipts and recovery: failed downloads/installs must not be marked successful; detect stale packages after updates, resume only if the content identity remains valid and do not repeat elevated actions after crash without approval. Test on a Windows VM or disposable environment before enabling production installers.

### P2 — Genuine app use, not merely executable detection

- Create versioned adapters for **CLI and GUI-only applications**. Primary targets: Blender (background `.py` API and tested `.blend`/GLB output), Godot (GDScript, scenes, editor, GUT/Android export), X4/Egosoft tools (vanilla assets/macros/MD and in-game verification), Android SDK/Gradle/ADB, Krita/GIMP/Inkscape, LibreOffice/Pandoc, FFmpeg/Audacity, FreeCAD, browsers and test frameworks.
- Use official per-version API docs, local executable `--help`, example projects and observed results; cache only attributed, hash-verified evidence. Model-authored scripts must be built in small verified stages, with full-source diffs, lint/parse tests, small safe integration tests, and explicit action approvals.
- Add permissioned GUI operator with application/window identity, screenshots, element discovery, focus validation, confirmation before edits/sends, unexpected-modal handling and automatic stop on ambiguous targets. Never treat hallucinated coordinates as verified controls.
- Add sandboxed process isolation (Windows low-privilege token, Job Objects, restricted filesystem/network and temporary workspace), rollback, reproducible toolchain snapshots, and tests for hostile project files.

### P3 — Project breadth: what DeepThorT should be able to deliver

| Work category | Examples | Evidence required |
|---|---|---|
| Games/mods | X4, RimWorld, 2D/3D games, mobile games, assets, AI behaviors | Real engine launch, schema/asset checks, automated behavior tests and playable build |
| Mobile/desktop/web | Android APK, Windows app, website, extension, API/service | Build output, installation, smoke tests, cross-platform test matrix |
| Literature/research | Book/manuscript, encyclopedia, citations, EPUB/PDF | Complete source provenance, structure/repetition checks, document render review |
| Audio/video | Music, podcasts, voiceover, short films, motion graphics | Real playable exports, waveform/codec inspection, content and rights checks |
| Art/design | Logo/vector, textures, 3D models, animation, CAD, 3D print | Image/model previews, geometry/manifold/unit checks, compatible exported files |
| Data/science | Analysis, dashboards, simulation, financial reports, notebooks | Reproducible inputs/calculations, data validation, uncertainty and visual checks |
| Automation/business | Data workflows, reports, documents, integrations | Dry run, scoped credentials, action logs, idempotence, rollback and user signoff |

### P4 — Long-horizon autonomy, compliance and model efficiency

1. Establish durable subproject graphs, explicit requirement-to-artifact-to-test coverage, semantic conflict review, change impact analysis, reversible Git checkpoints, and independent completion criteria; never silently edit the user's design.
2. Model ability assessment: benchmark offline Qwen context/prefill, tokens/sec, JSON validity, long-plan failure rates and success against small verified tasks. Maintain true local-only operation, no paid/cloud fallbacks, unless user changes the requirement.
3. Add a principled task prioritizer and autonomous *approved* work queue, with watchdog-based stall detection, bounded retries and restart continuity; zero-progress loops must stop with a diagnosis. Preserve game priority and the existing supervisor roles.
4. Create engine-specific acceptance harnesses and manual quality-review protocols. Cross-check deliverables independently: code compiling or XML parsing is insufficient proof of a working game/mod.
5. Add an offline searchable help assistant grounded in versioned docs, keyboard navigation, per-button "why disabled?" explanations, actionable error messages and user-configurable tooltip delay/accessibility.

## Open limitations (do not claim complete)

- v35 does **not** discover arbitrary tools on the internet, download vendor installers directly or automatically install apps based on a model proposal. Only the existing fixed winget installation catalog can install after explicit user review.
- v35 does **not** give Qwen a larger ONNX inference context or improve generation speed. Large specification input storage is separate from model context.
- Scripts approved for execution are **not sandboxed**. They can access resources available to the user; inspection alone is not a malware guarantee.
- Real Windows Blender/Godot/X4/Android end-to-end acceptance is not yet proven. Do not claim games/mods complete based on synthetic tests or static XML alone.
- Combined-process Tkinter teardown has an existing race; module-isolated test execution is the documented workaround, not a claimed production fix.
- Existing JANUS/Sentinel core behavior and model/resource architecture are retained; v35 changes are UI help, a curated publisher lookup and advisory tool coverage.

## Next-run minimal report

After installing v35, report (a) whether F1/hover help works in each tab, (b) whether selecting an official tool page opens the expected URL without an install, (c) any failed known-tool installation with the exact installer output, (d) whether real Windows Qwen replies/plan approvals execute and pass one small test, and (e) a fresh **Export diagnostics** ZIP. Avoid changing production X4 mods as a first installer test.
