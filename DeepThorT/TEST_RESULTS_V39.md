# DeepThorT v39 — test evidence (23 November 2026)

**Local isolated regression: PASS, 473 tests across 58 modules.**
Command: `python regression_cli.py --timeout 35 --report TEST_RESULTS_V39.json`.
The complete generated report records the module count and individual module states.
All modules reported pass. The older Tkinter callback-on-destroy warnings may still
appear inside isolated GUI tests; they are not proof of production GUI correctness.

New `tests/test_software_autonomy_v39.py` specifically covers 13 cases:
standing policy defaults and persistent opt-out, exact approved WinGet IDs,
allowed install/upgrade commands, denial of shell/hash/elevation-bypass flags,
audit tamper rejection, dependency selection limits, retry throttling, game/
queue/disk/process safeguards, saving audit before process start, recording
`completed_unverified`, no redundant manual catalog/search confirmation, and
accurate click-based consent for a recently inspected package.

Test **limitations**: Linux virtual X display, fake WinGet executable paths,
mocked process runs and synthetic catalog metadata. Actual Windows installs,
UAC prompts, installer signatures, package-manager output, PATH discovery,
post-install capability and full build/game acceptance are NOT verified.

GitHub Actions source tests: pending source synchronization and independent run.
The packaged `inference_server.mjs` and `DeepThorT.exe` are required to have
identical SHA-256 hashes to v38. No cloud inference, Scratch Chat or model
replacement is included.
