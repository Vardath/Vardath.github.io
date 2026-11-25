# DeepThorT v36 test evidence — 22 November 2026

- Python `compileall`: passed.
- Focused v36 + v33/v34 regression tests under Xvfb: **26 tests passed** (6 new online catalog tests and 20 existing generated-script/approval tests).
- The isolated v34 `tests.test_janus_sentinel` module: **11 tests passed** in a standalone virtual display.
- Full v35 baseline suite: 430 tests passed in 53 isolated modules (recorded in `TEST_RESULTS_V35.md`/`.json`).
- A complete sequential local v36 regression attempt did not finish: the local harness stalled after 24 passing modules. This is an *incomplete test run*, not a passing v36 full suite and not an observed source-test failure. All observed modules before the stall passed. GitHub Actions CI must be checked independently after pushing v36, and any failure investigated before declaring a green release.
- Native Windows and real network winget discovery, live model/planning speed, Blender/Godot/X4/Android execution remain unverified. The button strictly searches, and does not download or install software.
