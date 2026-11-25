# DeepThorT v51 verification

The v51 source changes require full Python syntax and isolated Xvfb GUI regressions plus Node `--check` of the primary/council server. Exact changed-file SHA-256 digests are recorded in `V51_SOURCE_SHA256.json` and verified by GitHub Actions before release packaging. Check all test modules, not merely the new focused tests. The original `inference_worker.mjs` and ONNX weights remain unchanged; the server coordinator is changed intentionally to add the second role and separate diagnostic log.

**Local regression:** 635 test cases across 77 isolated modules were run. The first sweep identified two missing tooltip mappings; those were added and `tests.test_ui_help_v35` was rerun successfully (7 tests). Additional focused v51 GUI and planning tests passed. Complete final GitHub Actions verification is separately required before shipping.

Focused local tests: inbox persistence, exact project/chat scope and deduplicated handoff, safe cancellation, council JSON schema and independent review, 40 GB RAM / 30% commit budget, unapproved planning checkpoint injection, real Tk message intake while a primary conversation is running. Existing JANUS, X4 repair, hierarchical planning and GUI staged-build regressions also ran green.

**Still untested on this CI system:** Actual Windows Job Object 30% CPU limit, original GUI executable bootstrap, memory-mapped ONNX replicas, concurrent model quality and performance, foreground gaming impact, real X4 PE extension creation and end-to-end playtest. Do not claim Linux CI proves any of these.
