# DeepThorT v31 — actionable X4 and engine diagnostic evidence

## Diagnosis: user export, 22 November 2026, 21:28 Brisbane

The exported `summary.json` showed a healthy, idle Qwen worker (not actively generating a plan), no pending conversations, no approved work, and a selected project called `vardath_faction_camouflage`. The desktop log recorded `X4 source inspection: reference candidates found`. However, v30 did not place its `self.x4_report` or `Scan this computer` readiness findings into the diagnostic ZIP. Thus the export cannot establish which exact PE macro, ship component connection tags, weapon/turret IDs or extracted game indexes were available. This is missing diagnostic evidence, **not proof that the X4 files were absent**.

The `desktop_init` log claimed version `27` even in v30 source. v31 corrects the recording version. The `desktop_app.py` byte count in the user's export (180,267) matched the packaged v30 file, so the version string was stale metadata rather than proof of a v27 application.

## Implemented

- `deepthort_local/diagnostic_evidence.py` produces bounded, privacy-reduced summaries of completed X4 source inspection and engine readiness scans. It includes actual parsed macro/component IDs, their relative source filenames and SHA prefixes, PE slot tags, evidence status, candidate counts and exact blocking reasons when available.
- Existing `Inspect X4 sources` and automatic X4 preflight handlers persist bounded summaries in `state/last-x4-inspection.json` and emit structured log events. The existing `Scan this computer` handler persists the selected project's engine-readiness summary in `state/last-engine-inventory.json` and logs its evidence level.
- **Export diagnostics** adds `application_state.x4_source_inspection` and `application_state.engine_readiness_scan` to `summary.json`. A stored summary is used after restart only when its project fingerprint matches the selected project; otherwise the export clearly says that inspection is unavailable.
- Hostnames, complete machine inventory, absolute Windows paths, source document text, model outputs, chat prompts, environment values and model weights are not added to the new summaries. Only path basenames, stable SHA-256 fingerprints and bounded X4 identifiers are present. Existing `computer-inventory.json` remains local and is not included in the export.
- `desktop_init` now records release version `31`.

## Verification and limitations

Five additional unit tests cover bounded X4 source evidence, privacy, empty scans, persistent snapshots, source/project scoping and the actual diagnostic ZIP. **373 tests passed across 46 isolated modules.** The old single-process Tkinter suite still aborts on teardown and must not be called green. The Windows ONNX worker and game were not executed here.

This change **does not** improve planning intelligence, produce a Xenon PE mod, verify turret compatibility, or prove gameplay. The new evidence allows a follow-up to identify the actual blocker instead of sending the user through another 40-pass run without sufficient source data.

## Windows follow-up

1. Close DeepThorT; extract v31 into `D:\deepthort`, preserving `models`, `state`, `node_modules`, `cache`, `reference` and project folders.
2. Select the existing X4 extension project (not an unrelated folder) and use **Computer & Tools > Scan this computer** and **Inspect X4 sources**.
3. Export diagnostics. The ZIP's `summary.json` should contain both evidence fields. A `ready_for_planning` flag refers to inspected candidates only, not a verified X4 mod.
