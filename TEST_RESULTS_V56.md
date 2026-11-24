# DeepThorT v56 — visible JANUS instruction retry

Baseline: exact locally verified v55 source overlay. This pass changes the JANUS instruction-inbox UI and a single atomic, project-scoped retry helper; no model, Windows launcher, ONNX JavaScript or shared CPU/committed-memory settings have changed.

**Local outcome: 666 regressions across 82 independent modules, zero failures.** All modules were executed under Xvfb as separate Python `unittest` processes. The 82 modules were checked in four groups to avoid test-runner execution time limits. `python -m compileall` and `node --check` succeeded. This is local verification, not GitHub Actions or a real Windows-DPI field test.

New tests: one-click latest failure retry is atomic and project-scoped; the newest failed neural instruction is selected over an older failure; staged/reviewable advice is not reinterpreted; invalid projects are rejected; Tk JANUS tab includes the distinct retry, the inbox opens with an already-selected row and the retry control visible; the inbox button changes only the durable instruction to pending; the main-tab button does not create approved jobs or change the main chat.

A failed neural instruction from older versions can be queued for read-only interpretation. A subsequent successful JANUS/Sentinel translation must still be shown by a Windows acceptance test. The known Xenon PE roadmap's nine X4 requirements have not been solved in this pass; no game files have been built or playtested.
