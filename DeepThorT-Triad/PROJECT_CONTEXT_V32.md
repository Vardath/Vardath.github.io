# DeepThorT v32 development handover — 22 November 2026

Previous v29/v30/v31 sources are retained; v30/v31 GitHub source sync was not confirmed. v32 was built from the full v31 Windows source tree and must be used as the packaging baseline (do not overwrite it with older GitHub files).

New files: `deepthort_local/tool_acquisition.py`, `tests/test_tool_acquisition_v32.py`, `tests/test_tool_acquisition_integration_v32.py`, `TOOL_ACQUISITION.md`.
Modified: `desktop_app.py`, `README.md`, `START HERE.txt`.

Workflow: real executable discovery -> explicit user-approved fixed CLI help JANUS action -> bounded help/doc ingestion -> local Qwen recipe proposal (unverified candidate) -> GUI preview -> explicit command approval -> actual supervised JANUS process -> artifact and process evidence reconciliation -> limited retrieval for future plans. No generic GUI control or cloud fallback. See TOOL_ACQUISITION.md.

Check provenance: executable stat identity, action approval_source, cwd, exact argv, success exit, process-log digest and changed artifact digest. Do not claim game behavior or output quality tested. Avoid calling a model proposal a verified skill.

Tests: isolated test modules should all pass; combined Tkinter teardown race existed in v31. Preserve full installation state and Windows launcher. Next steps include tool-specific adapters and API/GUI workflows, stronger artifact validation, bounded command timeouts, source-script content fingerprints at approval, and actual Blender/Godot/X4 Windows tests.
