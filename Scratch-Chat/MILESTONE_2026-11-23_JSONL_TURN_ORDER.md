# Scratch Chat milestone — 2026-11-23: JSONL turn-order validation

## Verified prior CI
GitHub Actions source-test run 45071733015 completed successfully at commit 1570c4640f97423c5e81a4dfc4af67dcaba5a844. The prior dialogue smoke run 45071719163 also completed successfully; a passing smoke run is not evidence of conversational capability.

## This change
- DeepThorT JSONL chat requests now require a user-first sequence (optional initial system), no later system messages, alternating user/assistant history, and a final user turn.
- Added regression coverage for orphan assistant, repeated user, late system, incomplete final assistant, and successful health recovery after errors.
- This is input validation, **not** a trained checkpoint or tool-use implementation.
- Commits: 592ea42d0a47d58ae776711359e7a21c1220e1fa and a1fc385dfb6f522007225c9b8ba6b930cd75bc04.

## Remaining gates
Dolly stays quarantined until provenance, licensing, privacy and contamination checks are approved. Original random-weight dialogue SFT, reproducible checkpoints, independent multi-turn quality, structured tool calls and actual checkpoint-backed DeepThorT subprocess acceptance remain incomplete. GitHub CPU is for bounded smoke tests, not large-scale pretraining. Free GPU options remain unallocated.

## Verification
The two source commits were accepted by GitHub; push CI must be checked separately before claiming green.
