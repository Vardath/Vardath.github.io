# Scratch Chat milestone — 2026-11-22 (capacity CLI)

Verified GitHub Actions run 44986884318: unit-tests job completed successfully, including source compilation and dialogue/protocol tests. This result predates the changes below.

Found a concrete integration defect: dialogue_sft_train.run() accepted architecture and seed controls, but the module's command-line parser did not expose them. Corrected CLI flags for width, layers, heads, context size, learning rate, and seed; added a subprocess CLI contract test and corrected invocation to python -m capability.dialogue_sft_train.

Commits: bec405f629db4a573e3d19b586aa5e012a52587c, d851bf3ac09a68c5b96881a8f9e7c1e463623156, e4334bc19c7b7376a5cca306c2ecb2489d0f59b7.

Pending: confirm the new CI run, obtain externally sourced dialogue records with verified revision/license/attribution, record provenance and permitted use, decontaminate split boundaries, execute bounded SFT, retain checkpoint and reproducibility manifest, evaluate multi-turn and tool-use independently, and run the actual DeepThorT JSONL provider. No external corpus acquired or model trained in this pass. GitHub Actions CPU is only for bounded pilot tests; free GPU capacity has not been provisioned or verified. No conversational acceptance claimed.
