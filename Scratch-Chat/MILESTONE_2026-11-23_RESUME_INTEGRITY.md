# Scratch Chat checkpoint resume hardening — 2026-11-23 16:44 Brisbane

Verified GitHub Actions source-test run [45121940179](https://github.com/Vardath/Vardath.github.io/actions/runs/45121940179): unit-tests job completed successfully, including dialogue/protocol tests and Python compilation. This baseline predates this change.

Commits:
- 39b91eccac7b05bb18e00c719cd5478e0db1f969: refuse invalid saved SFT step and RNG metadata.
- eae4a7171b5a4c8a4b632562dadc98de5c866347: add corrupt-checkpoint regression cases.
- 5bc86eedd99326c2c68c9120e77cf8e17e6fd0e2: validate metadata before restoring model/optimizer/RNG state.

The new regression includes negative/zero/string/boolean steps and absent or malformed RNG. Push CI is triggered by these commits but its result is not yet verified. No checkpoint was trained; no conversation improvement is claimed.

Outstanding: licensed, independently privacy-reviewed dialogue corpus; decontaminated immutable splits; meaningful original-weight training with reproducible checkpoints; independent held-out multi-turn and tool-use evaluations; actual DeepThorT JSONL integration acceptance. Dolly remains quarantined. GitHub CPU remains limited to bounded tests and pilots; no free GPU allocation is claimed. No Shakespeare-only run was performed.
