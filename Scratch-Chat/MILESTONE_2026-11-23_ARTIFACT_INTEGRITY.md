# Scratch Chat pilot artifact integrity — 2026-11-23

Verified baseline: [GitHub Actions run 45093092918](https://github.com/Vardath/Vardath.github.io/actions/runs/45093092918), unit-tests job success. This run predates the changes here. The latest prior repository head was 549e7deb45c281b7b4c477013d06b670d5999d4d.

Changes committed:
- 59e8672e3f432cb5ed8876ba9659950c5555811c: pilot report now records streaming SHA-256 for manifest, train/validation/test split bytes, fitted tokenizer and resulting original-weight SFT checkpoint. This makes artifact substitution detectable when hashes are compared.
- 56869fe1d89c3c7bc023b5dd5fa8e3e9eda593e2: binary integrity and missing-artifact regression tests.
- 54154feaa957a082dec37682c0cf750bce2a53dd: include those tests in bounded push-triggered source CI.

The source workflow is configured for pushes affecting Scratch-Chat. A commit is not proof of a green workflow. No new dataset was approved, downloaded or trained in this pass. No checkpoint, conversational-quality metric or DeepThorT application acceptance is claimed. Dolly remains quarantined.

Next: verify latest CI; independently review source rights/privacy and decontamination; produce approved corpus with immutable split hashes; train original random-initialized weights and retain hash-verified checkpoints; run real JSONL subprocess and independent held-out multi-turn/tool-use evaluations. GitHub CPU is only for bounded pilots; free GPU allocation is not assumed.
