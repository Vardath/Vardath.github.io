# DeepThorT — v29 handover (22 November 2026)

This handover accompanies the v29 Windows ZIP and preserves development continuity
if the GitHub repository has not been synchronized.

**Base:** Complete tested v28 Windows package, existing original desktop UI,
launcher, JANUS/Sentinel, Qwen ONNX worker, resource limits, SQLite state,
Capability Library, large-spec index and hierarchical milestone approvals.

**Implemented in v29:** `deepthort_local/engine_acceptance.py` (read-only,
bounded X4 extension XML, Mission Director, macro/component index checks; Godot
scene, resource and Android export preset inspection; Gradle manifest inspection).
`engine_acceptance_cli.py` is a standalone pure-audit entry point. The desktop
chooses the GUT unit runner when both its file and real tests exist, otherwise
editor-only Godot loading. X4 project verification prefers Python project tests
when present; otherwise uses the static auditor. No checks are run without the
existing approval confirmation. GUT must report nonzero complete passing tests;
zero-tests and parse errors fail. Approved milestone records now bind the hashes
of all engine files examined, even across earlier milestones. Changed artifacts
invalidate old verification. Explicit `verifies: REQ-N` claims can statically
recognize GUT and Kotlin/Java annotated tests; they do not prove coverage.

**Verification:** 351 tests passed across 44 isolated Xvfb Python test modules.
The single-process run ended with the preexisting X4 GUI async timing race; do
not claim the monolithic run passed. 108-file release ZIP passed CRC, and the
Windows executable, desktop launcher and ONNX worker were compared byte-for-byte
with v28. 40 final focused tests passed. No Windows/X4/Godot/Android live run.

**Artifacts:** `DeepThorT_Desktop_v29_Windows.zip` (full application source),
`DeepThorT_v29_SourceSync.json` (11 changed/additional files), and
`DeepThorT_v29_Git.patch` (apply to the v28 GitHub DeepThorT folder).

**GitHub:** Work repo is `Vardath/Vardath.github.io`, under `/DeepThorT`.
The v28 repository was already synchronized. **v29 was not yet committed** at
handover. The repository also has concurrent Scratch Chat updates: do not reset
or replace the main branch. Apply only v29 DeepThorT changes on top of the
current HEAD, review differences, commit then check CI before claiming green.

**Next:** Real machine acceptance: run audited Xenon PE extension against the
installed extracted vanilla X4 files, check actual macro/item connections,
Mission Director behavior and save compatibility; exercise Godot GUT and Android
export on installed SDK. Keep backend-specific checks separate from gameplay
verification and preserve approval before tool execution.
