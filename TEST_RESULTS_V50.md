# DeepThorT v50 test report — 23 November 2026

- New local test module `tests/test_neural_council_and_x4_refs_v50.py`: five tests passed. Covers hash-bound read-only reference selection, symlink/traversal protection, cached separate JANUS and Sentinel ONNX-role responses, stalled X4 correction to successful validated roadmap, and desktop reference preview/hide without disk changes.
- Existing focused GUI and X4 regressions passed in Xvfb, including v46 project-file exclusions and v49 progress logic.
- Full isolated GitHub Actions suite and packaged artifact are the release gate. Update the final release evidence after the workflow completes.
- Regression tests simulate ONNX model replies. No real Windows model-quality benchmark, original Xenon PE in-game validation, automatic Windows folder discovery acceptance or historical Llama comparison is claimed.
