# DeepThorT v40 regression evidence — 23 November 2026

**Verified GitHub Actions green:** run
https://github.com/Vardath/Vardath.github.io/actions/runs/45076618480
on feature commit `069b5316b25602c7bb05d15048cb203d6e851710`.
The regression workflow compiled all DeepThorT Python source files and ran
**486 unittest cases across 59 isolated modules**, with every module passing.
The new `test_project_authority_v40.py` contributed 13 tests. The old GUI
smoke test was updated to exercise the v40 job-bound authority and fixed
automatic verification rather than a legacy in-memory auto-save test hook.

**Source-overlay packaging:** the same successful run created and CRC-tested
`DeepThorT_v40_SourceOverlay.zip`, 828,536 bytes,
SHA-256 `aff872148494d745d21d5e97c372f2052f585d6f7e874907a530e2a437d4badb`,
containing 170 tracked source/document/assets files plus a machine-readable
manifest. It was uploaded as the GitHub Actions artifact
`DeepThorT-v40-source-overlay`, artifact ID `14775756021`.
This is NOT a standalone binary/ONNX/model installer. It is source to overlay
an existing v39 installation while preserving `DeepThorT.exe`, `models`,
`state`, `node_modules`, `reference`, `cache`, and projects.

**Failures corrected before the successful run:** the first branch build
caught a desktop initialization indentation error, then the regression run
found two test issues (old GUI auto-save hook and a missing colon in the new
backup-test expectation). Both were corrected, without weakening production
file or test approval boundaries.

**Evidence limit:** CI runs Linux/Python with an Xvfb virtual display and
mocked Windows tools. It does not validate native WinGet/UAC, Windows Job
Object behavior, real ONNX inference, installation effects, Windows GUI tests,
X4 gameplay, or an Android export. The fixed test command may execute project
code with normal user rights; it is NOT a sandbox. Passing tests do not
establish complete autonomous game creation.

**Later CI changes:** a small serial gate ensures auto software installations
and fixed project tests are not simultaneously launched by their two GUI
timers. Re-run the same workflow after this gate and report the new run
separately. The package-manifest SHA above specifically identifies the tested
first v40 source-overlay artifact, not future overlay files.
