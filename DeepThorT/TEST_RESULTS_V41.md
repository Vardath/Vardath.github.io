# DeepThorT v41 testing evidence — 23 November 2026

## Local focused testing

- `python -m unittest -q tests.test_development_cycle_v41`:
  **17** tests passed (SQLite durability, exact grant constraints, plan binding,
  retries, no replay after crashes, bounded/redacted diagnostics, prompt and
  answer validation, saved backups, source fingerprint checks, success/failure).
- `xvfb-run -a python -m unittest -q tests.test_development_cycle_gui_v41`:
  **1** integrated GUI test passed. Uses a fake Qwen response seam; a real
  `unittest` subprocess fails, the approved file is backed up and rewritten,
  and a second real subprocess passes. Verifies 2 tests/1 repair in SQLite.
- Existing GUI source-generation smoke test also passes with these additions.
- `python -m compileall -q .` passed for source. Local standalone runs use
  Linux/Python 3.13 and are *not* Windows hardware acceptance.

## GitHub Actions

Validate this exact v41 source commit through `.github/workflows/deepthort-tests.yml`:
1. Python compile under Ubuntu/Python 3.11.
2. Isolated per-module `xvfb-run` regression suite.
3. Release source overlay only if all tests pass, with SHA-256 manifest,
   original ONNX server checksum pin and ZIP CRC check.
4. Download the GitHub Actions artifact for the **green** commit, not a
   provisional branch version. Check its SHA256 before installation.

The exact CI run identifier and package SHA256 are reported separately when
confirmed. Do not treat an unstarted or pending CI run as green.

## Not claimed

- No native Windows ONNX loading/speed or 20% CPU/RAM acceptance test.
- No real WinGet/UAC/installer/code-signing checks.
- No real game engine, Android emulator or X4 gameplay acceptance.
- A successful local simulated-model integration does NOT demonstrate that
  Qwen independently generated a correct repair without guidance.
- No full general-purpose autonomous project creation is claimed.
