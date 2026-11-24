# DeepThorT v47 test and release evidence

- `tests/test_legacy_and_onnx_recovery_v47.py`: cross-request full-input response reuse, project/chat/attachment isolation, adjacency safety, invalid legacy draft rejection, exact large-document section inheritance, unsafe path exclusion, bounded transient transport retries and idle/busy model health gates.
- Existing v16 interrupted inference and v46 planning-continuation tests rerun. v47 neither changes the 40-pass budget nor the ONNX inference server SHA.
- Complete Linux/Xvfb isolated test suite, syntax compilation, per-source SHA-256 checksum gate and release overlay packaging are CI release requirements.
- Hardware and model exit-cause diagnosis requires real Windows/Event Viewer data; WinError 10054 is not a root-cause verdict.
